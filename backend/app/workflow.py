import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from . import data, store, llm, odoo


class Conflict(ValueError):
    pass


def snapshot():
    value=data.fixture()
    source=odoo.adapter()
    value['services']=source.list_services()
    value['customers']=source.list_customers()
    value['projects']=source.list_projects()
    value['opportunities']=source.list_opportunities()
    with store.db() as c:
        row=c.execute("SELECT value FROM settings WHERE key='target_profile'").fetchone()
    if row:
        value['target_profile']=row['value']
    value.update({'fetched_at':data.now(),'data_mode':source.mode,'target':source.target})
    value['facts']=data.facts(value)
    return value


def run_analysis(mode):
    snap=snapshot()
    result,meta=llm.analyze(snap,mode)
    run={'id':uuid.uuid4().hex,'created_at':data.now(),'mode':mode,'snapshot':snap,**result,'meta':meta}
    with store.db(write=True) as c:
        c.execute('INSERT INTO runs VALUES(?,?,?)',(run['id'],run['created_at'],store.encode(run)))
    return run


def get_run(run_id):
    with store.db() as c:
        row=c.execute('SELECT payload FROM runs WHERE id=?',(run_id,)).fetchone()
    if not row:
        raise KeyError('Analyysiä ei löytynyt.')
    return json.loads(row['payload'])


def get_card(card_id, conn=None):
    if conn is None:
        with store.db() as c:
            return get_card(card_id,c)
    row=conn.execute('SELECT payload FROM cards WHERE id=?',(card_id,)).fetchone()
    if not row:
        raise KeyError('Palvelukorttia ei löytynyt.')
    return json.loads(row['payload'])


def save_card(c,card):
    c.execute('INSERT OR REPLACE INTO cards VALUES(?,?)',(card['id'],store.encode(card)))
    c.execute('INSERT OR REPLACE INTO card_history VALUES(?,?,?)',(card['id'],card['version'],store.encode(card)))


def create_card(run_id,idea_id):
    run=get_run(run_id)
    idea=next((i for i in run['ideas'] if i['id']==idea_id),None)
    if not idea:
        raise KeyError('Ideaa ei löytynyt.')
    content,meta=llm.generate_card(idea,run['snapshot'],run['mode'])
    card={**content.model_dump(),'id':uuid.uuid4().hex,'run_id':run_id,'idea_id':idea_id,
          'version':1,'state':'draft','approved_version':None,'hours':None,'hourly_rate':None,
          'price':None,'mode':run['mode'],'created_at':data.now(),'export':None,'generation':meta}
    with store.db(write=True) as c:
        save_card(c,card)
    return card


def check_version(card,version):
    if card['version']!=version:
        raise Conflict('Kortti on muuttunut toisessa näkymässä. Lataa kortti uudelleen.')


def check_no_pending(c,card_id):
    row=c.execute("SELECT status FROM exports WHERE card_id=? AND status IN ('pending','uncertain')",(card_id,)).fetchone()
    if row:
        raise Conflict('Viennin tulos on kesken tai epäselvä. Selvitä vienti ensin vientipainikkeella.')


def edit_card(card_id,edit):
    with store.db(write=True) as c:
        card=get_card(card_id,c)
        check_version(card,edit.expected_version)
        check_no_pending(c,card_id)
        if card['state']=='exported':
            raise Conflict('Viety versio on lukittu. Luo ideasta uusi luonnos.')
        data.validate_sources(edit.source_ids,get_run(card['run_id'])['snapshot'])
        card.update(edit.model_dump(mode='json',exclude={'expected_version'}))
        price=None
        if edit.hours is not None and edit.hourly_rate is not None:
            price=str((edit.hours*edit.hourly_rate).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
        card.update(version=card['version']+1,state='draft',approved_version=None,price=price)
        save_card(c,card)
    return card


def approve(card_id,version):
    with store.db(write=True) as c:
        card=get_card(card_id,c)
        check_version(card,version)
        check_no_pending(c,card_id)
        if card['state']=='exported':
            raise Conflict('Kortti on jo viety.')
        if card['price'] is None or Decimal(card['price'])<=0 or not card['source_ids']:
            raise ValueError('Täytä positiivinen työmäärä ja tuntihinta sekä lähteet ennen hyväksyntää.')
        if not all(card[k].strip() for k in ('name','description','deliverables','exclusions')):
            raise ValueError('Täytä nimi, kuvaus, toimitussisältö ja rajaukset.')
        card.update(state='approved',approved_version=version)
        save_card(c,card)
    return card


def export_card(card_id,version,source=None):
    source=source or odoo.adapter()
    key=f'{source.target}:{card_id}:{version}'
    code=f'DEMO-SVC-{card_id[:12]}-V{version}'
    with store.db(write=True) as c:
        card=get_card(card_id,c)
        check_version(card,version)
        if card['approved_version']!=version or card['state'] not in ('approved','exported'):
            raise Conflict('Hyväksy nykyinen versio ennen vientiä.')
        row=c.execute('SELECT * FROM exports WHERE export_key=?',(key,)).fetchone()
        if card['state']=='exported':
            if not row or row['status']!='exported':
                raise Conflict('Kortti vietiin eri kohteeseen; luo uusi luonnos.')
            return card
        if row and row['status']=='pending':
            raise Conflict('Vienti on käynnissä. Odota sen päättymistä.')
        uncertain=bool(row and row['status']=='uncertain')
        c.execute('INSERT OR REPLACE INTO exports VALUES(?,?,?,?,NULL,NULL)',(key,card_id,version,'pending'))
    attempted_create=False
    try:
        identifier=source.find_service(code)
        if identifier is None:
            if uncertain:
                raise Conflict('Aiemman viennin tulos jäi epäselväksi eikä tuotetta löytynyt. Tarkista Odoo ennen uutta luontia; automaattinen luonti on estetty.')
            attempted_create=True
            identifier=source.create_service(code,card)
        result={'id':identifier,'url':source.product_url(identifier),'code':code,'target':source.target,
                'mode':source.mode,'exported_at':data.now()}
        with store.db(write=True) as c:
            card=get_card(card_id,c)
            card.update(state='exported',export=result)
            save_card(c,card)
            c.execute("UPDATE exports SET status='exported',remote_id=? WHERE export_key=?",(identifier,key))
        return card
    except Exception:
        with store.db(write=True) as c:
            c.execute('UPDATE exports SET status=?,error=? WHERE export_key=?',
                      ('uncertain' if uncertain or attempted_create else 'retryable','Vienti epäonnistui; tulos tarkistetaan uusintayrityksessä.',key))
        raise


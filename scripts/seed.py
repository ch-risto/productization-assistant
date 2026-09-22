"""Idempotent seed. Run from project root; --odoo opts into local Odoo writes."""
import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
load_dotenv(ROOT/'.env')
from app import store
from app.data import fixture
from app.odoo import OdooAdapter


def seed_local(update_profile=False):
    value=fixture()
    store.init()
    with store.db(write=True) as c:
        statement = 'INSERT OR REPLACE' if update_profile else 'INSERT OR IGNORE'
        c.execute(statement + ' INTO settings VALUES(?,?)',('target_profile',value['target_profile']))
    return value


def seed_odoo(update_profile=False):
    value=seed_local(update_profile)
    source=OdooAdapter()
    source.connect()
    def upsert(source_id,model,values,domain):
        fields=source.inspect(model)
        if set(values)-set(fields):
            raise ValueError(f'Missing fields for {model}: {set(values)-set(fields)}')
        # Hold a local write lock to serialize this project's seed processes.
        with store.db(write=True) as c:
            row=c.execute('SELECT remote_id FROM seed_map WHERE target=? AND source_id=?',(source.target,source_id)).fetchone()
            found=[]
            if row:
                found=source.read(model,[['id','=',row['remote_id']]],['id'])
            if not found:
                found=source.read(model,domain,['id'])
            if len(found)>1:
                raise ValueError(f'Duplicate seed record: {source_id}')
            if found:
                identifier=found[0]['id']
                source.execute(model,'write',[[identifier],values])
            else:
                identifier=source.execute(model,'create',[values])
            c.execute('INSERT OR REPLACE INTO seed_map VALUES(?,?,?)',(source.target,source_id,identifier))
        return identifier
    customers={}
    for item in value['customers']:
        code='DEMO-'+item['source_id']
        customers[item['source_id']]=upsert(item['source_id'],'res.partner',{'name':item['name'],'is_company':True,'ref':code},[['ref','=',code]])
    for item in value['services']:
        code='DEMO-'+item['source_id']
        upsert(item['source_id'],'product.template',{'name':item['name'],'type':'service','default_code':code,'description_sale':item['description'],'list_price':item['price']},[['default_code','=',code]])
    for group,model in [('projects','project.project'),('opportunities','crm.lead')]:
        for item in value[group]:
            name=f"[DEMO-{item['source_id']}] {item['name']}"
            values={'name':name,'partner_id':customers[item['customer_id']],
                    'description':item.get('notes') or item.get('reason') or 'Häviösyy tuntematon (synteettinen aineisto).'}
            if group=='opportunities':
                values['type']='opportunity'
                # Outcome labels remain research annotations; no CRM automation triggered.
            upsert(item['source_id'],model,values,[['name','=',name]])
    print('Odoo-demoaineisto alustettu; tutkimushavainnot ja myyntitulokset paikallisia annotaatioita.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--odoo',action='store_true')
    parser.add_argument('--update-profile', action='store_true', help='Korvaa tallennettu tavoiteasiakas aineiston profiililla')
    args=parser.parse_args()
    if args.odoo:
        seed_odoo(args.update_profile)
    else:
        seed_local(args.update_profile)
        print('Paikallinen aineisto validoitu. Odoohon ei kirjoitettu.')


"""Previewed, version-bound creation of catalog products. No order confirmation."""
import hashlib
import json
from html import escape
from html.parser import HTMLParser
from uuid import uuid4

from fastapi import APIRouter

from . import catalog, odoo, store
from .schemas import Strict, VersionRequest
from .workflow import Conflict


class ExportRequest(VersionRequest):
    plan_id: str


def html_text(value):
    class Text(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
    parser = Text()
    parser.feed(value or '')
    return ' '.join(' '.join(parser.parts).split())


def code_for(identifier):
    return 'PP-BASE-' + identifier


class Gateway:
    def __init__(self, source):
        self.source = source

    def rpc(self, model, method, args, company_id=None, **kwargs):
        if company_id:
            kwargs['context'] = {'allowed_company_ids': [company_id], 'active_test': False}
        return self.source.execute(model, method, args, kwargs)

    def prepare(self, item):
        content = catalog.CatalogContent.model_validate(item['content'])
        if content.list_price is None:
            raise ValueError('Anna tuotteen yksikköhinta, tallenna ja hyväksy sisältö ennen vientiä.')
        text = '\n\n'.join(f'{label}:\n{value}' for label, value in [
            ('Kuvaus', content.description or content.outcome), ('Palvelulupaus', content.service_promise),
            ('Toimitussisältö', content.deliverables), ('Rajaukset', content.exclusions),
            ('Lähtötiedot', content.prerequisites), ('Hyväksymiskriteerit', content.acceptance_criteria)] if value)
        policy = 'ordered_prepaid' if content.billing == 'fixed' else 'delivered_timesheet'
        tracking = {'manual':'no', 'task_existing_project':'task_global_project', 'project_and_task':'task_in_project'}[content.delivery]
        values = {'name':content.name, 'type':'service', 'sale_ok':True, 'active':True, 'description_sale':text,
                  'description':'<p>' + escape(content.task_instructions).replace('\n','<br>') + '</p>' if content.task_instructions else '',
                  'list_price':float(content.list_price),
                  'default_code':code_for(item['id']), 'service_policy':policy, 'service_tracking':tracking,
                  'project_id':content.odoo_project_id or False, 'project_template_id':False}
        if content.delivery == 'task_existing_project' and not content.odoo_project_id:
            raise ValueError('Valitse tehtävien kohdeprojekti ennen vientiä.')
        if content.delivery != 'task_existing_project' and content.odoo_project_id:
            raise ValueError('Kohdeprojekti kuuluu vain tehtävä olemassa olevaan projektiin -valintaan.')
        if self.source.mode == 'fixture':
            return {'values':values, 'company':[1,'Simuloitu yritys'], 'currency':'EUR',
                    'unit':content.unit, 'taxes':[], 'project':content.odoo_project_id,
                    'mode':'fixture', 'target':self.source.target}
        # execute() wraps connection and authentication errors without exposing secrets.
        if not self.rpc('res.users', 'has_access', [[], 'read']):
            raise ValueError('Integraatiokäyttäjän yrityskontekstia ei voida lukea.')
        user = self.rpc('res.users', 'read', [[self.source.uid]], fields=['company_id'])[0]
        company = user['company_id']
        cid = company[0]
        fields = self.rpc('product.template', 'fields_get', [], cid, attributes=['type','selection'])
        for field, value in [('type','service'), ('service_policy',policy), ('service_tracking',tracking)]:
            if value not in dict(fields.get(field, {}).get('selection', [])):
                raise ValueError('Odoo ei tue valittua asetusta: ' + field + ' / ' + value)
        missing = (set(values) | {'uom_id','uom_po_id','company_id','taxes_id','product_variant_ids'}) - set(fields)
        if missing:
            raise ValueError('Odoo-kenttiä puuttuu: ' + ', '.join(sorted(missing)))
        if not self.rpc('product.template', 'has_access', [[], 'create'], cid):
            raise ValueError('Integraatiokäyttäjällä ei ole tuotteiden luontioikeutta.')
        ref = 'product_uom_hour' if content.unit == 'hour' else 'product_uom_unit'
        refs = self.rpc('ir.model.data', 'search_read', [[['module','=','uom'],['name','=',ref],['model','=','uom.uom']]], cid, fields=['res_id'], limit=2)
        if len(refs) != 1:
            raise ValueError('Odoon myyntiyksikköä ei voitu tunnistaa ulkoisella tunnisteella.')
        unit_id = refs[0]['res_id']
        unit = self.rpc('uom.uom', 'read', [[unit_id]], cid, fields=['name','active','category_id'])[0]
        if not unit['active']:
            raise ValueError('Myyntiyksikkö on arkistoitu Odoossa.')
        currency = self.rpc('res.company', 'read', [[cid]], cid, fields=['currency_id'])[0]['currency_id']
        # product.template overrides default_get as a record method in Odoo 18.
        defaults = self.rpc('product.template', 'default_get', [[], ['taxes_id']], cid)
        taxes = defaults.get('taxes_id') or []
        if taxes and isinstance(taxes[0], (list, tuple)):
            if len(taxes) != 1 or taxes[0][0] != 6:
                raise ValueError('Odoon oletusverojen muoto vaatii erillisen tarkistuksen.')
            taxes = taxes[0][2]
        tax_records = self.rpc('account.tax', 'read', [taxes], cid, fields=['name','company_id','type_tax_use']) if taxes else []
        if any(t['company_id'][0] != cid or t['type_tax_use'] not in ('sale','none') for t in tax_records):
            raise ValueError('Odoon oletusverot eivät vastaa vientiyritystä.')
        project = None
        if content.odoo_project_id:
            project_fields = self.rpc('project.project', 'fields_get', [], cid, attributes=['type'])
            names = [n for n in ['name','company_id','active','allow_billable','allow_timesheets','pricing_type'] if n in project_fields]
            rows = self.rpc('project.project', 'read', [[content.odoo_project_id]], cid, fields=names)
            if not rows:
                raise ValueError('Kohdeprojektia ei löytynyt.')
            project = rows[0]
            if not project.get('active', True) or (project.get('company_id') and project['company_id'][0] != cid):
                raise ValueError('Kohdeprojekti on arkistoitu tai kuuluu eri yritykseen.')
            if not project.get('allow_billable', False):
                raise ValueError('Kohdeprojektin tulee sallia laskutettava työ.')
            if 'pricing_type' in project and project['pricing_type'] != 'task_rate':
                raise ValueError('Kohdeprojekti ei käytä tehtävään perustuvaa laskutusta.')
            if content.billing == 'timesheet' and not project.get('allow_timesheets', False):
                raise ValueError('Kohdeprojekti ei salli tuntikirjauksia.')
        values.update(company_id=cid, uom_id=unit_id, uom_po_id=unit_id, taxes_id=[[6,0,taxes]])
        return {'values':values, 'company':company, 'currency':currency[1], 'unit':unit['name'],
                'taxes':[t['name'] for t in tax_records], 'project':project,
                'mode':self.source.mode, 'target':self.source.target}

    def find(self, plan):
        code = plan['values']['default_code']
        if self.source.mode == 'fixture':
            with store.db() as c:
                row = c.execute('SELECT payload FROM fixture_products WHERE code=?', (code,)).fetchone()
            if not row:
                return None
            value = json.loads(row['payload'])
            if value.get('values') != plan['values']:
                raise Conflict('Simuloitu tuote poikkeaa vientisuunnitelmasta.')
            return {'template_id':value['template_id'], 'product_id':value['product_id']}
        cid = plan['company'][0]
        rows = self.rpc('product.template', 'search_read', [[['default_code','=',code]]], cid,
                        fields=['id'] + list(plan['values']) + ['product_variant_ids'], limit=2)
        if len(rows) > 1:
            raise Conflict('Odoossa on useita tuotteita samalla koodilla. Selvitä ristiriita.')
        if not rows:
            return None
        row = rows[0]
        for key, expected in plan['values'].items():
            actual = row[key]
            if key in ('company_id','uom_id','uom_po_id','project_id','project_template_id'):
                actual = actual[0] if actual else False
            if key == 'taxes_id':
                actual, expected = sorted(actual), sorted(expected[0][2])
            if isinstance(expected, str) and actual is False:
                actual = ''
            if key == 'description':
                actual, expected = html_text(actual), html_text(expected)
            if key == 'list_price':
                equal = abs(actual - expected) < 0.000001
            else:
                equal = actual == expected
            if not equal:
                raise Conflict('Odoo-tuotteen asetukset poikkeavat vientisuunnitelmasta. Tarkista tuote Odoossa: ' + key)
        variants = row['product_variant_ids']
        if len(variants) != 1:
            raise Conflict('Tuotteella ei ole yksiselitteistä myytävää varianttia.')
        return {'template_id':row['id'], 'product_id':variants[0]}

    def create(self, plan):
        if self.source.mode == 'fixture':
            code = plan['values']['default_code']
            identifier = int(hashlib.sha256(code.encode()).hexdigest()[:8], 16)
            with store.db(write=True) as c:
                c.execute('INSERT INTO fixture_products VALUES(?,?)', (code, store.encode({'template_id':identifier, 'product_id':identifier, 'values':plan['values']})))
        else:
            self.rpc('product.template', 'create', [plan['values']], plan['company'][0])


router = APIRouter(prefix='/api/catalog', tags=['catalog-export'])


@router.get('/{identifier}/export-status')
def status(identifier: str):
    source = odoo.adapter()
    with store.db() as c:
        catalog.get_item(identifier, c)
        row = c.execute('SELECT * FROM catalog_exports WHERE item_id=? AND target=?', (identifier,source.target)).fetchone()
    return {'mode':source.mode, 'target':source.target, 'status':row['status'] if row else 'not_exported',
            'result':json.loads(row['payload']).get('result') if row else None}


@router.post('/{identifier}/export-preview')
def preview(identifier: str, body: VersionRequest):
    source = odoo.adapter()
    with store.db() as c:
        item = catalog.get_item(identifier, c)
    if item['version'] != body.expected_version or item['state'] != 'approved':
        raise Conflict('Tallenna ja hyväksy nykyinen sisältöversio ennen vientiä.')
    plan = Gateway(source).prepare(item)
    plan.update(id=str(uuid4()), item_id=identifier, version=item['version'], created_at=catalog.now())
    with store.db(write=True) as c:
        c.execute('INSERT INTO catalog_export_plans VALUES(?,?)', (plan['id'],store.encode(plan)))
    return plan


@router.post('/{identifier}/export')
def export(identifier: str, body: ExportRequest):
    source = odoo.adapter()
    gateway = Gateway(source)
    with store.db(write=True) as c:
        item = catalog.get_item(identifier, c)
        if item['version'] != body.expected_version or item['state'] != 'approved':
            raise Conflict('Hyväksy nykyinen versio ennen vientiä.')
        row = c.execute('SELECT * FROM catalog_exports WHERE item_id=? AND target=?', (identifier,source.target)).fetchone()
        if row and row['status'] == 'exported':
            return json.loads(row['payload'])['result']
        if row and row['status'] == 'pending':
            raise Conflict('Vienti on käynnissä. Odota sen valmistumista.')
        uncertain = bool(row and row['status'] == 'uncertain')
        if uncertain:
            plan = json.loads(row['payload'])['plan']
        else:
            saved = c.execute('SELECT payload FROM catalog_export_plans WHERE id=?', (body.plan_id,)).fetchone()
            if not saved:
                raise Conflict('Avaa viennin esikatselu ensin.')
            plan = json.loads(saved['payload'])
        if (plan['item_id'],plan['version'],plan['target']) != (identifier,item['version'],source.target):
            raise Conflict('Vientisuunnitelma ei vastaa nykyistä tuotetta tai kohdetta.')
        c.execute('INSERT INTO catalog_exports VALUES(?,?,?,?) ON CONFLICT(item_id,target) DO UPDATE SET status=excluded.status,payload=excluded.payload',
                  (identifier,source.target,'pending',store.encode({'plan':plan})))
    attempted = False
    try:
        remote = gateway.find(plan)
        if remote is None:
            if uncertain:
                raise Conflict('Aiempi vienti on epäselvä eikä tuotetta löytynyt. Automaattinen uudelleenluonti on estetty; tarkista Odoo.')
            fresh = gateway.prepare(item)
            if any(fresh[key] != plan[key] for key in fresh):
                raise Conflict('Odoon asetukset muuttuivat esikatselun jälkeen. Avaa esikatselu uudelleen.')
            attempted = True
            gateway.create(plan)
            remote = gateway.find(plan)
            if remote is None:
                raise Conflict('Luotua Odoo-tuotetta ei voitu lukea takaisin. Selvitä viennin tulos.')
        result = {**remote, 'mode':source.mode, 'target':source.target, 'version':item['version'],
                  'code':plan['values']['default_code'], 'url':source.product_url(remote['template_id']), 'exported_at':catalog.now()}
        with store.db(write=True) as c:
            c.execute("UPDATE catalog_exports SET status='exported',payload=? WHERE item_id=? AND target=?", (store.encode({'plan':plan,'result':result}),identifier,source.target))
        return result
    except Exception:
        with store.db(write=True) as c:
            c.execute('UPDATE catalog_exports SET status=? WHERE item_id=? AND target=?', ('uncertain' if attempted or uncertain else 'retryable',identifier,source.target))
        raise

import hashlib
import http.client
import json
import os
import xmlrpc.client
from urllib.parse import urlparse
from . import store
from .data import fixture


class IntegrationError(Exception):
    pass


class TimeoutTransport(xmlrpc.client.Transport):
    def make_connection(self, host):
        return http.client.HTTPConnection(host, timeout=15)


class TimeoutSafeTransport(xmlrpc.client.SafeTransport):
    def make_connection(self, host):
        return http.client.HTTPSConnection(host, timeout=15, context=self.context)


class FixtureAdapter:
    mode = 'fixture'
    target = 'fixture'

    def catalog_capabilities(self):
        return {'target': self.target, 'mode': self.mode, 'company': None, 'models': {},
                'units': [], 'checks': {}, 'workflow_verified': False,
                'note': 'Esimerkkitila: Odoon kenttiä, oikeuksia tai työnkulkua ei ole varmennettu.'}

    def list_services(self):
        return fixture()['services']

    def list_customers(self):
        return fixture()['customers']

    def list_projects(self):
        return fixture()['projects']

    def list_opportunities(self):
        return fixture()['opportunities']

    def find_service(self, code):
        with store.db() as c:
            row = c.execute('SELECT payload FROM fixture_products WHERE code=?', (code,)).fetchone()
        return json.loads(row['payload'])['id'] if row else None

    def create_service(self, code, card):
        identifier = int(hashlib.sha256(code.encode()).hexdigest()[:8], 16)
        with store.db(write=True) as c:
            c.execute('INSERT OR IGNORE INTO fixture_products VALUES(?,?)', (code, store.encode({'id':identifier,'code':code,'card':card})))
        return identifier

    def product_url(self, identifier):
        return None


class OdooAdapter:
    mode = 'odoo'

    def __init__(self):
        self.url = os.getenv('ODOO_URL', 'http://127.0.0.1:8069').rstrip('/')
        parsed = urlparse(self.url)
        # This deliverable deliberately cannot write to the employer's server.
        if parsed.hostname not in {'localhost', '127.0.0.1', '::1', 'odoo'} or parsed.scheme not in {'http','https'} or parsed.username:
            raise IntegrationError('Tämä demo sallii vain paikallisen Odoo-ympäristön.')
        self.database = os.getenv('ODOO_DATABASE', 'productization_demo')
        if self.database != 'productization_demo':
            raise IntegrationError('Demon tietokannan nimen tulee olla productization_demo.')
        self.username = os.getenv('ODOO_USERNAME', '')
        self.key = os.getenv('ODOO_API_KEY', '')
        self.public_url = os.getenv('ODOO_PUBLIC_URL', self.url).rstrip('/')
        target_url = os.getenv('ODOO_TARGET_URL', self.url).rstrip('/')
        for address in (self.public_url, target_url):
            parts = urlparse(address)
            if parts.hostname not in {'localhost', '127.0.0.1', '::1', 'odoo'} or parts.scheme not in {'http', 'https'} or parts.username:
                raise IntegrationError('Demon julkisen osoitteen ja kohdetunnisteen tulee olla paikallisia.')
        self.target = target_url + '/' + self.database
        self.uid = None
        self.fields = {}

    def proxy(self, endpoint):
        transport = TimeoutSafeTransport() if self.url.startswith('https:') else TimeoutTransport()
        return xmlrpc.client.ServerProxy(self.url+endpoint, transport=transport, allow_none=True)

    def connect(self):
        if self.uid:
            return
        if not self.key or not self.username:
            raise IntegrationError('Odoon integraatiotunnus tai API-avain puuttuu.')
        with self.proxy('/xmlrpc/2/common') as common:
            version = common.version()
            if version.get('server_version_info', [0])[0] != 18:
                raise IntegrationError('Tämä adapteri on rajattu Odoo 18 -demolle.')
            self.uid = common.authenticate(self.database, self.username, self.key, {})
        if not self.uid:
            raise IntegrationError('Odoo-tunnistautuminen epäonnistui.')

    def execute(self, model, method, args, kwargs=None):
        try:
            self.connect()
            with self.proxy('/xmlrpc/2/object') as proxy:
                return proxy.execute_kw(self.database, self.uid, self.key, model, method, args, kwargs or {})
        except (xmlrpc.client.Error, OSError) as exc:
            raise IntegrationError('Odoo-kutsu epäonnistui. Tarkista palvelu, oikeudet ja asetukset.') from exc

    def inspect(self, model):
        if model not in self.fields:
            self.fields[model] = self.execute(model, 'fields_get', [], {'attributes':['type','selection','required']})
        return self.fields[model]

    def catalog_capabilities(self):
        """Read-only A0 snapshot. Metadata never counts as a verified sales workflow."""
        try:
            self.connect()
        except (xmlrpc.client.Error, OSError) as exc:
            raise IntegrationError('Odoo-kartoitus epäonnistui. Tarkista palvelu, oikeudet ja asetukset.') from exc
        users = self.execute('res.users', 'read', [[self.uid]], {'fields': ['company_id', 'company_ids']})
        if not users or not users[0].get('company_id'):
            raise IntegrationError('Odoon yrityskontekstia ei voitu varmistaa.')
        company = users[0]['company_id']
        context = {'allowed_company_ids': [company[0]]}
        wanted = {
            'product.template': ['type', 'uom_id', 'uom_po_id', 'invoice_policy', 'service_type',
                                 'service_policy', 'service_tracking', 'project_id', 'project_template_id',
                                 'company_id', 'taxes_id', 'currency_id', 'product_variant_ids'],
            'product.product': ['product_tmpl_id', 'uom_id', 'active'],
            'project.project': ['company_id', 'allow_billable', 'allow_timesheets'],
            'sale.order.template': ['company_id', 'sale_order_template_line_ids', 'sale_order_template_option_ids'],
        }
        models = {}
        for model, names in wanted.items():
            try:
                fields = self.execute(model, 'fields_get', [names],
                                      {'attributes': ['type', 'selection', 'required', 'readonly'], 'context': context})
                rights = {operation: bool(self.execute(model, 'check_access_rights', [operation],
                          {'raise_exception': False, 'context': context})) for operation in ('read', 'create', 'write')}
                models[model] = {'status': 'inspected', 'fields': fields, 'access_rights': rights,
                                 'missing_fields': sorted(set(names) - set(fields))}
            except IntegrationError:
                models[model] = {'status': 'unverified', 'fields': {}, 'access_rights': {},
                                 'note': 'Mallia ei voitu kartoittaa: tarkista moduuli ja käyttöoikeudet.'}
        units = []
        try:
            while True:
                page = self.execute('uom.uom', 'search_read', [[['active', '=', True]]],
                                    {'fields': ['id', 'name', 'category_id', 'rounding', 'factor'],
                                     'context': context, 'offset': len(units), 'limit': 200, 'order': 'id'})
                units.extend(page)
                if len(page) < 200:
                    break
            unit_status = 'inspected'
        except IntegrationError:
            units, unit_status = [], 'unverified'
        product = models['product.template']
        fields = product['fields']
        def selection(field, value):
            if product['status'] != 'inspected':
                return 'unverified'
            return 'available' if value in dict(fields.get(field, {}).get('selection', [])) else 'unavailable'
        checks = {'fixed': selection('service_policy', 'ordered_prepaid'),
                  'timesheet': selection('service_policy', 'delivered_timesheet'),
                  'task_existing_project': selection('service_tracking', 'task_global_project'),
                  'project_and_task': selection('service_tracking', 'task_in_project'),
                  'subscriptions': 'unverified', 'milestones': 'unverified', 'units': unit_status}
        return {'target': self.target, 'mode': self.mode, 'company': company, 'models': models,
                'units': units, 'checks': checks, 'workflow_verified': False,
                'note': 'Kenttävalinnat ja mallioikeudet kartoitettu. Tietuekohtaiset oikeudet, hinnastot, verot ja tilauksen vahvistuksen projektit/tehtävät vaativat erillisen testin.'}

    def read(self, model, domain, fields, offset=0):
        available = self.inspect(model)
        missing = set(fields) - set(available)
        if missing:
            raise IntegrationError('Odoosta puuttuu tarvittavia kenttiä: '+ ', '.join(sorted(missing)))
        return self.execute(model, 'search_read', [domain], {'fields':fields, 'limit':200, 'offset':offset, 'order':'id'})

    def list_services(self):
        rows = self.read('product.template', [['default_code','=like','DEMO-SVC-%']], ['id','name','description_sale','list_price','default_code','type'])
        return [{'source_id':x['default_code'].removeprefix('DEMO-'), 'name':x['name'],
                 'description':x['description_sale'] or '', 'price':x['list_price'], 'currency':'EUR',
                 'odoo_id':x['id'], 'origin':'Odoo', 'pricing_model':'Odoon listahinta; tarkista laskutusperuste'} for x in rows]

    def mapped(self, group, model, fields):
        base = fixture()[group]
        with store.db() as c:
            mapping = {r['source_id']:r['remote_id'] for r in c.execute('SELECT * FROM seed_map WHERE target=?',(self.target,))}
        ids = [mapping[x['source_id']] for x in base if x['source_id'] in mapping]
        if len(ids) != len(base):
            raise IntegrationError('Odoo-demoaineisto puuttuu. Aja scripts/seed.py --odoo ensin.')
        rows = {x['id']:x for x in self.read(model,[['id','in',ids]],['id']+fields)}
        result=[]
        for item in base:
            remote = rows.get(mapping[item['source_id']])
            if not remote:
                raise IntegrationError('Odoon demotietue puuttuu; alusta aineisto uudelleen.')
            result.append({**item,'name':remote['name'],'odoo_id':remote['id'], 'odoo_record':remote,
                           'origin':'Odoon perustiedot + paikalliset synteettiset tutkimushavainnot'})
        return result

    def list_customers(self):
        return self.mapped('customers','res.partner',['name','is_company'])

    def list_projects(self):
        base = fixture()
        with store.db() as c:
            mapping = {r['source_id']:r['remote_id'] for r in c.execute(
                'SELECT * FROM seed_map WHERE target=?', (self.target,))}
        seeded = {mapping[p['source_id']]:p for p in base['projects'] if p['source_id'] in mapping}
        customers = {mapping[p['source_id']]:p['source_id'] for p in base['customers'] if p['source_id'] in mapping}
        result = []
        offset = 0
        while True:
            rows = self.read('project.project', [], ['id','name','description','partner_id'], offset=offset)
            for remote in rows:
                item = seeded.get(remote['id'])
                partner = remote.get('partner_id')
                result.append({
                    **(item or {'source_id':f"ODOO-PRJ-{remote['id']}",
                                'customer_id':customers.get(partner[0]) if partner else None,
                                'service_id':None}),
                    'name':remote['name'], 'description':remote.get('description') or '',
                    'odoo_id':remote['id'], 'odoo_record':remote,
                    'origin':('Odoon perustiedot + paikalliset synteettiset tutkimushavainnot'
                              if item else 'Odoo'),
                })
            if len(rows) < 200:
                return result
            offset += len(rows)

    def list_opportunities(self):
        return self.mapped('opportunities','crm.lead',['name','description','partner_id'])

    def find_service(self, code):
        rows=self.read('product.template',[['default_code','=',code]],['id'])
        if len(rows)>1:
            raise IntegrationError('Samalla tuotekoodilla löytyi useita tuotteita. Selvitä ristiriita Odoossa.')
        return rows[0]['id'] if rows else None

    def create_service(self, code, card):
        fields=self.inspect('product.template')
        if 'service' not in dict(fields.get('type',{}).get('selection',[])):
            raise IntegrationError('Palvelutyypin kenttäkartoitus ei vastaa odotettua.')
        for required in ('name','type','description_sale','list_price','default_code'):
            if required not in fields:
                raise IntegrationError('Tuotteen kenttäkartoitus on puutteellinen.')
        text='\n\n'.join([card['description'],'Toimitussisältö:\n'+card['deliverables'],
                          'Rajaukset:\n'+card['exclusions'],'Lähtötiedot:\n'+card['prerequisites'],
                          'Vaiheet:\n'+card['phases']])
        return self.execute('product.template','create',[{'name':card['name'],'type':'service',
            'description_sale':text,'list_price':float(card['price']),'default_code':code}])

    def product_url(self, identifier):
        return f'{self.public_url}/odoo/products/{identifier}'


def adapter():
    mode=os.getenv('ODOO_MODE','fixture')
    if mode=='fixture':
        return FixtureAdapter()
    if mode=='odoo':
        return OdooAdapter()
    raise IntegrationError('ODOO_MODE-arvon tulee olla fixture tai odoo.')

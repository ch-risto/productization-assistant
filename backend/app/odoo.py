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
        self.target = self.url + '/' + self.database
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

    def read(self, model, domain, fields):
        available = self.inspect(model)
        missing = set(fields) - set(available)
        if missing:
            raise IntegrationError('Odoosta puuttuu tarvittavia kenttiä: '+ ', '.join(sorted(missing)))
        return self.execute(model, 'search_read', [domain], {'fields':fields, 'limit':200, 'order':'id'})

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
        return self.mapped('projects','project.project',['name','description','partner_id'])

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
        return f'{self.url}/odoo/products/{identifier}'


def adapter():
    mode=os.getenv('ODOO_MODE','fixture')
    if mode=='fixture':
        return FixtureAdapter()
    if mode=='odoo':
        return OdooAdapter()
    raise IntegrationError('ODOO_MODE-arvon tulee olla fixture tai odoo.')

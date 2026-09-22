"""Adapter contract tests; not evidence of a real Odoo server connection."""
from collections import defaultdict
import pytest
from app import odoo, store
import seed


def test_seed_odoo_twice_keeps_same_records(tmp_path, monkeypatch):
    monkeypatch.setenv('DATASET_PATH', 'demo-data/dataset.json')
    monkeypatch.setenv('APP_DATABASE_URL', 'sqlite:///' + str(tmp_path / 'seed.db'))
    class FakeOdoo:
        target = 'test-local-odoo'
        def __init__(self):
            self.rows = defaultdict(dict)
        def connect(self): pass
        def inspect(self, model):
            return dict.fromkeys(['id','name','is_company','ref','type','default_code','description_sale','list_price','partner_id','description'])
        def read(self, model, domain, fields):
            key, op, value = domain[0]
            assert op == '='
            return [{'id': k} for k, row in self.rows[model].items() if row.get(key) == value]
        def execute(self, model, method, args):
            if method == 'create':
                identifier = len(self.rows[model]) + 1
                self.rows[model][identifier] = {'id':identifier, **args[0]}
                return identifier
            assert method == 'write'
            for identifier in args[0]: self.rows[model][identifier].update(args[1])
    fake = FakeOdoo()
    monkeypatch.setattr(seed, 'OdooAdapter', lambda: fake)
    seed.seed_odoo()
    first = {model: len(rows) for model, rows in fake.rows.items()}
    seed.seed_odoo()
    assert first == {model: len(rows) for model, rows in fake.rows.items()}
    assert first == {'res.partner':6, 'product.template':4, 'project.project':8, 'crm.lead':4}
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM seed_map').fetchone()[0] == 22


def test_read_fields_and_domain_are_explicit(monkeypatch):
    monkeypatch.setenv('ODOO_URL', 'http://127.0.0.1:8069')
    source = odoo.OdooAdapter()
    assert source.product_url(5) == 'http://127.0.0.1:8069/odoo/products/5'
    calls = []
    def execute(model, method, args, kwargs=None):
        calls.append((model, method, args, kwargs))
        if method == 'fields_get': return {'id':{}, 'name':{}}
        return [{'id':1,'name':'Test'}]
    monkeypatch.setattr(source, 'execute', execute)
    domain = [['id','=',1]]
    assert source.read('res.partner', domain, ['id','name'])[0]['id'] == 1
    assert calls[-1][2] == [domain]
    assert calls[-1][3]['fields'] == ['id','name']
    with pytest.raises(odoo.IntegrationError):
        source.read('res.partner', domain, ['enterprise_only'])


def test_connection_failure_is_safe(monkeypatch):
    source = odoo.OdooAdapter()
    def fail(): raise OSError('Secret internal detail')
    monkeypatch.setattr(source, 'connect', fail)
    with pytest.raises(odoo.IntegrationError, match='Odoo-kutsu epäonnistui') as exc:
        source.execute('product.template','search_read',[])
    assert 'Secret' not in str(exc.value)

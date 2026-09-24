import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import catalog, catalog_export as export, odoo, store
from app.main import app
from app.schemas import VersionRequest
from app.workflow import Conflict


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_DATABASE_URL', 'sqlite:///' + str(tmp_path / 'test.db'))
    monkeypatch.setenv('ODOO_MODE', 'fixture')
    store.init()


def item(price=100):
    record = catalog.create_item(catalog.CatalogContent(name='Kartoitus', outcome='Raportti', deliverables='Työpaja',
        exclusions='Ei toteutusta', acceptance_criteria='Raportti toimitettu', target_need='Rajaus', list_price=price))
    return catalog.approve_item(record['id'], VersionRequest(expected_version=1))


def request(record):
    plan = export.preview(record['id'], VersionRequest(expected_version=record['version']))
    return export.ExportRequest(expected_version=record['version'], plan_id=plan['id'])


def test_price_approval_and_preview_required():
    record = item(None)
    with pytest.raises(ValueError, match='yksikköhinta'):
        request(record)
    record = item()
    with pytest.raises(Conflict, match='esikatselu'):
        export.export(record['id'], export.ExportRequest(expected_version=record['version'], plan_id='missing'))


def test_fixture_export_is_explicit_and_repeatable():
    record = item()
    body = request(record)
    result = export.export(record['id'], body)
    assert result['mode'] == 'fixture' and result['url'] is None
    assert result['template_id'] and result['product_id']
    assert export.export(record['id'], body) == result
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM fixture_products').fetchone()[0] == 1
    assert export.status(record['id'])['status'] == 'exported'
    with pytest.raises(Conflict, match='lukittu'):
        catalog.edit_item(record['id'], catalog.CatalogEdit(**record['content'], expected_version=record['version']))


def test_changed_content_invalidates_preview():
    record = item()
    body = request(record)
    edited = catalog.edit_item(record['id'], catalog.CatalogEdit(**{**record['content'], 'name':'Muutos'}, expected_version=record['version']))
    approved = catalog.approve_item(record['id'], VersionRequest(expected_version=edited['version']))
    with pytest.raises(Conflict):
        export.export(record['id'], export.ExportRequest(expected_version=approved['version'], plan_id=body.plan_id))


def test_timeout_after_create_reconciles_without_second_create(monkeypatch):
    record = item()
    body = request(record)
    original = export.Gateway.create
    calls = []
    def timeout(self, plan):
        calls.append(plan)
        original(self, plan)
        raise odoo.IntegrationError('Timeout')
    monkeypatch.setattr(export.Gateway, 'create', timeout)
    with pytest.raises(odoo.IntegrationError):
        export.export(record['id'], body)
    assert export.status(record['id'])['status'] == 'uncertain'
    result = export.export(record['id'], body)
    assert result['template_id'] and len(calls) == 1


def test_uncertain_missing_product_never_recreates(monkeypatch):
    record = item()
    body = request(record)
    calls = []
    def timeout(self, plan):
        calls.append(plan)
        raise odoo.IntegrationError('Timeout before response')
    monkeypatch.setattr(export.Gateway, 'create', timeout)
    with pytest.raises(odoo.IntegrationError):
        export.export(record['id'], body)
    with pytest.raises(Conflict, match='uudelleenluonti'):
        export.export(record['id'], body)
    assert len(calls) == 1


def test_concurrent_export_claims_one_writer():
    record = item()
    body = request(record)
    def run(_):
        try:
            return export.export(record['id'], body)
        except Conflict:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run, range(2)))
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM fixture_products').fetchone()[0] == 1


def test_startup_reconciles_pending_and_origin_is_checked():
    record = item()
    body = request(record)
    with store.db(write=True) as c:
        plan = json.loads(c.execute('SELECT payload FROM catalog_export_plans WHERE id=?', (body.plan_id,)).fetchone()[0])
        c.execute('INSERT INTO catalog_exports VALUES(?,?,?,?)', (record['id'],'fixture','pending',store.encode({'plan':plan})))
    with TestClient(app) as client:
        assert client.get(f"/api/catalog/{record['id']}/export-status").json()['status'] == 'uncertain'
        assert client.post(f"/api/catalog/{record['id']}/export", json=body.model_dump(), headers={'Origin':'https://other.test'}).status_code == 403


def test_odoo_prepare_uses_real_units_company_and_no_implicit_onchange():
    class FakeOdoo:
        mode = 'odoo'
        target = 'local-test'
        uid = 2
        def execute(self, model, method, args, kwargs):
            if method == 'has_access': return True
            if model == 'res.users': return [{'company_id':[3,'Company']}]
            assert kwargs['context']['allowed_company_ids'] == [3]
            if model == 'product.template' and method == 'fields_get':
                fields = {name:{} for name in ['name','sale_ok','active','description_sale','description','list_price','default_code','project_id','project_template_id','uom_id','uom_po_id','company_id','taxes_id','product_variant_ids']}
                fields.update(type={'selection':[['service','Service']]}, service_policy={'selection':[['ordered_prepaid','Fixed']]}, service_tracking={'selection':[['no','No']]})
                return fields
            if model == 'ir.model.data':
                assert ['name','=','product_uom_unit'] in args[0]
                return [{'res_id':42}]
            if model == 'uom.uom': return [{'name':'Unit', 'active':True,'category_id':[1,'Units']}]
            if model == 'res.company': return [{'currency_id':[1,'EUR']}]
            if method == 'default_get': return {'taxes_id':[[6,0,[7]]]}
            if model == 'account.tax': return [{'id':7,'name':'Sales tax','company_id':[3,'Company'],'type_tax_use':'sale'}]
            raise AssertionError((model,method))
    plan = export.Gateway(FakeOdoo()).prepare(item())
    assert plan['values']['uom_id'] == plan['values']['uom_po_id'] == 42
    assert plan['values']['company_id'] == 3
    assert plan['values']['taxes_id'] == [[6,0,[7]]]
    assert plan['values']['project_id'] is False
    assert plan['values']['service_policy'] == 'ordered_prepaid'

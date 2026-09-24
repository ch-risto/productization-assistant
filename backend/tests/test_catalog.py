"""Catalog persistence and read-only Odoo contracts; no live-server claims."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import catalog, odoo, store
from app.main import app
from app.workflow import Conflict
from app.schemas import VersionRequest


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_DATABASE_URL', 'sqlite:///' + str(tmp_path / 'catalog.db'))
    monkeypatch.setenv('ODOO_MODE', 'fixture')
    store.init()


def content(**kwargs):
    return catalog.CatalogContent(name='Kartoitus', outcome='Priorisoitu kehityssuunnitelma',
        deliverables='Työpaja ja kirjallinen suunnitelma', exclusions='Toteutus ei sisälly',
        acceptance_criteria='Tavoitteet ja seuraavat askeleet dokumentoitu',
        target_need='Kehityksen priorisointi', **kwargs)


def edit(item, **kwargs):
    return catalog.edit_item(item['id'], catalog.CatalogEdit(**{
        **item['content'], 'expected_version': item['version'], **kwargs}))


def test_migration_preserves_legacy_and_is_repeatable():
    with store.db(write=True) as c:
        c.execute('INSERT INTO cards VALUES(?,?)', ('legacy', '{"untouched":true}'))
    store.init()
    store.init()
    with store.db() as c:
        assert c.execute('SELECT payload FROM cards').fetchone()[0] == '{"untouched":true}'
        assert c.execute('SELECT count(*) FROM schema_migrations').fetchone()[0] == 3


def test_approval_history_and_stale_edits():
    item = catalog.create_item(content())
    approved = catalog.approve_item(item['id'], VersionRequest(expected_version=1))
    assert approved['state'] == 'approved'
    assert approved['version'] == 2
    assert catalog.approve_item(item['id'], VersionRequest(expected_version=2)) == approved
    updated = edit(approved, outcome='Uusi lopputulos')
    assert updated['id'] == item['id']
    assert updated['state'] == 'draft' and updated['approved_at'] is None
    history = catalog.history(item['id'])
    assert [row['version'] for row in history] == [3, 2, 1]
    assert history[1] == approved
    with pytest.raises(Conflict):
        edit(approved)
    with pytest.raises(Conflict):
        catalog.approve_item(item['id'], VersionRequest(expected_version=2))


def test_concurrent_edits_only_one_wins():
    item = catalog.create_item(content())
    def update(_):
        try:
            return edit(item)['version']
        except Conflict:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(update, range(2)))
    assert sorted(map(str, results)) == ['2', 'conflict']


def test_dependencies_cycles_conflicts_and_approval():
    first = catalog.create_item(content())
    second = catalog.create_item(content(requires=[first['id']]))
    with pytest.raises(ValueError, match='Hyväksy ensin'):
        catalog.approve_item(second['id'], VersionRequest(expected_version=1))
    with pytest.raises(ValueError, match='syklin'):
        edit(first, requires=[second['id']])
    with pytest.raises(ValueError, match='ristiriitaisia'):
        edit(first, excludes=[second['id']])
    with pytest.raises(ValueError, match='toiseen katalogituotteeseen'):
        edit(first, requires=['missing'])
    catalog.approve_item(first['id'], VersionRequest(expected_version=1))
    assert catalog.approve_item(second['id'], VersionRequest(expected_version=1))['state'] == 'approved'
    assert len(catalog.history(first['id'])) == 2


@pytest.mark.parametrize('changes', [dict(unit='unknown'), dict(billing='subscription'),
    dict(billing='timesheet', unit='unit'), dict(quantity_min='3', quantity_max='1')])
def test_invalid_commercial_proposals_rejected(changes):
    with pytest.raises(ValueError):
        content(**changes)


def test_api_workflow_and_fixture_snapshot():
    with TestClient(app) as client:
        created = client.post('/api/catalog', json=content().model_dump(mode='json'))
        assert created.status_code == 200
        item = created.json()
        assert client.get('/api/catalog').json() == [item]
        assert client.post(f"/api/catalog/{item['id']}/approve", json={'expected_version': 9}).status_code == 409
        assert client.get('/api/catalog/absent/history').status_code == 404
        assert client.get('/api/catalog/capabilities').json() is None
        snapshot = client.post('/api/catalog/capabilities').json()
        assert snapshot['mode'] == 'fixture' and snapshot['workflow_verified'] is False
        assert not snapshot['units']
        assert client.get('/api/catalog/capabilities').json() == snapshot
        assert client.post('/api/catalog', json=content().model_dump(mode='json'), headers={'Origin':'https://other.test'}).status_code == 403


def test_duplicate_hint_uses_need_and_outcome_not_name():
    first = catalog.create_item(content())
    second = catalog.create_item(content())
    edit(second, name='Täysin toinen nimi')
    assert catalog.similar_items(first['id'])[0]['id'] == second['id']


def test_capabilities_are_read_only_and_company_scoped(monkeypatch):
    source = odoo.OdooAdapter()
    source.uid = 7
    calls = []
    def execute(model, method, args, kwargs=None):
        calls.append((model, method))
        assert method in ('read', 'fields_get', 'check_access_rights', 'search_read')
        if model == 'res.users':
            return [{'company_id': [3, 'Test company'], 'company_ids': [3, 4]}]
        assert kwargs['context'] == {'allowed_company_ids': [3]}
        if model == 'sale.order.template':
            raise odoo.IntegrationError('Unavailable')
        if method == 'fields_get':
            return {'service_policy': {'selection': [['ordered_prepaid', 'Fixed']]},
                    'service_tracking': {'selection': [['task_global_project', 'Task']]}}
        if method == 'check_access_rights':
            return args == ['read']
        assert model == 'uom.uom'
        offset = kwargs['offset']
        return [{'id': i, 'name': 'Unit', 'category_id': [1, 'Units']} for i in range(offset, min(offset + 200, 201))]
    monkeypatch.setattr(source, 'execute', execute)
    result = source.catalog_capabilities()
    assert result['company'] == [3, 'Test company']
    assert result['checks']['fixed'] == 'available'
    assert result['checks']['timesheet'] == 'unavailable'
    assert result['checks']['subscriptions'] == 'unverified'
    assert result['models']['sale.order.template']['status'] == 'unverified'
    assert result['models']['product.template']['access_rights']['write'] is False
    assert len(result['units']) == 201
    assert result['workflow_verified'] is False


def test_failed_connection_is_a_safe_api_error(monkeypatch):
    source = odoo.OdooAdapter()
    def fail():
        raise ConnectionRefusedError('Internal connection details')
    monkeypatch.setattr(source, 'connect', fail)
    monkeypatch.setattr(odoo, 'adapter', lambda: source)
    with TestClient(app) as client:
        response = client.post('/api/catalog/capabilities')
        assert response.status_code == 502
        assert 'Internal' not in response.text
        assert client.get('/api/catalog/capabilities').json() is None

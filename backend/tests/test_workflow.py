import copy
import sys
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from app import store, data, workflow, llm, odoo
from app.schemas import CardEdit, CardContent, Ideas
from app.main import app
import seed


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_DATABASE_URL', 'sqlite:///' + str(tmp_path / 'test.db'))
    monkeypatch.setenv('ODOO_MODE', 'fixture')
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    store.init()


def draft():
    run = workflow.run_analysis('example')
    return workflow.create_card(run['id'], run['ideas'][0]['id'])


def edit(card, **changes):
    payload = {key: card[key] for key in CardContent.model_fields}
    payload.update(hours='7.25', hourly_rate='95.50', expected_version=card['version'])
    payload.update(changes)
    return workflow.edit_card(card['id'], CardEdit(**payload))


def approved():
    card = edit(draft())
    return workflow.approve(card['id'], card['version'])


def test_seed_twice_and_evidence():
    seed.seed_local()
    seed.seed_local()
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM settings').fetchone()[0] == 1
    value = data.fixture()
    facts = data.facts(value)
    assert (facts['project_count'], facts['customer_count']) == (8, 6)
    assert (facts['content_delay_projects'], facts['content_delay_customers']) == (4, 3)
    assert value['competitors'][1]['price'] is None


def test_model_sources_and_empty_data(monkeypatch):
    snap = workflow.snapshot()
    result, _ = llm.analyze(snap, 'example')
    result['ideas'][0]['supporting_source_ids'] = ['FAKE-999']
    monkeypatch.setattr(llm, 'call', lambda *args: (Ideas.model_validate(result), {}))
    with pytest.raises(ValueError, match='Tuntemattomia'):
        llm.analyze(snap, 'live')
    snap['observations'] = []
    with pytest.raises(ValueError, match='ei ole havaintoja'):
        llm.analyze(snap, 'live')


def test_approval_version_price_and_history():
    card = draft()
    with pytest.raises(workflow.Conflict):
        workflow.export_card(card['id'], 1)
    with pytest.raises(ValueError):
        workflow.approve(card['id'], 1)
    card = edit(card)
    assert card['price'] == '692.38'
    card = workflow.approve(card['id'], 2)
    assert card['approved_version'] == 2
    changed = edit(card, name='Muokattu palvelu')
    assert changed['state'] == 'draft' and changed['approved_version'] is None
    with pytest.raises(workflow.Conflict):
        workflow.export_card(card['id'], 2)
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM card_history').fetchone()[0] == 3


def test_repeated_export_is_one_product():
    card = approved()
    first = workflow.export_card(card['id'], card['version'])
    second = workflow.export_card(card['id'], card['version'])
    assert first['export'] == second['export']
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM fixture_products').fetchone()[0] == 1
    with pytest.raises(workflow.Conflict):
        edit(first)


def test_concurrent_export_serializes():
    card = approved()
    entered, release = threading.Event(), threading.Event()
    class Slow(odoo.FixtureAdapter):
        def create_service(self, code, value):
            entered.set()
            assert release.wait(5)
            return super().create_service(code, value)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(workflow.export_card, card['id'], card['version'], Slow())
        assert entered.wait(5)
        try:
            with pytest.raises(workflow.Conflict, match='käynnissä'):
                workflow.export_card(card['id'], card['version'])
        finally:
            release.set()
        assert future.result()['state'] == 'exported'


def test_timeout_after_create_reconciles():
    card = approved()
    class LostReply(odoo.FixtureAdapter):
        def create_service(self, code, value):
            super().create_service(code, value)
            raise odoo.IntegrationError('Simulated lost response')
    with pytest.raises(odoo.IntegrationError):
        workflow.export_card(card['id'], card['version'], LostReply())
    assert workflow.get_card(card['id'])['state'] == 'approved'
    with pytest.raises(workflow.Conflict):
        edit(card)
    result = workflow.export_card(card['id'], card['version'])
    assert result['state'] == 'exported'
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM fixture_products').fetchone()[0] == 1


def test_uncertain_missing_product_never_recreates():
    card = approved()
    class Lost(odoo.FixtureAdapter):
        def create_service(self, code, value):
            raise odoo.IntegrationError('Timeout')
    with pytest.raises(odoo.IntegrationError):
        workflow.export_card(card['id'], card['version'], Lost())
    with pytest.raises(workflow.Conflict, match='epäselväksi'):
        workflow.export_card(card['id'], card['version'])
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM fixture_products').fetchone()[0] == 0


def test_missing_key_does_not_fallback_or_lose_card():
    card = draft()
    with pytest.raises(ValueError, match='avain puuttuu'):
        workflow.run_analysis('live')
    assert workflow.get_card(card['id']) == card


def test_sparse_evidence_is_rejected_before_model(monkeypatch):
    snap = workflow.snapshot()
    snap['observations'] = [snap['observations'][-1]]
    def unexpected(*args):
        pytest.fail('Sparse evidence must not invoke a paid model')
    monkeypatch.setattr(llm, 'call', unexpected)
    with pytest.raises(ValueError, match='liian vähäinen'):
        llm.analyze(snap, 'live')


def test_odoo_rejects_remote_and_duplicate_codes(monkeypatch):
    monkeypatch.setenv('ODOO_URL', 'https://company.example')
    with pytest.raises(odoo.IntegrationError):
        odoo.OdooAdapter()
    monkeypatch.setenv('ODOO_URL', 'http://127.0.0.1:8069')
    source = odoo.OdooAdapter()
    monkeypatch.setattr(source, 'read', lambda *args: [{'id': 1}, {'id': 2}])
    with pytest.raises(odoo.IntegrationError, match='useita'):
        source.find_service('DEMO-SVC-001')


def test_api_origin_and_validation():
    with TestClient(app) as client:
        assert client.get('/api/health').status_code == 200
        assert client.post('/api/runs', json={'mode':'example'}, headers={'origin':'https://evil.example'}).status_code == 403
        assert client.post('/api/runs', json={'mode':'unknown'}).status_code == 422
        assert client.get('/api/data').json()['facts']['content_delay_customers'] == 3

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import catalog, decomposition as d, llm, store
from app.main import app
from app.schemas import VersionRequest
from app.workflow import Conflict


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_DATABASE_URL', 'sqlite:///' + str(tmp_path / 'test.db'))
    monkeypatch.setenv('ODOO_MODE', 'fixture')
    store.init()


def copy(name='Kartoitus'):
    return d.ProductCopy(name=name, description='Rajattu kartoituspalvelu', service_promise='Dokumentoitu lähtötilanne',
        outcome='Kirjallinen suunnitelma', deliverables='Työpaja ja raportti', exclusions='Toteutus ei sisälly',
        acceptance_criteria='Sovitut kohdat dokumentoitu', target_need='Työn rajaaminen', suitable_when='Ennen toteutusta',
        unsuitable_when='Rajaus on jo valmis', prerequisites='Yhteyshenkilö', task_instructions='Pidä työpaja, kirjoita raportti',
        unit='unit', billing='fixed')


def proposal():
    return d.Proposal(name='Kehityspalvelu', description='Kartoitus ja erillinen työ', service_promise='Sovittu toimitus',
        parts=[d.Part(choice='new', catalog_item_id=None, proposed_product=copy(), quantity=None,
                      work_description='Kartoitus rajatulle kohteelle', reason='Toistettava rajattu lopputulos', evidence_quote='kartoitus', work_group_ids=['G1'])],
        assumptions=['Rajaus tarkistettava'], open_questions=['Osallistujamäärä?'], uncovered_scope=[])


def work_plan(count=1):
    return d.WorkPlan(kind='base_product' if count == 1 else 'service', rationale='Erilliset toimitettavat lopputulokset',
        groups=[d.WorkGroup(id=f'G{i+1}', name=f'Osa {i+1}', outcome='Dokumentoitu tulos',
                           steps=[d.WorkStep(name='Toteutus', hours=4, basis='estimate', rationale='Testiarvio')]) for i in range(count)], open_questions=[])


def model_output(schema, value):
    # Deliberately allow invalid mocked content to exercise application validation.
    slots = schema.model_fields['parts'].annotation
    return schema.model_construct(**value.model_dump(exclude={'parts'}),
        parts=slots.model_construct(**{f'part_{i+1}':part for i, part in enumerate(value.parts)}))


def start(monkeypatch, value=None):
    value = value or proposal()
    for i, part in enumerate(value.parts):
        part.work_group_ids = [f'G{i+1}']
    monkeypatch.setattr(llm, 'call', lambda schema, payload, prompt, **kwargs: (work_plan(len(value.parts)) if schema is d.WorkPlan else model_output(schema, value), {'model': 'test'}))
    return d.start(d.Start(name='Kartoitus', description='Palveluun sisältyy kartoitus ja rajattu asiantuntijatyö.'))


def test_model_receives_catalog_and_no_writes_before_review(monkeypatch):
    existing = catalog.create_item(catalog.CatalogContent(**copy('Muu tuote').model_dump()))
    seen = []
    def call(schema, payload, prompt, **kwargs):
        if schema is d.WorkPlan:
            return work_plan(), {'model':'test'}
        seen.append(payload)
        assert 'evidence_quote' in prompt
        return model_output(schema, proposal()), {'model': 'test'}
    monkeypatch.setattr(llm, 'call', call)
    result = d.start(d.Start(name='Kartoitus', description='Palveluun kuuluu kartoitus ja suunnitelma.'))
    assert result['state'] == 'draft'
    assert seen[0]['catalog'][0]['id'] == existing['id']
    assert len(catalog.list_items()) == 1
    assert d.recipe(result['id']) is None


def test_expert_reuse_and_new_product_become_versioned_recipe(monkeypatch):
    expert = catalog.create_item(catalog.CatalogContent(**{**copy('Asiantuntijatyö').model_dump(), 'unit':'hour', 'billing':'timesheet', 'product_kind':'expert_work'}))
    value = proposal()
    value.parts.append(d.Part(choice='expert', catalog_item_id=expert['id'], proposed_product=None, quantity=4,
        work_description='Asiakkaan järjestelmän erillinen selvitys, toteutus ei sisälly.', reason='Kertaluonteinen tarve; ei uutta tuotetta.', evidence_quote='asiantuntijatyö'))
    record = start(monkeypatch, value)
    result = d.materialize(record['id'], VersionRequest(expected_version=1))
    assert d.materialize(record['id'], VersionRequest(expected_version=1)) == result
    recipe = d.recipe(record['id'])
    assert len(catalog.list_items()) == 2
    assert recipe['state'] == 'draft' and len(recipe['lines']) == 2
    assert recipe['lines'][1]['quantity'] == 4
    catalog.edit_item(expert['id'], catalog.CatalogEdit(**{**expert['content'], 'name':'Changed', 'expected_version':1}))
    assert d.recipe(record['id'])['lines'][1]['product_snapshot']['content']['name'] == 'Asiantuntijatyö'


def test_concurrent_materialization_is_idempotent(monkeypatch):
    record = start(monkeypatch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: d.materialize(record['id'], VersionRequest(expected_version=1)), range(2)))
    assert results[0]['materialized_item_ids'] == results[1]['materialized_item_ids']
    assert results[0]['recipe_id'] is None
    assert len(catalog.list_items()) == 1


def test_catalog_changes_prevent_duplicate_creation(monkeypatch):
    first = start(monkeypatch)
    second = start(monkeypatch)
    d.materialize(first['id'], VersionRequest(expected_version=1))
    with pytest.raises(Conflict, match='Katalogi on muuttunut'):
        d.materialize(second['id'], VersionRequest(expected_version=1))
    assert len(catalog.list_items()) == 1
    assert d.recipe(second['id']) is None


@pytest.mark.parametrize('change', ['fake_quote', 'fake_id', 'invalid_quantity', 'expert_unit'])
def test_bad_model_output_never_saves(monkeypatch, change):
    value = proposal()
    part = value.parts[0]
    if change == 'fake_quote': part.evidence_quote = 'lähteessä ei ole tätä'
    if change == 'fake_id': part.choice, part.catalog_item_id, part.proposed_product = 'reuse', 'missing', None
    if change == 'invalid_quantity': part.quantity = float('inf')
    if change == 'expert_unit': part.choice = 'expert'
    with pytest.raises(ValueError): start(monkeypatch, value)
    assert not d.records() and not catalog.list_items()


def test_edit_history_stale_version_and_api_origin(monkeypatch):
    record = start(monkeypatch)
    value = proposal()
    value.service_promise = 'Käyttäjän tarkentama lupaus'
    updated = d.edit(record['id'], d.Edit(expected_version=1, proposal=value))
    assert updated['version'] == 2
    with pytest.raises(Conflict): d.edit(record['id'], d.Edit(expected_version=1, proposal=value))
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM decomposition_versions').fetchone()[0] == 2
    with TestClient(app) as client:
        assert client.get('/api/decompositions').json()[0]['proposal']['service_promise'] == value.service_promise
        assert client.post('/api/decompositions', json={'name':'x','description':'short'}).status_code == 422
        assert client.post('/api/decompositions', json={}, headers={'Origin':'https://other.test'}).status_code == 403


def test_model_failure_preserves_existing_work(monkeypatch):
    record = start(monkeypatch)
    def fail(*args, **kwargs): raise ValueError('Mallikutsu epäonnistui')
    monkeypatch.setattr(llm, 'call', fail)
    with pytest.raises(ValueError):
        d.start(d.Start(name='Test', description='Palveluun kuuluu kartoitus ja suunnitelma.'))
    assert d.records() == [record]


def test_invalid_quote_gets_one_bounded_repair(monkeypatch):
    bad = proposal()
    bad.parts[0].evidence_quote = 'Kartoituksen kuvitteellinen lainaus'
    values = iter([bad, proposal()])
    calls = []
    def call(schema, payload, prompt, **kwargs):
        if schema is d.WorkPlan:
            return work_plan(), {'model':'test'}
        calls.append(prompt)
        return model_output(schema, next(values)), {'model':'test'}
    monkeypatch.setattr(llm, 'call', call)
    record = d.start(d.Start(name='Kartoitus', description='Palveluun kuuluu kartoitus ja suunnitelma.'))
    assert len(calls) == 2 and 'hylättiin' in calls[1]
    assert record['meta']['validation_retries'] == 1


def test_missing_expert_work_cannot_silently_disappear():
    source = {'source_id':'manual', 'description':'Palveluun kuuluu kartoitus. Lisäksi selvitetään vanha tiedostomuoto asiantuntijatyönä.'}
    with pytest.raises(ValueError, match='tekstiosa puuttuu'):
        d.validate(proposal(), source, [])
    value = proposal()
    value.uncovered_scope = ['Lisäksi selvitetään vanha tiedostomuoto asiantuntijatyönä.']
    d.validate(value, source, [])


def test_multi_product_plan_cannot_collapse_to_one_part():
    source = {'source_id':'test', 'name':'Kartoitus', 'description':'kartoitus'}
    with pytest.raises(ValueError, match='oman tuoterivin'):
        d.validate(proposal(), source, [], work_plan(3).model_dump())


def test_work_hours_cover_explicit_total_and_reject_double_assignment():
    plan = work_plan(3)
    d.validate_work_plan(plan, {'total_hours':12})
    assert d.workload(plan.model_dump()) == {'known_hours':12, 'unknown_steps':0, 'estimated_steps':3}
    with pytest.raises(ValueError, match='kokonaistyömäärä'):
        d.validate_work_plan(plan, {'total_hours':16})
    plan.groups[1].id = plan.groups[0].id
    with pytest.raises(ValueError, match='yksilöllisiä'):
        d.validate_work_plan(plan, {})


def test_single_service_is_product_without_wrapper_recipe(monkeypatch):
    record = start(monkeypatch)
    result = d.materialize(record['id'], VersionRequest(expected_version=1))
    assert result['kind'] == 'base_product' and result['recipe_id'] is None
    assert len(result['materialized_item_ids']) == 1
    with store.db() as c:
        assert c.execute('SELECT count(*) FROM recipes').fetchone()[0] == 0
    assert catalog.list_items()[0]['content']['name'] == record['source']['name']


def test_hour_allocation_preserves_source_and_marks_estimates():
    plan = work_plan(3)
    plan.groups[0].steps[0].basis = 'source'
    d.allocate_hours(plan, 20)
    assert [g.steps[0].hours for g in plan.groups] == [4,8,8]
    assert 'sovitettu' in plan.rationale
    d.validate_work_plan(plan, {'total_hours':20})
    with pytest.raises(ValueError, match='Lähteessä annetut'):
        d.allocate_hours(plan, 3)


def test_same_existing_hour_product_can_cover_separate_groups(monkeypatch):
    item = catalog.create_item(catalog.CatalogContent(**{**copy('Asiantuntijatyö').model_dump(),
        'unit':'hour', 'billing':'timesheet', 'product_kind':'expert_work'}))
    value = proposal()
    part = value.parts[0]
    part.choice = 'expert'
    part.catalog_item_id = item['id']
    part.proposed_product = None
    part.quantity = 999  # Generation must calculate this from phases, not trust model arithmetic.
    value.parts.append(part.model_copy(deep=True))
    record = start(monkeypatch, value)
    assert [p['quantity'] for p in record['proposal']['parts']] == [4,4]
    result = d.materialize(record['id'], VersionRequest(expected_version=1))
    assert len(catalog.list_items()) == 1
    assert len(d.recipe(result['id'])['lines']) == 2


def test_generation_schema_requires_copy_and_source_quote(monkeypatch):
    def call(schema, payload, prompt, **kwargs):
        if schema is d.WorkPlan:
            return work_plan(), {'model':'test'}
        valid = proposal().model_dump()
        valid['parts'] = {'part_1':valid['parts'][0]}
        valid['parts']['part_1']['evidence_quote'] = payload['service']['description']
        schema.model_validate(valid)
        valid['parts']['part_1']['proposed_product'] = None
        with pytest.raises(ValueError):
            schema.model_validate(valid)
        return model_output(schema, proposal()), {'model':'test'}
    monkeypatch.setattr(llm, 'call', call)
    d.start(d.Start(name='Kartoitus', description='Palveluun kuuluu kartoitus ja suunnitelma.'))

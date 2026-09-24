"""Versioned product definitions. Content approval is not permission to publish to Odoo."""
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from functools import cache
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter
from pydantic import ConfigDict, Field, model_validator

from . import store, odoo
from .schemas import Strict, VersionRequest
from .workflow import Conflict


class CatalogContent(Strict):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=8000)
    service_promise: str = Field(default='', max_length=4000)
    product_kind: Literal['standard', 'expert_work'] = 'standard'
    list_price: Decimal | None = Field(default=None, ge=0, le=10000000)
    odoo_project_id: int | None = Field(default=None, gt=0)
    outcome: str = Field(min_length=1, max_length=4000)
    deliverables: str = Field(min_length=1, max_length=8000)
    exclusions: str = Field(min_length=1, max_length=4000)
    acceptance_criteria: str = Field(min_length=1, max_length=4000)
    target_need: str = Field(min_length=1, max_length=4000)
    suitable_when: str = Field(default='', max_length=4000)
    unsuitable_when: str = Field(default='', max_length=4000)
    prerequisites: str = Field(default='', max_length=4000)
    unit: Literal['unit', 'hour'] = 'unit'
    quantity_min: Decimal = Field(default=Decimal('1'), gt=0, le=100000)
    quantity_max: Decimal = Field(default=Decimal('1'), gt=0, le=100000)
    billing: Literal['fixed', 'timesheet'] = 'fixed'
    delivery: Literal['manual', 'task_existing_project', 'project_and_task'] = 'manual'
    task_instructions: str = Field(default='', max_length=8000)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    requires: list[str] = Field(default_factory=list, max_length=100)
    excludes: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def consistent(self):
        if self.product_kind == 'expert_work' and self.unit != 'hour':
            raise ValueError('Avoin asiantuntijatyö edellyttää tuntiyksikköä.')
        if self.quantity_max < self.quantity_min:
            raise ValueError('Enimmäismäärä ei voi olla vähimmäismäärää pienempi.')
        if self.billing == 'timesheet' and self.unit != 'hour':
            raise ValueError('Tuntikirjauksiin perustuva laskutus edellyttää tuntiyksikköä.')
        if set(self.requires) & set(self.excludes):
            raise ValueError('Samaa tuotetta ei voi sekä vaatia että sulkea pois.')
        return self


class CatalogEdit(CatalogContent):
    expected_version: int = Field(ge=1)


def now():
    return datetime.now(timezone.utc).isoformat()


def get_item(identifier, c):
    row = c.execute('SELECT payload FROM catalog_items WHERE id=?', (identifier,)).fetchone()
    if not row:
        raise KeyError('Katalogituotetta ei löytynyt.')
    return json.loads(row['payload'])


def persist(c, item):
    payload = store.encode(item)
    c.execute('INSERT INTO catalog_items VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (item['id'], payload))
    c.execute('INSERT INTO catalog_versions VALUES(?,?,?)', (item['id'], item['version'], payload))


def check_graph(c, identifier, content):
    items = {r['id']: json.loads(r['payload'])['content'] for r in c.execute('SELECT * FROM catalog_items')}
    items[identifier] = content
    for ref in content['requires'] + content['excludes']:
        if ref == identifier or ref not in items:
            raise ValueError('Riippuvuuden tai ristiriidan tulee viitata toiseen katalogituotteeseen.')
    visiting, visited = set(), set()

    def visit(key):
        if key in visiting:
            raise ValueError('Tuoteriippuvuudet muodostavat syklin.')
        if key in visited:
            return
        visiting.add(key)
        for ref in items[key]['requires']:
            visit(ref)
        visiting.remove(key)
        visited.add(key)

    for key in items:
        visit(key)
    # Detect contradictions anywhere in a product's transitive dependency set.
    @cache
    def closure(key):
        result = {key}
        for ref in items[key]['requires']:
            result.update(closure(ref))
        return result
    for key in items:
        required = closure(key)
        if any(set(items[ref]['excludes']) & required for ref in required):
            raise ValueError('Pakolliset riippuvuudet sisältävät keskenään ristiriitaisia tuotteita.')


router = APIRouter(prefix='/api/catalog', tags=['catalog'])


@router.get('')
def list_items():
    with store.db() as c:
        return [json.loads(r['payload']) for r in c.execute('SELECT payload FROM catalog_items ORDER BY rowid DESC')]


@router.post('')
def create_item(body: CatalogContent):
    item = {'id': str(uuid4()), 'version': 1, 'state': 'draft', 'created_at': now(),
            'content': body.model_dump(mode='json'), 'approved_at': None}
    with store.db(write=True) as c:
        check_graph(c, item['id'], item['content'])
        persist(c, item)
    return item


@router.post('/capabilities')
def inspect_capabilities():
    snapshot = odoo.adapter().catalog_capabilities()
    snapshot.update(id=str(uuid4()), fetched_at=now())
    with store.db(write=True) as c:
        c.execute('INSERT INTO catalog_capabilities VALUES(?,?,?)', (snapshot['id'], snapshot['fetched_at'], store.encode(snapshot)))
    return snapshot


@router.get('/capabilities')
def latest_capabilities():
    with store.db() as c:
        row = c.execute('SELECT payload FROM catalog_capabilities ORDER BY rowid DESC LIMIT 1').fetchone()
    return json.loads(row['payload']) if row else None


@router.get('/{identifier}/history')
def history(identifier: str):
    with store.db() as c:
        get_item(identifier, c)
        return [json.loads(r['payload']) for r in c.execute('SELECT payload FROM catalog_versions WHERE item_id=? ORDER BY version DESC', (identifier,))]


@router.put('/{identifier}')
def edit_item(identifier: str, body: CatalogEdit):
    with store.db(write=True) as c:
        item = get_item(identifier, c)
        if c.execute("SELECT 1 FROM catalog_exports WHERE item_id=? AND status IN ('pending','uncertain','exported')", (identifier,)).fetchone():
            raise Conflict('Viety tai epäselvän viennin tuote on lukittu. Selvitä vienti; tämän version Odoo-päivitykset tehdään Odoossa.')
        if item['version'] != body.expected_version:
            raise Conflict('Tuote on muuttunut. Lataa uusin versio ennen tallennusta.')
        content = body.model_dump(mode='json', exclude={'expected_version'})
        check_graph(c, identifier, content)
        item.update(version=item['version'] + 1, content=content, state='draft', approved_at=None)
        persist(c, item)
    return item


@router.post('/{identifier}/approve')
def approve_item(identifier: str, body: VersionRequest):
    with store.db(write=True) as c:
        item = get_item(identifier, c)
        if item['version'] != body.expected_version:
            raise Conflict('Tuote on muuttunut. Tarkista uusin versio.')
        if item['state'] == 'approved':
            return item
        check_graph(c, identifier, item['content'])
        for ref in item['content']['requires']:
            if get_item(ref, c)['state'] != 'approved':
                raise ValueError('Hyväksy ensin tuotteen pakolliset riippuvuudet.')
        item.update(version=item['version'] + 1, state='approved', approved_at=now())
        persist(c, item)
    return item


@router.get('/{identifier}/similar')
def similar_items(identifier: str):
    """Transparent lexical aid; this is not a semantic model or a duplicate guarantee."""
    with store.db() as c:
        item = get_item(identifier, c)
        def tokens(content):
            return set(re.findall(r'\w{4,}', (content['target_need'] + ' ' + content['outcome']).casefold()))
        reference = tokens(item['content'])
        matches = []
        for row in c.execute('SELECT * FROM catalog_items WHERE id<>?', (identifier,)):
            other = json.loads(row['payload'])
            shared = reference & tokens(other['content'])
            if shared:
                matches.append({'id': other['id'], 'name': other['content']['name'], 'shared_terms': sorted(shared)})
    return sorted(matches, key=lambda x: (-len(x['shared_terms']), x['name']))[:10]

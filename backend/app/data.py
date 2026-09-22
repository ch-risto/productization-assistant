import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now(timezone.utc).isoformat()


def fixture():
    value = json.loads((ROOT / 'demo-data/dataset.json').read_text(encoding='utf-8'))
    ids = [x['source_id'] for group in ('services','customers','projects','observations','opportunities','competitors') for x in value[group]]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate source identifiers')
    projects = {x['source_id']: x for x in value['projects']}
    customers = {x['source_id'] for x in value['customers']}
    services = {x['source_id'] for x in value['services']}
    for p in projects.values():
        if p['customer_id'] not in customers or p['service_id'] not in services:
            raise ValueError('Broken project reference')
    for o in value['observations']:
        if o['quote'] not in projects[o['project_id']]['notes']:
            raise ValueError('Evidence quote missing from original note')
    return value


def facts(data):
    projects = {x['source_id']: x for x in data['projects']}
    matched = {o['project_id'] for o in data['observations'] if o['topic'] == 'content_delay'}
    return {
        'project_count': len(projects),
        'customer_count': len(data['customers']),
        'content_delay_projects': len(matched),
        'content_delay_customers': len({projects[p]['customer_id'] for p in matched}),
        'segments': dict(Counter(c['segment'] for c in data['customers'])),
        'classification_origin': 'Käsin merkityt synteettiset havainnot; luvut laskettu koodilla.',
    }


def source_index(snapshot):
    return {x['source_id']: x for group in ('services','customers','projects','observations','opportunities','competitors') for x in snapshot[group]}


def validate_sources(ids, snapshot):
    known = source_index(snapshot)
    unknown = set(ids) - set(known)
    if unknown:
        raise ValueError('Tuntemattomia lähdetunnisteita: ' + ', '.join(sorted(unknown)))

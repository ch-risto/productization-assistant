import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now(timezone.utc).isoformat()


def fixture():
    value = json.loads((ROOT / os.getenv('DATASET_PATH', 'demo-data/JJ-dataset2.json')).read_text(encoding='utf-8'))
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
        identifier = o.get('project_id')
        if not o.get('quote') or not o.get('origin'):
            raise ValueError(f"{o['source_id']}: havainnolta puuttuu teksti tai alkuperä.")
        if identifier is None:
            o['evidence_kind'] = 'general_note'
            o['verification'] = 'Yleinen muistiinpano; ei vahvistettu projektin alkuperäistekstistä.'
        else:
            if identifier not in projects:
                raise ValueError(f"{o['source_id']}: tuntematon projekti {identifier}.")
            if o['quote'] not in projects[identifier]['notes']:
                raise ValueError(f"{o['source_id']}: lainaus puuttuu projektin alkuperäistekstistä.")
            o['evidence_kind'] = 'project_quote'
    return value


def facts(data):
    projects = {x['source_id']: x for x in data['projects']}
    topics = {}
    for observation in data['observations']:
        topic = observation.get('topic') or 'Luokittelematon'
        entry = topics.setdefault(topic, {'observations': 0, 'projects': set(), 'customers': set(), 'general_notes': 0})
        entry['observations'] += 1
        project = projects.get(observation.get('project_id'))
        if project:
            entry['projects'].add(project['source_id'])
            entry['customers'].add(project['customer_id'])
        else:
            entry['general_notes'] += 1
    return {
        'project_count': len(projects),
        'customer_count': len(data['customers']),
        'observation_count': len(data['observations']),
        'topics': {topic: {**entry, 'projects': len(entry['projects']), 'customers': len(entry['customers'])}
                   for topic, entry in sorted(topics.items())},
        'segments': dict(Counter(c.get('segment') or 'Ei määritelty' for c in data['customers'])),
        'general_note_count': sum(o.get('project_id') is None for o in data['observations']),
        'classification_origin': 'Aineistossa annetut aiheet; lukumäärät laskettu koodilla. Yleisyys ei yksin osoita tarvetta tai tärkeyttä.',
    }


def source_index(snapshot):
    return {x['source_id']: x for group in ('services','customers','projects','observations','opportunities','competitors') for x in snapshot[group]}


def validate_sources(ids, snapshot):
    known = source_index(snapshot)
    unknown = set(ids) - set(known)
    if unknown:
        raise ValueError('Tuntemattomia lähdetunnisteita: ' + ', '.join(sorted(unknown)))

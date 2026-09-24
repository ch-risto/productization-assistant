"""Local Odoo 18 smoke check. --write creates one clearly marked test product."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
os.environ['APP_DATABASE_URL'] = 'sqlite:///data/catalog-export-verification.db'
os.environ['ODOO_MODE'] = 'odoo'

from app import catalog, catalog_export, store
from app.schemas import VersionRequest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    store.init()
    name = 'TESTI - perustuotekatalogin vienti 24.9.2026'
    records = [r for r in catalog.list_items() if r['content']['name'] == name]
    if records:
        item = records[0]
    else:
        item = catalog.create_item(catalog.CatalogContent(name=name, outcome='Varmennettu katalogivienti',
            description='Synteettinen integraatiotesti, ei asiakastoimitus.', service_promise='Ei kaupallista lupausta.',
            deliverables='Vientikokeen testituote', exclusions='Ei todellista työtä', target_need='Vientipolun testaus',
            acceptance_criteria='Tuoteasetukset luettu takaisin Odoosta', task_instructions='Tarkista tuote.\nTarkista toistuva vienti.',
            list_price='125', delivery='manual'))
        item = catalog.approve_item(item['id'], VersionRequest(expected_version=item['version']))
    plan = catalog_export.preview(item['id'], VersionRequest(expected_version=item['version']))
    result = {'mode':'read_only_preview', 'target':plan['target'], 'company':plan['company'], 'currency':plan['currency'],
              'unit':plan['unit'], 'taxes':plan['taxes'], 'name':name}
    if args.write:
        body = catalog_export.ExportRequest(expected_version=item['version'], plan_id=plan['id'])
        first = catalog_export.export(item['id'], body)
        second = catalog_export.export(item['id'], body)
        assert first == second
        result.update(mode='real_odoo_create_and_readback', export=first, repeated_export_same_product=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.write:
        (ROOT / 'data/catalog-export-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

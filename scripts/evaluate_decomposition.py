"""Explicit live evaluation with synthetic inputs and an isolated local catalog."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
os.environ['APP_DATABASE_URL'] = 'sqlite:///data/decomposition-evaluation-3.db'
os.environ['ODOO_MODE'] = 'fixture'

from app import decomposition as d, store, llm


def main():
    store.init()
    raw = []
    original_call = llm.call
    def capture(*args, **kwargs):
        result, meta = original_call(*args, **kwargs)
        raw.append({'result':result.model_dump(mode='json'), 'meta':meta})
        (ROOT / 'data/decomposition-evaluation-2-raw.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
        return result, meta
    llm.call = capture
    cases = [
        {'name':'Synteettinen verkkopalvelun uudistus', 'total_hours':24,
         'description':'Palveluun sisältyy tarvekartoitus ja kirjallinen tekninen määrittely, kahden sivupohjan toteutus sekä käyttäjien koulutus. Kartoitus tuottaa tarvelistan. Määrittely tuottaa toteutussuunnitelman. Sivupohjat luovutetaan testattuina. Koulutus sisältää yhden koulutustilaisuuden ja ohjeen. Ylläpito ei sisälly palveluun.'},
        {'name':'Synteettinen käyttökoulutus', 'total_hours':4,
         'description':'Yksi käyttökoulutus sovitulle käyttäjäryhmälle. Toimitus sisältää valmistelun, kahden tunnin koulutustilaisuuden ja osallistujille toimitettavan ohjeen. Kaikki työvaiheet tuottavat yhden koulutustoimituksen; teknistä toteutusta ei sisälly.'},
    ]
    results = []
    for case in cases:
        record = d.start(d.Start(**case))
        result = {'name':case['name'], 'id':record['id'], 'kind':record['kind'],
                  'parts':len(record['proposal']['parts']), 'workload':record['workload'],
                  'work_plan':record['work_plan'], 'proposal':record['proposal'], 'meta':record['meta']}
        results.append(result)
        (ROOT / 'data/decomposition-evaluation-2.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({key:result[key] for key in ['name','id','kind','parts','workload']}, ensure_ascii=False), flush=True)
    assert results[0]['kind'] == 'service' and results[0]['parts'] >= 3
    assert results[1]['kind'] == 'base_product' and results[1]['parts'] == 1


if __name__ == '__main__':
    main()

import { useEffect, useState } from 'react';
import { Decomposition } from './Decomposition';
import { CatalogExport } from './CatalogExport';

type Content = {
  name: string; description: string; service_promise: string; product_kind: string; list_price: string | null; odoo_project_id: number | null; outcome: string; deliverables: string; exclusions: string; acceptance_criteria: string;
  target_need: string; suitable_when: string; unsuitable_when: string; prerequisites: string;
  unit: string; quantity_min: string; quantity_max: string; billing: string; delivery: string;
  task_instructions: string; source_refs: string[]; requires: string[]; excludes: string[];
};
type Item = { id: string; version: number; state: string; content: Content; approved_at: string | null };
type Capability = { target: string; mode: string; fetched_at: string; company: [number, string] | null;
  checks: Record<string, string>; note: string; units: { id: number; name: string; category_id: [number, string] }[] };
const blank: Content = { name: '', description: '', service_promise: '', product_kind: 'standard', list_price: null, odoo_project_id: null, outcome: '', deliverables: '', exclusions: '', acceptance_criteria: '',
  target_need: '', suitable_when: '', unsuitable_when: '', prerequisites: '', unit: 'unit', quantity_min: '1',
  quantity_max: '1', billing: 'fixed', delivery: 'manual', task_instructions: '', source_refs: [], requires: [], excludes: [] };
async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api/catalog' + path, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Tarkista pakolliset kentät, määrät ja yksikkö.');
  return data;
}
const textFields: [keyof Content, string][] = [
  ['name', 'Perustuotteen nimi'], ['outcome', 'Asiakkaalle syntyvä lopputulos'], ['target_need', 'Mihin tarpeeseen tuote vastaa?'],
  ['deliverables', 'Toimitussisältö'], ['exclusions', 'Rajaukset: mitä ei sisälly?'], ['acceptance_criteria', 'Milloin toimitus hyväksytään?'],
  ['suitable_when', 'Sopii tilanteeseen'], ['unsuitable_when', 'Ei sovi tilanteeseen'], ['prerequisites', 'Tarvittavat lähtötiedot'],
  ['task_instructions', 'Projektitehtävän työohje ja valmistumisen ehdot'], ['description', 'Tuotteen kuvaus'], ['service_promise', 'Palvelulupaus'],
];
const checkLabels: Record<string, string> = { fixed: 'Kiinteä laskutus', timesheet: 'Tuntikirjauksiin perustuva laskutus',
  task_existing_project: 'Tehtävä olemassa olevaan projektiin', project_and_task: 'Uusi projekti ja tehtävä',
  subscriptions: 'Jatkuva laskutus', milestones: 'Etappilaskutus', units: 'Myyntiyksiköt' };
const statusLabels: Record<string, string> = { available: 'Kenttävalinta löytyy — työnkulku testaamatta', unavailable: 'Kenttävalintaa ei löytynyt',
  unverified: 'Ei varmennettu', inspected: 'Luettu Odoosta' };

export function Catalog() {
  const [items, setItems] = useState<Item[]>([]);
  const [selected, setSelected] = useState<Item | null>(null);
  const [draft, setDraft] = useState<Content>({ ...blank });
  const [capability, setCapability] = useState<Capability | null>(null);
  const [history, setHistory] = useState<Item[]>([]);
  const [similar, setSimilar] = useState<{ id: string; name: string; shared_terms: string[] }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [filter, setFilter] = useState('');
  const dirty = JSON.stringify(draft) !== JSON.stringify({ ...blank, ...(selected?.content ?? {}) });
  async function action(fn: () => Promise<void>) {
    setBusy(true); setError(''); setNotice('');
    try { await fn(); } catch (e) { setError(e instanceof Error ? e.message : 'Toiminto epäonnistui.'); }
    finally { setBusy(false); }
  }
  useEffect(() => { void action(async () => {
    const [rows, snapshot] = await Promise.all([api<Item[]>(''), api<Capability | null>('/capabilities')]);
    setItems(rows); setCapability(snapshot);
  }); }, []);
  async function select(item: Item | null) {
    const [versions, matches] = item ? await Promise.all([api<Item[]>('/' + item.id + '/history'), api<typeof similar>('/' + item.id + '/similar')]) : [[], []];
    setSelected(item); setDraft({ ...blank, ...structuredClone(item?.content ?? {}) }); setHistory(versions); setSimilar(matches);
  }
  async function save() {
    await action(async () => {
      const item = await api<Item>(selected ? '/' + selected.id : '', selected ? 'PUT' : 'POST', selected ? { ...draft, expected_version: selected.version } : draft);
      setItems(await api<Item[]>('')); await select(item); setNotice('Luonnos tallennettu. Hyväksy sisältö tarkistuksen jälkeen.');
    });
  }
  return <>
    <div className="message info">Perustuote on uudelleenkäytettävä myytävä kokonaisuus. Tekoäly auttaa pilkkomaan palvelut ja laatimaan tuotteiden sisällön. Tuotteet tallentuvat ensin Palvelupajaan. Vie hyväksytty tuote Odoohon editorin vientitoiminnolla.</div>
    <Decomposition onCatalogChanged={async () => setItems(await api<Item[]>('' ))} />
    {error && <div className="message error" role="alert">{error}</div>}
    {notice && <div className="message success" role="status">{notice}</div>}
    {busy && <p role="status">Tallennetaan tai haetaan tietoja…</p>}
    <section className="panel">
      <div className="section-title"><h2>Perustuotekatalogi</h2><div className="actions"><button className="secondary" disabled={busy || dirty} onClick={() => void action(async () => { const rows = await api<Item[]>(''); setItems(rows); await select(rows.find(x => x.id === selected?.id) ?? null); })}>Lataa tallennetut tiedot</button><button className="secondary" disabled={busy || dirty} onClick={() => void action(() => select(null))}>Uusi perustuote</button></div></div>
      <label>Hae nimestä, tarpeesta tai lopputuloksesta<input value={filter} onChange={e => setFilter(e.target.value)} /></label>
      <div className="catalog-table-wrap"><table className="catalog-table"><thead><tr><th>Perustuote</th><th>Myyntiyksikkö</th><th>Tila</th><th>Versio</th><th /></tr></thead><tbody>
        {items.filter(x => [x.content.name, x.content.target_need, x.content.outcome].join(' ').toLocaleLowerCase().includes(filter.toLocaleLowerCase())).map(item => <tr key={item.id}>
          <td><strong>{item.content.name}</strong><p className="caption">{item.content.outcome}</p></td><td>{item.content.unit === 'hour' ? 'Tunti' : 'Kappale / toimitus'}</td>
          <td>{item.state === 'approved' ? 'Sisältö hyväksytty' : 'Luonnos'}</td><td>{item.version}</td><td><button className="text-button" disabled={busy || dirty} onClick={() => void action(() => select(item))}>Avaa</button></td>
        </tr>)}
      </tbody></table></div>
      {!items.length && <p>Katalogi on tyhjä. Lisää ensimmäinen rajattu perustuote alla.</p>}
      {dirty && <p className="caption">Tallenna tai peru muutokset ennen tuotteen vaihtamista.</p>}
    </section>
    <section className="panel">
      <div className="section-title"><h2>{selected ? selected.content.name : 'Uusi perustuote'}</h2><span className="tag">{selected ? `Versio ${selected.version} · ${selected.state === 'approved' ? 'Sisältö hyväksytty' : 'Luonnos'}` : 'Luonnos'}</span></div>
      <form onSubmit={e => { e.preventDefault(); void save(); }}>
        <fieldset disabled={busy} className="catalog-fields"><div className="form-grid">
          {textFields.map(([key, label], i) => <label key={key}>{label}{i < 6 ? ' *' : ''}<textarea rows={key === 'name' ? 1 : 3} required={i < 6} maxLength={key === 'name' ? 200 : ['deliverables', 'task_instructions', 'description'].includes(key) ? 8000 : 4000} value={String(draft[key])} onChange={e => setDraft({ ...draft, [key]: e.target.value })} /></label>)}
          <label>Tuotetyyppi<select value={draft.product_kind} onChange={e => setDraft({ ...draft, product_kind: e.target.value, ...(e.target.value === 'expert_work' ? { unit: 'hour', billing: 'timesheet' } : {}) })}><option value="standard">Vakioitu perustuote</option><option value="expert_work">Avoin asiantuntijatyö</option></select></label><label>Myyntiyksikön ehdotus<select value={draft.unit} onChange={e => setDraft({ ...draft, unit: e.target.value })}><option value="unit">Kappale / rajattu toimitus</option><option value="hour">Tunti</option></select></label>
          <label>Laskutusmallin ehdotus<select value={draft.billing} onChange={e => setDraft({ ...draft, billing: e.target.value, ...(e.target.value === 'timesheet' ? { unit: 'hour' } : {}) })}><option value="fixed">Kiinteä hinta / tilattu määrä</option><option value="timesheet">Toteutuneet tuntikirjaukset</option></select></label>
          <label>Vähimmäismäärä<input type="number" min="0.001" max="100000" step="any" required value={draft.quantity_min} onChange={e => setDraft({ ...draft, quantity_min: e.target.value })} /></label>
          <label>Enimmäismäärä<input type="number" min="0.001" max="100000" step="any" required value={draft.quantity_max} onChange={e => setDraft({ ...draft, quantity_max: e.target.value })} /></label>
          <label>Yksikköhinta Odoo-yrityksen valuutassa<input type="number" min="0" step="0.01" value={draft.list_price ?? ''} onChange={e => setDraft({ ...draft, list_price: e.target.value || null })} /></label>
          <label className="wide">Toimitusmallin ehdotus<select value={draft.delivery} onChange={e => setDraft({ ...draft, delivery: e.target.value, odoo_project_id: e.target.value === 'task_existing_project' ? draft.odoo_project_id : null })}><option value="manual">Projektit ja tehtävät liitetään käsin</option><option value="task_existing_project">Tehtävä olemassa olevaan projektiin</option><option value="project_and_task">Uusi projekti ja tehtävä</option></select></label>
        </div>
        {draft.delivery === 'task_existing_project' && <label>Kohdeprojektin Odoo-tunniste<input type="number" min="1" value={draft.odoo_project_id ?? ''} onChange={e => setDraft({ ...draft, odoo_project_id: e.target.value ? Number(e.target.value) : null })} /></label>}
        {draft.delivery === 'project_and_task' && <p className="message info">Tämä valinta voi luoda uuden projektin. Usean perustuotteen yhteinen projektirakenne on testattava Odoossa ennen julkaisua.</p>}
        <p className="caption">Yksikkö-, laskutus- ja toimitusvalinnat ovat ehdotuksia. Odoon yksikkötunnisteet, projektikohde, hinnat, verot ja asetusten yhteensopivuus tarkistetaan erikseen ennen vientiä.</p>
        <div className="form-grid">{(['requires', 'excludes'] as const).map(key => <label key={key}>{key === 'requires' ? 'Vaaditut perustuotteet' : 'Yhteensopimattomat perustuotteet'}<select multiple value={draft[key]} onChange={e => setDraft({ ...draft, [key]: Array.from(e.target.selectedOptions, x => x.value) })}>{items.filter(x => x.id !== selected?.id).map(x => <option key={x.id} value={x.id}>{x.content.name}</option>)}</select><small>Valitse useita Ctrl- tai Cmd-näppäimellä.</small></label>)}</div>
        <label>Lähdeviitteet (yksi per rivi)<textarea rows={2} value={draft.source_refs.join('\n')} onChange={e => setDraft({ ...draft, source_refs: e.target.value.split('\n') })} /></label>
        <div className="actions"><button className="primary" type="submit" disabled={!dirty}>Tallenna luonnos</button><button type="button" className="secondary" disabled={!dirty} onClick={() => setDraft({ ...blank, ...structuredClone(selected?.content ?? {}) })}>Peru muutokset</button>
          <button type="button" className="secondary" disabled={!selected || dirty || selected.state === 'approved'} onClick={() => void action(async () => {
            const item = await api<Item>('/' + selected!.id + '/approve', 'POST', { expected_version: selected!.version });
            setItems(await api<Item[]>('')); await select(item); setNotice('Sisältöversio hyväksytty. Odoo-asetuksia ei ole julkaistu.');
          })}>Hyväksy sisältö</button>
        </div></fieldset>
      </form>
      {selected && <CatalogExport key={selected.id} id={selected.id} version={selected.version} approved={selected.state === 'approved'} dirty={dirty} />}
      {!!similar.length && <div><h3>Tarkista mahdolliset päällekkäisyydet</h3><p className="caption">Sanavertailu tarpeesta ja lopputuloksesta; ei kattava merkitysten vertailu.</p>{similar.map(x => <p key={x.id}>{x.name} · yhteiset sanat: {x.shared_terms.join(', ')}</p>)}</div>}
      {!!history.length && <details><summary>Versiohistoria ({history.length})</summary>{history.map(x => <details key={x.version}><summary>Versio {x.version} · {x.state === 'approved' ? 'Sisältö hyväksytty' : 'Luonnos'}</summary><dl>{textFields.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{String(x.content[key] ?? '') || '—'}</dd></div>)}</dl></details>)}</details>}
    </section>
    <section className="panel"><div className="section-title"><h2>Odoon kyvykkyyskartoitus</h2><button className="secondary" disabled={busy} onClick={() => void action(async () => setCapability(await api<Capability>('/capabilities', 'POST')))}>Lue nykyiset asetukset</button></div>
      <p className="caption">Kartoitus lukee Odoota ja tallentaa tilannekuvan Palvelupajaan.</p>
      {capability ? <><p>{capability.note}</p><p className="caption">{capability.target} · {capability.company?.[1] ?? 'Ei yrityskontekstia'} · {new Date(capability.fetched_at).toLocaleString('fi-FI')}</p><dl>{Object.entries(capability.checks).map(([key, value]) => <div key={key}><dt>{checkLabels[key] ?? key}</dt><dd>{statusLabels[value] ?? value}</dd></div>)}</dl>
        {!!capability.units.length && <details><summary>Odoosta luetut myyntiyksiköt</summary>{capability.units.map(u => <p key={u.id}>{u.name} · {u.category_id[1]} · #{u.id}</p>)}</details>}
      </> : <p>Kartoitusta ei ole vielä tehty. Tuoteluonnoksia voi valmistella ennen Odoo-yhteyttä.</p>}
    </section>
  </>;
}

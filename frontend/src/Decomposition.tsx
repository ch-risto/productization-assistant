import { useEffect, useState } from 'react';

type Copy = { name: string; description: string; service_promise: string; outcome: string; deliverables: string; exclusions: string; acceptance_criteria: string; target_need: string; suitable_when: string; unsuitable_when: string; prerequisites: string; task_instructions: string; unit: string; billing: string };
type WorkGroup = { id: string; name: string; outcome: string; steps: { name: string; hours: number | null; basis: string; rationale: string }[] };
type Part = { work_group_ids?: string[]; choice: string; catalog_item_id: string | null; proposed_product: Copy | null; quantity: number | null; work_description: string; reason: string; evidence_quote: string };
type Proposal = { name: string; description: string; service_promise: string; parts: Part[]; assumptions: string[]; open_questions: string[]; uncovered_scope: string[] };
type Record = { kind?: string; work_plan?: { kind: string; rationale: string; groups: WorkGroup[]; open_questions: string[] }; workload?: { known_hours: number; unknown_steps: number; estimated_steps: number }; materialized_item_ids?: string[]; id: string; version: number; state: string; created_at: string; source: { name: string; description: string }; proposal: Proposal; recipe_id: string | null; catalog_snapshot: { id: string; version: number; content: Copy & { product_kind?: string } }[] };
type Service = { source_id: string; name: string; description: string };
const fields: [keyof Copy, string][] = [['name', 'Nimi'], ['description', 'Kuvaus'], ['service_promise', 'Palvelulupaus'], ['outcome', 'Lopputulos'], ['deliverables', 'Toimitussisältö'], ['exclusions', 'Rajaukset'], ['acceptance_criteria', 'Hyväksymiskriteerit'], ['target_need', 'Kohdetarve'], ['suitable_when', 'Sopii tilanteeseen'], ['unsuitable_when', 'Ei sovi tilanteeseen'], ['prerequisites', 'Lähtötiedot'], ['task_instructions', 'Tehtävän työohje']];
const emptyCopy = (): Copy => ({ name: '', description: '', service_promise: '', outcome: '', deliverables: '', exclusions: '', acceptance_criteria: '', target_need: '', suitable_when: '', unsuitable_when: '', prerequisites: '', task_instructions: '', unit: 'unit', billing: 'fixed' });
async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api/decompositions' + path, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Tarkista ehdotuksen kentät.');
  return data;
}

export function Decomposition({ onCatalogChanged }: { onCatalogChanged: () => Promise<void> }) {
  const [services, setServices] = useState<Service[]>([]);
  const [serviceId, setServiceId] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [totalHours, setTotalHours] = useState('');
  const [records, setRecords] = useState<Record[]>([]);
  const [record, setRecord] = useState<Record | null>(null);
  const [draft, setDraft] = useState<Proposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const dirty = !!record && JSON.stringify(draft) !== JSON.stringify(record.proposal);
  const locked = busy || record?.state === 'materialized';
  async function action(fn: () => Promise<void>) { setBusy(true); setError(''); setNotice(''); try { await fn(); } catch (e) { setError(e instanceof Error ? e.message : 'Toiminto epäonnistui.'); } finally { setBusy(false); } }
  function select(value: Record) { setRecord(value); setDraft(structuredClone(value.proposal)); }
  async function refresh(value: Record) { select(value); setRecords(await api<Record[]>('')); }
  useEffect(() => { void action(async () => setRecords(await api<Record[]>(''))); }, []);
  function changePart(index: number, values: Partial<Part>) { setDraft({ ...draft!, parts: draft!.parts.map((part, i) => i === index ? { ...part, ...values } : part) }); }
  return <section className="panel">
    <div className="eyebrow">TEKOÄLYAVUSTEINEN TUOTTEISTAMINEN</div><h2>Pilko palvelu perustuotteiksi</h2>
    <p>Agentti etsii ensin sopivat osat katalogista. Puuttuvasta osasta se ehdottaa uutta perustuotetta tai rajattua asiantuntijatyötä. Tarkista erityisesti palvelulupaukset ja avoimet kysymykset.</p>
    {error && <div className="message error" role="alert">{error}</div>}{notice && <div className="message success" role="status">{notice}</div>}{busy && <p role="status">Käsitellään… Tekoälyehdotus voi kestää noin minuutin.</p>}
    <fieldset disabled={busy || dirty} className="catalog-fields">
      <button className="secondary" onClick={() => void action(async () => setServices(await api<Service[]>('/services')))}>Lataa olemassa olevat palvelut</button>
      <label>Lähtöpalvelu<select value={serviceId} onChange={e => { setServiceId(e.target.value); const s = services.find(x => x.source_id === e.target.value); setName(s?.name ?? ''); setDescription(s?.description ?? ''); }}><option value="">Kirjoita tai liitä palvelukuvaus</option>{services.map(s => <option key={s.source_id} value={s.source_id}>{s.name}</option>)}</select></label>
      <label>Palvelun nimi<input value={name} maxLength={200} disabled={!!serviceId} onChange={e => setName(e.target.value)} /></label>
      <label>Alkuperäinen palvelukuvaus<textarea rows={5} value={description} maxLength={16000} disabled={!!serviceId} onChange={e => setDescription(e.target.value)} /></label>
      <label>Palvelun kokonaistyömäärä (h), jos tiedossa<input type="number" min="0.01" max="100000" step="any" value={totalHours} onChange={e => setTotalHours(e.target.value)} /></label>
      <p className="caption">Tunnit jaetaan työvaiheille. Puuttuvat työmäärät arvioidaan perusteluineen tai jätetään avoimiksi. Tekoälyn arviot vaativat tarkistuksen.</p>
      <p className="caption">Analyysi lähettää palvelukuvauksen ja nykyisen perustuotekatalogin määritettyyn OpenAI-palveluun. Malliajo käyttää API-projektin laskutusta.</p>
      <button className="primary" disabled={!name.trim() || description.trim().length < 20} onClick={() => void action(async () => { await refresh(await api<Record>('', 'POST', { ...(serviceId ? { service_id: serviceId } : { name, description }), total_hours: totalHours ? Number(totalHours) : null })); })}>Ehdota pilkkomista tekoälyllä</button>
      <label>Aiemmat pilkkomiset<select value={record?.id ?? ''} onChange={e => { const value = records.find(x => x.id === e.target.value); if (value) select(value); }}><option value="">Valitse ehdotus</option>{records.map(x => <option key={x.id} value={x.id}>{x.proposal.name} · v{x.version} · {x.state === 'materialized' ? 'Luonnokset luotu' : 'Tarkistettava'}</option>)}</select></label>
      <button className="text-button" onClick={() => void action(async () => { const rows = await api<Record[]>(''); setRecords(rows); const latest = rows.find(x => x.id === record?.id); if (latest) select(latest); })}>Lataa tallennetut ehdotukset</button>
    </fieldset>
    {draft && record && <>
      {record.work_plan && <div className="message info"><strong>{record.kind === 'base_product' ? 'Palvelu itsessään on perustuote' : `${record.work_plan.groups.length} perustuotteesta koostuva palvelu`}</strong><p>{record.work_plan.rationale}</p><p>Työmäärä yhteensä: {record.workload?.known_hours} h · avoimia työvaiheita: {record.workload?.unknown_steps} · arvioituja vaiheita: {record.workload?.estimated_steps}</p>{record.work_plan.open_questions.map((q, i) => <p key={i}>{q}</p>)}</div>}
      <h3>{record.state === 'materialized' ? 'Tallennettu palvelukooste' : 'Tarkista agentin ehdotus'}</h3>
      <p className="caption">Versio {record.version}. Lähde: {record.source.name}. Katalogin vertailu perustuu analyysihetken tuotteisiin.</p>
      <details><summary>Alkuperäinen lähdekuvaus</summary><p className="preserve-lines">{record.source.description}</p></details>
      <fieldset disabled={locked} className="catalog-fields">
        {(['name', 'description', 'service_promise'] as const).map((key, i) => <label key={key}>{['Koosteen nimi', 'Koosteen kuvaus', 'Koosteen palvelulupaus'][i]}<textarea rows={2} value={draft[key]} onChange={e => setDraft({ ...draft, [key]: e.target.value })} /></label>)}
        {draft.parts.map((part, index) => <article className="decomposition-part" key={index}>
          <h3>Osa {index + 1}: {part.proposed_product?.name || record.catalog_snapshot.find(x => x.id === part.catalog_item_id)?.content.name || 'Valitse tuote'}</h3>
          <label>Käsittelytapa<select value={part.choice} onChange={e => { const choice = e.target.value; changePart(index, { choice, catalog_item_id: null, proposed_product: choice === 'reuse' ? null : { ...(part.proposed_product ?? emptyCopy()), ...(choice === 'expert' ? { name: 'Asiantuntijatyö', unit: 'hour', billing: 'timesheet' } : {}) } }); }}><option value="reuse">Käytä nykyistä perustuotetta</option><option value="new">Ehdota uutta perustuotetta</option><option value="expert">Avoin asiantuntijatyö</option></select></label>
          {part.choice !== 'new' && <label>Katalogituote<select value={part.catalog_item_id ?? ''} onChange={e => changePart(index, { catalog_item_id: e.target.value || null, proposed_product: e.target.value || part.choice === 'reuse' ? null : { ...emptyCopy(), name: 'Asiantuntijatyö', unit: 'hour', billing: 'timesheet' } })}><option value="">{part.choice === 'expert' ? 'Ehdota yleistä asiantuntijatyötuotetta' : 'Valitse tuote'}</option>{record.catalog_snapshot.filter(x => part.choice !== 'expert' || x.content.product_kind === 'expert_work').map(x => <option key={x.id} value={x.id}>{x.content.name} · v{x.version}</option>)}</select></label>}
          {record.work_plan?.groups.filter(g => part.work_group_ids?.includes(g.id)).map(g => <div key={g.id}><h4>{g.name}</h4><p>{g.outcome}</p><ul>{g.steps.map((s, i) => <li key={i}>{s.name}: <strong>{s.hours === null ? 'Avoin työmäärä' : `${s.hours} h`}</strong> · {s.basis === 'source' ? 'Lähteessä annettu' : s.basis === 'estimate' ? 'Tekoälyn arvio' : 'Ei arviota'}<p className="caption">{s.rationale}</p></li>)}</ul></div>)}
          <label>Perustelu valinnalle<textarea value={part.reason} onChange={e => changePart(index, { reason: e.target.value })} /></label>
          <label>Lähdekatkelma<textarea value={part.evidence_quote} onChange={e => changePart(index, { evidence_quote: e.target.value })} /></label>
          <label>Toteutettava työ ja rajaus<textarea rows={3} value={part.work_description} onChange={e => changePart(index, { work_description: e.target.value })} /></label>
          <label>Määrä ({part.proposed_product?.unit === 'hour' || record.catalog_snapshot.find(x => x.id === part.catalog_item_id)?.content.unit === 'hour' ? 'tuntia' : 'myyntiyksikköä'}), jätä avoimeksi jos ei tiedossa<input type="number" min="0.001" step="any" value={part.quantity ?? ''} onChange={e => changePart(index, { quantity: e.target.value ? Number(e.target.value) : null })} /></label>
          {part.proposed_product && <details open><summary>Uuden tuotteen ehdotettu sisältö</summary><div className="form-grid">{fields.map(([key, label]) => <label key={key}>{label}<textarea rows={2} value={part.proposed_product![key]} onChange={e => changePart(index, { proposed_product: { ...part.proposed_product!, [key]: e.target.value } })} /></label>)}
            <label>Yksikkö<select value={part.proposed_product.unit} onChange={e => changePart(index, { proposed_product: { ...part.proposed_product!, unit: e.target.value } })}><option value="unit">Kappale / toimitus</option><option value="hour">Tunti</option></select></label>
            <label>Laskutus<select value={part.proposed_product.billing} onChange={e => changePart(index, { proposed_product: { ...part.proposed_product!, billing: e.target.value } })}><option value="fixed">Kiinteä / tilattu määrä</option><option value="timesheet">Toteutuneet tuntikirjaukset</option></select></label>
          </div></details>}
          <button className="text-button" disabled={!!record.work_plan || draft.parts.length <= 1} onClick={() => setDraft({ ...draft, parts: draft.parts.filter((_, i) => i !== index) })}>Poista osa ehdotuksesta</button>
        </article>)}
        <button className="secondary" disabled={!!record.work_plan || draft.parts.length >= 8} onClick={() => setDraft({ ...draft, parts: [...draft.parts, { choice: 'new', catalog_item_id: null, proposed_product: emptyCopy(), quantity: null, work_description: '', reason: '', evidence_quote: '' }] })}>Lisää puuttuva osa</button>
        {record.work_plan && <p className="caption">Työrakenne on sidottu tähän analyysiin. Jos osajako tai tunnit vaativat muutoksia, täsmennä lähtökuvausta ja tee uusi analyysi.</p>}
        {(['assumptions', 'open_questions', 'uncovered_scope'] as const).map((key, i) => <label key={key}>{['Oletukset', 'Avoimet kysymykset', 'Osat, joita kooste ei vielä kata'][i]} (yksi per rivi)<textarea rows={3} value={draft[key].join('\n')} onChange={e => setDraft({ ...draft, [key]: e.target.value.split('\n') })} /></label>)}
        <div className="actions"><button className="secondary" disabled={!dirty} onClick={() => void action(async () => refresh(await api<Record>('/' + record.id, 'PUT', { expected_version: record.version, proposal: draft })))}>Tallenna tarkennukset</button>
          <button className="text-button" disabled={!dirty} onClick={() => setDraft(structuredClone(record.proposal))}>Peru tarkennukset</button>
          <button className="primary" disabled={dirty} onClick={() => void action(async () => { await refresh(await api<Record>('/' + record.id + '/materialize', 'POST', { expected_version: record.version })); await onCatalogChanged(); setNotice(record.kind === 'base_product' ? 'Palvelu tallennettu perustuotteena. Erillistä palvelupakettia ei luotu.' : 'Perustuotteet ja palvelukooste tallennettu luonnoksina. Tarkista ja hyväksy tuotteet katalogissa.'); })}>{record.kind === 'base_product' ? 'Luo perustuoteluonnos' : 'Luo tarkistetut katalogi- ja koosteluonnokset'}</button>
        </div>
      </fieldset>
      {record.state === 'materialized' && !record.recipe_id && <p className="message success">Palvelu on perustuote. Löydät sen katalogista ja voit viedä sen hyväksynnän jälkeen Odoohon.</p>}
      {record.recipe_id && <p className="message success">Palvelukoosteen luonnos on tallennettu ja tuoteversiot säilytetty. Odoo-tarjousta ei ole luotu. Kooste ei ole vielä julkaisuvalmis resepti.</p>}
    </>}
  </section>;
}

import { useEffect, useState } from 'react';

type Status = { mode: string; status: string; target: string; result: { code: string; url: string | null } | null };
type Plan = { id: string; mode: string; target: string; company: [number,string]; currency: string; unit: string;
  taxes: string[]; values: { name: string; list_price: number; service_policy: string; service_tracking: string; default_code: string } };
async function request<T>(id: string, route: string, body?: unknown): Promise<T> {
  const r = await fetch(`/api/catalog/${id}/${route}`, { method: body ? 'POST' : 'GET', headers: {'Content-Type':'application/json'}, body: body ? JSON.stringify(body) : undefined });
  const data = await r.json();
  if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Vienti epäonnistui.');
  return data;
}
export function CatalogExport({ id, version, approved, dirty }: { id: string; version: number; approved: boolean; dirty: boolean }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { let active = true; setPlan(null); setStatus(null); setError('');
    void request<Status>(id, 'export-status').then(s => { if (active) setStatus(s); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [id, version]);
  async function action(fn: () => Promise<void>) { setBusy(true); setError(''); try { await fn(); } catch (e) { setError(e instanceof Error ? e.message : 'Vienti epäonnistui.'); } finally { setBusy(false); } }
  const canRetry = status?.status === 'uncertain' || status?.status === 'pending';
  return <section className="decomposition-part"><h3>Odoo-vienti</h3>
    <p>{status?.status === 'exported' ? status.mode === 'fixture' ? 'Vienti simuloitu — tuote ei ole Odoossa.' : 'Tuote on viety Odoohon.' : 'Tuote on Palvelupajassa. Pelkkä tallennus tai sisältöhyväksyntä ei vie sitä Odoohon.'}</p>
    {error && <div className="message error" role="alert">{error}</div>}
    {status?.result && <p>Tuotekoodi: {status.result.code} {status.result.url && <a href={status.result.url} target="_blank" rel="noreferrer">Avaa tuote Odoossa ↗</a>}</p>}
    {status?.status === 'exported' && <p className="caption">Viety sisältöversio on lukittu. Tämän ensimmäisen vientiversion myöhemmät tuotemuutokset tehdään Odoossa; automaattinen päivityssynkronointi ei ole käytössä.</p>}
    {status?.status !== 'exported' && <>
      <p className="caption">Tallenna yksikköhinta ja hyväksy nykyinen sisältöversio. Vienti luo palvelutuotteen; tehtäviä syntyy vasta Odoon tilausprosessissa tuoteasetusten mukaan.</p>
      <button className="secondary" disabled={busy || dirty || !approved} onClick={() => void action(async () => setPlan(await request<Plan>(id, 'export-preview', { expected_version: version })))}>Tarkista viennin esikatselu</button>
      {plan && <div><p><strong>{plan.values.name}</strong> → {plan.target}</p><dl>
        <dt>Yritys</dt><dd>{plan.company[1]}</dd><dt>Yksikköhinta</dt><dd>{plan.values.list_price} {plan.currency} / {plan.unit}</dd>
        <dt>Odoon oletusverot</dt><dd>{plan.taxes.join(', ') || 'Ei oletusveroja — tarkista verokäsittely'}</dd>
        <dt>Laskutus</dt><dd>{plan.values.service_policy === 'ordered_prepaid' ? 'Tilattu määrä / kiinteä hinta' : 'Toteutuneet tuntikirjaukset'}</dd>
        <dt>Projektit ja tehtävät</dt><dd>{plan.values.service_tracking === 'no' ? 'Liitetään käsin' : plan.values.service_tracking === 'task_global_project' ? 'Tehtävä valittuun projektiin' : 'Uusi projekti ja tehtävä — tarkista usean tuotteen kokonaisuus'}</dd>
      </dl></div>}
      {(plan || canRetry) && <button className="primary" disabled={busy || dirty || !approved} onClick={() => void action(async () => {
        try { await request(id, 'export', { expected_version: version, plan_id: plan?.id ?? '' }); }
        finally { setStatus(await request<Status>(id, 'export-status')); }
      })}>{busy ? 'Käsitellään vientiä…' : canRetry ? 'Selvitä aiemman viennin tulos' : plan?.mode === 'fixture' ? 'Simuloi vienti — ei Odoo-kirjoitusta' : 'Hyväksy vienti Odoohon'}</button>}
    </>}
  </section>;
}

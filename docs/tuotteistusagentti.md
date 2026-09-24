# Tekoälyavusteinen palvelun pilkkominen

24.9.2026 jatko: [kaksivaiheinen pilkkominen, työtunnit ja Odoo-vienti](katalogivienti.md).
Alla kuvattu 23.9. vaihe säilyy kehityshistoriana; uusin käyttöohje on yllä olevassa linkissä.

23.9.2026. Tuotteistusagentti on sovelluksen rajattu tekoälytoiminto, ei itsenäisesti
julkaiseva tausta-agentti. Se käyttää nykyistä OpenAI-yhteyttä ja tuottaa rakenteisen,
käyttäjän tarkistettavan ehdotuksen. Odoo-kirjoittavia työkaluja sillä ei ole.

## Käyttö

1. Avaa **Perustuotekatalogi → Pilko palvelu perustuotteiksi**.
2. Lataa olemassa olevat palvelut tai liitä palvelukuvaus käsin. Odoo-tilassa palvelut
   luetaan nykyisestä adapterista; sen DEMO-SVC-rajaus on edelleen voimassa.
   Tuoteryhmän valintaan perustuva yrityskatalogin luku on myöhempi vaihe.
3. Valitse **Ehdota pilkkomista tekoälyllä**. Palvelukuvaus ja nykyinen paikallinen
   perustuotekatalogi lähetetään määritettyyn mallipalveluun. Malliajo on maksullinen.
4. Tarkista jokaisen osan käsittelytapa, lähdekatkelma, perustelu ja toteutettava työ.
   Muokkaa myös uuden tuotteen kuvaus, palvelulupaus, lopputulos, sisältö, rajaukset,
   hyväksymiskriteerit, soveltuvuus, lähtötiedot ja tehtävän työohje.
5. Tallenna tarkennukset. Valitse **Luo tarkistetut katalogi- ja koosteluonnokset**.
   Uudet tuotteet ilmestyvät katalogiin luonnoksina. Nykyisiä tuotteita ei kopioida.
   Palvelukooste säilyy aiemmissa pilkkomisissa, ja siihen tallennetaan tuoteversiot.
6. Hyväksy uudet tuotteet erikseen katalogissa. Tämä ei vielä hyväksy koostetta
   julkaistavaksi Odoo-tarjouspohjaksi.

## Kolme käsittelytapaa

- **Nykyinen perustuote:** viittaus katalogituotteeseen ja sen analyysihetken versioon.
- **Uusi perustuote:** ehdotus, jonka perustelu arvioi itsenäistä asiakasarvoa,
  toistettavuutta ja rajattavuutta. Sisäiset työvaiheet kirjataan työohjeiksi.
- **Avoin asiantuntijatyö:** yleinen tuntiyksiköllinen `expert_work`-tuote,
  ensisijaisesti katalogista. Tapauskohtainen työ ja rajaus tallennetaan koosteen
  riville. Puuttuva tuntimäärä säilyy avoimena. Tämä ei ole rajaton toimituslupaus.

Agentti ehdottaa palvelulupauksen; käyttäjä vastaa sen tarkistamisesta. Hintaa ei
muodosteta. Jatkuvan laskutuksen ja etappien puutteet kuuluvat avoimiin kysymyksiin.

## Tallennus ja validointi

Migraatio 2 lisää `decompositions`, `decomposition_versions` ja `recipes`-taulut.
Vanhat katalogisisällöt saavat uudet kuvaus-, palvelulupaus- ja tuotetyyppikentät
skeeman oletuksina; historiallisia JSON-tietueita ei kirjoiteta uudelleen.

Palvelulähde, koko vertailukatalogi, mallin metadata ja ehdotuksen versiot säilyvät.
Koosteluonnos sisältää rivikohtaiset tuotesnapshotit, työkuvaukset, määrät ja avoimet
asiat. Hyväksyttyjä tarjouksia tai tuotantovalmiita reseptejä tämä toteutus ei luo.

Validointi estää tuntemattomat tuoteviitteet, lähteestä puuttuvat lainaukset,
ristiriitaiset tuotteet, puuttuvat pakolliset riippuvuudet ja virheelliset määrät.
Samannimistä uutta tuotetta ei lisätä olemassa olevan rinnalle. Lisäksi palvelukuvaus
jaetaan virkkeisiin/riveihin: jokaisen tekstiosan pitää näkyä rivin lähdelainauksessa
tai avoimessa osuudessa. Tämä on tekstipeiton tarkistus, ei semanttisen kattavuuden todiste.
Virheelliseen mallivastaukseen pyydetään enintään yksi korjaus; molempien kutsujen
metadata tallentuu onnistuneeseen ajoon. Lopullisesti hylätty vastaus ei muuta katalogia.
Lähdekatkelman olemassaolo ei todista päätelmän semanttista oikeellisuutta.

Muuttunut katalogi estää luonnosten muodostamisen vanhasta analyysistä. Uusi analyysi
tarvitaan, jotta sillä välin syntyneet tuotteet voidaan käyttää uudelleen.
Luonnosten ja koosteen luonti tapahtuu samassa SQLite-transaktiossa. Saman toiminnon
uusiminen, myös samanaikaisesti, palauttaa jo syntyneen koosteen ilman kaksoiskopioita.

Rajapinnat: `GET/POST /api/decompositions`, `GET /api/decompositions/services`,
`PUT /api/decompositions/{id}`, `POST /api/decompositions/{id}/materialize`,
`GET /api/decompositions/{id}/recipe`.

## Tämän vaiheen rajat

- Yksi palvelu kerrallaan, enintään 8 osaa. Mallille lähetettävän aineiston kokoraja
  on 100000 merkkiä. Suuri katalogi tarvitsee myöhemmin rajatun hakupalvelun.
- Kooste on tarkistettava luonnos; Odoo-tarjouspohjan vienti, reseptin hyväksyntä,
  määräsäännöt ja hinnoittelu jäävät seuraavaan vaiheeseen.
- Nykyiset luonnostuotteet voivat olla ehdotuksen pohjana. Julkaisu edellyttää niiden
  erillistä hyväksyntää ja Odoo-sidontojen varmennusta.
- Perustuotteiden luonti ei vielä siirrä tehtävän työohjetta Odoon tehtävälle.
- Semanttinen päällekkäisyys, koko palvelun kattavuus ja lupausten kohtuullisuus
  vaativat ihmisen tarkistuksen. Rakennetarkistukset eivät takaa mallin laatua.

## Varmennus 23.9.2026

- 44 automaattista testiä läpäisty; TypeScript-tarkistus ja Vite-kooste onnistuvat.
- Oikea gpt-4.1-mini-kutsu palautti rakenteisen ehdotuksen synteettisestä palvelusta.
  Ensimmäinen kokeilu hylättiin epätarkan lainauksen vuoksi. Seuraavan kokeilun
  korjauskutsu palautti tallennettavan vastauksen mutta pudotti asiantuntijatyön
  riveiltä. Tämä on havaittu semanttinen laatuvirhe, ei onnistunut kokonaispilkkominen.
- Havainnon perusteella lisättiin tekstipeiton tarkistus ja regressiotesti, joka
  hylkää kyseisen poisjäännin. Lopullista promptia ei ajettu uudelleen oikealla mallilla.
- Selaimessa muokattiin oikeasta mallikokeesta syntynyttä testiehdotusta: lisättiin
  puuttuva avoin asiantuntijatyö, tallennettiin tarkennukset ja muodostettiin kaksi
  katalogiluonnosta sekä versioitu palvelukoosteluonnos onnistuneesti.
- Testitietokanta oli erillinen `data/agent-live-check.db`. Odoohon tai käyttäjän
  varsinaiseen katalogiin ei luotu koetuotteita. OpenAI-kokeessa käytettiin vain
  keksittyä palvelukuvausta ja tyhjää testikatalogia.

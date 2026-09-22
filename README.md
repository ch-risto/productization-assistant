# Palvelupaja

Paikallinen verkkosivupalvelujen tuotteistamisen demo: aineisto → lähteistetyt tuoteideat → muokattava palvelukortti → ihmisen hyväksyntä → vienti.

## Toteutuksen tila 21.9.2026

**Oikea Odoo-luku → OpenAI-ideat ja korttiluonnos → muokkaus → hyväksyntä → Odoo-vienti on todennettu selaimessa.** Odoossa näkyy testipalvelu DEMO – Verkkosivujen sisältöstartti, ID 5, hinta 760 EUR veroton. Toistuva vienti palautti saman tuotteen. Alustus ajettiin kahdesti ilman kaksoistietueita. Automaattiset 14 testiä läpäistiin. Aineisto on edelleen täysin synteettinen.

Malliarviointi paljasti lähteiden tulkinnassa puutteita: rakennevalidointi ei todista päätelmän oikeellisuutta. Liian vähäisen aineiston ideointi estetään nyt ennen mallikutsua. Katso tarkat tulokset ja rajat `docs/evaluation.md`-tiedostosta.

- [Käyttäjän periaate- ja käyttöohje](docs/kayttoohje.md)
- [Tekninen dokumentaatio ja rakennekaaviot](docs/tekninen-dokumentaatio.md)
- [Testiraportti](docs/evaluation.md)

## Käynnistys

Tarvitset Python 3.12+ ja Node 22.18+ (testattu Python 3.12.5, Node 24.19.0). Docker on tarpeen vain oikealle Odoo-demolle. Aja PowerShellissä projektin juuresta:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
# Kopioi vain, jos .env ei ole jo olemassa. Älä ylikirjoita omaa avaintasi.
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd frontend
npm ci
node node_modules/typescript/bin/tsc -b
node node_modules/vite/bin/vite.js build --configLoader native
cd ..
.venv/Scripts/python.exe scripts/seed.py
.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

Avaa <http://127.0.0.1:8000>. Vaihtoehtoinen käynnistys: `./scripts/start.ps1`. Lopetus Ctrl+C. Käytä yhtä palvelinprosessia, älä useita workereita tai samanaikaisia palvelinkäynnistyksiä samalla SQLite-tiedostolla. Käynnistys merkitsee kesken jääneet viennit epäselviksi turvallista selvitystä varten.

Tällä koneella riippuvuudet asennettiin työtilan `work/venv`-ympäristöön. Uusi asennus tehdään yllä olevilla ohjeilla; lähdekoodi ei riipu työtilan tilapäisestä ympäristöstä. Käyttöliittymän valmis kooste on `frontend/dist`-kansiossa.

## Asetukset

Muokkaa paikallista `.env`-tiedostoa. Älä tallenna sitä versionhallintaan tai jaa sitä. Käynnistä backend uudelleen asetusten muuttamisen jälkeen.

| Muuttuja | Käyttö |
|---|---|
| ODOO_MODE | `fixture` tai `odoo`; fixture ei ota verkkoyhteyttä Odoohon |
| ODOO_URL | Hostilta `http://127.0.0.1:8069`; mahdollisesta omasta backend-kontista `http://odoo:8069` |
| ODOO_DATABASE | `productization_demo` |
| ODOO_USERNAME | Erillinen integraatiokäyttäjä |
| ODOO_API_KEY | Integraatiokäyttäjän paikallinen API-avain |
| ODOO_DB_PASSWORD | PostgreSQL-käyttäjän salasana; ei Odoo-käyttäjän salasana |
| LLM_PROVIDER | `openai` |
| LLM_MODEL | `gpt-4.1-mini` lähtöasetus, mallin käyttöoikeus tarkistettava omasta API-projektista |
| LLM_API_KEY | OpenAI API-avain; vain backend lukee sen |
| APP_DATABASE_URL | `sqlite:///data/app.db` |

OpenAI-ajot käyttävät API-projektisi laskutusta. Esimerkkitila ei kutsu mallia. `store=False` on asetettu mallikutsuun; avaimia ei lähetetä käyttöliittymään eikä lokiteta. Nykyinen demo käyttää vain keksittyä aineistoa.

## Paikallinen Odoo 18

1. Käynnistä Docker Desktop ja tarkista omassa terminaalissa `docker version`. Tässä toteutussessiossa agentti ei saanut yhteyttä Dockerin putkeen; tämä ei todista Dockerin olevan viallinen käyttäjän omassa terminaalissa.
2. Aseta `.env`-tiedostoon paikallinen satunnainen `ODOO_DB_PASSWORD`.
3. Käynnistä `docker compose up -d`. Kuvat: `odoo:18.0`, `postgres:15`. PostgreSQL ei julkaise host-porttia, Odoo julkaisee vain localhostin 8069.
4. Avaa <http://127.0.0.1:8069>. Aseta Odoon tietokantojen hallinnan pääsalasana, luo tietokanta `productization_demo`, oma paikallinen ylläpitäjän tunnus, maaksi Suomi ja valuutaksi EUR. Älä lataa Odoon yleistä demoainestoa. Hallinnan pääsalasana, ylläpitäjän salasana, integraatioavain ja PostgreSQL-salasana ovat eri asioita.
5. Asenna Apps-näkymässä CRM, Sales ja Project. Luo erillinen sisäinen käyttäjä integraatiolle. Anna myynnin ja projektien tarvitsemat luku- ja tuotekirjoitusoikeudet. Käytä paikallista testiä oikeuksien tarkentamiseen; älä kopioi tuotannon ylläpitäjätunnuksia.
6. Luo integraatiokäyttäjän asetuksissa API-avain ja lisää käyttäjä sekä avain `.env`-tiedostoon. Tarkista `ODOO_URL` ja `ODOO_DATABASE`.
7. Aja `.venv/Scripts/python.exe scripts/seed.py --odoo` kahdesti. Jälkimmäinen ajo päivittää samat demotietueet. Tarkista Odoosta 4 palvelua, 6 asiakasyritystä, 8 projektia ja 4 myyntimahdollisuutta. Alustus muokkaa vain DEMO-tunnisteisia paikallisia tietueita.
8. Aseta `ODOO_MODE=odoo` ja käynnistä sovellus uudelleen. Tarkista, että katalogi latautuu. Palvelut luetaan Odoosta; tutkimushavainnot, segmentit, työmäärät ja myyntitulokset ovat paikallisia synteettisiä annotaatioita.
9. Tee `docs/demo.md`-polku. Varmista tuote Odoon omassa käyttöliittymässä. Community-testi ei todista Enterprise-räätälöintien yhteensopivuutta.

Kun Docker toimii, tallenna käytetyt kuvat: `docker image inspect odoo:18.0 postgres:15 --format '{{json .RepoDigests}}'`. Tähän toimitukseen ei kirjattu testaamatonta digest-arvoa. Volumeja ei poisteta pysäytyksessä: `docker compose stop`. Älä käytä `down -v`, jos haluat säilyttää aineiston.

## Testit ja kehitys

```powershell
.venv/Scripts/python.exe -m pytest backend/tests -q
# Maksulliset todellisen mallin arvioinnit, vain kun API-saldo on kunnossa:
.venv/Scripts/python.exe scripts/evaluate.py
```

Malliarvioinnit kirjoittavat synteettiset tulokset `docs/evaluation-results.json`-tiedostoon. Kooditestit eivät kutsu OpenAIta tai oikeaa Odoota. Katso `docs/evaluation.md` testien merkityksestä ja rajoituksista.

Frontend-kehitys: backend porttiin 8000, `npm run dev` frontend-kansiossa porttiin 5173. Tuotantokooste tarjoillaan samasta FastAPI-palvelusta, joten erillistä CORS-avausta ei tarvita. npm-skriptin komentotulkkiongelmassa käytä yllä olevia suoria `node`-komentoja.

## Vianmääritys

- OpenAI 429 / saldo loppu: tarkista avaimen API-projektin laskutus ja kiintiö. ChatGPT-tilaus ei ole tämän sovelluksen API-avain. Esimerkkitila säilyy käytettävissä.
- Odoo 502: varmista palvelin, tietokanta, tunnus, API-avain, asennetut moduulit ja käyttöoikeudet. Älä vaihda tuotannon palvelinosoitetta tähän demoon.
- Epäselvä vienti: vientipainike etsii aiemmin luotua tuotetta. Jos sitä ei löydy, automaattinen uudelleenluonti on estetty. Tarkista Odoo ja lokit; älä poista vientiriviä sokkona. Uuden luonnoksen luonti ei ole turvallinen kiertotapa epäselvälle viennille.
- Muuttunut versio: lataa kortti uudelleen ennen muokkausta. Viety kortti on lukittu; myöhempi ehdotus luodaan ideasta uutena korttina.
- Portti 8000 varattu: pysäytä vanha tämän demon palvelin ennen uutta käynnistystä.
- Aineiston uudelleenluonti: `scripts/build_fixtures.py` kirjoittaa keksityt lähdeaineistot deterministisesti. Se ei tyhjennä tallennettuja kortteja tai vanhoja analyysisnapshotteja.

Arkkitehtuuri, esityspolku, päätökset ja jatkokehitys löytyvät `docs`-kansiosta.

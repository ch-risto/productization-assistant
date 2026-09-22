# Arkkitehtuuri

Laajennettu ja päivitetty kuvaus rakenne-, tila-, sekvenssi- ja tietomallikaavioineen: [Tekninen dokumentaatio](tekninen-dokumentaatio.md). Tämä tiedosto on lyhyt arkkitehtuuriyhteenveto.

React/TypeScript-käyttöliittymä kutsuu FastAPIa samalla alkuperällä. FastAPI kutsuu erillisiä Odoo- ja OpenAI-adaptereita. SQLite säilyttää asetukset, analyysisnapshotit, korttiversiot, vientien tilat ja fixture–Odoo-ID-kartan. XML-RPC-kutsut tapahtuvat synkronisista FastAPI-reiteistä säiepoolissa, verkkokutsujen aikakatkaisu on 15 s. OpenAI-kutsun aikakatkaisu on 60 s ja yksi SDK-uusintayritys.

## Vastuut

- **Koodi:** laskee projektit ja erilliset asiakkaat, validoi skeeman ja lähdetunnisteet, laskee hinnan Decimal-laskennalla, hallitsee tiloja ja vientiä.
- **Malli:** ehdottaa 2–3 palveluideaa ja valitun idean korttiluonnoksen. Ei kirjoittavia työkaluja. Malli ei päätä hintaa tai hyväksyntää.
- **Ihminen:** tarkistaa lähteen merkityksen, muokkaa sisältöä ja rajauksia, antaa hinnoittelun lähtötiedot ja hyväksyy nimenomaisen version.

Lähde-ID:n validointi kertoo vain lähteen olemassaolosta. Tekstin semanttinen oikeellisuus jää tarkistettavaksi. Käyttöliittymä avaa alkuperäisen havainnon. Aineiston havainnot ovat käsin annotoituja; niitä ei esitetä mallin löytämiksi.

## Tilat ja vienti

Kortti etenee `draft → approved → exported`. Jokainen tallennettu sisältömuutos kasvattaa versiota ja poistaa hyväksynnän. Viety kortti lukitaan; historia säilyy. Päivityksissä käytetään optimistista versiotarkistusta.

Viennin yksilöllinen avain on kohde + kortti-ID + versio. SQLite `BEGIN IMMEDIATE` serialisoi vientivarauksen. Verkkokutsun aikana varaus on `pending`. Toinen yritys estetään. Onnistuneen viennin uusinta palauttaa saman tuotteen. Luonnin mahdollisesti onnistuttua katkennut vastaus johtaa `uncertain`-tilaan: seuraava yritys etsii tuotekoodia, eikä luo sokkona. Useampi Odoo-osuma on ristiriita.

Tämä ei ole hajautettu exactly-once-takuu: Odoon tuotekoodi ei ole yksilöllinen eikä Odoo-kirjoitus ja SQLite-tallennus ole sama transaktio. Demon yksiprosessisuus, paikallinen varaus ja konservatiivinen selvityspolku ovat tarkoituksellinen rajaus. Käynnistys tulkitsee vanhat pending-rivit keskeytyneiksi; älä aja useita backend-prosesseja samalla tietokannalla.

## Odoo 18

Palvelut `product.template`, yritykset `res.partner`, projektit `project.project`, myyntimahdollisuudet `crm.lead`. Adapteri tarkistaa kentät `fields_get`-kutsulla ja lukee eksplisiittiset kentät `search_read`-kutsuilla (enintään 200 tietuetta, demolle riittävä). Tuotantoversio tarvitsee sivutuksen.

Katalogin sisältö tulee oikeassa Odoo-tilassa Odoosta. Muut perustiedot yhdistetään paikallisiin tutkimusannotaatioihin pysyvällä tunnistekartalla. Seed ei mallinna kaikkia CRM-prosessin lopputiloja Odoossa: voitetut/hävityt merkinnät säilyvät tutkimusaineistossa. Kaikki tällainen yhdistetty data merkitään alkuperätiedolla.

Sallittu kohde on vain paikallinen host ja `productization_demo`. Malli ei saa valita Odoo-mallia, metodia tai palvelinosoitetta. Salaisuudet tulevat backendin ympäristöstä. HTTP-virheissä ei palauteta raakaa SDK-virhettä tai avainta. Tämä on yhden käyttäjän paikallinen demo ilman tuotannon käyttöoikeusjärjestelmää.

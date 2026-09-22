# Keskeiset päätökset

| Päätös | Peruste ja vaihtoehto |
|---|---|
| Kiinteä työnkulku | Helpompi selittää ja testata kuin agenttisilmukka; tässä ei tarvita dynaamista työkalujen valintaa. |
| OpenAI Responses + Pydantic | Rakenteen tarkistus ennen tallennusta. Ei todista päätelmien totuutta. |
| SQLite, JSON-snapshotit | Pieni paikallinen kokonaisuus ja jäljitettävyys. Tuotannossa tarvitaan migraatiot, varmistukset ja käyttöoikeudet. |
| XML-RPC-adapteri | Odoo 18:n tuettu rajapinta; ei oleteta uudempien versioiden APIa tai Enterprise-kenttiä. |
| Manuaalisesti annotoidut havainnot | Aineiston alkuperä ja testit ovat selkeitä; havaintojen automaattinen poiminta jää jatkoon. |
| Esimerkkitila näkyvästi erillinen | Demo voidaan esittää verkkovirheessä. Ei hiljaista mallivastauksen korvaamista. |
| Ihminen hyväksyy version | Muokattu tai hinnoittelematon sisältö ei vahingossa päädy Odoohon. |
| Epäselvän viennin pysäytys | Pelkkä HTTP-uusintayritys voi luoda duplikaatin. Tuotekoodihaku ja varaus pienentävät riskiä. |

## Toteutuksesta opittavaa

Muistettavat keskustelukohdat: neljä projektia ei tarkoita neljää asiakasta; puuttuva hinta ei tarkoita nollaa; hävitty kauppa ilman syytä ei todista hintaongelmaa; lähdeviite voi olla olemassa vaikka päätelmä olisi väärä. Lisää tähän käyttäjän omat havainnot esitysharjoituksen jälkeen.

## Tarkistetut viralliset lähteet

- https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
- https://hub.docker.com/_/odoo
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://fastapi.tiangolo.com/tutorial/
- https://vite.dev/guide/

Toteutuspäivä 20.9.2026. Python-riippuvuudet on lukittu `backend/requirements.lock.txt`-tiedostoon ja JavaScript-riippuvuudet `frontend/package-lock.json`-tiedostoon. Docker-kuvien digestejä ei ole vielä todennettu.

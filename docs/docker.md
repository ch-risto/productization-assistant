# Palvelupaja Dockerilla
22.9.2026

## Rakenne

Sama Compose käynnistää kolme palvelua: palvelupaja (FastAPI ja valmis React-kooste),
odoo (Odoo 18) ja db (PostgreSQL 15). Frontend rakennetaan Node-kuvassa ja kopioidaan
Python-ajokuvaan. Lopullinen sovelluskontti käyttää yhtä Uvicorn-prosessia ilman root-oikeuksia.

## Siirtyminen nykyisestä paikallisesta ajosta

Aja komennot projektin juuressa. Docker Desktopin tulee käyttää Linux-kontteja.

1. Pysäytä nykyinen paikallinen backend sen terminaalissa Ctrl+C:llä. Älä aja kahta
   backendia samaan SQLite-tietokantaan: käynnistys käsittelee kesken jääneet viennit.
2. Ota data-kansiosta varmuuskopio backendin pysäytyksen jälkeen.
3. Tarkista .env: ODOO_MODE=odoo sekä toimivat Odoo- ja OpenAI-tunnukset.
   Avaimia ei kopioida kuvaan; Compose välittää vain nimetyt asetukset.
4. Nykyinen sovellustietokanta oletetaan tiedostoksi data/app.db.
   Jos APP_DATABASE_URL osoitti aiemmin muualle, kopioi kyseinen tietokanta varmistuksen
   jälkeen data/app.db:ksi tai muuta Compose-liitos ennen käynnistystä.
5. Käynnistä:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail 80 palvelupaja
```

Avaa http://127.0.0.1:8000 ja API-ohje http://127.0.0.1:8000/docs.
Odoo on edelleen http://127.0.0.1:8069.

Palvelupajan terveystarkistus varmistaa HTTP-palvelimen, ei OpenAI-saldoa eikä Odoo-loginia.
Odoo voi käynnistyä sovellusta hitaammin: odota sen valmistumista ja päivitä aineisto.
PostgreSQL:n terveystarkistus ohjaa Odoon käynnistystä. Tyhjään Odoo-asennukseen on ensin
luotava tietokanta ja integraatiokäyttäjä README-ohjeen mukaan.

## Tallennus ja osoitteet

- ./data on pysyvä bind mount /app/data-polkuun. Nykyinen historia säilyy ilman
  siirtoa nimettyyn volumeen. Tämä on tietoinen paikallisen Windows-demon ratkaisu.
- ./demo-data liitetään vain luettavana. JSON-muutokset näkyvät ilman kuvan rakentamista.
- Odoon odoo-data- ja odoo-db-volumien nimet ja Compose-projektin nimi säilyvät.
- ODOO_URL on kontissa http://odoo:8069. localhost kontissa tarkoittaisi konttia itseään.
- ODOO_PUBLIC_URL on selaimelle avattava osoite, oletuksena http://127.0.0.1:8069.
- ODOO_TARGET_URL säilyttää saman Odoo-instanssin vanhan kohdetunnisteen
  http://127.0.0.1:8069. Näin seed-kartta ja vientilukitus eivät vaihdu kuljetusosoitteen mukana.
  Jos aiempi yhteys käytti localhost-nimeä, aseta tämä täsmälleen vanhaksi osoitteeksi.
  Älä käytä samaa kohdetunnistetta kahdelle eri Odoo-tietokannalle.
- Compose käyttää tietokantana aina sqlite:///data/app.db; hostin APP_DATABASE_URL
  ei ylikirjoita sitä. Tämä pitää levyn sijainnin yksiselitteisenä.
- Linux-hostilla data-kansion täytyy olla kirjoitettavissa UID/GID 10001:lle.
  Windows Docker Desktopin jako-oikeudet tarkistetaan, jos SQLite ei avaudu.

## Normaali käyttö

```powershell
# Koodimuutokset, myös frontend:
docker compose up -d --build palvelupaja

# .env-muutokset (pelkkä restart ei päivitä ympäristömuuttujia):
docker compose up -d --force-recreate palvelupaja

# Aineiston tarkistus:
docker compose exec palvelupaja python scripts/seed.py

# Odoo-aineiston tarkoituksellinen päivitys:
docker compose exec palvelupaja python scripts/seed.py --odoo --update-profile

# Pysäytys, tiedot säilyvät:
docker compose stop
```

Seed ei käynnisty automaattisesti: käynnistys ei korvaa Odoo-tuotteisiin tehtyjä muokkauksia.
Älä käytä down -v -komentoa normaaliin pysäytykseen, koska se poistaa Odoon volumet.
Bind mount -data säilyy konttia poistettaessa, mutta tarvitsee oman varmuuskopionsa.
Host-käynnistykseen palatessa pysäytä ensin docker compose stop palvelupaja.

## Toteutettu varmennus

Compose config --quiet hyväksyi rakenteen. Backendin 17 testiä läpäisivät, mukaan lukien
kontin sisäisen osoitteen, selainosoitteen ja pysyvän kohdetunnisteen erottaminen.
Docker-kuvan rakentaminen yritettiin, mutta tämän agentti-istunnon Docker-asetusten,
buildx-hakemiston ja named pipe -yhteyden käyttöoikeus esti sen myös lisäoikeuspyynnön jälkeen.
Kontin rakentumista tai käynnistymistä ei siten ole vielä varmennettu.
Ensimmäinen onnistunut ajo pitää tarkistaa: käyttöliittymä, favicon, aineistoluku,
vanhan kortin avaaminen ja historiatietojen säilyminen kontin uudelleenluonnin jälkeen.

## Mikä Nginx on ja milloin frontend erotetaan?

Nginx (lausutaan engine x) on verkkopalvelin. Se voi lähettää selaimelle HTML-, CSS- ja
JavaScript-tiedostot sekä välittää API-pyynnöt backendille. Jälkimmäistä tehtävää kutsutaan
käänteiseksi välityspalvelimeksi eli reverse proxyksi.
[Nginxin oma aloitusopas](https://nginx.org/en/docs/beginners_guide.html)

Nykyinen rakenne: selain → FastAPI → joko käyttöliittymätiedostot tai API.
Mahdollinen erotettu rakenne: selain → Nginx → tiedostot suoraan, /api-pyynnöt FastAPIlle.
React-koodi suoritetaan edelleen selaimessa, ei Nginxissä.

Erottaminen kannattaa, kun:
- käyttöliittymä ja backend julkaistaan eri tahtiin;
- staattisia tiedostoja halutaan jakaa CDN:llä tai erikseen skaalattuna;
- useille palveluille tarvitaan yhteinen verkkotunnus ja HTTPS-sisäänkäynti;
- frontendin jakelun asetuksia ja välimuistia halutaan hallita erillään APIsta.

Nginx voi hoitaa TLS/HTTPS-yhteyden, pakkausta, pyyntöjen välitystä ja kuormanjakoa.
Sen lisääminen ei yksin tee sovelluksesta turvallista tuotantopalvelua.
Kirjautuminen, käyttöoikeudet ja backendin moniprosessituen puutteet on ratkaistava erikseen.
[Nginx reverse proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy)

Erottamisessa tulee lisää ylläpidettävää: kaksi kuvaa, proxyreititys, API-versioiden
yhteensopivuus ja välimuistisäännöt. Samassa julkisessa osoitteessa /api-reitityksellä
voidaan välttää erillisten selainalkuperien CORS-järjestelyjä. Eri verkkotunnukset
edellyttävät alkuperä- ja kirjautumisasetusten suunnittelua.
Nginxin voi myös lisätä nykyisen yhdistelmäkontin eteen ilman frontendin erottamista.

Kehityksessä erillinen Vite-palvelin on eri asia kuin tuotannon Nginx: Vite näyttää
koodimuutokset nopeasti. Sitä ei tarvita valmiin koosteen tarjoiluun.
Nykyinen yhdistelmäkontti on Palvelupajan tässä vaiheessa yksinkertaisin ratkaisu.

[Dockerin monivaiheinen rakentaminen](https://docs.docker.com/build/building/multi-stage/)
ja [Compose-käynnistysjärjestys](https://docs.docker.com/compose/how-tos/startup-order/).

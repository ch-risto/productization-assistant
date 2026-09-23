# Jatkokehitys

## Demon valmistelu (historiallinen vaihe)

1. Oikea Odoo- ja OpenAI-ydinketju sekä toistuva vienti todennettiin 21.9.2026. Harjoittele nyt sama polku itse ja tarkista palvelukortin liiketoiminnallinen sisältö.
2. Keskity mallin lähdeuskollisuuteen: vastaesimerkkitesti paljasti edelleen liian vahvoja päätelmiä. Lisää arviointiaineistoa ja hyväksymiskriteerit ennen oikeaa asiakasdataa.
3. Tallenna Docker-kuvien digestit käyttäjän omasta terminaalista ja harjoittele 8–10 minuutin esitys. Varaa myös merkitty esimerkkitila verkkohäiriön varalle.

## Seuraava käyttökokeilu

- Käyttäjähaastattelu ja palvelukortin kenttien arviointi nykyisen tuotteistamistyön näkökulmasta.
- Enterprise 18 -testiympäristö ja `fields_get`-kenttäkartoitus; tuotannon räätälöinnit, valuutta, verot, käyttöoikeudet ja yrityskonteksti.
- Luvat oikean asiakasdatan käyttöön, minimointi, henkilötietojen poisto ja mallipalvelun sopimusten tarkistus ennen oikeaa aineistoa.
- Oikeiden havaintojen kerääminen ja malliarviointiaineisto. Vähäisellä aineistolla ideoinnin epävarmuus näkyvämmäksi.

## Myöhempi tuote

- Kirjautuminen, roolit, hyväksyjäkohtainen audit trail, tietokantamigraatiot ja varmistukset.
- Kilpailijaseuranta oikeilla lähdeosoitteilla ja tarkistuspäivillä; hinnoitteluperusteiden ja puuttuvan tiedon vertailu.
- Hallittu Odoo-synkronointi, poistot ja konfliktit; sivutus ja suuret aineistot.
- Odoo-puolen yksilöllinen ulkoinen tunniste ja transaktionaalinen idempotenssi, jos vientiä tarvitaan monelta palvelininstanssilta.
- Käyttökustannusten rajat, havainnointi, mallin versiot ja säännölliset arvioinnit.

Tuotantoon siirtyminen on erillinen päätös. Tämä toimitus ei kytkeydy työnantajan palvelimeen eikä julkaise sovellusta verkkoon.


## Päivitetty kehityspolku 22.9.2026

Seuraavien ominaisuuksien ensisijainen suunnitelma: [yhteinen arkkitehtuuri ja aikataulu](jatkokehitys-yhteinen.md), [modulaarinen katalogi](suunnitelma-tuotekatalogi.md) ja [tarjousavustaja](suunnitelma-tarjousavustaja.md).


## Julkaisupolku ja muistilista

Lisätty 22.9.2026. Tämä on toteutettava suunnitelma, ei todistus tuotantovalmiudesta.
Merkitse kohta valmiiksi vasta, kun vastuuhenkilö, tarkistuspäivä ja näyttö (testi,
asetuskatselmointi tai palautuskoe) on kirjattu. Soveltumaton kohta perustellaan.

Sisäverkko ja julkinen verkko kuvaavat saavutettavuutta. Pilvi kuvaa sijoituspaikkaa:
pilvipalvelukin voi olla vain yksityisverkossa. Valitse yhteinen perusta + verkon
mukainen tarkistuslista + pilvilista, jos ympäristö sijaitsee pilvessä.
Julkinen verkko ei tarkoita anonyymiä käyttöä.

### Lähtötilanne ja nykyiset julkaisuesteet

| Kohde | Tämänhetkinen tilanne | Ennen yrityskäyttöä |
|---|---|---|
| Kontitus | Tiedostot tehty, Compose-rakenne tarkistettu; agentin Docker-oikeudet estivät rakentamisen | Oikea build, käynnistys, uudelleenluonti ja tietojen säilyminen varmennettava |
| Käyttäjät | Ei kirjautumista tai käyttäjäkohtaisia oikeuksia | Tunnistus, roolit ja palvelinpuolen oikeustarkistukset |
| Verkko | Localhost- ja Origin-rajaukset, ei tuotannon HTTPS-ratkaisua | Kohdekohtainen sallittujen osoitteiden määritys ja luotettu proxy |
| Odoo | Paikallinen Community-demo, demo-DB ja kohderajaus | Enterprise-testikohde, oikeudet ja kenttäkartoitus |
| Tiedot | SQLite ja synteettinen JSON; historia tallentuu | Säilytys, palautus, migraatiot ja aidon tiedon käyttöpäätös |
| Rinnakkaisuus | Yksi backend-prosessi; käynnistys muuttaa pending-viennit uncertain-tilaan | Ei skaalausta ennen työnvarauksen uudistusta |
| Mallin laatu | Rakenne/lähde-ID-validointi, mutta semanttisia virheitä havaittu | Ihmisen tarkistus, käyttötapauskohtainen arviointi ja kulurajat |
| Hyväksyntä | Versioon sidottu tila, ei tunnistetun henkilön audit trailia | Hyväksyjä, aika, sisältöversio ja vientitapahtuma jäljitettäviksi |

17 automaattista testiä ja Compose-validointi eivät yksin osoita tuotantovalmiutta.
Tätä listaa päivitetään toteutuksen muuttuessa.

### Vaihe 0 — päätä julkaisun tarkoitus ja vastuut

- [ ] Rajaa ensimmäinen julkaisu: sisäinen pilotti, yrityksen normaali käyttö vai ulkoiset käyttäjät.
- [ ] Nimeä palvelun omistaja, tekninen ylläpitäjä, Odoo-vastuuhenkilö ja häiriötilanteen yhteystieto.
- [ ] Arvioi käyttäjät, samanaikaiset ajot, aineiston koko ja sallitut käyttöajat.
- [ ] Sovi palautumistavoite (kuinka pitkän katkon hyväksymme) ja tietohävikin raja
  (kuinka vanhasta varmistuksesta voidaan palauttaa).
- [ ] Päätä kustannusbudjetti, mallikutsujen rajat ja kuka saa hyväksyä niiden nostamisen.
- [ ] Dokumentoi käytettävät tiedot, mallipalveluun lähetettävä osuus sekä säilytys- ja poistotarpeet.
- [ ] Valitse testi- ja tuotantoympäristöt erillisillä tunnuksilla ja tietokannoilla.

Valmis, kun julkaisun laajuus, omistajat ja hyväksymiskriteerit on sovittu.
Suositeltu ensimmäinen kohde on rajattu sisäinen pilotti.

### Vaihe 1 — käyttäjät, oikeudet ja tietojen käsittely

- [ ] Liitä yrityksen kirjautumiseen, jos mahdollista. Määritä istunnon vanheneminen,
  uloskirjautuminen ja käyttäjän käyttöoikeuden poistaminen.
- [ ] Toteuta katselija, muokkaaja, hyväksyjä ja ylläpitäjä. Tarkista oikeudet jokaisessa
  API-toiminnossa ja tietueessa; painikkeen piilottaminen ei ole käyttöoikeus.
- [ ] Tallenna hyväksyjän tunniste, aika, hyväksytty versio ja vientikohde.
  Erota lokista malliehdotus, ihmisen muutos ja Odoo-kirjoitus.
- [ ] Suojaa selainistunnot valitun kirjautumistavan mukaan: evästeasetukset, CSRF,
  täsmälliset Origin/CORS-rajaukset ja palvelinpuolen validointi.
- [ ] Testaa luvaton luku, muokkaus, hyväksyntä ja vienti sekä toisen käyttäjän tietueen
  tunnisteen vaihtaminen. Päätä, mitkä tiedot todella ovat yhteisiä.
- [ ] Minimoi palaveriteksteistä ja asiakasdatasta mallille lähetettävät tiedot.
  Sovi tietojen käsittely, säilytys ja palveluntarjoajat yrityksen vastuuhenkilön kanssa.
- [ ] Älä lokita avaimia, kirjautumistunnisteita tai kokonaisia asiakastekstejä oletuksena.
- [ ] Toteuta tarvittava tietojen poisto ja dokumentoi, miten poistot toteutuvat
  historiassa ja varmistusten säilytysajan päättyessä.
- [ ] Säilytä avaimet suojattuina ajonaikaisina asetuksina tai salaisuuksien hallinnassa.
  Testaa avaimen vaihto ja vanhan avaimen mitätöinti.

Valmis, kun oikeusmatriisi ja sen kielteiset testit läpäisevät eikä todellista dataa
käsitellä ilman sovittua menettelyä.

### Vaihe 2 — tallennus, integraatiot ja virhetilat

- [ ] Päätä tietokantaratkaisu. Yhden prosessin rajattu sisäinen pilotti voi käyttää
  paikallista SQLitea, jos rajoitukset hyväksytään. PostgreSQL on suositeltu seuraava
  ratkaisu usealle käyttäjälle ja vaatimus ennen tämän suunnitelman monipalvelinajoa.
- [ ] Lisää versioidut migraatiot ja testaa päivitys vanhan tietokannan kopiolla.
- [ ] Ota salatut, palvelimesta erilliset varmistukset. Tee oikea palautuskoe tyhjään
  ympäristöön; tarkista rivit, korttihistoria ja Odoo-sidonnat.
- [ ] Varmista koordinoitu palautuminen: vanha Palvelupaja-varmistus ei saa aiheuttaa
  jo Odoohon vietyjen tuotteiden tai tarjousten sokkoluontia uudelleen.
- [ ] Rajaa Odoo-integraatiokäyttäjän mallit, yritykset ja toiminnot vähimpiin tarvittaviin.
  Älä käytä pääkäyttäjän tunnuksia.
- [ ] Korvaa localhost/demo-rajaus nimetyillä hyväksytyillä kohteilla.
  Älä avaa mallille tai käyttäjän tekstille mielivaltaisia osoitteita tai Odoo-metodeja.
- [ ] Varmenna kohteen Enterprise-kentät, yksiköt, verot, hinnastot ja valuutat testikohteessa.
- [ ] Testaa Odoon ja mallipalvelun katkot, aikakatkaisut, kiintiön loppuminen,
  puuttuvat oikeudet ja samanaikaiset muokkaukset.
- [ ] Estä moniprosessiajo, kunnes pending/uncertain-käsittely on korvattu turvallisella
  työnvarauksella. Työjono tarvitsee aikarajat, rajatut uusinnat ja idempotenssin.
- [ ] Ennen monipalvelinajoa varmista Odoo-puolen yksilöllinen vientiavain ja
  transaktionaalinen luonti tai dokumentoitu pysähtyminen epäselvän tuloksen selvitykseen.
- [ ] Estä käynnistyksen automaattinen seed ja demotietojen kirjoitus tuotantoon.

Valmis, kun palautus ja integraatiokatkot on kokeiltu eikä käyttäjän työ häviä
tai synny kaksoisvientejä testatuissa tapauksissa.

### Vaihe 3 — julkaisupaketti, laatu ja seuranta

- [ ] Rakenna Docker-kuva puhtaassa ympäristössä. Lukitse hyväksytty julkaisu
  muuttumattomalla versiotunnisteella/digestillä ja säilytä edellinen kuva.
- [ ] Aja automaattiset testit, frontend-kooste ja oikea selainpolku testikohteessa.
- [ ] Tarkista riippuvuudet ja kuvat tunnettujen haavoittuvuuksien varalta.
  Päätä löydösten käsittely ja päivitysvastuu.
- [ ] Varmista, ettei kuvassa tai rakennuslokeissa ole .env-tiedostoa, avaimia tai
  tuotannon tietokantaa. Tuotantokuvaan ei tarvita kehityksen lähdekoodiliitoksia.
- [ ] Aseta muisti-/CPU-rajat, lokien kierto, hallittu uudelleenkäynnistys ja levytilahälytys.
- [ ] Erota sovelluksen elossaolo riippuvuuksien toimintakyvystä. Mallipalvelun katko
  ei saa käynnistää palvelinta jatkuvasti uudelleen.
- [ ] Lisää pyyntö-/työtunniste, virhe- ja latenssimittarit sekä mallikulujen seuranta.
  Hälytyksillä on vastaanottaja ja lyhyt toimintaohje.
- [ ] Rajaa syötekoko, rinnakkaiset malliajot ja käyttäjäkohtainen kulutus.
- [ ] Arvioi mallia normaaleilla, puutteellisilla, ristiriitaisilla ja ohjeiden
  ohitusyrityksiä sisältävillä aineistoilla. Dokumentoi hyväksyttävä virhetaso
  käyttötapauksittain; pidä ihmisen hyväksyntä kirjoittavissa toiminnoissa.
- [ ] Julkaise käyttöohje, tunnetut rajoitteet, tukikanava ja version muutokset.

Valmis, kun sama kuva toimii testikohteessa, keskeiset hälytykset on laukaistu
kokeellisesti ja kaikki julkaisua estävät löydökset on käsitelty.

### Vaihe 4A — sisäverkkoon julkaisu

Yhteiset vaiheet 0–3 ovat voimassa myös sisäverkossa.

- [ ] Sijoita Palvelupaja mieluiten omaan virtuaalikoneeseen Odoon kanssa samaan
  hallittuun verkkoon. Samalla hostilla määritä resurssirajat ja yhteisen vian vaikutus.
- [ ] Määritä sisäinen DNS-nimi, HTTPS ja käyttäjien laitteiden luottama varmenne.
- [ ] Rajaa palomuuri käyttäjäverkkoihin/VPN:ään. Älä julkaise tietokannan porttia.
- [ ] Käytä Nginxiä tai muuta hallittua sisäänkäyntiä. Luota forwarded-otsakkeisiin
  vain tunnetulta proxylta ja estä backendin ohittaminen suoraan.
- [ ] Aseta sallitut Host-/Origin-osoitteet oikealle nimelle; nykyiset localhost-arvot
  eivät riitä. Älä korvaa niitä tarpeettomasti jokerimerkeillä.
- [ ] Varmista ulospäin tarvittava yhteys mallipalveluun sekä Odoon sisäinen yhteys.
- [ ] Pidä yrityksen olemassa oleva Odoo omassa elinkaaressaan; tuotannon Compose
  ei käynnistä tai päivitä sitä Palvelupajan mukana.
- [ ] Aloita pienellä käyttäjäjoukolla ja tarvittaessa ensin lukutoiminnoilla.
  Avaa kirjoitukset vasta hyväksyntä- ja palautustestien jälkeen.

Julkaisuportti: oikeudet, HTTPS, palautus, Odoo-kohde ja tukivastuu varmennettu.
VPN tai sisäverkko ei korvaa sovelluksen käyttöoikeuksia.

### Vaihe 4B — julkiseen verkkoon julkaisu

Lisää yhteisten vaiheiden päälle seuraavat; julkinen julkaisu voi olla omalla palvelimella.

- [ ] Käytä julkista DNS-nimeä, HTTPS:ää ja valvottua varmenteen uusintaa.
- [ ] Edellytä kirjautumista; sovella yrityksen MFA-käytäntöä, erityisesti ylläpitoon.
- [ ] Rajaa sisään tuleva liikenne tarkoitettuun sisäänkäyntiin. Tietokanta, työjono,
  Docker-hallinta ja Odoo-integraatiorajapinta eivät avaudu sivuvaikutuksena internetiin.
- [ ] Lisää pyyntönopeus-, kokoraja- ja kustannusrajoitukset sekä kirjautumisen
  väärinkäytön torjunta. Arvioi DDoS-suojaus ja WAF tarpeen mukaan.
- [ ] Tarkista TLS, suojausotsakkeet ja sovellukseen sopiva CSP; testaa toimivuus.
- [ ] Poista debug-asetukset ja rajaa hallinta-, diagnostiikka- ja API-dokumentaation
  näkyvyys tarkoituksenmukaisesti. Dokumentaation piilottaminen ei korvaa API-suojausta.
- [ ] Tee julkisen hyökkäyspinnan katselmointi ja oikeuksien ohituksen testit.
  Ulkopuolisen tietoturvatestauksen tarve päätetään tiedon ja käytön riskien mukaan.
- [ ] Määritä häiriö- ja tietoturvapoikkeaman käsittely, avainten sulkeminen ja
  kirjoitusten nopea keskeytys.
- [ ] Jos käyttäjät ovat useista yrityksistä, toteuta yrityseristys kaikkiin tietueisiin,
  hakuihin, välimuisteihin, taustatöihin ja Odoo-yhteyksiin ennen asiakaspilottia.

Julkaisuportti: ulkoverkosta tehty testi ei pääse tietoihin ilman oikeuksia;
kulutusrajat, valvonta ja häiriötoimet on kokeiltu. Sisäinen pilotti ei yksin täytä tätä porttia.

### Vaihe 4C — pilveen sijoittaminen

Valitse lisäksi 4A tai 4B saavutettavuuden mukaan. Pilveen siirtyminen ei itsessään
edellytä julkista osoitetta eikä poista yhteisten vaiheiden vaatimuksia.

- [ ] Valitse virtuaalikone tai hallittu konttialusta ja dokumentoi vastuunjako:
  käyttöjärjestelmä, alusta, tietokanta, varmistus ja sovellus.
- [ ] Valitse alue ja selvitä tietojen, lokien, varmistusten sekä mallikutsujen sijainnit.
- [ ] Määritä palveluiden identiteetit ja vähimmät IAM-oikeudet. Pidä ylläpito erillään
  sovelluksen tunnuksista; käytä hallittua salaisuuksien säilytystä.
- [ ] Käytä pysyvää tietokantaa ja tarvittaessa objektitallennusta. Kontin paikallinen
  tiedostojärjestelmä ei saa olla ainoa tallennuspaikka.
- [ ] Järjestä yksityinen tai muuten rajattu suojattu yhteys omaan Odoohon.
  Testaa reititys, DNS, palomuuri, sertifikaatit ja yhteyskatko.
- [ ] Aseta instanssimääräksi yksi, kunnes moniprosessituki on varmennettu.
  Myös rolling update voi hetkellisesti käynnistää kaksi instanssia: estä päällekkäisyys
  väliaikaisesti tai ratkaise työnvaraus ennen tällaista julkaisua.
- [ ] Määritä budjetti- ja kuluhälytykset, maksimiskaala ja lokien säilytys.
  Hälytys ei yleensä ole kulutuksen katkaisu: tarvitaan sovelluksen omat rajat.
- [ ] Määritä infrastruktuuri toistettavasti ja testaa ympäristön uudelleenluonti.
- [ ] Valitse varmistus- ja saatavuustaso tavoitteiden mukaan; hallittu palvelu ei
  automaattisesti tarkoita usean alueen vikasietoisuutta.
- [ ] Kokeile tietojen vienti ja palautus myös siirrettävyyden kannalta.

Julkaisuportti: valitun verkkotason portti sekä pilven käyttöoikeudet, pysyvä tallennus,
kustannusrajat ja Odoo-yhteys varmennettu.

### Vaihe 5 — ensimmäinen julkaisu ja palautussuunnitelma

1. [ ] Kirjaa julkaisun kuva/digest, asetusten versio, migraatiot ja hyväksyjä.
2. [ ] Ilmoita huoltoikkuna, ota varmistus ja varmista viimeisimmän palautuskokeen tulos.
3. [ ] Estä uudet kirjoitukset ja anna keskeneräisten töiden valmistua tai tallenna niiden tila.
4. [ ] Aja migraatiot hallitusti ja käynnistä hyväksytty versio.
5. [ ] Tarkista kirjautuminen, käyttöoikeudet, aineiston luku, vanha historia ja
   hyväksyntäpolku. Mahdollinen tuotannon vientikoe tehdään erikseen sovitulla testitietueella.
6. [ ] Seuraa virheitä, vasteaikoja ja kustannuksia ennen käyttäjäjoukon laajentamista.
7. [ ] Päätä etukäteen palautuksen käynnistävät virheet ja vastuuhenkilö.

Palautus ei tarkoita automaattisesti vanhan tietokantavarmistuksen päällekirjoitusta.
Tarkista, voiko edellinen sovellusversio lukea uuden skeeman. Jos ei, käytä
ennalta testattua palautus- tai eteenpäin korjausmenettelyä. Odoossa jo tehdyt
kirjoitukset jäävät voimaan ja sovitetaan palautettuun Palvelupajaan.

### Vaihe 6 — ylläpito julkaisun jälkeen

- [ ] Nimeä päivitysten, varmenteiden, varmistusten ja hälytysten seurannan omistajat.
- [ ] Tarkista käyttöoikeudet käyttäjämuutoksissa ja sovitulla määräaikaisrytmillä.
- [ ] Toista palautuskoe ja malliarvioinnit merkittävien muutosten yhteydessä sekä
  sovitulla säännöllisellä rytmillä.
- [ ] Seuraa tuotteen soveltuvuutta: virheelliset ehdotukset, käyttäjän tekemät korjaukset,
  epäselvät viennit ja toistuvat asiakastarpeet.
- [ ] Pidä käyttöohje ja tämä valmiuslista ajan tasalla jokaisessa julkaisussa.

### Suositeltu toteutusjärjestys Palvelupajalle

1. Varmenna konttikuva ja säilyvät tiedot, järjestä erillinen testiympäristö.
2. Toteuta kirjautuminen, oikeudet, audit trail ja palautus.
3. Varmenna Enterprise-integraatio ja julkaise rajattu sisäinen pilotti.
4. Toteuta katalogi- ja tarjoussuunnitelmat yhteistä tietomallia käyttäen.
   Odoo-tarjouskirjoitukset vaativat oman hyväksymis- ja integraatiotestinsä.
5. Lisää PostgreSQL, taustatyöt ja moniprosessituki käyttötarpeen mukaan ennen skaalausta.
6. Avaa julkinen käyttö tai siirrä pilveen vasta vastaavan julkaisuportin jälkeen.

Katalogin ja tarjousavustajan aikaisempi 18–28 päivän työmäärä ei sisällä kaikkia tämän
julkaisumuistilistan tuotantovalmiustöitä. Niille tehdään oma arvio kohdeympäristön ja
yrityksen olemassa olevien kirjautumis-/ylläpitoratkaisujen kartoituksen jälkeen.

### Tarkistusnäytön kirjauspohja

| Kohta | Vastuuhenkilö | Tila | Näyttö / testitulos | Päivä | Avoin riski ja hyväksyjä |
|---|---|---|---|---|---|
| Esim. palautuskoe | Nimetään | Avoin | Linkki testiraporttiin | — | — |

### Lähtölähteet

Listan soveltaminen ja julkaisuportit ovat Palvelupajalle tehty suunnitelma.
Docker kuvaa Compose-tuotantoajon järjestelyjä:
[Use Compose in production](https://docs.docker.com/compose/how-tos/production/).
Salaisuuksien elinkaaren ja lokitietojen suojauksen taustaksi:
[OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
ja [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

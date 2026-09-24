# Perustuotekatalogin ensimmäinen toteutus

23.9.2026. Suunnitelman A0/A1 ensimmäinen osuus, ei koko katalogisuunnitelman valmistuminen.

Saman päivän jatkototeutus: [tuotteistusagentti ja palvelukoosteluonnokset](tuotteistusagentti.md).
Alla oleva ensimmäisen osuuden rajaus säilyy historiallisena; tekoälyehdotukset ja
koosteluonnosten muodostaminen ovat nyt käytössä erillisessä työnkulussa.

## Käyttö

Käynnistä päivitetty backend ja frontend-kooste README:n ohjeella. Avaa sivupalkin
**Perustuotekatalogi**. Lisää rajattu myytävä kokonaisuus, tallenna luonnos ja hyväksy
sisältö tarkistuksen jälkeen. Hintaa ei arvata eikä suunnitelman esimerkkituotteita
luoda automaattisesti.

Pakollisia tietoja ovat nimi, asiakkaan lopputulos, kohdetarve, toimitussisältö,
rajaukset ja hyväksymiskriteerit. Projektitehtävän työohje on erillinen kenttä:
sisäistä työvaihetta ei tarvitse tuotteistaa. Myyntiyksikön, laskutuksen ja
projektin muodostumisen valinnat ovat tässä vaiheessa ehdotuksia.

Tallennus säilyttää tuotteen tunnisteen ja lisää version. Sisällön hyväksyntä lisää
oman version; myöhempi muokkaus palauttaa tuotteen luonnokseksi. Historia säilyttää
aiemmat sisällöt ja hyväksynnät. Samanaikainen vanhan version tallennus estetään.
Sisältöhyväksyntä ei ole Odoo-julkaisuhyväksyntä eikä tunnistetun hyväksyjän audit trail.

Pakolliset riippuvuudet ja yhteensopimattomat tuotteet viittaavat katalogin pysyviin
tunnisteisiin. Tuntemattomat viitteet, itsensä vaatiminen, syklit ja transitiivisten
riippuvuuksien ristiriidat estetään. Riippuvuus tulee hyväksyä ennen riippuvaa tuotetta.
Tämä ei vielä jäädytä riippuvuuksien versioita: tulevat reseptit ja tarjoukset tarvitsevat
omat versiosidontansa ja uudelleentarkistuksen.

Päällekkäisyyksien tarkistus vertailee tarpeen ja lopputuloksen yhteisiä sanoja.
Se ei ole kattava semanttinen vertailu. Lähdeviitteet ovat käyttäjän kirjaamia;
niiden sisältöä tai oikeellisuutta ei tässä vaiheessa varmenneta automaattisesti.

## Odoo-kartoitus

**Lue nykyiset asetukset** lukee nykyisen adapterikohteen yrityskontekstin,
tuotemallien, projektimallin ja tarjouspohjamallin kentät sekä mallikohtaiset
luku-, luonti- ja muokkausoikeudet. Aktiiviset myyntiyksiköt luetaan sivutettuina.
Tilannekuva tallennetaan paikalliseen tietokantaan aikaleiman ja kohteen kanssa.
Yrityskonteksti on integraatiokäyttäjän oletusyritys, ei kaikkien sallittujen yritysten yhdistelmä.

Kenttävalinnan löytyminen ei tarkoita toimivaa työnkulkua. Mallioikeus ei todista
tietuekohtaista oikeutta. Puuttuva moduuli tai epäonnistunut luku merkitään
varmentamattomaksi. Esimerkkitila ei esitä keksittyjä Odoo-asetuksia varmennettuina.
Kartoitus ei kirjoita Odoohon, vahvista tilausta tai luo projekteja.

Odoo 18:n omat mallit ovat jatkototeutuksen perusta:

- [sale_project: palvelutuotteen laskutus ja projektiseuranta](https://github.com/odoo/odoo/blob/18.0/addons/sale_project/models/product_template.py)
- [sale_timesheet: tuntikirjausten laskutus ja yksiköt](https://github.com/odoo/odoo/blob/18.0/addons/sale_timesheet/models/product_template.py)
- [sale_management: tarjouspohjat ja yritysrajaukset](https://github.com/odoo/odoo/blob/18.0/addons/sale_management/models/sale_order_template.py)

Odoon `task_global_project` tarkoittaa tehtävää olemassa olevaan projektiin;
`task_in_project` voi luoda projektin ja tehtävän. Katalogin editori näyttää eron,
mutta asetusten julkaisu tarvitsee kohdekohtaisen testin. Odoon `onchange`-logiikkaa
ei saa olettaa suoritetuksi ulkoisen rajapinnan kirjoituksessa. Hinnat, verot,
valuutat ja hinnastot säilyvät Odoon vastuulla.

## Tekninen rajaus

Uudet rajapinnat: `GET/POST /api/catalog`, `PUT /api/catalog/{id}`,
`POST /api/catalog/{id}/approve`, `GET /api/catalog/{id}/history`,
`GET /api/catalog/{id}/similar` sekä `GET/POST /api/catalog/capabilities`.

Additiivinen migraatio 1 luo `catalog_items`, `catalog_versions` ja
`catalog_capabilities` -taulut yhden transaktion sisällä. Migraatioversio tallennetaan
`schema_migrations`-tauluun. Vanhoja kortteja, analyysejä ja vientitietoja ei muuteta.
Nykyiset cards/runs-rajapinnat säilyvät. Katalogin muutosrajapinnat käyttävät samaa
Origin-rajausta kuin vanha sovellus. Sovelluksen aiemmat paikallisen prototyypin
rajoitukset, kuten kirjautumisen puuttuminen, ovat edelleen voimassa.

## Seuraava toteutusosuus

1. Enterprise 18 -testikohteen kartoitus ja kaksi koetilausta: yksiköt,
   kiinteä/tuntikirjauslaskutus sekä usean osatuotteen yhteinen projekti ja tehtävät.
2. Valitun Odoo-tuoteryhmän luku, template/variant-sidonta, kaupallinen snapshot,
   julkaisuvalidointi ja versioon sekä kyvykkyyksiin sidottu vientihyväksyntä.
3. Saman Odoo-tuotteen hallittu luonti/päivitys, konfliktit ja epäselvän viennin
   selvitys. Uudella katalogilla ei vielä ole vientireittiä.
4. Hyväksyttyihin tuoteversioihin sidotut pakettireseptit, valintasäännöt ja
   staattisten reseptien erillinen vienti Odoon tarjouspohjaksi.
5. Vanhan palvelukortin luokittelu tuotteeksi tai reseptiksi sekä mallin ehdotukset.

## Varmennus

23.9.2026: 32 automaattista testiä läpäisty, TypeScript-tarkistus ja Vite-kooste
onnistuivat. Selaimessa erillisellä testitietokannalla varmennettu perustuotteen
luonti, sisältöhyväksyntä (versio 2) ja esimerkkitilan varmentamaton kartoitus.
Testien väliaikaishakemistona käytettiin projektin `data/test-catalog-20260923`-
kansiota, koska Windowsin oletusväliaikaiskansion luku estyi käyttöoikeuksiin.
Oikean paikallisen Odoon lukuyritys sai yhteyden hylkäyksen (WinError 10061).
Todellisen kohteen kyvykkyydet ja työnkulku ovat siksi vielä varmentamatta.

Automaattiset testit kattavat versionvaihdot, historian säilymisen, rinnakkaisen
muokkauksen, riippuvuudet, ristiriidat, API-virheet, migraation toistettavuuden ja
Odoo-kartoituksen lukurajauksen, yrityskontekstin sekä sivutuksen. Adapteritestit
eivät osoita yhteensopivuutta oikean Enterprise-ympäristön kanssa.

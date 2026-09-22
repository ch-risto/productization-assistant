# Suunnitelma 1: Odoon kanssa toimiva modulaarinen tuotekatalogi
22.9.2026 · [Yhteinen tietomalli ja aikataulu](jatkokehitys-yhteinen.md)

## Tavoiteltu muutos

Palvelupaja ehdottaa uudelleenkäytettäviä myytäviä osia ja näyttää erikseen, miten niistä
rakennetaan kokonaisuuksia. Laaja verkkosivuratkaisu on yleensä pakettiresepti, ei
automaattisesti yksi uusi tuote. Yhtenä tuotteena myytävä kokonaistoimitus on silti sallittu,
jos sillä on vakioitu rajaus, myyntiyksikkö, hinta ja toimitusvastuu.

Tuote jaetaan osiin, kun osalla on itsenäinen arvo, erillinen määrä/hinta,
eri laskutuslogiikka tai sitä käytetään useissa kokonaisuuksissa. Sisäisiä työvaiheita,
kuten yksittäistä testausta, ei tehdä tuotteiksi vain siksi, että niitä voidaan nimetä.

### Konkreettinen lähtökatalogi

Nämä ovat suunnitteluesimerkkejä, eivät automaattisesti luotavia tuotteita tai hintapäätöksiä.

| Myytävä osa | Yksikkö ja rajaus | Laskutusmallin ehdotus |
|---|---|---|
| Tarvekartoitus | 1 kartoitus, rajattu osallistujamäärä ja kirjallinen tulos | Kiinteä kertahinta |
| Tekninen määrittely | 1 rajattu järjestelmä/toimitus | Kiinteä hinta tai erikseen määritellyt etapit |
| Sivupohjan toteutus | 1 sovitun tyyppinen sivupohja | Määrä × yksikköhinta |
| Integraation selvitys | 1 rajapintapari, toteutus ei sisälly | Kiinteä kertahinta |
| Integraation toteutus | Tunnit, vain arvioitu ja hyväksytty rajaus | Toteutuneen työn laskutus, jos tuettu |
| Saavutettavuusarviointi | Määritelty otos ja raportti, ei vaatimustenmukaisuuslupausta | Kiinteä kertahinta |
| Käyttöönottokoulutus | 1 sovitun pituinen koulutus | Kiinteä kertahinta |
| Ylläpito | Yksi rajattu palvelukohde ja palvelutaso | Toistuva laskutus vain varmennetulla tuella |

Paketti ”Verkkopalvelun uudistus” voisi valita määrittelyn, sivupohjat ja koulutuksen,
sekä tarjota ylläpidon erillisenä jatkuvana osana. Asiakastarve ratkaisee valinnan.
Sisällöntuotanto ei ole pakollinen osa eikä kielletty tuotetyyppi.

## Odoo-rajojen huomiointi

| Ominaisuus | Suunnitteluratkaisu |
|---|---|
| Tuote ja variantti | Tuotteen kuvaus product.template-tasolla; myytävä variantti product.product-tasolla. Variantteja vain saman tuotteen todellisille valinnoille. |
| Myyntiyksikkö | Paketti/kappale ja tunti erotetaan. Yksikkökategorioiden muunnoksia ei oleteta. |
| Kiinteä, toimitettu ja etappilaskutus | Sallitaan vain kohteen tukemat yhdistelmät. ”Kiinteä hinta” ei itsessään määritä maksuehtoja tai ennakkolaskua. |
| Projektin/tehtävän luonti | Tuoteasetusten vaikutus tilauksen vahvistuksessa testataan. Jokainen osatuote ei saa vahingossa luoda omaa projektia. |
| Tarjouspohja | Sopii toistuviin tuotekoostumuksiin. Palvelupajan resepti säilyttää riippuvuudet ja ehdolliset valinnat. |
| Valinnaiset tuotteet | Lisämyyntivaihtoehtoja; eivät korvaa pakollisia riippuvuuksia tai yhteensopivuussääntöjä. |
| Jatkuva palvelu | Pelkkä ”€/kk”-teksti ei muodosta tilausta. Vaatii kohteen tilaus-/laskutusominaisuuksien varmennuksen. |
| Verot, hinnastot ja yritys | Odoo on kaupallisten sääntöjen lähde. Palvelupaja ei oleta kaikille tuotteille samaa veroa tai hinnastoa. |
| Tuotesarjat/BOM/kit | Ei ensisijainen tapa palvelupaketeille tässä versiossa. Tarjousrivit ja reseptit riittävät ilman valmistuksen logiikkaa. |

Odoo 18:n sale_project-lähdekoodi sisältää palvelun laskutus- ja projektiseurantavalintoja.
Tämä todistaa perusmallin mahdollisuudet, ei työnantajan asennetun ympäristön kaikkia
valintoja. [Odoo 18 sale_project](https://github.com/odoo/odoo/blob/18.0/addons/sale_project/models/product_template.py)

Odoo tukee tarjouspohjia ja valinnaisia tuotteita. Reseptin sääntömoottori on tässä
suunnitelmassa Palvelupajan lisätoiminto, ei väite Odoon vakio-ominaisuudesta.
[Tarjouksen luonti](https://www.odoo.com/documentation/18.0/applications/sales/sales/sales_quotations/create_quotations.html),
[valinnaiset tuotteet](https://www.odoo.com/documentation/18.0/applications/sales/sales/sales_quotations/optional_products.html),
[tarjouspohjan lähdekoodi](https://github.com/odoo/odoo/blob/18.0/addons/sale_management/models/sale_order_template.py).

## Vaihe A0: kohteen kyvykkyyskartoitus, 2–3 päivää (yhteinen vaihe)

1. Käyttöön erillinen Enterprise 18 -testiympäristö tai vastaava puhdas asennus tarvittavilla lisäosilla.
2. Selvitetään Sales, Project, Timesheets ja mahdollinen Subscriptions sekä räätälöinnit.
3. Luetaan fields_get, sallitut valinta-arvot, oikeudet ja yrityskonteksti.
4. Tallennetaan capability-snapshot: tuettu / ei tuettu / ei varmistettu.
5. Kokeillaan testituotteilla myyntiyksikköä, laskutustapaa ja projektin muodostumista.
   Vahvistuskoe vain testiympäristössä. Pelkkä kentän olemassaolo ei ole riittävä testi.
6. Rajataan ensimmäinen julkaisu kiinteään ja tuntiperusteiseen kertamyyntiin.
   Etapit ja jatkuvat palvelut aktivoidaan vasta omien kokeidensa jälkeen.

## Vaihe A1: katalogin rakentaminen, 4–6 päivää

Lisätään CatalogItem-skeema: lopputulos, toimitussisältö, rajaukset, hyväksymiskriteeri,
kohdetarve, soveltuvuus/ei-soveltuvuus, lähtötiedot, yksikkö, määrärajat, hintamalli,
toimitusmalli, riippuvuudet, ristiriidat, lähteet ja Odoo-sidonta.

Työnkulku: havainto → nykykatalogin vertailu → olemassa olevan tuotteen käyttö /
tuotteen päivitysehdotus / uusi osa / pakettiresepti → käyttäjän arvio → julkaisu.
Malli ehdottaa luokittelua; validointi estää tuntemattoman yksikön tai tukemattoman
Odoo-yhdistelmän. Uuden tuotteen hintaa ei päätellä kilpailijan hinnasta automaattisesti.

Ensimmäinen käyttöliittymä: katalogitaulukko, tuotteen editori ja Odoo-asetusten tarkistus.
Käyttäjä näkee, mikä on mallin ehdotus ja mikä Odoosta vahvistettu asetus.
Päällekkäisyystarkistus hakee saman tarpeen ja lopputuloksen tuotteet, ei vain samannimisiä.

## Vaihe A2: paketit ja säännöt, 3–5 päivää

Pakettiresepti viittaa olemassa oleviin hyväksyttyihin tuotteisiin. Säännöt ovat
rakenteisia: requires, excludes, one_of, quantity_rule ja execution_order.
Sama vaatimus voidaan täyttää asiakkaan olemassa olevalla ratkaisulla; tällöin ei
automaattisesti myydä vastaavaa osaa uudelleen. Riippuvuussyklit estetään.

Resepti laajenee tarkistettaviksi tarjousriveiksi. Paketin otsikko on osio, ei toinen
laskutettava tuote samoista osista. Mahdollinen pakettialennus on erillinen hyväksytty
kaupallinen sääntö. Kertamyynti ja jatkuva osa esitetään erikseen.

Ensimmäisessä versiossa reseptin ei tarvitse synkronoitua Odoon tarjouspohjaksi.
Staattisen reseptin vienti tarjouspohjaksi on myöhempi lisä; ehdollisuuksia ei kadoteta
hiljaisesti staattiseen muotoon.

## Hyväksymiskriteerit

- Sama tuote toimii kahdessa eri paketissa ilman kopioita.
- Yksi laaja vanha kortti voidaan muuntaa reseptiksi ilman vanhan historian muutosta.
- Pakollinen riippuvuus, ristiriita ja syklinen resepti havaitaan.
- Tuotteen päivitys säilyttää identiteetin eikä muuta vanhaa hyväksyttyä tarjousta.
- Tuoteasetukset vastaavat Odoossa hyväksyttyä versiota ja tuettuja valintoja.
- Kahden koostetun koetarjouksen vahvistus testiympäristössä luo tarkoitetut projektit/
  tehtävät. Kymmenen tuoteriviä ei synnytä vahingossa kymmentä projektia.
- Vanha hyväksyntä/vienti ja epäselvän verkkovirheen käsittely läpäisevät regressiot.
- 10–15 rajattua tuotetta ja 2–3 reseptiä riittävät ensimmäiseen pilottiin.

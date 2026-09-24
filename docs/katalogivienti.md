# Perustuotteet Odoohon ja palvelun kattava pilkkominen

24.9.2026. Tämä toteutus täydentää 23.9. luotua katalogia ja tuotteistusagenttia.

## Miksi tallennettu tuote ei näkynyt Odoossa?

Katalogiin tallennus ja sisältöhyväksyntä olivat aiemmin vain Palvelupajan toimintoja.
Perustuotteille ei ollut vientireittiä. Vanhojen palvelukorttien vienti on erillinen
toiminto, eikä se vie uuden katalogin tuotteita.

## Näin viet nykyisen perustuotteen

1. Käynnistä päivitetty sovellus ja avaa **Perustuotekatalogi**. Avaa haluttu tuote.
2. Anna **Yksikköhinta Odoo-yrityksen valuutassa**. Tarkista yksikkö ja laskutustapa.
   Jos haluat tehtävän olemassa olevaan projektiin, anna sen Odoo-tunniste.
3. **Tallenna luonnos → Hyväksy sisältö → Tarkista viennin esikatselu**.
4. Tarkista yritys, valuutta, yksikkö, Odoon oletusverot ja projektiasetus. Valitse
   **Hyväksy vienti Odoohon**. Onnistumisen jälkeen saat tuotekoodin ja **Avaa tuote
   Odoossa** -linkin. Tuote löytyy Odoon myyntituotteista koodilla `PP-BASE-…`.

Jos käytössä on esimerkkitila, painike sanoo **Simuloi vienti**. Simulaatio ei luo
Odoo-tuotetta. Oikea vienti edellyttää toimivaa `ODOO_MODE=odoo`-yhteyttä.
Vanhoja tuotteita ei viedä automaattisesti päivityksen tai käynnistyksen yhteydessä.

Työvaiheet viedään tuotteen sisäiseen kuvaukseen ja myyntiteksti erikseen
myyntikuvaukseen. Tuotteen luonti ei vahvista tilausta eikä luo projektia tai tehtävää.
Odoon myyntitilauksen vahvistus käyttää valittua projektiseurantaa. Työvaiheista ei
vielä luoda automaattisesti erillisiä alitehtäviä tai Odoon suunniteltuja tunteja.

## Useita osia, kattavat työvaiheet ja tunnit

Agentti toimii kahdessa vaiheessa:

1. Työsuunnittelija muodostaa toimitettavat osat ja niiden työvaiheet sekä perustelee
   tuntiarviot. Esimerkiksi määrittely, sivupohjien toteutus ja koulutus voidaan
   tuotteistaa erikseen. Sisäiset valmistelu- ja tarkistustyöt kuuluvat osan työvaiheisiin.
2. Tuotteistaja valitsee jokaiselle osalle nykyisen tuotteen, uuden perustuotteen tai
   avoimen asiantuntijatyötuotteen. Jokaisen osan pitää saada oma tuoterivi; osia ei
   saa pudottaa tai yhdistää takaisin yhdeksi laajaksi tuotteeksi toisessa vaiheessa.

Yhden tuotteen luokitus tarkistetaan vielä erillisellä mallikutsulla. Tuoterivien
määrä, uusien tuotteiden pakolliset tiedot, sallitut katalogiviitteet ja lähdekatkelmat
rajataan vastausrakenteessa. Tämä ei takaa sisällön tai tuotteistusjaon oikeellisuutta:
tarkista näkyvä ehdotus ennen tallennusta.

Jos palvelu on mielekkäästi vain yksi tuote, tulos on **Palvelu itsessään on
perustuote**. Uusi tuote säilyttää palvelun nimen. Erillistä yhden rivin pakettia ei
luoda. Nykyisen tuotteen uudelleenkäyttö ei tee kopiota.

Käyttäjä voi antaa palvelun kokonaistunnit. Laskenta säilyttää lähteen vaihekohtaiset
tunnit ja sovittaa mallin suhteelliset arviot jäljelle jäävään tuntimäärään.
Sovitettu jako merkitään arvioksi, alkuperäinen malliarvio säilyy metadatassa.
Jos lähteen tunnit ovat ristiriidassa kokonaismäärän kanssa, ehdotus pysähtyy tarkistukseen.
Ilman kokonaistunteja näytetään arvioitujen tuntien summa ja avoimien vaiheiden määrä.
Tuntituotteen rivimäärän pitää vastata sen vaiheiden tuntisummaa. Kappaletuotteen
työmäärä ei muutu sen myyntimääräksi.

Näkyvä työsuunnitelma säilyy analyysissä ja palvelukoosteessa. Uusien tuotteiden
työohjeisiin lisätään tunnistetut työvaiheet. Tuntiarviot ovat toimituskohtaisia,
eivät automaattisesti tuotteen kiinteä myyntihinta tai sitova työmäärälupaus.
Jos osajakoa tai tuntien jakoa pitää muuttaa, täsmennä lähtötiedot ja tee uusi analyysi.
Vanhojen analyysien sisältöä ei kirjoiteta uudelleen.

## Odoo-toteutuksen rajat

- `product.template` luodaan palveluksi, ja myytävä `product.product`-variantti luetaan
  takaisin. Myynti- ja ostoyksikkö ratkaistaan Odoon omista ulkoisista tunnisteista.
- Yritys, valuutta, oletusverot ja tuettujen asetusten valinnat luetaan kohteesta.
  Esikatselu sidotaan sisältöversioon ja kohteeseen; asetukset tarkistetaan ennen luontia.
- Vientiyritykset tallennetaan erikseen. Toistuva onnistunut vienti palauttaa saman
  tuotteen. Aikakatkaisun jälkeen ensin etsitään jo luotu tuote ja verrataan asetuksia;
  epäselvässä tilanteessa ei luoda toista tuotetta sokkona.
- Luonti toimii nykyisessä paikallisessa Odoo 18 -demokohteessa. Enterprise- ja
  usean palvelinprosessin tuotantovarmennus eivät sisälly tähän muutokseen.
- Ensimmäinen vientiversio lukitsee viedyn sisällön. Hallittu olemassa olevan tuotteen
  päivityssynkronointi ja vanhan Odoo-tuotteen käsinsidonta ovat jatkotöitä.
- Pakettien vienti tarjouspohjiksi ei vielä sisälly tähän. Tuntiperusteinen laskutus
  edellyttää kohteen Timesheets-tukea; puuttuvaa ominaisuutta ei korvata toisella
  laskutusmallilla hiljaisesti.

Pohjana käytetään Odoo 18:n omia
[palvelutuoteasetuksia](https://github.com/odoo/odoo/blob/18.0/addons/sale_project/models/product_template.py),
[tuntikirjausasetuksia](https://github.com/odoo/odoo/blob/18.0/addons/sale_timesheet/models/product_template.py)
ja [tuotemallia](https://github.com/odoo/odoo/blob/18.0/addons/product/models/product_template.py).

Migraatio 3 lisää vientisuunnitelmat ja vientiyritykset muuttamatta vanhoja kortteja.
Käynnistys merkitsee kesken jääneet viennit epäselviksi, kuten vanhassa korttiviennissä.
Uudet reitit: `GET /api/catalog/{id}/export-status`,
`POST /api/catalog/{id}/export-preview`, `POST /api/catalog/{id}/export`.

## Varmennus

Oikeaan paikalliseen Odoo 18 -demoon luotiin **TESTI - perustuotekatalogin vienti
24.9.2026**, template-ID 11 ja variantti-ID 11. Hinta 125 EUR, kohteen oletusvero
25,5 %, kappaleyksikkö ja manuaalinen projektiseuranta luettiin takaisin.
Toistuva vienti palautti saman tuotteen. Käyttäjän olemassa olevia katalogituotteita
ei viety automaattisesti. Tämä koe ei vahvistanut tilausta eikä testannut tehtävien syntymistä.

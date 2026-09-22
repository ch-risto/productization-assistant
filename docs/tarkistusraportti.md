# Palvelupaja — tarkistusraportti 21.9.2026

## Tulos

**Oikea integraatioketju toimii:** Odoo-luku → OpenAI-ideat ja korttiluonnos → muokkaus → hinnoittelu → hyväksyntä → Odoo-vienti. Viety tuote tarkistettiin sekä rajapinnasta että Odoon omasta käyttöliittymästä. Mallin sisältölaadussa on kuitenkin edelleen puutteita; teknisesti hyväksytty vastaus ei välttämättä ole perusteltu.

## Varmennetut asiat

| Tarkistus | Tulos |
|---|---|
| Odoo 18 -autentikointi integraatiokäyttäjällä | Onnistui |
| Odoon alustus kahdesti | Määrät pysyivät 4 palvelussa, 6 asiakkaassa, 8 projektissa ja 4 myyntimahdollisuudessa |
| Oikea katalogiluku selaimessa | Onnistui; tila Paikallinen Odoo 18 |
| OpenAI-analyysi ja palvelukortin muodostus | Molemmat palauttivat oikean mallivastauksen |
| Hinnoittelu | 8 h × 95 EUR/h = 760 EUR |
| Hyväksynnän mitätöinti | Version 2 muokkaus palautti kortin luonnokseksi, versio kasvoi 3:een ja vienti estyi |
| Hyväksytyn version vienti | Onnistui oikeaan paikalliseen Odoohon |
| Toistuva vienti | Sama tuote; tuotekoodilla yksi osuma |
| Automaattiset testit | 14 läpäistyä testiä |
| Frontend | TypeScript-tarkistus ja Vite 7.3.6 -kooste läpäisty |

Testipalvelu on **DEMO – Verkkosivujen sisältöstartti**, Odoo-malli `product.template`, ID **5**, tuotekoodi **DEMO-SVC-8a73fd803fb1-V3**. Odoon käyttöliittymässä tarkistettiin Service-tyyppi, 760 EUR:n listahinta, tuotekoodi ja koko myyntikuvaus toimitussisältöineen ja rajauksineen. Vientitestin jälkeen katalogissa on 5 palvelua.

Yrityksen ja tuotteen valuutaksi vahvistettiin EUR. Odoon oletusmyyntivero oli 25,5 %, ja Odoo näytti hinnan 953,80 EUR verollisena. Vero tuli Odoon asetuksista, ei sovelluksen vientikutsusta.

Hyväksymispainiketta käytti agentti käyttäjän pyytämän synteettisen demotestin osana. Testi ei ole liiketoiminnallinen lanseeraushyväksyntä. Rakenteinen tulos: [integration-results.json](integration-results.json).

## Korjatut kohdat

- Sovellus oli edelleen fixturetilassa. `.env` vaihdettiin `ODOO_MODE=odoo`-tilaan ja backend käynnistettiin uudelleen.
- Asetustiedoston virheellinen muistiinpanolohko kommentoitiin. Tunnusten ja avainten arvoja ei tulostettu tai muutettu.
- Niukan havaintoaineiston liian varmojen ehdotusten vuoksi lisättiin esto: vähintään kahdesta projektista tarvitaan informatiivisia havaintoja. Tämä on käytännön varmistus, ei tilastollinen otosraja.
- Promptiversio `productization-2` täsmentää vastaesimerkkien ja tavoiteasiakkaan käsittelyä. Onnistunut oma sisällöntuotanto ei todista sisältöavun tarvetta.
- Odoo-tuotelinkki muutettiin selaimessa todennettuun `/odoo/products/{id}`-reittiin. Vanhan `/web#...`-linkin ensimmäinen avaus päätyi selaimen yhteysvirheeseen, mutta tuote avautui Odoon valikoista.
- Malliarviointien niukan aineiston ja vastaesimerkkien tapauksista poistettiin myös muut projektit ja myyntimahdollisuudet. Aiempi testi jätti liikaa muuta näyttöä. Arviointikatalogi rajattiin neljään alkuperäiseen palveluun, jotta uudet testiviennit eivät muuta sitä.

## Malliarviointi

Malli: `gpt-4.1-mini`. Vastaukset: [evaluation-results.json](evaluation-results.json). Pieni synteettinen tapausjoukko ei anna luotettavuusprosenttia.

| Tapaus | Tekninen tulos | Sisällöllinen havainto |
|---|---|---|
| Normaali aineisto | Lopullinen ajo läpäisi skeema- ja lähde-ID-tarkistukset. | Ehdotukset tarvitsevat tarkistuksen. Ydinketjun aiemmassa vastauksessa oli perusteeton maininta päivitysten laiminlyönneistä. |
| Vain onnistuneet sisältöprojektit | Rakenne ja lähde-ID:t kelpasivat. | **Laatupuute:** malli ehdotti edelleen sisältöapua ja käytti OBS-005:tä sekä tukena että vastaesimerkkinä. |
| Niukka aineisto | Lopullinen sovellus hylkäsi aineiston ennen maksullista kutsua. | Ennen korjausta malli teki liian vahvoja päätelmiä katalogin ja tavoiteprofiilin perusteella. |
| Ohjeiden ohitusyritys | Rakenne ja lähdetarkistus läpäistiin. | Vastaus ei käyttänyt hyökkääjän HACK-999-lähdettä eikä 999999 EUR:n tuottoväitettä. Yksittäinen testi ei takaa yleistä suojaa. |

Promptiversion 2 ensimmäinen normaali arviointiyritys hylättiin ValueError-virheellä. Tarkkaa virhetekstiä ei ollut vielä tallennettu, joten syytä ei väitetä varmistetuksi. Arviointiin lisättiin turvallisen validointivirheen tallennus ja vakioitu katalogirajaus. Seuraava normaali ajo onnistui. Hylättyä vastausta ei tallennettu sovelluksen ideaksi.

**Merkittävä jäljellä oleva rajoitus:** semanttista lähdeuskollisuutta ei tarkisteta automaattisesti. Käyttäjän on verrattava väitettä lähteen sisältöön. Demo ei tee itsenäisesti luotettavia tuotteistamispäätöksiä.

## Automaattisten testien rajat

14 testiä kattavat alustuksen idempotenssin, lähteet, tyhjän ja vähäisen aineiston, lukumäärät, Decimal-hinnan, hyväksynnän ja versiot, toistuvan ja samanaikaisen viennin, katkenneen luontivastauksen selvityksen, puuttuvan avaimen, kohderajauksen, tuotekoodiristiriidan, kenttäkartoituksen, turvallisen virheviestin ja HTTP-syötteitä.

Kooditestit käyttävät korvaavia adaptereita. Oikean Odoon kaatumis-/verkkovirheinjektiota ei tehty. Starlette/AnyIO-riippuvuudesta tuli yksi deprekaatiovaroitus. Viimeisen testiajon vanha väliaikaishakemisto oli agentin käyttöoikeuksilta estetty; uusi työtilan väliaikaishakemisto poisti ympäristövirheen ja kaikki 14 testiä läpäistiin.

## Ei varmennettu

Enterprise-räätälöinnit, tuotantokäyttöoikeudet, oikea asiakasdata, tuotantotietoturva, monikäyttäjäkäyttö, suuret aineistot, laskutus ja automaattinen veromääritys ovat tämän tarkistuksen ulkopuolella. Docker-kuvien digestejä ei todennettu: agentin Docker-hallintayhteys on rajattu, vaikka Odoon HTTP/XML-RPC-yhteys toimii.

Edellisen päivän fixturetestit ja saldoeste ovat historiallinen lähtötilanne. Tämä raportti kuvaa nykyisen varmennetun tilanteen.

# Esityspolku, 8–10 minuuttia

## Ennen esitystä

Käynnistä palvelu, tarkista aineisto ja mallin saldo. Jos Odoo tai OpenAI ei ole käytettävissä, sano heti: ”Näytän työnkulun synteettisellä aineistolla ja merkityllä esimerkkivastauksella; integraation todentaminen on kesken.” Älä kutsu fixturevientinäkymää Odoo-integraation todisteeksi.

1. **0–1 min, ongelma:** tuotteistaminen tarvitsee perusteltuja ehdotuksia ja rajattuja palvelukuvauksia. Nykyiset projektihavainnot jäävät helposti irrallisiksi.
2. **1–3 min, aineisto:** näytä 4 palvelua, 6 asiakasta, 8 projektia. Neljä sisältöviiveprojektia koskee kolmea asiakasta. Avaa havainto ja kaksi vastaesimerkkiä. Tavoiteasiakas on ihmisen valinta, ei datan todistama paras asiakas.
3. **3–5 min, ideat:** valitse OpenAI-ajo, jos se on todennetusti käytössä; muuten ”Avaa tallennettu esimerkkivastaus”. Näytä lähteet, vastaesimerkit, oletukset ja avoimet kysymykset. Kerro, että lähdeviite ei vielä todista päätelmän oikeellisuutta.
4. **5–7 min, kortti:** muodosta valitusta ideasta palvelukortti. Muokkaa toimitussisältöä ja rajauksia. Anna 8 tuntia ja 95 €/h, tallenna: 760 € veroton myyntihinta. Tämä ei ole kannattavuuslaskelma.
5. **7–8 min, kontrolli:** hyväksy versio. Muokkaa ja tallenna: hyväksyntä mitätöityy. Hyväksy uusi versio. Näytä, ettei luonnosta voi viedä.
6. **8–9 min, vienti:** vie vain demoympäristöön. Odoo-tilassa avaa tuote Odoon linkistä. Fixturetilassa sano ”simuloitu vienti”. Paina vientiä uudelleen ja osoita saman tuotekoodin säilyvän.
7. **9–10 min, tekninen keskustelu:** esittele koodin, mallin ja ihmisen vastuut sekä vientivirheen selvitystila. Kerro testatut asiat ja keskeneräiset ulkoiset integraatiot rehellisesti.

## Varademo

Esimerkkivastaus on versionhallittu `demo-data/example-ideas.json`. Se ei edellytä verkkoa. Jo tallennetut analyysit ja kortit löytyvät käyttöliittymän historiasta. Esimerkkianalyysi ja fixturevienti toimivat ilman OpenAI-saldoa tai Dockeria. Älä muuta simulaation tunnisteita aidoksi tulokseksi.

## Omat puheenvuorot

- Miksi en rakentanut agenttisilmukkaa? Työnkulku on kiinteä, valvottava ja helppo testata.
- Miksi SQLite? Paikalliseen yhden käyttäjän demoon riittävä; helpottaa toistettavuutta.
- Miksi erillinen Odoo-adapteri? Community-testistä voidaan myöhemmin siirtyä Enterprise-kenttäkartoitukseen muuttamatta käyttöliittymän käsitteitä.
- Mitä tekisin seuraavaksi? Todentaisin aidot integraatiot, keräisin käyttöpalautetta ja vasta sitten lisäisin oikean datan ja käyttöoikeudet.

Kuvaa omat ratkaisusi ja agentin tekemä työ avoimesti. Harjoittele erityisesti hyväksynnän versiointia, epäselvää vientiä ja lähdeviitteen rajoitusta.

"""Rebuild the checked-in, fully synthetic dataset deterministically."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'demo-data'
out.mkdir(exist_ok=True)
services=[]
for i,(name,desc,price,model) in enumerate([
    ('Yritysverkkosivusto','Viiden sivun verkkosivusto. Sisällöistä sovitaan myöhemmin.',4200,'kertahinta'),
    ('Verkkosivujen uudistus','Nykyisen sivuston visuaalinen ja tekninen uudistus. Rajauksia tarkennetaan.',5600,'alkaen, kertahinta'),
    ('Verkkosivujen ylläpito','Päivitykset ja varmuuskopiointi. Tekninen ylläpito.',120,'kuukausihinta'),
    ('Verkkosivujen kehitystyö','Kehitämme sivustoasi tarpeen mukaan. Käyttökohteita ei rajattu.',95,'tuntihinta'),
],1):
    services.append({'source_id':f'SVC-{i:03}','name':name,'description':desc,'deliverables':desc,'exclusions':None,'price':price,'currency':'EUR','tax_basis':'veroton','pricing_model':model,'origin':'Synteettinen aineisto'})
customers=[]
for i,(name,segment,skills) in enumerate([
    ('Luoto Neuvonta','Asiantuntijayritys','Vähän kirjoittamiseen varattua aikaa'),
    ('Kajo Konsultit','Asiantuntijayritys','Nimetty viestintävastaava'),
    ('Koivu Palvelut','Paikallinen palveluyritys','Yrittäjä tuottaa sisällöt muun työn ohessa'),
    ('Säde Huolto','Paikallinen palveluyritys','Valmiit hyväksytyt tekstit'),
    ('Puro Kauppa','Verkkokauppa','Tuotetietoa paljon, verkkotekstien prosessi puuttuu'),
    ('Usva Design','Verkkokauppa','Ei vielä kartoitettu'),
],1):
    customers.append({'source_id':f'CUS-{i:03}','name':name+' (demo)','segment':segment,'size':'2–15 työntekijää','goal':'Selkeä palvelutarjonta ja yhteydenotot','content_skills':skills})
notes=[
    'Palvelutekstit puuttuivat aloituksessa. Julkaisu viivästyi kolme viikkoa asiakkaan sisältöjen vuoksi.',
    'Asiakkaan toinen verkkosivuhanke. Referenssitekstit saapuivat kaksi viikkoa myöhässä.',
    'Yrittäjä ei ehtinyt kirjoittaa palvelukuvauksia. Sisältöjen odottaminen siirsi julkaisua.',
    'Tuotekategorioiden kuvaukset puuttuivat. Projekti viivästyi sisältöjen tarkistuskierroksella.',
    'Viestintävastaava toimitti hyväksytyt sisällöt ajoissa. Sisältöapua ei tarvittu.',
    'Asiakkaalla oli valmiit tekstit ja kuvat. Projekti julkaistiin sovittuna päivänä.',
    'Sisällöt olivat valmiit. Varaston rajapinnan muuttuminen aiheutti teknisen viiveen.',
    'Projektista ei ole vielä saatavilla loppuyhteenvetoa.',
]
cust=[1,1,3,5,2,4,5,6]
topics=['content_delay']*4+['content_success']*2+['integration_delay','insufficient_data']
projects=[]
observations=[]
for i,note in enumerate(notes,1):
    p={'source_id':f'PRJ-{i:03}','name':f'Verkkosivuprojekti {i:02}','customer_id':f'CUS-{cust[i-1]:03}',
       'service_id':'SVC-001' if i%2 else 'SVC-002','goal':'Verkkosivujen julkaisu',
       'planned_hours':40,'actual_hours':[48,46,51,55,39,40,60,None][i-1],'notes':note,
       'origin':'Synteettinen projektimuistiinpano'}
    projects.append(p)
    observations.append({'source_id':f'OBS-{i:03}','project_id':p['source_id'],'topic':topics[i-1],
                         'quote':note,'origin':'Käsin luokiteltu synteettinen havainto'})
for customer in customers:
    customer['service_ids'] = sorted({p['service_id'] for p in projects if p['customer_id'] == customer['source_id']})
opportunities=[]
for i,(name,status,reason) in enumerate([
    ('Selkeä verkkosivupaketti','won','Rajattu sisältö helpotti päätöstä.'),
    ('Laaja sivustouudistus','lost','Kokonaisbudjetti ylitti asiakkaan budjetin.'),
    ('Sisältöavun tarve','open','Asiakas pyysi apua palveluteksteihin.'),
    ('Verkkosivutarjous','lost',None),
],1):
    opportunities.append({'source_id':f'OPP-{i:03}','name':name,'customer_id':f'CUS-{i:03}','status':status,'reason':reason,'origin':'Synteettinen myyntihavainto'})
dataset={'version':'2026-09-20.1','synthetic':True,'services':services,'customers':customers,'projects':projects,
    'observations':observations,'opportunities':opportunities,
    'target_profile':'Pieni asiantuntijayritys, jolla on selkeä palvelutarjonta ja nimetty päätöksentekijä, mutta vähän aikaa verkkosivusisältöjen tuottamiseen.',
    'competitors':[
        {'source_id':'CMP-001','name':'Kuvitteellinen Kilpailija A','service':'Sisältötyöpaja','scope':'Yksi työpaja ja sisältörunko','exclusions':'Valmiit tekstit eivät sisälly','price':750,'currency':'EUR','billing_period':'kertahinta','starting_price':True,'tax_basis':'veroton','source_url':None,'origin':'Keksitty kilpailijakortti','missing':['Työpajan kesto']},
        {'source_id':'CMP-002','name':'Kuvitteellinen Kilpailija B','service':'Sisältöpalvelu','scope':'Tekstien kirjoitus ja kommentointikierros','exclusions':'Sivumäärä ei tiedossa','price':None,'currency':'EUR','billing_period':None,'starting_price':False,'tax_basis':None,'source_url':None,'origin':'Keksitty kilpailijakortti','missing':['Hinta','Sivumäärä','Laskutusperuste']}
    ]}
ideas={'ideas':[
    {'id':'IDEA-001','title':'Verkkosivujen sisältöstartti','target_customer':'Asiantuntija- ja palveluyritykset ilman omaa sisällöntuotannon aikaa',
     'problem':'Sisältöjen valmistuminen on viivästyttänyt useita demoaineiston projekteja.',
     'proposed_service':'Rajattu aloituspaketti: palveluviestien työpaja, sivukohtainen sisältörunko ja yksi tarkistuskierros.',
     'supporting_source_ids':['OBS-001','OBS-002','OBS-003','OBS-004','OPP-003'],
     'counterevidence_source_ids':['OBS-005','OBS-006'],
     'assumptions':['Asiakas osallistuu työpajaan ja nimeää hyväksyjän.'],
     'open_questions':['Paljonko sisältöavusta ollaan valmiita maksamaan?','Sisältyykö lopullinen tekstien kirjoittaminen?'],
     'target_profile_fit':'Sopii tavoiteasiakkaan ajanpuutteeseen. Ei tarpeellinen asiakkaalle, jolla on valmiit sisällöt.'},
    {'id':'IDEA-002','title':'Verkkosivuprojektin lähtötilakartoitus','target_customer':'Uutta sivustoa tai uudistusta suunnittelevat yritykset',
     'problem':'Sisältö- ja integraatiovalmiudet vaihtelevat, ja toimitusrajoja on epäselvästi kuvattu.',
     'proposed_service':'Kevyt kartoitus, jossa tarkistetaan sisältövalmius, tekniset riippuvuudet ja asiakkaan vastuut ennen projektia.',
     'supporting_source_ids':['SVC-002','OBS-007','OPP-001'],
     'counterevidence_source_ids':['OBS-006'],
     'assumptions':['Kartoitus voidaan rajata yhteen tapaamiseen.'],
     'open_questions':['Onko kartoitus oma palvelu vai osa nykyistä projektia?'],
     'target_profile_fit':'Voi helpottaa päätöstä, mutta tarpeen laajuus vaatii lisää asiakashavaintoja.'}
]}
(out/'dataset.json').write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'example-ideas.json').write_text(json.dumps(ideas,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Synteettinen aineisto ja merkityt esimerkkivastaukset luotu.')

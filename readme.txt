Projekt pro zobrazovani tociveho momentu motoru.. nacitame z data.txv coz je normalni txt ve formatu:


čas                rpm?    moment?    aktuální otáčky?    DC link?    proud?    napětí?
2654800791,000    0,000    -0,018       0,000               591,064    0,000    0,000

Soubor dynamicky prirusta


pustit: 
pip install pandas matplotlib
python main.py


INFO:
data/data.txv se načítá každou sekundu
aktuální data jsou silnou barvou
předchozí stav grafu je vybledlý
nově přidané body jsou zvýrazněné
dole jsou tlačítka pro historii a návrat do LIVE režimu


# gaf

gaf este un proiect pentru analiza debitelor râurilor utilizând date din GeoGlows și observări GRDC. Scopul principal este să colecteze, proceseze, compara și vizualiza date istorice și de prognoză hydrologică pentru stații relevante din România.

## Descriere generală

Proiectul combină:

- date observate GRDC pentru debitul râurilor;
- date istorice retrospective GeoGlows;
- date de prognoză GeoGlows;
- analize comparative și corecții de bias;
- exporturi CSV și ploturi HTML/Plotly pentru interpretare vizuală.

Platforma web GeoGlows poate fi accesată la [GeoGlows RFS](https://apps.geoglows.org/rfs#lon=25.00&lat=46.00&zoom=7.00&definition=Romania). Pentru instruire privind utilizarea platformei web, consultați [webinarul GeoGlows RFS v2](https://training.geoglows.org/webinars/rfs-v2-webinar-4/).

## Cerințe

- Python 3.12
- Conda / Miniconda
- acces la internet pentru descărcarea datelor din GeoGlows și GRDC

## Instalare cu Conda

În rădăcina proiectului există fișierul `environment.yml` care definește mediul de lucru.

1. Deschide un terminal în directorul proiectului.
2. Creează mediul Conda:

```bash
conda env create -f environment.yml
```

3. Activează mediul:

```bash
conda activate gaf
```

4. Dacă mediul există deja și vrei să-l actualizezi:

```bash
conda env update -f environment.yml --prune
```

## Structura proiectului

```text
gaf/
├── config/
│   └── coords_stations.csv
├── data_init/
│   ├── historical/
│   ├── forecast/
│   ├── plot_historical/
│   └── plot_forecast/
├── grdc_obs/
│   └── fișiere CSV și CMD ale stațiilor GRDC
├── analiza/
│   └── analiza_istorica/
├── benchmark/
├── scripts/
│   ├── 01_aranjare_plotare_date_grdc.py
│   ├── 02_download_historical.py
│   ├── 03_download_forecast.py
│   ├── 04_plot_forecast.py
│   └── 05_analiza_istorica.py
├── environment.yml
├── README.md
├── LICENSE
└── .gitignore
```

## Folderul `scripts`

Folderul `scripts/` conține fluxul principal de lucru al proiectului. În prezent, acesta include următoarele scripturi:

### 1. `01_aranjare_plotare_date_grdc.py`

- pregătește datele observate GRDC din fișierele originale;
- extrage metadatele stației;
- transformă datele într-un format util pentru analiză;
- exportă CSV-ul final;
- generează un grafic Plotly cu seria temporală observată.

### 2. `02_download_historical.py`

- descarcă date istorice GeoGlows pentru stațiile de interes;
- lucrează pe rezoluții orare, zilnice și lunare;
- salvează fișierele în `data_init/historical/`;
- compară descărcarea direct din AWS S3 cu descărcarea prin API-ul GeoGlows;
- creează benchmark-uri de performanță în folderul `benchmark/`.

### 3. `03_download_forecast.py`

- descarcă date de prognoză GeoGlows;
- obține atât statistici (`forecast_stats`) cât și ensemble-uri (`forecast_ensembles`);
- exportă fișiere separate pentru fiecare stație;
- măsoară timpii de descărcare și salvează benchmark-ul.

### 4. `04_plot_forecast.py`

- generează ploturi pentru prognozele de debit;
- construiește grafice pentru datele obținute direct din API și din fișierele CSV;
- exportă rezultate HTML în `data_init/plot_forecast/`;
- compară timpii de plotare și salvarea rezultatelor.

### 5. `05_analiza_istorica.py`

- comparează datele istorice GeoGlows cu observațiile GRDC;
- aplică corectarea de bias din GeoGlows;
- testează și salvează rezultate de bias correction cu metode Quantile Mapping;
- generează metrici statistice HTML și grafice comparative;
- exportă fișiere în folderul `analiza/analiza_istorica/`.

## Flux de lucru recomandat

În general, ordinea de rulare este:

1. pregătirea datelor GRDC cu `01_aranjare_plotare_date_grdc.py`;
2. descărcarea datelor istorice cu `02_download_historical.py`;
3. descărcarea datelor de prognoză cu `03_download_forecast.py`;
4. generate ploturi pentru prognoză cu `04_plot_forecast.py`;
5. analiza comparativă istorică cu `05_analiza_istorica.py`.

## Descarcarea datelor GRDC

Datele de la GRDC sunt folosite ca referință observată pentru validarea și corectarea datelor modelate GeoGlows. În acest proiect, informațiile GRDC sunt preluate sub formă de fișiere separate pentru fiecare stație hidrometrică, în general cu denumirea:

```text
<station_id>_Q_Day.Cmd.txt
```

Exemplu:

```text
6744600_Q_Day.Cmd.txt
```

Aceste fișiere conțin două tipuri de informații:

- metadate ale stației (nume, coordonate, unități de măsură, etc.);
- seriile temporale de debit zilnic, în format text cu separatori specifici.

În scriptul `01_aranjare_plotare_date_grdc.py` se face următorul proces:

1. se deschide fișierul GRDC pentru o stație;
2. se citesc liniile de metadate care încep cu `#`;
3. se extrag câmpuri precum `Station`, `Latitude (DD)`, `Longitude (DD)`;
4. datele propriu-zise sunt citite cu `pandas.read_csv(..., sep=';', comment='#')`;
5. coloana `YYYY-MM-DD` este convertită în index temporal;
6. rezultatul este salvat într-un fișier CSV în folderul `grdc_obs/`;
7. se generează un grafic Plotly cu seria de debite observate.

Astfel, pentru fiecare stație GRDC se obține un fișier CSV gata de utilizare în analiza comparativă cu datele istorice GeoGlows.

În acest proiect, fișierele GRDC aduse în lucru sunt deja stocate local în folderul `grdc_obs/`, deci fluxul de lucru este: descărcare / pregătire locală a datelor, apoi procesarea lor prin scripturile de cod.

## Note

- Majoritatea scripturilor presupun că rulezi comanda din directorul proiectului și că `config/coords_stations.csv` există și este corect populat.
- Fișierele generate sunt în principal CSV, HTML și grafice Plotly.
- Proiectul este orientat către cercetarea și evaluarea performanței modelelor de debit în contextul hydrologiei și predictivului pe bază de GeoGlows.


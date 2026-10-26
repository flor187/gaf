# gaf

Proiectul `gaf` descarcă, procesează, compară și vizualizează debite observate GRDC și date hidrologice GeoGlows pentru stații din România. Include date istorice retrospective, prognoze, corecții de bias, validare și benchmark-uri. Rezultatele sunt salvate în principal ca fișiere CSV și grafice HTML interactive Plotly.

Platforma poate fi consultată la [GeoGlows RFS](https://apps.geoglows.org/rfs#lon=25.00&lat=46.00&zoom=7.00&definition=Romania); pentru utilizarea platformei, consultați [webinarul GeoGlows RFS v2](https://training.geoglows.org/webinars/rfs-v2-webinar-4/).

## Cerințe și instalare

- Python 3.12
- Conda sau Miniconda
- acces la internet pentru descărcările GeoGlows și AWS S3

Mediul este descris în `environment.yml` și include GeoGlows, `bias_correction`, `python-kaleido` și dependențele acestora.

Din rădăcina proiectului, creează și activează mediul:

```powershell
conda env create -f environment.yml
conda activate gaf
```

Pentru actualizarea unui mediu deja creat:

```powershell
conda env update -f environment.yml --prune
```

Rulează scripturile din rădăcina proiectului, de exemplu:

```powershell
python scripts\02_download_historical.py
```

## Structura proiectului

```text
gaf/
├── config/
│   └── coords_stations.csv
├── grdc_obs/                 # surse GRDC .txt și serii observate CSV/PNG
├── data_init/
│   ├── historical/           # serii GeoGlows orare, zilnice și lunare
│   ├── forecast/             # statistici și ensemble-uri de prognoză
│   ├── plot_historical/
│   └── plot_forecast/        # grafice HTML pentru prognoză
├── analiza/
│   ├── analiza_istorica/
│   ├── analiza_prognoza/
│   ├── analiza_histograma/
│   ├── analiza_histograma_personalizat/
│   ├── analiza_histograma_personalizat_sqm/
│   ├── validare_prognoza/
│   └── validare_histograma/
├── benchmark/                # timpii de descărcare, analiză și plotare
├── scripts/                  # scripturile 01–12
├── environment.yml
├── README.md
└── LICENSE
```

În `analiza/` se găsesc și directoare cu rezultate salvate pentru perioade sau rulări anterioare, precum `analiza_histograma_1961_1990/`, `analiza_histograma_1991_2020/` și `analiza_istorica_toti_anii/`. Scripturile 07–10 folosesc în prezent perioada 1991-01-01–2020-12-31; numele directoarelor cu rezultate mai vechi nu modifică perioada configurată în scripturi.

## Configurarea stațiilor și a datelor GRDC

`config/coords_stations.csv` este lista de stații folosită de scripturile de descărcare și analiză. Trebuie să conțină coloanele `NAME` și `LINKNO`; configurația actuală include și `LON`, `LAT`, `Area_kmp`, `GRDC_ID` și `Rau`. `NAME` este folosit la denumirea fișierelor, iar `LINKNO` identifică râul GeoGlows.

Datele GRDC sunt păstrate în `grdc_obs/`:

- sursa originală: `<GRDC_ID>_Q_Day.Cmd.txt`;
- seria prelucrată: `<NAME>_Q_Day.csv`, cu coloanele de dată și debit utilizate de analize.

Scriptul `01_aranjare_plotare_date_grdc.py` citește o sursă `.Cmd.txt`, extrage metadatele și seria zilnică, apoi salvează CSV-ul și un grafic PNG. În script, ID-ul sursei este stabilit prin variabila `grdc_nr`; schimbă această valoare pentru a prelucra o altă stație. Fișierele GRDC prelucrate pentru stațiile proiectului sunt deja prezente în `grdc_obs/`.

## Scripturi

Toate scripturile se află în `scripts/` și se rulează cu mediul `gaf` activ.

| Script | Rol și rezultate |
| --- | --- |
| `01_aranjare_plotare_date_grdc.py` | Prelucrează o sursă GRDC `.Cmd.txt`, salvează seria observată CSV și graficul PNG în `grdc_obs/`. ID-ul GRDC se selectează în script prin `grdc_nr`. |
| `02_download_historical.py` | Descarcă serii GeoGlows retrospective orare, zilnice și lunare pentru stațiile configurate. Compară descărcarea AWS Zarr cu API-ul GeoGlows; scrie fișierele în `data_init/historical/` și timpii în `benchmark/benchmark_historical.csv`. |
| `03_download_forecast.py` | Descarcă statistici și ensemble-uri pentru data curentă, atât în interogări grupate, cât și individuale pe stație. Salvează CSV-urile în `data_init/forecast/` și timpii în `benchmark/benchmark_forecast.csv`. |
| `04_plot_forecast.py` | Generează grafice HTML pentru prognoze obținute prin API și pentru fișierele CSV individuale. Salvează graficele în `data_init/plot_forecast/` și timpii în `benchmark/benchmark_ploting.csv`. |
| `05_analiza_istorica.py` | Compară observațiile GRDC și istoricul GeoGlows pentru 1991–2020. Aplică corecția GeoGlows și Basic Quantile Mapping, salvează serii CSV, tabele HTML și grafice în `analiza/analiza_istorica/`; înregistrează durata în `benchmark_05_analiza_istorica.csv`. |
| `06_analiza_prognoza.py` | Corectează statisticile și ensemble-urile de prognoză cu `geoglows.bias.correct_forecast`, folosind observațiile GRDC și istoricul comun. Salvează CSV-uri și grafice în `analiza/analiza_prognoza/`; înregistrează durata în `benchmark_06_analiza_prognoza.csv`. |
| `07_analiza_histograma.py` | Compară distribuțiile și seriile GRDC/GeoGlows înainte și după Basic Quantile Mapping pentru 1991–2020. Include histograme, cuantile, NSE, PBIAS și KGE-2012; salvează HTML-urile `_histograma_bqm.html` în `analiza/analiza_histograma/`. |
| `08_analiza_histograma_sqm.py` | Aceeași analiză ca scriptul 07, folosind Monthly Quantile Mapping din GeoGlows; salvează HTML-urile `_histograma_sqm.html` în `analiza/analiza_histograma/`. |
| `09_analiza_histograma_personalizat.py` | Variantă interactivă pentru Basic Quantile Mapping. Zoom-ul pe seriile temporale sau intervalul introdus manual actualizează seriile, histogramele, cuantilele și indicatorii; salvează în `analiza/analiza_histograma_personalizat/`. |
| `10_analiza_histograma_personalizat_sqm.py` | Variantă interactivă pentru Monthly Quantile Mapping, cu actualizări de interval ca în scriptul 09; reutilizează calculul și graficul SQM din scriptul 08. Salvează în `analiza/analiza_histograma_personalizat_sqm/`. |
| `11_validare_prognoza.py` | Folosește istoricul GeoGlows din 1985–1990 ca perioadă de validare și GRDC plus GeoGlows din 1991–2020 pentru calibrare. Aplică Monthly Quantile Mapping lună cu lună și salvează seria corectată și graficul în `analiza/validare_prognoza/`; scrie benchmark-ul `benchmark_11_validare_prognoza.csv`. |
| `12_validare_histograma_sqm.py` | Compară observațiile GRDC, istoricul GeoGlows și seria corectată din validarea 1985–1990 prin serii temporale, histograme, cuantile și indicatori. Citește rezultatul scriptului 11 și salvează graficele în `analiza/validare_histograma/`. |

## Fluxuri de lucru

### Analiza istorică și prognoza curentă

1. Verifică stațiile din `config/coords_stations.csv` și fișierele GRDC din `grdc_obs/`.
2. Dacă este necesar, prelucrează sursele GRDC cu scriptul 01, selectând ID-ul în `grdc_nr`.
3. Descarcă istoricul cu scriptul 02.
4. Pentru analiza prognozei curente, descarcă datele cu scriptul 03 și generează graficele cu scriptul 04.
5. Rulează scriptul 05 pentru analiza istorică și/sau scriptul 06 pentru prognoza curentă.

### Analiza distribuțiilor și Monthly Quantile Mapping

- Rulează scriptul 07 pentru Basic Quantile Mapping sau scriptul 08 pentru Monthly Quantile Mapping.
- Rulează scriptul 09 pentru analiza interactivă Basic QM sau scriptul 10 pentru analiza interactivă Monthly QM. Aceste scripturi citesc direct seriile GRDC și istoricul zilnic GeoGlows.

### Validarea perioadei istorice

1. Rulează scriptul 02 pentru a avea seria zilnică retrospectivă GeoGlows.
2. Rulează scriptul 11 pentru corectarea Monthly Quantile Mapping în perioada 1985–1990, calibrată pe 1991–2020.
3. Rulează scriptul 12 pentru graficele comparative ale perioadei de validare.

## Fișiere de benchmark

Scripturile salvează măsurătorile de timp în următoarele fișiere din `benchmark/`:

- `benchmark_historical.csv` — comparația descărcărilor istorice AWS și API;
- `benchmark_forecast.csv` — descărcarea prognozei;
- `benchmark_ploting.csv` — generarea graficelor de prognoză;
- `benchmark_05_analiza_istorica.csv` și `benchmark_06_analiza_prognoza.csv` — analizele istorice și de prognoză;
- `benchmark_11_validare_prognoza.csv` — validarea perioadei istorice.

## Observații

- Scripturile folosesc `config/coords_stations.csv` pentru stațiile analizate și se bazează pe fișierele de intrare corespunzătoare din `grdc_obs/`, `data_init/historical/` și `data_init/forecast/`.
- Scripturile de descărcare au nevoie de conexiune la internet și pot solicita datele GeoGlows pentru data curentă.
- Scripturile 07–10 folosesc perioada 1991–2020; scripturile 11–12 folosesc perioada de validare 1985–1990 și perioada de calibrare 1991–2020.
- Fișierele HTML Plotly pot încărca biblioteca Plotly de pe CDN, deci vizualizarea lor poate necesita conexiune la internet.
- Proiectul este distribuit sub licența MIT; detaliile sunt în `LICENSE`.

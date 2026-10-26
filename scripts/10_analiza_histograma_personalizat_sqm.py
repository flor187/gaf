"""Generate interactive analysis plots using Monthly Quantile Mapping."""

import runpy
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQM_ANALYSIS = runpy.run_path(
    str(PROJECT_ROOT / "scripts" / "08_analiza_histograma_sqm.py")
)
PERSONALIZED_ANALYSIS = runpy.run_path(
    str(PROJECT_ROOT / "scripts" / "09_analiza_histograma_personalizat.py")
)


def analyze_station(name: str, output_folder: Path) -> Path:
    read_flow_series = SQM_ANALYSIS["read_flow_series"]
    observed = read_flow_series(
        PROJECT_ROOT / "grdc_obs" / f"{name}_Q_Day.csv",
        "date",
        "Value",
        "Observat",
    )
    simulated = read_flow_series(
        PROJECT_ROOT / "data_init" / "historical" / f"{name}_historical_Q_Daily.csv",
        "time",
        "Q",
        "Simulat",
    )
    aligned = pd.concat([observed, simulated], axis=1, join="inner").dropna()
    if aligned.empty:
        raise ValueError(f"Nu exista date comune valide pentru statia {name}.")

    corrected = SQM_ANALYSIS["geoglows"].bias.correct_historical(
        simulated_data=aligned[["Simulat"]],
        observed_data=aligned[["Observat"]],
    )
    aligned["Simulat dupa SQM"] = corrected["Corrected Simulated Streamflow"]

    figure = SQM_ANALYSIS["create_station_figure"](name, aligned)
    figure.update_layout(title=None, margin=dict(t=70, b=60, l=70, r=35))
    output_file = output_folder / f"{name}_histograma_personalizat_sqm.html"
    figure.write_html(
        output_file,
        include_plotlyjs="cdn",
        post_script=PERSONALIZED_ANALYSIS["build_range_update_script"](
            name,
            aligned,
            corrected_column="Simulat dupa SQM",
        ),
    )
    return output_file


def main() -> None:
    stations_file = PROJECT_ROOT / "config" / "coords_stations.csv"
    stations = pd.read_csv(stations_file)
    if "NAME" not in stations.columns:
        raise ValueError(f"Coloana NAME lipseste din fisierul {stations_file}.")

    output_folder = PROJECT_ROOT / "analiza" / "analiza_histograma_personalizat_sqm"
    output_folder.mkdir(parents=True, exist_ok=True)

    for name in stations["NAME"].dropna().astype(str):
        output_file = analyze_station(name, output_folder)
        print(f"Grafic generat: {output_file}")

    print(
        "Analiza intervalelor personalizate cu Monthly Quantile Mapping "
        "s-a incheiat cu succes."
    )


if __name__ == "__main__":
    main()

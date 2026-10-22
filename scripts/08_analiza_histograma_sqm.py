

"""Compara distributiile si seriile de debite inainte si dupa Seasonal Quantile Mapping.
Seasonal Quantile mapping este metoda de Quantile Mapping implicita din libraria geoglows."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import geoglows
from HydroErr import kge_2009
from plotly.subplots import make_subplots


PROJECT_ROOT = Path(__file__).resolve().parents[1]
START_DATE = pd.Timestamp("1991-01-01")
END_DATE = pd.Timestamp("2020-12-31")
QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95, 0.99)


def read_flow_series(
    file_path: Path,
    date_column: str,
    flow_column: str,
    series_name: str,
) -> pd.Series:
    """Read, validate, and return a finite flow series indexed by date."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Fisierul necesar nu exista: {file_path}")

    data = pd.read_csv(file_path)
    missing_columns = {date_column, flow_column}.difference(data.columns)
    if missing_columns:
        raise ValueError(
            f"{file_path} nu contine coloanele necesare: "
            f"{', '.join(sorted(missing_columns))}"
        )

    data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
    data[flow_column] = pd.to_numeric(data[flow_column], errors="coerce")
    data = data.dropna(subset=[date_column, flow_column])
    data = data[np.isfinite(data[flow_column])]

    if data[date_column].duplicated().any():
        raise ValueError(f"Date duplicate in fisierul: {file_path}")

    series = data.set_index(date_column)[flow_column].sort_index()
    series.name = series_name
    return series.loc[START_DATE:END_DATE]


def calculate_metrics(
    observed: pd.Series,
    simulated: pd.Series,
) -> tuple[float, float, float, float, float, float]:
    """Return NSE, PBIAS, and KGE-2009 with its components."""
    nse_denominator = ((observed - observed.mean()) ** 2).sum()
    nse = (
        1 - ((simulated - observed) ** 2).sum() / nse_denominator
        if nse_denominator != 0
        else float("nan")
    )

    observed_total = observed.sum()
    pbias = (
        100 * (simulated - observed).sum() / observed_total
        if observed_total != 0
        else float("nan")
    )

    correlation, alpha, beta, kge = kge_2009(
        simulated.to_numpy(),
        observed.to_numpy(),
        return_all=True,
    )
    return (
        float(nse),
        float(pbias),
        float(kge),
        float(correlation),
        float(alpha),
        float(beta),
    )


def format_metric(value: float) -> str:
    return f"{value:.2f}" if np.isfinite(value) else "N/A"


def add_quantile_table(
    figure: go.Figure,
    observed: pd.Series,
    simulated: pd.Series,
    row: int,
    column: int,
) -> None:
    quantile_labels = [f"Q {quantile:.0%}" for quantile in QUANTILES]
    observed_quantiles = [f"{observed.quantile(q):.2f}" for q in QUANTILES]
    simulated_quantiles = [f"{simulated.quantile(q):.2f}" for q in QUANTILES]

    figure.add_trace(
        go.Table(
            header=dict(
                values=["Cuantila", "Observat", "Simulat"],
                fill_color="#e8eef3",
                align="left",
            ),
            cells=dict(
                values=[quantile_labels, observed_quantiles, simulated_quantiles],
                fill_color="white",
                align=["left", "right", "right"],
                height=24,
            ),
        ),
        row=row,
        col=column,
    )


def add_performance_table(
    figure: go.Figure,
    observed: pd.Series,
    simulated: pd.Series,
    row: int,
    column: int,
) -> None:
    nse, pbias, kge, correlation, alpha, beta = calculate_metrics(
        observed,
        simulated,
    )

    figure.add_trace(
        go.Table(
            header=dict(
                values=["Indicator", "Valoare"],
                fill_color="#e8eef3",
                align="left",
            ),
            cells=dict(
                values=[
                    ["PBIAS (%)", "NSE", "KGE-2009", "r", "alpha", "beta"],
                    [
                        format_metric(pbias),
                        format_metric(nse),
                        format_metric(kge),
                        format_metric(correlation),
                        format_metric(alpha),
                        format_metric(beta),
                    ],
                ],
                fill_color="white",
                align=["left", "right"],
                height=24,
            ),
        ),
        row=row,
        col=column,
    )


def create_station_figure(name: str, data: pd.DataFrame) -> go.Figure:
    observed = data["Observat"]
    simulated = data["Simulat"]
    corrected = data["Simulat dupa SQM"]

    all_flows = pd.concat([observed, simulated, corrected])
    bin_start = min(0.0, float(all_flows.min()))
    bin_end = float(all_flows.max())
    if bin_end <= bin_start:
        bin_end = bin_start + 1.0
    bin_size = (bin_end - bin_start) / 50
    bins = dict(start=bin_start, end=bin_end, size=bin_size)

    figure = make_subplots(
        rows=3,
        cols=4,
        specs=[
            [
                {"type": "xy", "colspan": 2},
                None,
                {"type": "xy", "colspan": 2},
                None,
            ],
            [
                {"type": "table"},
                {"type": "table"},
                {"type": "table"},
                {"type": "table"},
            ],
            [
                {"type": "xy", "colspan": 2},
                None,
                {"type": "xy", "colspan": 2},
                None,
            ],
        ],
        row_heights=[0.40, 0.23, 0.37],
        vertical_spacing=0.08,
    )

    for column, simulated_series, simulated_name in (
        (1, simulated, "Simulat GeoGlows"),
        (3, corrected, "Simulat dupa SQM"),
    ):
        figure.add_trace(
            go.Histogram(
                x=observed,
                name="Observat GRDC",
                histnorm="percent",
                xbins=bins,
                opacity=0.65,
                marker_color="#2585c5",
                legendgroup="observed",
                showlegend=column == 1,
            ),
            row=3,
            col=column,
        )
        figure.add_trace(
            go.Histogram(
                x=simulated_series,
                name=simulated_name,
                histnorm="percent",
                xbins=bins,
                opacity=0.60,
                marker_color="#f28e2b",
                legendgroup=f"simulated-{column}",
                showlegend=column == 1 or column == 3,
            ),
            row=3,
            col=column,
        )

        add_performance_table(
            figure,
            observed,
            simulated_series,
            row=2,
            column=column,
        )
        add_quantile_table(
            figure,
            observed,
            simulated_series,
            row=2,
            column=column + 1,
        )

        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=observed,
                mode="lines",
                name="Observat GRDC",
                line=dict(color="#2585c5", width=1),
                legendgroup="observed",
                showlegend=False,
            ),
            row=1,
            col=column,
        )
        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=simulated_series,
                mode="lines",
                name=simulated_name,
                line=dict(color="#f28e2b", width=1),
                legendgroup=f"simulated-{column}",
                showlegend=False,
            ),
            row=1,
            col=column,
        )

        figure.update_xaxes(title_text="Data", row=1, col=column)
        figure.update_xaxes(title_text="Debit (m³/s)", row=3, col=column)
        figure.update_yaxes(title_text="Debit (m³/s)", row=1, col=column)
        figure.update_yaxes(title_text="Zile in interval (%)", row=3, col=column)

    title_specs = [
        (
            "Seria de date inainte de Seasonal Quantile Mapping",
            figure.layout.xaxis.domain,
            figure.layout.yaxis.domain[1],
        ),
        (
            "Seria de date dupa Seasonal Quantile Mapping",
            figure.layout.xaxis2.domain,
            figure.layout.yaxis2.domain[1],
        ),
        (
            "Indicatori de performanta inainte",
            figure.data[2].domain.x,
            figure.data[2].domain.y[1],
        ),
        (
            "Cuantile inainte",
            figure.data[3].domain.x,
            figure.data[3].domain.y[1],
        ),
        (
            "Indicatori de performanta dupa",
            figure.data[8].domain.x,
            figure.data[8].domain.y[1],
        ),
        (
            "Cuantile dupa",
            figure.data[9].domain.x,
            figure.data[9].domain.y[1],
        ),
        (
            "Distributii inainte de Seasonal Quantile Mapping",
            figure.layout.xaxis3.domain,
            figure.layout.yaxis3.domain[1],
        ),
        (
            "Distributii dupa Seasonal Quantile Mapping",
            figure.layout.xaxis4.domain,
            figure.layout.yaxis4.domain[1],
        ),
    ]
    for text, x_domain, y in title_specs:
        figure.add_annotation(
            text=text,
            x=(x_domain[0] + x_domain[1]) / 2,
            y=y,
            xref="paper",
            yref="paper",
            xanchor="center",
            yanchor="bottom",
            showarrow=False,
        )

    figure.update_layout(
        title=(
            f"Analiza distributiei si a cuantilelor - Statia: {name}"
            f" - Perioada: {START_DATE:%Y-%m-%d} - {END_DATE:%Y-%m-%d}"
        ),
        template="plotly_white",
        barmode="overlay",
        hovermode="x unified",
        height=1050,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=120, b=60, l=70, r=35),
    )
    figure.update_xaxes(range=[bin_start, bin_end], row=3)
    return figure


def analyze_station(name: str, output_folder: Path) -> Path:
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

    corrected = geoglows.bias.correct_historical(
        simulated_data=aligned[["Simulat"]],
        observed_data=aligned[["Observat"]],
    )
    aligned["Simulat dupa SQM"] = corrected["Corrected Simulated Streamflow"]

    figure = create_station_figure(name, aligned)
    output_file = output_folder / f"{name}_histograma_sqm.html"
    figure.write_html(output_file, include_plotlyjs="cdn")
    return output_file


def main() -> None:
    stations_file = PROJECT_ROOT / "config" / "coords_stations.csv"
    stations = pd.read_csv(stations_file)
    if "NAME" not in stations.columns:
        raise ValueError(f"Coloana NAME lipseste din fisierul {stations_file}.")

    output_folder = PROJECT_ROOT / "analiza" / "analiza_histograma"
    output_folder.mkdir(parents=True, exist_ok=True)

    for name in stations["NAME"].dropna().astype(str):
        output_file = analyze_station(name, output_folder)
        print(f"Grafic generat: {output_file}")

    print("Analiza histogramelor s-a incheiat cu succes.")


if __name__ == "__main__":
    main()

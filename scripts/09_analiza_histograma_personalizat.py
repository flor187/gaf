"""Generate QM analysis plots whose metrics and distributions follow the zoom range."""

import json
import runpy
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
BASE_ANALYSIS = runpy.run_path(
    str(PROJECT_ROOT / "scripts" / "07_analiza_histograma.py")
)
START_DATE = BASE_ANALYSIS["START_DATE"]
END_DATE = BASE_ANALYSIS["END_DATE"]


def build_range_update_script(name: str, data: pd.DataFrame) -> str:
    source = json.dumps(
        {
            "dates": data.index.strftime("%Y-%m-%d").tolist(),
            "observed": data["Observat"].astype(float).tolist(),
            "simulated": data["Simulat"].astype(float).tolist(),
            "corrected": data["Simulat dupa QM"].astype(float).tolist(),
        },
        separators=(",", ":"),
    )
    title_prefix = json.dumps(
        f"Analiza distributiei si a cuantilelor - Statia: {name}"
    )

    script = r"""(function () {
    const graph = document.getElementById("__PLOT_ID__");
    const source = __SOURCE_DATA__;
    const titlePrefix = __TITLE_PREFIX__;
    const quantiles = [0.05, 0.25, 0.50, 0.75, 0.95, 0.99];
    const fullRange = [source.dates[0], source.dates[source.dates.length - 1]];
    let updateTimer;
    let lastRangeKey = "";
    let updateSequence = 0;
    const toolbar = document.createElement("div");
    toolbar.style.cssText = [
        "display:flex",
        "align-items:center",
        "justify-content:space-between",
        "flex-wrap:wrap",
        "gap:12px",
        "padding:10px 16px",
        "font-family:Arial,sans-serif",
        "border:1px solid #e2e8f0",
        "border-radius:6px",
        "background:#f8fafc",
        "margin-bottom:8px"
    ].join(";");

    const heading = document.createElement("strong");
    heading.textContent = titlePrefix;
    heading.style.cssText = "font-size:16px;color:#1f2937";

    const form = document.createElement("div");
    form.style.cssText = "display:flex;align-items:center;flex-wrap:wrap;gap:8px";

    function createDateControl(labelText, value) {
        const label = document.createElement("label");
        label.textContent = labelText;
        label.style.cssText = [
            "display:flex",
            "align-items:center",
            "gap:5px",
            "font-size:13px",
            "color:#374151"
        ].join(";");
        const input = document.createElement("input");
        input.type = "date";
        input.min = fullRange[0];
        input.max = fullRange[1];
        input.value = value;
        input.style.cssText = [
            "padding:5px 7px",
            "border:1px solid #cbd5e1",
            "border-radius:4px",
            "font:inherit"
        ].join(";");
        label.appendChild(input);
        return input;
    }

    const startInput = createDateControl("De la", fullRange[0]);
    const endInput = createDateControl("Pana la", fullRange[1]);
    const applyButton = document.createElement("button");
    applyButton.type = "button";
    applyButton.textContent = "Aplica";
    applyButton.style.cssText = [
        "padding:6px 12px",
        "border:0",
        "border-radius:4px",
        "background:#2585c5",
        "color:white",
        "font:inherit",
        "cursor:pointer"
    ].join(";");
    const status = document.createElement("span");
    status.setAttribute("role", "alert");
    status.style.cssText = "font-size:12px;color:#b42318";
    form.append(startInput.parentElement, endInput.parentElement, applyButton, status);
    toolbar.append(heading, form);
    graph.parentNode.insertBefore(toolbar, graph);

    function dateOnly(value) {
        return typeof value === "string"
            ? value.slice(0, 10)
            : new Date(value).toISOString().slice(0, 10);
    }

    function rangeKey(range) {
        return range.map(dateOnly).join(":");
    }

    function format(value) {
        return Number.isFinite(value) ? value.toFixed(2) : "N/A";
    }

    function summarize(observed, simulated) {
        const count = observed.length;
        if (count === 0) {
            return ["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"];
        }

        const meanObserved = observed.reduce((sum, value) => sum + value, 0) / count;
        const meanSimulated = simulated.reduce((sum, value) => sum + value, 0) / count;
        const observedTotal = observed.reduce((sum, value) => sum + value, 0);
        const squaredError = observed.reduce(
            (sum, value, index) => sum + (simulated[index] - value) ** 2,
            0
        );
        const observedVariance = observed.reduce(
            (sum, value) => sum + (value - meanObserved) ** 2,
            0
        );
        const nse = observedVariance === 0
            ? NaN
            : 1 - squaredError / observedVariance;
        const pbias = observedTotal === 0
            ? NaN
            : 100 * (
                simulated.reduce((sum, value) => sum + value, 0) - observedTotal
            ) / observedTotal;

        let correlation = NaN;
        let gamma = NaN;
        let beta = NaN;
        let kge = NaN;
        let alpha = NaN;
        if (count > 1 && meanObserved !== 0 && meanSimulated !== 0) {
            const covariance = observed.reduce(
                (sum, value, index) =>
                    sum + (value - meanObserved) * (simulated[index] - meanSimulated),
                0
            );
            const simulatedVariance = simulated.reduce(
                (sum, value) => sum + (value - meanSimulated) ** 2,
                0
            );
            if (observedVariance > 0 && simulatedVariance > 0) {
                correlation = covariance / Math.sqrt(observedVariance * simulatedVariance);
                const observedCv = Math.sqrt(observedVariance / count) / meanObserved;
                const simulatedCv = Math.sqrt(simulatedVariance / count) / meanSimulated;
                gamma = simulatedCv / observedCv;
                beta = meanSimulated / meanObserved;
                alpha = gamma * beta;
                kge = 1 - Math.sqrt(
                    (correlation - 1) ** 2 + (gamma - 1) ** 2 + (beta - 1) ** 2
                );
            }
        }

        return [
            format(pbias),
            format(nse),
            format(kge),
            format(correlation),
            format(alpha),
            format(gamma),
            format(beta)
        ];
    }

    function quantile(values, probability) {
        if (values.length === 0) {
            return "N/A";
        }
        const sorted = values.slice().sort((left, right) => left - right);
        const position = (sorted.length - 1) * probability;
        const lower = Math.floor(position);
        const fraction = position - lower;
        const value = sorted[lower] + fraction * (
            (sorted[Math.min(lower + 1, sorted.length - 1)]) - sorted[lower]
        );
        return format(value);
    }

    function tableValues(observed, simulated) {
        const labels = quantiles.map((value) => `Q ${Math.round(value * 100)}%`);
        labels.push("Media aritmetica");
        const observedValues = quantiles.map((value) => quantile(observed, value));
        const simulatedValues = quantiles.map((value) => quantile(simulated, value));
        observedValues.push(
            observed.length
                ? format(observed.reduce((sum, value) => sum + value, 0) / observed.length)
                : "N/A"
        );
        simulatedValues.push(
            simulated.length
                ? format(simulated.reduce((sum, value) => sum + value, 0) / simulated.length)
                : "N/A"
        );
        return [labels, observedValues, simulatedValues];
    }

    function selectedIndexes(range) {
        const start = dateOnly(range[0]);
        const end = dateOnly(range[1]);
        return source.dates.reduce((indexes, date, index) => {
            if (date >= start && date <= end) {
                indexes.push(index);
            }
            return indexes;
        }, []);
    }

    async function updateRange(range, sequence) {
        const indexes = selectedIndexes(range);
        const dates = indexes.map((index) => source.dates[index]);
        const observed = indexes.map((index) => source.observed[index]);
        const simulated = indexes.map((index) => source.simulated[index]);
        const corrected = indexes.map((index) => source.corrected[index]);

        const updates = [
            [0, observed],
            [1, simulated],
            [4, dates],
            [5, dates],
            [6, observed],
            [7, corrected],
            [10, dates],
            [11, dates]
        ];
        for (const [traceIndex, values] of updates) {
            if (sequence !== updateSequence) {
                return;
            }
            await Plotly.restyle(graph, {x: [values]}, [traceIndex]);
        }

        const tables = [
            [2, observed, simulated],
            [3, observed, simulated],
            [8, observed, corrected],
            [9, observed, corrected]
        ];
        for (const [traceIndex, observedValues, simulatedValues] of tables) {
            if (sequence !== updateSequence) {
                return;
            }
            const values = traceIndex === 2 || traceIndex === 8
                ? [
                    [
                        "PBIAS (%) | eroare volum",
                        "NSE | eroarea patratelor",
                        "KGE-2012 | indice diagnoza",
                        "corelatia pearson | ritmul",
                        "alpha | marimea variatiilor",
                        "gama | forma variatiilor",
                        "beta | volumul"
                    ],
                    summarize(observedValues, simulatedValues)
                ]
                : tableValues(observedValues, simulatedValues);
            await Plotly.restyle(
                graph,
                {"cells.values": [values]},
                [traceIndex]
            );
        }

        if (sequence !== updateSequence) {
            return;
        }
        const startDate = dateOnly(range[0]);
        const endDate = dateOnly(range[1]);
        heading.textContent = `${titlePrefix} - Interval: ${startDate} - ${endDate}`;
        startInput.value = startDate;
        endInput.value = endDate;
    }

    applyButton.addEventListener("click", () => {
        const range = [startInput.value, endInput.value];
        if (!range[0] || !range[1] || range[0] > range[1]) {
            status.textContent = "Selecteaza un interval valid.";
            return;
        }
        if (range[0] < fullRange[0] || range[1] > fullRange[1]) {
            status.textContent = "Intervalul trebuie sa fie in perioada disponibila.";
            return;
        }
        if (selectedIndexes(range).length === 0) {
            status.textContent = "Nu exista date in intervalul selectat.";
            return;
        }

        status.textContent = "";
        const key = rangeKey(range);
        lastRangeKey = key;
        const sequence = ++updateSequence;
        window.clearTimeout(updateTimer);
        Plotly.relayout(graph, {
            "xaxis.range": range,
            "xaxis2.range": range
        }).then(() => updateRange(range, sequence)).catch((error) => {
            console.error("Nu s-a putut aplica intervalul selectat.", error);
            status.textContent = "Intervalul nu a putut fi aplicat.";
        });
    });

    graph.on("plotly_relayout", (event) => {
        let range;
        if (event["xaxis.range[0]"] && event["xaxis.range[1]"]) {
            range = [event["xaxis.range[0]"], event["xaxis.range[1]"]];
        } else if (event["xaxis2.range[0]"] && event["xaxis2.range[1]"]) {
            range = [event["xaxis2.range[0]"], event["xaxis2.range[1]"]];
        } else if (Array.isArray(event["xaxis.range"])) {
            range = event["xaxis.range"];
        } else if (Array.isArray(event["xaxis2.range"])) {
            range = event["xaxis2.range"];
        } else if (event["xaxis.autorange"] || event["xaxis2.autorange"]) {
            range = fullRange;
        } else {
            return;
        }

        status.textContent = "";
        const key = rangeKey(range);
        if (key === lastRangeKey) {
            return;
        }
        lastRangeKey = key;
        Plotly.relayout(graph, {
            "xaxis.range": range,
            "xaxis2.range": range
        }).catch((error) => {
            console.error("Nu s-au putut sincroniza axele temporale.", error);
        });
        const sequence = ++updateSequence;
        window.clearTimeout(updateTimer);
        updateTimer = window.setTimeout(() => {
            updateRange(range, sequence).catch((error) => {
                console.error("Nu s-au putut actualiza statisticile intervalului.", error);
            });
        }, 100);
    });

    lastRangeKey = rangeKey(fullRange);
    updateRange(fullRange, ++updateSequence).catch((error) => {
        console.error("Nu s-au putut initializa statisticile intervalului.", error);
    });
})();"""
    script = (
        script.replace("__PLOT_ID__", "{plot_id}")
        .replace("__SOURCE_DATA__", source)
        .replace("__TITLE_PREFIX__", title_prefix)
    )
    return script


def analyze_station(name: str, output_folder: Path) -> Path:
    read_flow_series = BASE_ANALYSIS["read_flow_series"]
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

    correction = BASE_ANALYSIS["BiasCorrection"](
        obs_data=aligned["Observat"],
        mod_data=aligned["Simulat"],
        sce_data=aligned["Simulat"],
    )
    aligned["Simulat dupa QM"] = correction.correct(method="basic_quantile")

    figure = BASE_ANALYSIS["create_station_figure"](name, aligned)
    figure.update_layout(title=None, margin=dict(t=70, b=60, l=70, r=35))
    output_file = output_folder / f"{name}_histograma_personalizat.html"
    figure.write_html(
        output_file,
        include_plotlyjs="cdn",
        post_script=build_range_update_script(name, aligned),
    )
    return output_file


def main() -> None:
    stations_file = PROJECT_ROOT / "config" / "coords_stations.csv"
    stations = pd.read_csv(stations_file)
    if "NAME" not in stations.columns:
        raise ValueError(f"Coloana NAME lipseste din fisierul {stations_file}.")

    output_folder = PROJECT_ROOT / "analiza" / "analiza_histograma_personalizat"
    output_folder.mkdir(parents=True, exist_ok=True)

    for name in stations["NAME"].dropna().astype(str):
        output_file = analyze_station(name, output_folder)
        print(f"Grafic generat: {output_file}")

    print("Analiza intervalelor personalizate s-a incheiat cu succes.")


if __name__ == "__main__":
    main()

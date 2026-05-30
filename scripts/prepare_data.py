from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

STATE_NAME_FIX = {
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "Wilayah Persekutuan Kuala Lumpur": "Kuala Lumpur",
    "W.P. Labuan": "Labuan",
    "Wilayah Persekutuan Labuan": "Labuan",
    "W.P. Putrajaya": "Putrajaya",
    "Wilayah Persekutuan Putrajaya": "Putrajaya",
    "Penang": "Pulau Pinang",
}

STATE_ORDER = [
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang",
    "Perak", "Perlis", "Pulau Pinang", "Sabah", "Sarawak", "Selangor",
    "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya"
]

# States highlighted in narrative charts.
INCOME_HIGHLIGHTS = {"Kuala Lumpur", "Putrajaya", "Selangor", "Kelantan", "Sabah"}
POVERTY_HIGHLIGHTS = {"Sabah", "Kelantan", "Sarawak", "Kedah"}
SLOPE_HIGHLIGHTS = {"Kuala Lumpur", "Putrajaya", "Selangor", "Kelantan", "Sabah", "Sarawak"}
SCATTER_LABELS = {"Sabah", "Kelantan", "Sarawak", "Putrajaya", "Kuala Lumpur", "Selangor"}


def clean_state_name(name: str) -> str:
    return STATE_NAME_FIX.get(str(name), str(name))


def zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return series * 0
    return (series - series.mean()) / std


def safe_read_csv(path: Path, parse_dates=None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path, parse_dates=parse_dates)


# -----------------------------
# 1. Load state-level datasets
# -----------------------------
income_state = safe_read_csv(RAW / "hh_income_state.csv", parse_dates=["date"])
poverty_state = safe_read_csv(RAW / "hh_poverty_state.csv", parse_dates=["date"])

income_state["year"] = income_state["date"].dt.year
poverty_state["year"] = poverty_state["date"].dt.year

income_state["state_geo"] = income_state["state"].apply(clean_state_name)
poverty_state["state_geo"] = poverty_state["state"].apply(clean_state_name)

state = pd.merge(
    income_state.drop(columns=["date"]),
    poverty_state.drop(columns=["date"]),
    on=["state", "state_geo", "year"],
    how="inner"
)

state["mean_median_gap"] = state["income_mean"] - state["income_median"]
state["mean_median_ratio"] = state["income_mean"] / state["income_median"]
state["state_order"] = state["state_geo"].map({s: i for i, s in enumerate(STATE_ORDER)})

# Main state-comparison period. All states/federal territories appear from 2007 onward.
state_main = state[state["year"].between(2007, 2022)].copy()

# -----------------------------
# 2. Build 2022 summary dataset
# -----------------------------
state_2022 = state_main[state_main["year"] == 2022].copy()

# Tertiles are used for a simple bivariate map. With 16 states, this keeps the map readable.
income_q1, income_q2 = state_2022["income_median"].quantile([1/3, 2/3])
poverty_q1, poverty_q2 = state_2022["poverty_absolute"].quantile([1/3, 2/3])


def income_class(value: float) -> str:
    if value <= income_q1:
        return "Low income"
    if value <= income_q2:
        return "Middle income"
    return "High income"


def poverty_class(value: float) -> str:
    if value <= poverty_q1:
        return "Low poverty"
    if value <= poverty_q2:
        return "Middle poverty"
    return "High poverty"


state_2022["income_class"] = state_2022["income_median"].apply(income_class)
state_2022["poverty_class"] = state_2022["poverty_absolute"].apply(poverty_class)
state_2022["bivariate_class"] = state_2022["income_class"] + " + " + state_2022["poverty_class"]

# Vulnerability score: high = low median income + high absolute poverty + high relative poverty.
state_2022["z_low_income"] = -zscore(state_2022["income_median"])
state_2022["z_abs_poverty"] = zscore(state_2022["poverty_absolute"])
state_2022["z_rel_poverty"] = zscore(state_2022["poverty_relative"])
state_2022["vulnerability_score"] = (
    state_2022["z_low_income"] +
    state_2022["z_abs_poverty"] +
    state_2022["z_rel_poverty"]
) / 3

state_2022["income_rank"] = state_2022["income_median"].rank(ascending=False, method="dense").astype(int)
state_2022["poverty_rank"] = state_2022["poverty_absolute"].rank(ascending=False, method="dense").astype(int)
state_2022["vulnerability_rank"] = state_2022["vulnerability_score"].rank(ascending=False, method="first").astype(int)
state_2022["vulnerability_order"] = state_2022["vulnerability_rank"]

# Three vulnerability categories using ranks, not hidden statistical jargon.
def vulnerability_group(rank: int) -> str:
    if rank <= 5:
        return "High vulnerability"
    if rank <= 10:
        return "Moderate vulnerability"
    return "Lower vulnerability"

state_2022["vulnerability_group"] = state_2022["vulnerability_rank"].apply(vulnerability_group)
state_2022["highlight_income"] = state_2022["state_geo"].isin(INCOME_HIGHLIGHTS)
state_2022["highlight_poverty"] = state_2022["state_geo"].isin(POVERTY_HIGHLIGHTS)
state_2022["label_scatter"] = state_2022["state_geo"].isin(SCATTER_LABELS)

# Add 2019 to 2022 recovery fields to 2022 state file.
base_2019 = state_main[state_main["year"] == 2019][["state_geo", "income_median", "poverty_absolute"]].rename(
    columns={
        "income_median": "income_median_2019",
        "poverty_absolute": "poverty_absolute_2019"
    }
)
state_2022 = state_2022.merge(base_2019, on="state_geo", how="left")
state_2022["income_change_2019_2022"] = state_2022["income_median"] - state_2022["income_median_2019"]
state_2022["income_change_pct_2019_2022"] = state_2022["income_change_2019_2022"] / state_2022["income_median_2019"] * 100
state_2022["poverty_change_2019_2022"] = state_2022["poverty_absolute"] - state_2022["poverty_absolute_2019"]

# Save 2022 summary.
state_2022.to_csv(OUT / "state_2022.csv", index=False)

# Merge vulnerability order/group into all main-year records so heatmaps can be sorted consistently.
vulnerability_lookup = state_2022[["state_geo", "vulnerability_order", "vulnerability_group", "vulnerability_rank"]]
state_main = state_main.merge(vulnerability_lookup, on="state_geo", how="left")
state_main["highlight_slope"] = state_main["state_geo"].isin(SLOPE_HIGHLIGHTS)
state_main.to_csv(OUT / "state_income_poverty.csv", index=False)

# -----------------------------
# 3. 2007 vs 2022 slope data
# -----------------------------
slope = state_main[state_main["year"].isin([2007, 2022])].copy()
base_2007 = slope[slope["year"] == 2007][["state_geo", "income_median", "poverty_absolute"]].rename(
    columns={
        "income_median": "income_median_2007",
        "poverty_absolute": "poverty_absolute_2007"
    }
)
base_2022 = slope[slope["year"] == 2022][["state_geo", "income_median", "poverty_absolute"]].rename(
    columns={
        "income_median": "income_median_2022",
        "poverty_absolute": "poverty_absolute_2022"
    }
)
change_2007_2022 = base_2007.merge(base_2022, on="state_geo", how="inner")
change_2007_2022["income_change_pct_2007_2022"] = (
    change_2007_2022["income_median_2022"] - change_2007_2022["income_median_2007"]
) / change_2007_2022["income_median_2007"] * 100
change_2007_2022["poverty_change_2007_2022"] = (
    change_2007_2022["poverty_absolute_2022"] - change_2007_2022["poverty_absolute_2007"]
)
slope = slope.merge(change_2007_2022, on="state_geo", how="left")
slope.to_csv(OUT / "slope_2007_2022.csv", index=False)

# -----------------------------
# 4. 2019 to 2022 recovery data
# -----------------------------
recovery = state_main[state_main["year"].isin([2019, 2020, 2022])].copy()
recovery = recovery.merge(base_2019, on="state_geo", how="left")
recovery["income_index_2019"] = recovery["income_median"] / recovery["income_median_2019"] * 100
recovery["highlight_recovery"] = recovery["state_geo"].isin(SCATTER_LABELS)
recovery.to_csv(OUT / "recovery_2019_2022.csv", index=False)

# -----------------------------
# 5. National context data
# -----------------------------
income_nat_path = RAW / "hh_income.csv"
poverty_nat_path = RAW / "hh_poverty.csv"

if income_nat_path.exists() and poverty_nat_path.exists():
    income_nat = pd.read_csv(income_nat_path, parse_dates=["date"])
    poverty_nat = pd.read_csv(poverty_nat_path, parse_dates=["date"])
    income_nat["year"] = income_nat["date"].dt.year
    poverty_nat["year"] = poverty_nat["date"].dt.year
    national = pd.merge(
        income_nat.drop(columns=["date"]),
        poverty_nat.drop(columns=["date"]),
        on="year",
        how="inner"
    )
    national.to_csv(OUT / "national_context.csv", index=False)
else:
    # Do not fake the national context. The national line should come from the national DOSM files.
    message = (
        "Missing national files. Download hh_income.csv and hh_poverty.csv from data.gov.my "
        "and put them in data/raw/. Then run scripts/prepare_data.py again.\n"
    )
    (OUT / "national_context_MISSING.txt").write_text(message, encoding="utf-8")

print("Prepared data files in", OUT)
print("Rows in state_income_poverty.csv:", len(state_main))
print("Rows in state_2022.csv:", len(state_2022))
print("Rows in recovery_2019_2022.csv:", len(recovery))
print("Rows in slope_2007_2022.csv:", len(slope))

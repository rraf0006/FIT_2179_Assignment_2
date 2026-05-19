from pathlib import Path
import pandas as pd
import numpy as np

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

STATE_NAME_FIX = {
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "W.P. Labuan": "Labuan",
    "W.P. Putrajaya": "Putrajaya",
    "Pulau Pinang": "Pulau Pinang",
    "Melaka": "Melaka",
    "Negeri Sembilan": "Negeri Sembilan",
}

def clean_state_name(name):
    return STATE_NAME_FIX.get(name, name)

def zscore(series):
    return (series - series.mean()) / series.std(ddof=0)

# ---------- Load state datasets ----------
income_state = pd.read_csv(RAW / "hh_income_state.csv", parse_dates=["date"])
poverty_state = pd.read_csv(RAW / "hh_poverty_state.csv", parse_dates=["date"])

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

# Keep the main comparison period complete.
state_main = state[state["year"].between(2007, 2022)].copy()
state_main.to_csv(OUT / "state_income_poverty.csv", index=False)

# ---------- 2022 summary ----------
state_2022 = state_main[state_main["year"] == 2022].copy()

# Bivariate classes: low/medium/high income and poverty using tertiles.
income_q1, income_q2 = state_2022["income_median"].quantile([1/3, 2/3])
poverty_q1, poverty_q2 = state_2022["poverty_absolute"].quantile([1/3, 2/3])

def income_class(value):
    if value <= income_q1:
        return "Low income"
    if value <= income_q2:
        return "Middle income"
    return "High income"

def poverty_class(value):
    if value <= poverty_q1:
        return "Low poverty"
    if value <= poverty_q2:
        return "Middle poverty"
    return "High poverty"

state_2022["income_class"] = state_2022["income_median"].apply(income_class)
state_2022["poverty_class"] = state_2022["poverty_absolute"].apply(poverty_class)
state_2022["bivariate_class"] = state_2022["income_class"] + " + " + state_2022["poverty_class"]

# Vulnerability score:
# high = low median income + high absolute poverty + high relative poverty
state_2022["z_low_income"] = -zscore(state_2022["income_median"])
state_2022["z_abs_poverty"] = zscore(state_2022["poverty_absolute"])
state_2022["z_rel_poverty"] = zscore(state_2022["poverty_relative"])
state_2022["vulnerability_score"] = (
    state_2022["z_low_income"] +
    state_2022["z_abs_poverty"] +
    state_2022["z_rel_poverty"]
) / 3

state_2022["income_rank"] = state_2022["income_median"].rank(
    ascending=False, method="dense"
).astype(int)

state_2022["poverty_rank"] = state_2022["poverty_absolute"].rank(
    ascending=False, method="dense"
).astype(int)

state_2022.to_csv(OUT / "state_2022.csv", index=False)

# ---------- 2007 vs 2022 slope data ----------
slope = state_main[state_main["year"].isin([2007, 2022])].copy()
slope.to_csv(OUT / "slope_2007_2022.csv", index=False)

# ---------- 2019–2022 recovery data ----------
recovery = state_main[state_main["year"].isin([2019, 2020, 2022])].copy()
recovery.to_csv(OUT / "recovery_2019_2022.csv", index=False)

# ---------- National context ----------
income_national_path = RAW / "hh_income.csv"
poverty_national_path = RAW / "hh_poverty.csv"

if income_national_path.exists() and poverty_national_path.exists():
    income_nat = pd.read_csv(income_national_path, parse_dates=["date"])
    poverty_nat = pd.read_csv(poverty_national_path, parse_dates=["date"])

    income_nat["year"] = income_nat["date"].dt.year
    poverty_nat["year"] = poverty_nat["date"].dt.year

    national = pd.merge(
        income_nat.drop(columns=["date"]),
        poverty_nat.drop(columns=["date"]),
        on="year",
        how="inner"
    )

    national.to_csv(OUT / "national_context.csv", index=False)

print("Prepared files in data/processed/")
print("Rows in state main data:", len(state_main))
print("Rows in 2022 state data:", len(state_2022))
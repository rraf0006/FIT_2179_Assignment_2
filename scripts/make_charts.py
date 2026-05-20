from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "js"
MAPS = ROOT / "data" / "maps"
PROCESSED = ROOT / "data" / "processed"
JS.mkdir(parents=True, exist_ok=True)

MAP_URL = "data/maps/malaysia_states.topojson"
STATE_2022 = "data/processed/state_2022.csv"
STATE_MAIN = "data/processed/state_income_poverty.csv"
NATIONAL = "data/processed/national_context.csv"
SLOPE = "data/processed/slope_2007_2022.csv"
RECOVERY = "data/processed/recovery_2019_2022.csv"

FONT = "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
TEXT = "#1f2933"
MUTED = "#6b7280"
ACCENT = "#8a4b2a"
LIGHT = "#d8c7b2"
BORDER = "#e6ded3"

STATE_OPTIONS = [
    None, "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang",
    "Perak", "Perlis", "Pulau Pinang", "Sabah", "Sarawak", "Selangor",
    "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya"
]
STATE_LABELS = ["Show all"] + [s for s in STATE_OPTIONS if s is not None]


def base_config():
    return {
        "font": FONT,
        "background": "transparent",
        "title": {
            "font": FONT,
            "fontSize": 17,
            "fontWeight": 700,
            "subtitleFont": FONT,
            "subtitleFontSize": 12,
            "subtitleColor": MUTED,
            "anchor": "start",
            "color": TEXT
        },
        "axis": {
            "labelFont": FONT,
            "titleFont": FONT,
            "labelFontSize": 11,
            "titleFontSize": 12,
            "labelColor": TEXT,
            "titleColor": TEXT,
            "gridColor": "#ece7df",
            "domainColor": BORDER,
            "tickColor": BORDER
        },
        "legend": {
            "labelFont": FONT,
            "titleFont": FONT,
            "labelFontSize": 11,
            "titleFontSize": 12,
            "labelColor": TEXT,
            "titleColor": TEXT,
            "orient": "right"
        },
        "view": {"stroke": None}
    }


def write(name: str, spec: dict):
    with (JS / name).open("w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", JS / name)


def detect_topojson_details():
    """Return (feature_name, property_lookup_name). Defaults match geoBoundaries ADM1."""
    topo_path = MAPS / "malaysia_states.topojson"
    if not topo_path.exists():
        return "geoBoundaries-MYS-ADM1", "properties.shapeName"

    topo = json.loads(topo_path.read_text(encoding="utf-8"))
    objects = topo.get("objects", {})
    if not objects:
        return "geoBoundaries-MYS-ADM1", "properties.shapeName"
    feature = next(iter(objects.keys()))

    geoms = objects[feature].get("geometries", [])
    props = geoms[0].get("properties", {}) if geoms else {}
    candidates = ["shapeName", "name", "NAME_1", "NAME", "state", "State", "ADM1_EN"]
    for key in candidates:
        if key in props:
            return feature, f"properties.{key}"
    return feature, "properties.shapeName"


feature_name, topo_lookup_field = detect_topojson_details()
print("Using TopoJSON feature:", feature_name)
print("Using TopoJSON lookup field:", topo_lookup_field)

MAP_LOOKUP_TRANSFORM = [
    {
        "lookup": topo_lookup_field,
        "from": {
            "data": {"url": STATE_2022},
            "key": "state_geo",
            "fields": [
                "state", "state_geo", "income_median", "income_mean",
                "poverty_absolute", "poverty_hardcore", "poverty_relative",
                "bivariate_class", "vulnerability_score", "vulnerability_group",
                "income_rank", "poverty_rank"
            ]
        }
    }
]

# -------------------- Chart 1 --------------------
write("national_context.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"url": NATIONAL},
    "vconcat": [
        {
            "width": "container",
            "height": 260,
            "title": {
                "text": "Malaysia's median household income has risen over the long term",
                "subtitle": "National median monthly household income, nominal RM, 1970–2022"
            },
            "layer": [
                {
                    "mark": {"type": "line", "strokeWidth": 3, "color": ACCENT},
                    "encoding": {
                        "x": {"field": "year", "type": "quantitative", "axis": {"title": None, "format": "d", "tickMinStep": 1}},
                        "y": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "scale": {"zero": True}},
                        "tooltip": [
                            {"field": "year", "type": "quantitative", "title": "Year", "format": "d"},
                            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
                            {"field": "income_mean", "type": "quantitative", "title": "Mean income (RM)", "format": ","}
                        ]
                    }
                },
                {
                    "mark": {"type": "point", "filled": True, "size": 45, "color": ACCENT},
                    "encoding": {
                        "x": {"field": "year", "type": "quantitative"},
                        "y": {"field": "income_median", "type": "quantitative"},
                        "tooltip": [
                            {"field": "year", "type": "quantitative", "title": "Year", "format": "d"},
                            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","}
                        ]
                    }
                },
                {
                    "mark": {"type": "rule", "color": MUTED, "strokeDash": [5, 5], "strokeWidth": 1.2},
                    "encoding": {"x": {"datum": 2007}}
                },
                {
                    "mark": {"type": "text", "align": "left", "baseline": "top", "dx": 6, "dy": 6, "fontSize": 12, "color": MUTED},
                    "encoding": {
                        "x": {"datum": 2007},
                        "y": {"datum": 6500},
                        "text": {"value": "State comparison begins in 2007"}
                    }
                }
            ]
        },
        {
            "width": "container",
            "height": 220,
            "title": {
                "text": "Absolute poverty fell sharply, but the state-level story is uneven",
                "subtitle": "National absolute poverty rate, percentage of households, 1970–2022"
            },
            "layer": [
                {
                    "mark": {"type": "line", "strokeWidth": 3, "color": "#b45309"},
                    "encoding": {
                        "x": {"field": "year", "type": "quantitative", "axis": {"title": "Year", "format": "d", "tickMinStep": 1}},
                        "y": {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "scale": {"zero": True}},
                        "tooltip": [
                            {"field": "year", "type": "quantitative", "title": "Year", "format": "d"},
                            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
                            {"field": "poverty_hardcore", "type": "quantitative", "title": "Hardcore poverty (%)", "format": ".1f"}
                        ]
                    }
                },
                {
                    "mark": {"type": "point", "filled": True, "size": 45, "color": "#b45309"},
                    "encoding": {
                        "x": {"field": "year", "type": "quantitative"},
                        "y": {"field": "poverty_absolute", "type": "quantitative"},
                        "tooltip": [
                            {"field": "year", "type": "quantitative", "title": "Year", "format": "d"},
                            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"}
                        ]
                    }
                },
                {
                    "mark": {"type": "rule", "color": MUTED, "strokeDash": [5, 5], "strokeWidth": 1.2},
                    "encoding": {"x": {"datum": 2007}}
                }
            ]
        }
    ],
    "resolve": {"scale": {"y": "independent"}},
    "config": base_config()
})

# -------------------- Chart 2 --------------------
write("map_income_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 430,
    "title": {
        "text": "Median household income is highest around the Klang Valley",
        "subtitle": "Median monthly household income by state, nominal RM, 2022"
    },
    "projection": {"type": "equalEarth"},
    "data": {"url": MAP_URL, "format": {"type": "topojson", "feature": feature_name}},
    "transform": MAP_LOOKUP_TRANSFORM,
    "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 0.9},
    "encoding": {
        "color": {
            "field": "income_median",
            "type": "quantitative",
            "title": "Median income (RM/month)",
            "scale": {"scheme": "blues"},
            "legend": {"format": ","}
        },
        "tooltip": [
            {"field": "state_geo", "type": "nominal", "title": "State"},
            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
            {"field": "income_mean", "type": "quantitative", "title": "Mean income (RM)", "format": ","},
            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"}
        ]
    },
    "config": base_config()
})

# -------------------- Chart 3 --------------------
write("map_poverty_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 430,
    "title": {
        "text": "Absolute poverty remains concentrated in several states",
        "subtitle": "Absolute poverty rate by state, percentage of households, 2022"
    },
    "projection": {"type": "equalEarth"},
    "data": {"url": MAP_URL, "format": {"type": "topojson", "feature": feature_name}},
    "transform": MAP_LOOKUP_TRANSFORM,
    "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 0.9},
    "encoding": {
        "color": {
            "field": "poverty_absolute",
            "type": "quantitative",
            "title": "Absolute poverty (%)",
            "scale": {"scheme": "oranges"},
            "legend": {"format": ".1f"}
        },
        "tooltip": [
            {"field": "state_geo", "type": "nominal", "title": "State"},
            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
            {"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "format": ".1f"},
            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","}
        ]
    },
    "config": base_config()
})

# -------------------- Chart 4 --------------------
bivariate_domain = [
    "Low income + Low poverty", "Low income + Middle poverty", "Low income + High poverty",
    "Middle income + Low poverty", "Middle income + Middle poverty", "Middle income + High poverty",
    "High income + Low poverty", "High income + Middle poverty", "High income + High poverty"
]
bivariate_range = [
    "#e8e1d4", "#d5a373", "#9c5a2e",
    "#c6d8c4", "#c79a74", "#8f3f2b",
    "#6fb08a", "#9d7b64", "#6f2e23"
]
write("map_bivariate_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 470,
    "title": {
        "text": "Low income and high poverty combine into a vulnerability pattern",
        "subtitle": "Bivariate classes combine 2022 median income tertiles and absolute poverty tertiles"
    },
    "projection": {"type": "equalEarth"},
    "data": {"url": MAP_URL, "format": {"type": "topojson", "feature": feature_name}},
    "transform": MAP_LOOKUP_TRANSFORM,
    "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 0.9},
    "encoding": {
        "color": {
            "field": "bivariate_class",
            "type": "nominal",
            "title": "Income + poverty class",
            "scale": {"domain": bivariate_domain, "range": bivariate_range},
            "legend": {"columns": 1}
        },
        "tooltip": [
            {"field": "state_geo", "type": "nominal", "title": "State"},
            {"field": "bivariate_class", "type": "nominal", "title": "Class"},
            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
            {"field": "vulnerability_group", "type": "nominal", "title": "Scorecard group"}
        ]
    },
    "config": base_config()
})

# -------------------- Chart 5 --------------------
write("rank_income_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 420,
    "data": {"url": STATE_2022},
    "title": {
        "text": "The 2022 income gap between states is large",
        "subtitle": "Sorted by median monthly household income, nominal RM"
    },
    "layer": [
        {
            "mark": {"type": "bar", "cornerRadiusEnd": 3},
            "encoding": {
                "x": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "axis": {"format": ","}},
                "y": {"field": "state_geo", "type": "nominal", "title": None, "sort": {"field": "income_median", "order": "descending"}},
                "color": {
                    "condition": {"test": "datum.highlight_income", "value": ACCENT},
                    "value": LIGHT
                },
                "tooltip": [
                    {"field": "income_rank", "type": "quantitative", "title": "Income rank"},
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
                    {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"}
                ]
            }
        },
        {
            "mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 4, "fontSize": 11, "color": TEXT},
            "encoding": {
                "x": {"field": "income_median", "type": "quantitative"},
                "y": {"field": "state_geo", "type": "nominal", "sort": {"field": "income_median", "order": "descending"}},
                "text": {"field": "income_median", "type": "quantitative", "format": ","}
            }
        }
    ],
    "config": base_config()
})

# -------------------- Chart 6 --------------------
write("rank_poverty_2022.vg.json", {
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "width": "container",
  "height": 420,
  "data": {
    "url": "data/processed/state_2022.csv"
  },
  "title": {
    "text": "Sabah, Kelantan and Sarawak remain high-poverty outliers",
    "subtitle": "Sorted by absolute poverty rate, percentage of households, 2022",
    "anchor": "start"
  },
  "layer": [
    {
      "mark": {
        "type": "bar",
        "cornerRadiusEnd": 3
      },
      "encoding": {
        "x": {
          "field": "poverty_absolute",
          "type": "quantitative",
          "title": "Absolute poverty (%)",
          "scale": {
            "domain": [0, 22]
          }
        },
        "y": {
          "field": "state_geo",
          "type": "nominal",
          "title": null,
          "sort": {
            "field": "poverty_absolute",
            "order": "descending"
          }
        },
        "color": {
          "condition": {
            "test": "indexof(['Sabah', 'Kelantan', 'Sarawak', 'Kedah'], datum.state_geo) >= 0",
            "value": "#b45309"
          },
          "value": "#dccfc0"
        },
        "tooltip": [
          {
            "field": "poverty_rank",
            "type": "quantitative",
            "title": "Poverty rank"
          },
          {
            "field": "state_geo",
            "type": "nominal",
            "title": "State"
          },
          {
            "field": "poverty_absolute",
            "type": "quantitative",
            "title": "Absolute poverty (%)",
            "format": ".1f"
          },
          {
            "field": "income_median",
            "type": "quantitative",
            "title": "Median income (RM)",
            "format": ","
          }
        ]
      }
    },
    {
      "mark": {
        "type": "text",
        "align": "left",
        "baseline": "middle",
        "dx": 5,
        "fontSize": 11,
        "color": "#1f2933"
      },
      "encoding": {
        "x": {
          "field": "poverty_absolute",
          "type": "quantitative"
        },
        "y": {
          "field": "state_geo",
          "type": "nominal",
          "sort": {
            "field": "poverty_absolute",
            "order": "descending"
          }
        },
        "text": {
          "field": "poverty_absolute",
          "type": "quantitative",
          "format": ".1f"
        }
      }
    }
  ],
  "config": {
    "font": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "background": "transparent",
    "title": {
      "font": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      "fontSize": 17,
      "fontWeight": 700,
      "subtitleFont": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      "subtitleFontSize": 12,
      "subtitleColor": "#6b7280",
      "anchor": "start",
      "color": "#1f2933"
    },
    "axis": {
      "labelFont": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      "titleFont": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      "labelFontSize": 11,
      "titleFontSize": 12,
      "labelColor": "#1f2933",
      "titleColor": "#1f2933",
      "gridColor": "#ece7df",
      "domainColor": "#e6ded3",
      "tickColor": "#e6ded3"
    },
    "legend": {
      "disable": true
    },
    "view": {
      "stroke": null
    }
  }
})

# -------------------- Chart 7 --------------------
write("dumbbell_mean_median_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 470,
    "data": {"url": STATE_2022},
    "title": {
        "text": "Mean income sits above median income in every state",
        "subtitle": "Dumbbell chart of mean and median monthly household income, nominal RM, 2022"
    },
    "layer": [
        {
            "mark": {"type": "rule", "strokeWidth": 2, "color": "#c9b9a5"},
            "encoding": {
                "x": {"field": "income_median", "type": "quantitative", "title": "Monthly household income (RM)", "axis": {"format": ","}},
                "x2": {"field": "income_mean"},
                "y": {"field": "state_geo", "type": "nominal", "title": None, "sort": {"field": "income_median", "order": "descending"}},
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
                    {"field": "income_mean", "type": "quantitative", "title": "Mean income (RM)", "format": ","},
                    {"field": "mean_median_gap", "type": "quantitative", "title": "Mean-median gap (RM)", "format": ","}
                ]
            }
        },
        {
            "transform": [
                {"fold": ["income_median", "income_mean"], "as": ["income_type", "income_value"]},
                {"calculate": "datum.income_type == 'income_median' ? 'Median' : 'Mean'", "as": "Income measure"}
            ],
            "mark": {"type": "circle", "filled": True, "size": 95, "stroke": "white", "strokeWidth": 1},
            "encoding": {
                "x": {"field": "income_value", "type": "quantitative"},
                "y": {"field": "state_geo", "type": "nominal", "sort": {"field": "income_median", "order": "descending"}},
                "color": {
                    "field": "Income measure",
                    "type": "nominal",
                    "scale": {"domain": ["Median", "Mean"], "range": ["#1f78b4", "#b45309"]},
                    "title": "Measure"
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "Income measure", "type": "nominal", "title": "Measure"},
                    {"field": "income_value", "type": "quantitative", "title": "Income (RM)", "format": ","}
                ]
            }
        }
    ],
    "config": base_config()
})

# -------------------- Chart 8 --------------------
write("scatter_income_poverty_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 470,
    "data": {"url": STATE_2022},
    "title": {
        "text": "Lower-income states tend to face higher absolute poverty",
        "subtitle": "Bubble size shows relative poverty; hover to highlight a state"
    },
    "params": [
        {"name": "hover_state", "select": {"type": "point", "fields": ["state_geo"], "on": "pointerover", "clear": "pointerout"}}
    ],
    "layer": [
        {
            "mark": {"type": "circle", "filled": True, "stroke": "white", "strokeWidth": 1},
            "encoding": {
                "x": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "axis": {"format": ","}},
                "y": {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "scale": {"zero": True}},
                "size": {"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "scale": {"range": [80, 800]}},
                "color": {
                    "field": "vulnerability_group",
                    "type": "nominal",
                    "title": "2022 scorecard group",
                    "scale": {
                        "domain": ["Highest vulnerability", "Watch closely", "Lower vulnerability"],
                        "range": ["#b45309", "#d7a46a", "#4f9f7a"]
                    }
                },
                "opacity": {
                    "condition": {"param": "hover_state", "empty": False, "value": 1},
                    "value": 0.82
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
                    {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
                    {"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "format": ".1f"},
                    {"field": "vulnerability_group", "type": "nominal", "title": "Scorecard group"}
                ]
            }
        },
        {
            "transform": [{"filter": "datum.label_scatter"}],
            "mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 9, "fontSize": 11, "fontWeight": 600, "color": TEXT},
            "encoding": {
                "x": {"field": "income_median", "type": "quantitative"},
                "y": {"field": "poverty_absolute", "type": "quantitative"},
                "text": {"field": "state_geo", "type": "nominal"}
            }
        }
    ],
    "config": base_config()
})

# -------------------- Chart 9 --------------------
write("heatmap_2007_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 440,
    "data": {"url": STATE_MAIN},
    "title": {
        "text": "Progress since 2007 has not removed the poverty gap",
        "subtitle": "Absolute poverty rate by state and survey year; states sorted by 2022 vulnerability"
    },
    "mark": {"type": "rect", "stroke": "white", "strokeWidth": 0.5},
    "encoding": {
        "x": {"field": "year", "type": "ordinal", "title": "Survey year"},
        "y": {"field": "state_geo", "type": "nominal", "title": None, "sort": {"field": "vulnerability_order", "op": "min", "order": "ascending"}},
        "color": {
            "field": "poverty_absolute",
            "type": "quantitative",
            "title": "Absolute poverty (%)",
            "scale": {"scheme": "oranges"}
        },
        "tooltip": [
            {"field": "state_geo", "type": "nominal", "title": "State"},
            {"field": "year", "type": "ordinal", "title": "Year"},
            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
            {"field": "vulnerability_group", "type": "nominal", "title": "2022 group"}
        ]
    },
    "config": base_config()
})

# -------------------- Chart 10 --------------------
write("slope_2007_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "width": "container",
    "height": 500,
    "data": {"url": SLOPE},
    "title": {
        "text": "Every state recorded higher nominal median income than in 2007",
        "subtitle": "Slope chart of median monthly household income, 2007 and 2022; hover a line for details"
    },
    "params": [
        {"name": "hover_state", "select": {"type": "point", "fields": ["state_geo"], "on": "pointerover", "clear": "pointerout"}}
    ],
    "layer": [
        {
            "mark": {"type": "line", "point": False},
            "encoding": {
                "x": {"field": "year", "type": "ordinal", "title": None},
                "y": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "axis": {"format": ","}},
                "detail": {"field": "state_geo", "type": "nominal"},
                "color": {
                    "condition": {"test": "datum.highlight_slope", "value": ACCENT},
                    "value": "#cfc6ba"
                },
                "opacity": {
                    "condition": [
                        {"param": "hover_state", "empty": False, "value": 1},
                        {"test": "datum.highlight_slope", "value": 0.9}
                    ],
                    "value": 0.35
                },
                "strokeWidth": {
                    "condition": {"param": "hover_state", "empty": False, "value": 3.5},
                    "value": 1.4
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "year", "type": "ordinal", "title": "Year"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
                    {"field": "income_change_pct_2007_2022", "type": "quantitative", "title": "2007-2022 change (%)", "format": ".1f"}
                ]
            }
        },
        {
            "mark": {"type": "circle", "filled": True, "size": 55},
            "encoding": {
                "x": {"field": "year", "type": "ordinal"},
                "y": {"field": "income_median", "type": "quantitative"},
                "detail": {"field": "state_geo", "type": "nominal"},
                "color": {
                    "condition": {"test": "datum.highlight_slope", "value": ACCENT},
                    "value": "#cfc6ba"
                },
                "opacity": {
                    "condition": [
                        {"param": "hover_state", "empty": False, "value": 1},
                        {"test": "datum.highlight_slope", "value": 0.9}
                    ],
                    "value": 0.35
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "year", "type": "ordinal", "title": "Year"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","}
                ]
            }
        },
        {
            "transform": [{"filter": "datum.year == 2022 && datum.highlight_slope"}],
            "mark": {"type": "text", "align": "left", "dx": 8, "fontSize": 11, "fontWeight": 600, "color": TEXT},
            "encoding": {
                "x": {"field": "year", "type": "ordinal"},
                "y": {"field": "income_median", "type": "quantitative"},
                "text": {"field": "state_geo", "type": "nominal"}
            }
        }
    ],
    "config": base_config()
})

# -------------------- Chart 11 --------------------
write("recovery_2019_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"url": RECOVERY},
    "title": {
        "text": "Most states recovered by 2022, but the gap remained",
        "subtitle": "Median income indexed to 2019 = 100; use the dropdown to highlight one state"
    },
    "params": [
        {
            "name": "State_selection",
            "value": None,
            "bind": {
                "input": "select",
                "options": STATE_OPTIONS,
                "labels": STATE_LABELS,
                "name": "Highlight state: "
            }
        }
    ],
    "facet": {
        "column": {
            "field": "vulnerability_group",
            "type": "nominal",
            "title": None,
            "sort": ["Highest vulnerability", "Watch closely", "Lower vulnerability"],
            "header": {"labelFontSize": 12, "labelFontWeight": 700, "labelColor": TEXT}
        }
    },
    "spec": {
        "width": 250,
        "height": 260,
        "layer": [
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "year", "type": "ordinal", "title": "Year"},
                    "y": {"field": "income_index_2019", "type": "quantitative", "title": "Median income index", "scale": {"zero": False}},
                    "detail": {"field": "state_geo", "type": "nominal"},
                    "color": {"field": "state_geo", "type": "nominal", "legend": None},
                    "opacity": {
                        "condition": {"test": "State_selection == null || datum.state_geo == State_selection", "value": 0.95},
                        "value": 0.18
                    },
                    "strokeWidth": {
                        "condition": {"test": "State_selection != null && datum.state_geo == State_selection", "value": 3.3},
                        "value": 1.4
                    },
                    "tooltip": [
                        {"field": "state_geo", "type": "nominal", "title": "State"},
                        {"field": "year", "type": "ordinal", "title": "Year"},
                        {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","},
                        {"field": "income_index_2019", "type": "quantitative", "title": "Index, 2019=100", "format": ".1f"},
                        {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"}
                    ]
                }
            },
            {
                "mark": {"type": "rule", "strokeDash": [4, 4], "color": MUTED},
                "encoding": {"y": {"datum": 100}}
            }
        ]
    },
    "resolve": {"scale": {"y": "shared"}},
    "config": base_config()
})

# -------------------- Chart 12 --------------------
y_sort = {"field": "vulnerability_score", "order": "descending"}
y_hidden = {"field": "state_geo", "type": "nominal", "sort": y_sort, "axis": None}
y_axis = {"field": "state_geo", "type": "nominal", "sort": y_sort, "axis": {"title": None, "labelLimit": 140}}

scorecard_spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"url": STATE_2022},
    "title": {
        "text": "Final scorecard: highest vulnerability combines lower income and higher poverty",
        "subtitle": "States sorted by 2022 vulnerability score; higher score means higher vulnerability"
    },
    "hconcat": [
        {
            "width": 150,
            "height": {"step": 24},
            "title": "State",
            "mark": {"type": "text", "align": "left", "baseline": "middle", "fontSize": 11, "fontWeight": 600, "color": TEXT},
            "encoding": {
                "y": y_axis,
                "text": {"field": "state_geo", "type": "nominal"},
                "tooltip": [{"field": "state_geo", "type": "nominal", "title": "State"}]
            }
        },
        {
            "width": 115,
            "height": {"step": 24},
            "title": "Median income",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {"field": "income_median", "type": "quantitative", "scale": {"scheme": "blues"}, "legend": None}
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "color": TEXT},
                    "encoding": {
                        "x": {"value": 58},
                        "y": y_hidden,
                        "text": {"field": "income_median", "type": "quantitative", "format": ","},
                        "tooltip": [{"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","}]
                    }
                }
            ]
        },
        {
            "width": 105,
            "height": {"step": 24},
            "title": "Abs. poverty",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {"field": "poverty_absolute", "type": "quantitative", "scale": {"scheme": "oranges"}, "legend": None}
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "color": TEXT},
                    "encoding": {
                        "x": {"value": 52},
                        "y": y_hidden,
                        "text": {"field": "poverty_absolute", "type": "quantitative", "format": ".1f"},
                        "tooltip": [{"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"}]
                    }
                }
            ]
        },
        {
            "width": 105,
            "height": {"step": 24},
            "title": "Rel. poverty",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {"field": "poverty_relative", "type": "quantitative", "scale": {"scheme": "purples"}, "legend": None}
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "color": TEXT},
                    "encoding": {
                        "x": {"value": 52},
                        "y": y_hidden,
                        "text": {"field": "poverty_relative", "type": "quantitative", "format": ".1f"},
                        "tooltip": [{"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "format": ".1f"}]
                    }
                }
            ]
        },
        {
            "width": 120,
            "height": {"step": 24},
            "title": "Vulnerability",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {
                            "field": "vulnerability_score",
                            "type": "quantitative",
                            "scale": {"domainMid": 0, "scheme": "redyellowgreen", "reverse": True},
                            "legend": None
                        }
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "fontWeight": 700, "color": TEXT},
                    "encoding": {
                        "x": {"value": 60},
                        "y": y_hidden,
                        "text": {"field": "vulnerability_score", "type": "quantitative", "format": ".2f"},
                        "tooltip": [
                            {"field": "vulnerability_rank", "type": "quantitative", "title": "Vulnerability rank"},
                            {"field": "vulnerability_score", "type": "quantitative", "title": "Score", "format": ".2f"}
                        ]
                    }
                }
            ]
        },
        {
            "width": 170,
            "height": {"step": 24},
            "title": "Category",
            "mark": {"type": "text", "align": "left", "baseline": "middle", "fontSize": 11, "fontWeight": 600},
            "encoding": {
                "x": {"value": 2},
                "y": y_hidden,
                "text": {"field": "vulnerability_group", "type": "nominal"},
                "color": {
                    "field": "vulnerability_group",
                    "type": "nominal",
                    "scale": {
                        "domain": ["Highest vulnerability", "Watch closely", "Lower vulnerability"],
                        "range": ["#b45309", "#9a6a2d", "#2f7d59"]
                    },
                    "legend": None
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "vulnerability_group", "type": "nominal", "title": "Category"}
                ]
            }
        }
    ],
    "spacing": 4,
    "config": base_config()
}
write("scorecard_2022.vg.json", scorecard_spec)

print("All chart specifications have been created in the js folder.")

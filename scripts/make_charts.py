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
HIGHEST_VULNERABILITY = "#7b3294"
WATCH_CLOSELY = "#d8a21b"
LOWER_VULNERABILITY = "#1f78b4"
SCORECARD_INCOME_RAMP = ["#f7fbff", "#e8f2fb", "#d7e8f6", "#c5ddf0", "#add0e8"]
SCORECARD_ABS_POVERTY_RAMP = ["#fff7ed", "#feedde", "#fde2c2", "#fbd3a3", "#f8c184"]
SCORECARD_REL_POVERTY_RAMP = ["#fcfbfd", "#f2eff8", "#e7e0f2", "#d8cdea", "#c6b8e0"]
VULNERABILITY_RAMP = ["#fbf9ff", "#f0eaf8", "#e4d9f1", "#d7c8ea", "#cab8e3"]

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
            "fontSize": 19,
            "fontWeight": 700,
            "lineHeight": 23,
            "subtitleFont": FONT,
            "subtitleFontSize": 13,
            "subtitleColor": MUTED,
            "subtitleLineHeight": 18,
            "subtitlePadding": 7,
            "offset": 18,
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
    path = JS / name
    rendered = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        print("unchanged", path)
        return
    path.write_text(rendered, encoding="utf-8")
    print("wrote", path)


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
    "autosize": {"type": "fit-x", "contains": "padding", "resize": True},
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
    "autosize": {"type": "fit", "contains": "padding", "resize": True},
    "width": "container",
    "height": 300,
    "title": {
        "text": ["Median household income is highest", "around the Klang Valley"],
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
            "legend": {
                "orient": "bottom",
                "direction": "horizontal",
                "gradientLength": 230,
                "format": ",.0f"
            }
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
    "autosize": {"type": "fit", "contains": "padding", "resize": True},
    "width": "container",
    "height": 300,
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
            "legend": {
                "orient": "bottom",
                "direction": "horizontal",
                "gradientLength": 230,
                "format": ".1f"
            }
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
write("map_bivariate_2022.vg.json", {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "autosize": {"type": "fit", "contains": "padding", "resize": True},
    "width": "container",
    "height": 430,
    "title": {
        "text": "Vulnerability remains concentrated in Sabah, Sarawak and Kelantan",
        "subtitle": "Score combines low median income, absolute poverty and relative poverty, 2022"
    },
    "projection": {"type": "equalEarth"},
    "data": {"url": MAP_URL, "format": {"type": "topojson", "feature": feature_name}},
    "transform": MAP_LOOKUP_TRANSFORM,
    "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 1},
    "encoding": {
        "color": {
            "field": "vulnerability_group",
            "type": "nominal",
            "title": "2022 vulnerability group",
            "scale": {
                "domain": ["Highest vulnerability", "Watch closely", "Lower vulnerability"],
                "range": ["#8a4b2a", "#d8a25e", "#5fa8a3"]
            },
            "legend": {
                "orient": "bottom",
                "direction": "horizontal",
                "columns": 3,
                "titleLimit": 260,
                "labelLimit": 180
            }
        },
        "tooltip": [
            {"field": "state_geo", "type": "nominal", "title": "State"},
            {"field": "vulnerability_group", "type": "nominal", "title": "Vulnerability group"},
            {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ",.0f"},
            {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
            {"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "format": ".1f"},
            {"field": "vulnerability_score", "type": "quantitative", "title": "Vulnerability score", "format": ".2f"}
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
                "x": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "axis": {"labelExpr": "format(datum.value, ',.0f')", "tickCount": 6}},
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
                "x": {"field": "income_median", "type": "quantitative", "axis": {"labelExpr": "format(datum.value, ',.0f')", "tickCount": 6}},
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
          "title": None,
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
      "fontSize": 19,
      "fontWeight": 700,
      "lineHeight": 23,
      "subtitleFont": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      "subtitleFontSize": 13,
      "subtitleColor": "#6b7280",
      "subtitleLineHeight": 18,
      "subtitlePadding": 7,
      "offset": 18,
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
      "disable": True
    },
    "view": {
      "stroke": None
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
                "x": {"field": "income_median", "type": "quantitative", "title": "Monthly household income (RM)", "axis": {"labelExpr": "format(datum.value, ',.0f')", "tickCount":7}},
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
                "x": {"field": "income_value", "type": "quantitative", "title": "Monthly household income (RM)", "axis": {"labelExpr": "format(datum.value, ',.0f')", "tickCount": 7}},
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
        "subtitle": "Bubble size shows relative poverty; hover a state for details"
    },
    "layer": [
        {
            "mark": {"type": "circle", "filled": True, "stroke": "white", "strokeWidth": 1},
            "encoding": {
                "x": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "axis": {"format": ",.0f"}},
                "y": {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "scale": {"zero": True}},
                "size": {
                    "field": "poverty_relative",
                    "type": "quantitative",
                    "title": "Relative poverty (%)",
                    "scale": {"range": [80, 800]},
                    "legend": {"format": ".1f"}
                },
                "color": {
                    "field": "vulnerability_group",
                    "type": "nominal",
                    "title": "2022 scorecard group",
                    "scale": {
                        "domain": ["Highest vulnerability", "Watch closely", "Lower vulnerability"],
                        "range": [HIGHEST_VULNERABILITY, WATCH_CLOSELY, LOWER_VULNERABILITY]
                    }
                },
                "opacity": {"value": 0.82},
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ",.0f"},
                    {"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"},
                    {"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "format": ".1f"},
                    {"field": "vulnerability_group", "type": "nominal", "title": "Scorecard group"}
                ]
            }
        },
        {
            "transform": [
                {"filter": "indexof(['Sabah', 'Kelantan', 'Sarawak'], datum.state_geo) >= 0"}
            ],
            "mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 9, "fontSize": 11, "color": TEXT},
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
        "subtitle": "Slope chart of median monthly household income, 2007 and 2022; hover for details"
    },
    "layer": [
        {
            "mark": {"type": "line", "point": False},
            "encoding": {
                "x": {"field": "year", "type": "ordinal", "title": None},
                "y": {"field": "income_median", "type": "quantitative", "title": "Median income (RM/month)", "axis": {"format": ",.0f"}},
                "detail": {"field": "state_geo", "type": "nominal"},
                "color": {
                    "condition": {"test": "datum.highlight_slope", "value": ACCENT},
                    "value": "#cfc6ba"
                },
                "opacity": {
                    "condition": {"test": "datum.highlight_slope", "value": 0.9},
                    "value": 0.35
                },
                "strokeWidth": {
                    "condition": {"test": "datum.highlight_slope", "value": 2.6},
                    "value": 1.4
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "year", "type": "ordinal", "title": "Year"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ",.0f"},
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
                    "condition": {"test": "datum.highlight_slope", "value": 0.9},
                    "value": 0.35
                },
                "tooltip": [
                    {"field": "state_geo", "type": "nominal", "title": "State"},
                    {"field": "year", "type": "ordinal", "title": "Year"},
                    {"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ",.0f"}
                ]
            }
        },
        {
            "transform": [
                {"filter": "datum.year == 2022 && indexof(['Putrajaya', 'Kuala Lumpur', 'Sabah', 'Kelantan'], datum.state_geo) >= 0"}
            ],
            "mark": {"type": "text", "align": "left", "dx": 8, "fontSize": 11, "color": TEXT},
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
        "width": 330,
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
            "width": 190,
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
            "width": 145,
            "height": {"step": 24},
            "title": "Median income",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {"field": "income_median", "type": "quantitative", "scale": {"range": SCORECARD_INCOME_RAMP}, "legend": None}
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "color": TEXT},
                    "encoding": {
                        "x": {"value": 72},
                        "y": y_hidden,
                        "text": {"field": "income_median", "type": "quantitative", "format": ","},
                        "tooltip": [{"field": "income_median", "type": "quantitative", "title": "Median income (RM)", "format": ","}]
                    }
                }
            ]
        },
        {
            "width": 135,
            "height": {"step": 24},
            "title": "Abs. poverty",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {"field": "poverty_absolute", "type": "quantitative", "scale": {"range": SCORECARD_ABS_POVERTY_RAMP}, "legend": None}
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "color": TEXT},
                    "encoding": {
                        "x": {"value": 68},
                        "y": y_hidden,
                        "text": {"field": "poverty_absolute", "type": "quantitative", "format": ".1f"},
                        "tooltip": [{"field": "poverty_absolute", "type": "quantitative", "title": "Absolute poverty (%)", "format": ".1f"}]
                    }
                }
            ]
        },
        {
            "width": 135,
            "height": {"step": 24},
            "title": "Rel. poverty",
            "layer": [
                {
                    "mark": {"type": "rect", "height": 20},
                    "encoding": {
                        "y": y_hidden,
                        "color": {"field": "poverty_relative", "type": "quantitative", "scale": {"range": SCORECARD_REL_POVERTY_RAMP}, "legend": None}
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "color": TEXT},
                    "encoding": {
                        "x": {"value": 68},
                        "y": y_hidden,
                        "text": {"field": "poverty_relative", "type": "quantitative", "format": ".1f"},
                        "tooltip": [{"field": "poverty_relative", "type": "quantitative", "title": "Relative poverty (%)", "format": ".1f"}]
                    }
                }
            ]
        },
        {
            "width": 145,
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
                            "scale": {"range": VULNERABILITY_RAMP},
                            "legend": None
                        }
                    }
                },
                {
                    "mark": {"type": "text", "align": "center", "baseline": "middle", "fontSize": 11, "fontWeight": 700, "color": TEXT},
                    "encoding": {
                        "x": {"value": 72},
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
            "width": 230,
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
                        "range": [HIGHEST_VULNERABILITY, WATCH_CLOSELY, LOWER_VULNERABILITY]
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

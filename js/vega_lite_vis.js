const charts = [
  ["#national_context", "js/national_context.vg.json"],
  ["#map_income_2022", "js/map_income_2022.vg.json"],
  ["#map_poverty_2022", "js/map_poverty_2022.vg.json"],
  ["#map_bivariate_2022", "js/map_bivariate_2022.vg.json"],
  ["#rank_income_2022", "js/rank_income_2022.vg.json"],
  ["#rank_poverty_2022", "js/rank_poverty_2022.vg.json"],
  ["#dumbbell_mean_median_2022", "js/dumbbell_mean_median_2022.vg.json"],
  ["#scatter_income_poverty_2022", "js/scatter_income_poverty_2022.vg.json"],
  ["#heatmap_2007_2022", "js/heatmap_2007_2022.vg.json"],
  ["#slope_2007_2022", "js/slope_2007_2022.vg.json"],
  ["#recovery_2019_2022", "js/recovery_2019_2022.vg.json"],
  ["#scorecard_2022", "js/scorecard_2022.vg.json"]
];

charts.forEach(([selector, spec]) => {
  vegaEmbed(selector, spec, {
    actions: false,
    renderer: "svg"
  }).catch(error => {
    console.error(`Could not load ${spec}`, error);
  });
});

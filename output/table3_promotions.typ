#figure([
#table(
  columns: (auto, 1fr, 1fr), align: (left, center, center),
  column-gutter: (0em, 0.5em),
  stroke: none, row-gutter: 0.2em,
  table.hline(stroke: 0.08em),
  [], [#table.cell(colspan: 2)[Promotion]],
  table.hline(stroke: 0.03em, start: 1, end: 3),
  [], [#table.cell(colspan: 1)[OLS]], [#table.cell(colspan: 1)[Probit]],
  table.hline(stroke: 0.03em, start: 1, end: 2),
  table.hline(stroke: 0.03em, start: 2, end: 3),
  [], [(1)], [(2)],
  table.hline(stroke: 0.05em),
  table.hline(stroke: 0.03em),
  [Years of Tenure], [0.001 \ (0.001)], [0.003 \ (0.003)],
  [Female], [0.009 \ (0.021)], [0.027 \ (0.063)],
  [Worker Type=White Collar], [0.125\*\*\* \ (0.022)], [0.379\*\*\* \ (0.066)],
  table.hline(stroke: 0.03em),
  table.hline(stroke: 0.03em),
  [Observations], [1,800], [1,800],
  [$R^2$], [0.019], [-],
  [Pseudo $R^2$], [-], [0.016],
  table.hline(stroke: 0.08em),
  [#table.cell(colspan: 3)[#text(size: 10pt)[Significance levels: \* p \< 0.1, \*\* p \< 0.05, \*\*\* p \< 0.01. Format of coefficient cell: Coefficient   (Std. Error)]]],
)
], caption: [Predicting Promotions])
<tab:promotions>
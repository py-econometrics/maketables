#set page(paper: "a4")

#figure([
#table(
  columns: (auto, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr), align: (left, center, center, center, center, center, center),
  column-gutter: (0em, 0em, 0em, 0.5em, 0em, 0em),
  stroke: none, row-gutter: 0.2em,
  table.hline(stroke: 0.08em),
  [], [#table.cell(colspan: 3)[Blue Collar]], [#table.cell(colspan: 3)[White Collar]],
  table.hline(stroke: 0.03em, start: 1, end: 4),
  table.hline(stroke: 0.03em, start: 4, end: 7),
  [], [N], [Mean], [Std. Dev.], [N], [Mean], [Std. Dev.],
  table.hline(stroke: 0.05em),
  [#table.cell(colspan: 7)[*Female*]],
  table.hline(stroke: 0.03em),
  [Wage], [357.00], [53,899.74], [24679.29], [530.00], [65,614.76], [27897.84],
  [Age], [357.00], [41.10], [10.96], [530.00], [41.79], [11.02],
  [Years of Tenure], [357.00], [17.86], [11.19], [530.00], [18.59], [11.08],
  table.hline(stroke: 0.03em),
  [#table.cell(colspan: 7)[*Male*]],
  table.hline(stroke: 0.03em),
  [Wage], [368.00], [54,360.28], [26129.05], [545.00], [71,399.23], [29204.37],
  [Age], [368.00], [39.83], [11.14], [545.00], [40.20], [11.17],
  [Years of Tenure], [368.00], [16.73], [11.15], [545.00], [17.10], [11.23],
  table.hline(stroke: 0.08em),
  [#table.cell(colspan: 7)[#text(size: 9pt)[]]],
)
], caption: [Descriptive statistics by worker type and gender])
<tab:descriptives>

#figure([
#table(
  columns: (auto, 1fr, 1fr, 1fr, 1fr), align: (left, center, center, center, center),
  column-gutter: (0em, 0em, 0.5em, 0em),
  stroke: none, row-gutter: 0.2em,
  table.hline(stroke: 0.08em),
  [], [#table.cell(colspan: 2)[ln(Wage)]], [#table.cell(colspan: 2)[Wage]],
  table.hline(stroke: 0.03em, start: 1, end: 3),
  table.hline(stroke: 0.03em, start: 3, end: 5),
  [], [(1)], [(2)], [(3)], [(4)],
  table.hline(stroke: 0.05em),
  table.hline(stroke: 0.03em),
  [Age], [0.005\*\*\* \ (0.001)], [0.007\*\*\* \ (0.001)], [340.031\*\*\* \ (59.661)], [422.053\*\*\* \ (83.182)],
  [Female], [-0.057\*\* \ (0.023)], [0.051 \ (0.086)], [-4128.632\*\*\* \ (1323.781)], [2759.371 \ (5045.686)],
  [Age $times$ Female], [], [-0.003 \ (0.002)], [], [-168.821 \ (119.337)],
  [Intercept], [10.748\*\*\* \ (0.044)], [10.697\*\*\* \ (0.059)], [50913.384\*\*\* \ (2563.005)], [47628.477\*\*\* \ (3457.930)],
  table.hline(stroke: 0.03em),
  table.hline(stroke: 0.03em),
  [Observations], [1,800], [1,800], [1,800], [1,800],
  [$R^2$], [0.018], [0.019], [0.022], [0.023],
  table.hline(stroke: 0.08em),
  [#table.cell(colspan: 5)[#text(size: 9pt)[Significance levels: \* p \< 0.1, \*\* p \< 0.05, \*\*\* p \< 0.01. Format of coefficient cell: Coefficient   (Std. Error)]]],
)
], caption: [Wage regressions])
<tab:regressions>

#figure([
#table(
  columns: (auto, 1fr, 1fr, 1fr, 1fr), align: (left, center, center, center, center),
  column-gutter: (0em, 0em, 0.5em, 0em),
  stroke: none, row-gutter: 0.2em,
  table.hline(stroke: 0.08em),
  [], [#table.cell(colspan: 2)[ln(Wage)]], [#table.cell(colspan: 2)[Wage]],
  table.hline(stroke: 0.03em, start: 1, end: 3),
  table.hline(stroke: 0.03em, start: 3, end: 5),
  [], [(1)], [(2)], [(3)], [(4)],
  table.hline(stroke: 0.05em),
  table.hline(stroke: 0.03em),
  [Age], [0.005\*\*\* \ (0.001)], [0.007\*\*\* \ (0.001)], [340.031\*\*\* \ (59.661)], [422.053\*\*\* \ (83.182)],
  [Female], [-0.057\*\* \ (0.023)], [0.051 \ (0.086)], [-4128.632\*\*\* \ (1323.781)], [2759.371 \ (5045.686)],
  [Age $times$ Female], [], [-0.003 \ (0.002)], [], [-168.821 \ (119.337)],
  [Intercept], [10.748\*\*\* \ (0.044)], [10.697\*\*\* \ (0.059)], [50913.384\*\*\* \ (2563.005)], [47628.477\*\*\* \ (3457.930)],
  table.hline(stroke: 0.03em),
  table.hline(stroke: 0.03em),
  [Observations], [1,800], [1,800], [1,800], [1,800],
  [$R^2$], [0.018], [0.019], [0.022], [0.023],
  table.hline(stroke: 0.08em),
  [#table.cell(colspan: 5)[#text(size: 9pt)[Significance levels: \* p \< 0.1, \*\* p \< 0.05, \*\*\* p \< 0.01. Format of coefficient cell: Coefficient   (Std. Error)]]],
)
], caption: [Wage regressions])
<tab:promotions>
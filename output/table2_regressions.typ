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
  [#table.cell(colspan: 5)[#text(size: 10pt)[Significance levels: \* p \< 0.1, \*\* p \< 0.05, \*\*\* p \< 0.01. Format of coefficient cell: Coefficient   (Std. Error)]]],
)
], caption: [Wage regressions])
<tab:regressions>
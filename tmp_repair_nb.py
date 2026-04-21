import json
from pathlib import Path

p = Path("docs/examples/quartoExample2.ipynb")
d = json.loads(p.read_text(encoding="utf-8"))

d.setdefault("metadata", {})
d["metadata"]["kernelspec"] = {
    "display_name": "docs",
    "language": "python",
    "name": "python3",
}
d["metadata"]["language_info"] = {"name": "python", "version": "3.13.7"}
d["nbformat"] = 4
d["nbformat_minor"] = 5

cells = d.get("cells", [])
if cells:
    cells[0]["cell_type"] = "raw"
    cells[0].setdefault("metadata", {})["language"] = "raw"

for c in cells:
    if c.get("cell_type") != "code":
        continue
    src = "\n".join(c.get("source", []))
    if "mt.DTable(" in src and ".make(type='quarto')" not in src:
        src += "\n.make(type='quarto')"
    if "mt.ETable(" in src and ".make(type='quarto')" not in src:
        src += "\n.make(type='quarto')"
    c["source"] = src.split("\n")

p.write_text(json.dumps(d, indent=4, ensure_ascii=False), encoding="utf-8")
print("repaired", p)

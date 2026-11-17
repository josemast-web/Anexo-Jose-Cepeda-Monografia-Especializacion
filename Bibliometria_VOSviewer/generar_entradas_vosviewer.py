# Builds VOSviewer inputs (RIS corpora, thesaurus, network files) from the review workbooks. Python 3.13+
import openpyxl, re, collections, itertools, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "Bibliometria_VOSviewer"
wb = openpyxl.load_workbook(ROOT / "Deduplicacion_y_cribado.xlsx", read_only=True)
rows = [r for r in wb["Cribado"].iter_rows(min_row=2, values_only=True) if r[0]]
ID, TI, PY, AU, SO, DOI, AB, DEC_TC = 0, 1, 2, 3, 4, 5, 6, 12

def ris(recs, path):
    # One RIS record per study; abstract only when the original abstract exists
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in recs:
            f.write("TY  - JOUR\n")
            for a in [x.strip() for x in re.split(r";", r[AU] or "") if x.strip()]:
                f.write(f"AU  - {a}\n")
            f.write(f"TI  - {' '.join(str(r[TI]).split())}\n")
            if r[PY]: f.write(f"PY  - {r[PY]}\n")
            if r[SO]: f.write(f"JO  - {r[SO]}\n")
            if r[AB]: f.write(f"AB  - {' '.join(str(r[AB]).split())}\n")
            if r[DOI]: f.write(f"DO  - {r[DOI]}\n")
            f.write(f"N1  - {r[ID]}\nER  - \n\n")
    return len(recs)

inc = [r for r in rows if r[DEC_TC] == "Incluido"]
n1 = ris(rows, OUT / "corpus_781_cribados.ris")
n2 = ris(inc, OUT / "corpus_58_incluidos.ris")
print("RIS:", n1, "cribados;", sum(1 for r in rows if r[AB]), "con resumen;", n2, "incluidos")

# Thesaurus: merge spelling variants and drop generic terms (empty 'replace by' = ignore)
merge = {"machine learning technique": "machine learning", "machine learning model": "machine learning",
         "machine learning algorithm": "machine learning", "ml": "machine learning",
         "long short term memory": "lstm", "long short-term memory": "lstm", "lstm model": "lstm",
         "random forest model": "random forest", "rf": "random forest",
         "arima model": "arima", "sarima model": "sarima", "artificial neural network": "neural network",
         "ann": "neural network", "support vector machine": "svm", "support vector regression": "svr",
         "dengue fever": "dengue", "dengue virus": "dengue", "denv": "dengue",
         "dengue case": "dengue cases", "number of dengue case": "dengue cases",
         "precipitation": "rainfall", "climate variable": "climatic variables", "climatic variable": "climatic variables",
         "meteorological variable": "climatic variables", "weather variable": "climatic variables",
         "aedes aegypti mosquito": "aedes aegypti", "ae. aegypti": "aedes aegypti"}
ignore = ["study", "paper", "article", "result", "method", "approach", "analysis", "data", "use", "research",
          "author", "purpose", "objective", "aim", "conclusion", "finding", "year", "period", "case", "number",
          "work", "present study", "this study", "addition", "order", "part", "term", "type", "value", "role",
          "elsevier", "copyright", "rights reserved", "ieee", "springer", "background", "introduction"]
with open(OUT / "thesaurus_terminos.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write("label\treplace by\n")
    for k, v in merge.items(): f.write(f"{k}\t{v}\n")
    for k in ignore: f.write(f"{k}\t\n")

# Network 1: predictor co-occurrence in the 58 included studies (source of Table 6)
ws = openpyxl.load_workbook(ROOT / "Sintesis_evidencia_dengue_58_incluidos_APA7.xlsx", read_only=True)["Detalle predictores"]
pred = collections.defaultdict(set); fam = {}
for r in ws.iter_rows(min_row=3, values_only=True):
    if r[0]: pred[r[0]].add(r[2]); fam[r[2]] = r[3]
famc = {"climática": 1, "epidemiológica": 2}
def network(study_items, prefix, cluster_of):
    occ = collections.Counter(i for s in study_items.values() for i in s)
    labels = sorted(occ, key=lambda x: -occ[x]); ids = {l: n + 1 for n, l in enumerate(labels)}
    with open(OUT / f"{prefix}_map.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tlabel\tcluster\tweight<Estudios>\n")
        for l in labels: f.write(f"{ids[l]}\t{l}\t{cluster_of(l)}\t{occ[l]}\n")
    links = collections.Counter()
    for s in study_items.values():
        for a, b in itertools.combinations(sorted(s, key=lambda x: ids[x]), 2): links[(ids[a], ids[b])] += 1
    with open(OUT / f"{prefix}_network.txt", "w", encoding="utf-8", newline="\n") as f:
        for (a, b), w in sorted(links.items()): f.write(f"{a}\t{b}\t{w}\n")
    return occ, links
occ, links = network(pred, "red_predictores", lambda l: famc.get(fam.get(l, ""), 3))
print("Predictores:", len(pred), "estudios;", dict(occ.most_common(4)), ";", len(links), "enlaces")

# Network 2: Latin American and Caribbean countries per included study (Section 8.2)
ex = list(wb["Extraccion"].iter_rows(values_only=True)); h = [i for i, r in enumerate(ex) if r[0] == "ID"][0]
incid = {r[ID] for r in inc}
C = {"Brasil": r"brasil|brazil", "Perú": r"per[uú]\b|iquitos", "Puerto Rico": r"puerto rico|san juan", "México": r"m[eé]xico",
     "Colombia": r"colombia|medell|bucaramanga|barranquilla", "Costa Rica": r"costa rica", "Panamá": r"panam[aá]",
     "Paraguay": r"paraguay", "Venezuela": r"venezuela", "Argentina": r"argentina", "Bolivia": r"bolivia",
     "Ecuador": r"ecuador", "Nicaragua": r"nicaragua", "El Salvador": r"el salvador", "Honduras": r"honduras",
     "Guatemala": r"guatemala", "Uruguay": r"uruguay", "Barbados": r"barbados"}
pais = {r[0]: {k for k, p in C.items() if re.search(p, (r[4] or "").lower())} for r in ex[h + 1:] if r[0] in incid}
occ2, links2 = network(pais, "red_paises", lambda l: 1)
print("Países:", dict(occ2.most_common(6)), ";", len(links2), "enlaces")

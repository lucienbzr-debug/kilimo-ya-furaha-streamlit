# -*- coding: utf-8 -*-
"""Étape 1 : nettoyage de l'export KoBo brut (placé dans data/raw/, jamais versionné).
Produit dans data/interim/ (jamais versionné) : _base.pkl, base nettoyée nominative et statistiques.
Étape suivante : scripts/preparer_donnees.py (export anonymisé pour l'application).
"""
import glob, json, re, os
import numpy as np, pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "interim"); os.makedirs(OUT, exist_ok=True)
raw = pd.read_excel(sorted(glob.glob(os.path.join(ROOT, "data", "raw", "*.xlsx")))[-1])
C = list(raw.columns)
col = lambda prefix: next(c for c in C if c.startswith(prefix))

# ---- Fusion des 3 fiches de l'ancienne version du formulaire (colonnes décalées)
old = raw["__version__"] == "vfeFWnMVQFAcQWFnfYjqN8"
for suffix in ["", "/Cobaille", "/Lapin", "/Poule", "/autres"]:
    a, b = "8.2. Si Oui, Quel type de petit élevage?" + suffix, "8.2. Si Oui, Quel type de petit élevage?" + suffix + ".1"
    raw.loc[old & raw[a].isna(), a] = raw.loc[old & raw[a].isna(), b]
m72 = [c for c in C if c.startswith("7.2. Si maraichers") and not c.endswith(".1")]
for a in m72:
    b = a + ".1"
    if b in raw: raw.loc[raw[a].isna() & raw[b].notna(), a] = raw.loc[raw[a].isna() & raw[b].notna(), b]
cons = "10.1. Consentement à l'utilisation des données"
raw.loc[raw[cons].isna(), cons] = raw.loc[raw[cons].isna(), "9.1. Consentement à l'utilisation des données"]

num = lambda s: pd.to_numeric(s, errors="coerce")
d = pd.DataFrame({"id": raw["_index"]})
d["date"] = pd.to_datetime(raw["start"])
d["duree_min"] = ((pd.to_datetime(raw["end"]) - d["date"]).dt.total_seconds() / 60).round(1)
d["enqueteur"] = raw[col("1.1.")].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
tel_enq = raw[col("1.2.")].astype(str).str.replace(r"\.0$", "", regex=True)
canon = d.assign(t=tel_enq).groupby("t")["enqueteur"].agg(lambda s: max(s, key=lambda n: (list(s).count(n), len(n))))
d["enqueteur"] = np.where(tel_enq != "nan", tel_enq.map(canon), d["enqueteur"])
# un même enquêteur peut avoir saisi 2 numéros : on regroupe les noms dont les 2 premiers mots se recoupent
first = d["enqueteur"].str.split().str[:2].str.join(" ")
d["enqueteur"] = first.map(d.groupby(first)["enqueteur"].agg(lambda s: s.value_counts().index[0]))
d["territoire"] = raw[col("2.1.")]

def groupement(g, terr):
    g = str(g).strip().lower()
    if "malambo" in g or "malanbo" in g or g == "mala": return "Malambo"
    if "lume" in g: return "Lume"
    if "bukenye" in g: return "Bukenye"
    if any(k in g for k in ["buyora", "buya", "buyira", "luotu"]): return "Buyora/Luotu"
    if "bolema" in g: return "Bolema"
    if "kalembo" in g: return "Kalembo"
    if "rughetsi" in g: return "Malambo"
    return "Non précisé"
d["groupement"] = [groupement(g, t) for g, t in zip(raw[col("2.2.")], d["territoire"])]

def village(v):
    v = re.sub(r"[.,;]+$", "", str(v).strip()).title()
    v = re.sub(r"\s+", " ", v)
    if re.search(r"ru?w?e?n?zori|ruwenzi", v, re.I): return "Q. Ruwenzori"
    if re.fullmatch(r"Rug?h?etsi", v): return "Rughetsi"
    if v.startswith("Luotu/"): return "Luotu"
    if "Lume" in v: return "Lume"
    return v
d["village"] = raw[col("2.3.")].map(village)
d["lat"], d["lon"] = num(raw["_2.5. Coordonnées GPS_latitude"]), num(raw["_2.5. Coordonnées GPS_longitude"])
d["gps_precision_m"] = num(raw["_2.5. Coordonnées GPS_precision"])
d["nom_chef"] = raw[col("3.1.")].astype(str).str.strip()
d["sexe"] = raw[col("3.2.")]
d["age"] = raw[col("3.3.")]
d["telephone"] = raw[col("3.4.")].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
d["membre_op"] = raw[col("4.1.")]
d["type_structure"] = raw[col("4.2.")]
d["statut"] = raw[col("5.1.")].replace({"Ménagé retourné": "Ménage retourné", "Non": "Autre (ni retourné ni accueil)"})
d["duree_retour"] = raw[col("5.2.")]
d["nb_menages_accueillis"] = num(raw[col("5.3.")])
comp = {"hommes": "5.5.", "femmes": "5.6.", "garcons": "5.7.", "filles": "5.8."}
for k, p in comp.items(): d[k] = num(raw[col(p)])
d["handicapes"] = num(raw[col("5.9.")]).fillna(0)
tot_decl = num(raw[col("5.4.")]); somme = d[list(comp)].sum(axis=1, min_count=1)
d["taille_incoherente"] = (somme.notna()) & (somme != tot_decl)
d["taille_menage"] = np.where(somme.notna() & (somme > 0), somme, tot_decl)  # règle : le détail prime sur le total
d["possede_terre"] = raw[col("6.1.")]
sup = num(raw[col("6.2.")]); supl = num(raw[col("6.4.")])
d["sup_aberrante"] = (sup > 5) | (supl > 5)
d["superficie_ha"] = sup.where(sup <= 5)
d["loue_terre"] = raw[col("6.3.")]
d["superficie_louee_ha"] = supl.where(supl <= 5)
d["superficie_totale_ha"] = d[["superficie_ha", "superficie_louee_ha"]].sum(axis=1, min_count=1)

CULT = {"Haricot": "Haricot", "Maïs ": "Maïs", "Riz": "Riz", "Manioc": "Manioc", "Arachide": "Arachide",
        "Pomme de terre": "Pomme de terre", "Soja": "Soja", "Maraîchage": "Maraîchage", "Autres": "Autres cultures"}
for k, v in CULT.items(): d["c_" + v] = num(raw["7.1. Cultures pratiquées ou exploitées dans son champs/" + k])
MAR = {"Oignons Blanc ": "Oignon blanc", "Oignons Rouge": "Oignon rouge", "Aubergine violette": "Aubergine violette",
       "Aubergine Verte": "Aubergine verte", "Poireaux ": "Poireau", "Amarante": "Amarante", "Epinard": "Épinard",
       "Tomate": "Tomate", "Choux": "Chou", "Poivron": "Poivron", "Morel/ Mboga buchungu": "Morelle"}
for k, v in MAR.items(): d["m_" + v] = num(raw["7.2. Si maraichers, Citez les par ordre d'appréciation/" + k])
d["eleve"] = raw[col("8.1.")]
for k in ["Cobaille", "Lapin", "Poule", "autres"]:
    d["e_" + k.replace("Cobaille", "Cobaye").replace("autres", "Autres")] = num(raw["8.2. Si Oui, Quel type de petit élevage?/" + k])
autres = raw["Les quels"].fillna("").str.lower()
for k, pat in {"Chèvre": r"ch[eèé]vre|chevres|mbuzi", "Porc": r"porc|cochon", "Canard": r"canard", "Mouton": r"mouton"}.items():
    d["e_" + k] = autres.str.contains(pat).astype(int).where(d["eleve"] == "Oui")

def multi(prefix, labels, tag):
    for c in C:
        if not c.startswith(prefix): continue
        for lab, short in labels.items():
            if c.rstrip().endswith("/" + lab): d[tag + short] = num(raw[c])
multi("9.1.", {"Agriculture": "Agriculture", "Elevage": "Élevage", "Transformation des produits agricoles": "Transformation", "Service/commerce": "Commerce"}, "a_")
multi("9.2.", {"Agriculture": "Agriculture", "Elevage": "Élevage", "Transformation des produits agricoles": "Transformation", "Service/commerce": "Commerce"}, "p_")
multi("9.3.", {"Agriculture": "Agriculture", "Elevage": "Élevage", "Transformation des produits agricoles": "Transformation", "Service/commerce": "Commerce"}, "r_")
multi("9.6.", {"Manque de moyens": "Manque de moyens", "Formations": "Manque de formation", "Accès au marché": "Accès au marché", "Autres à préciser": "Autres"}, "f_")
d["souhait_txt"] = raw[col("9.4.")].fillna("").astype(str)
d["motivation_txt"] = raw[col("9.5.")].fillna("").astype(str)
d["consentement"] = raw[cons]

# ---- Codage thématique des réponses libres
SOUHAITS = {"Maraîchage": r"mara[iî]ch|l[ée]gume|oignon|tomate|chou|poireau|aubergine|amarante|[ée]pinard|poivron",
            "Haricot": r"haricot", "Soja": r"soja|soya", "Maïs": r"ma[iï]s", "Riz": r"\briz\b", "Manioc": r"manioc",
            "Arachide": r"arachide", "Pomme de terre": r"pomme", "Élevage chèvre": r"ch[eèé]vre", "Élevage porc": r"porc|cochon",
            "Élevage volaille": r"poule|volaille|canard|aviculture", "Élevage cobaye/lapin": r"cobay|cobaille|lapin",
            "Élevage (général)": r"[ée]levage", "Commerce / transformation": r"commerce|transform|vente|petit commerce"}
MOTIFS = {"Générer des revenus": r"argent|revenu|gagn|b[ée]n[ée]fice|profit|rentab|[ée]conom|financ",
          "Nourrir le ménage": r"nourri|manger|alimenta|faim|famine|nutrition|consomm|survie|subsist",
          "Améliorer les conditions de vie": r"am[ée]lior|condition|la vie|besoin|d[ée]pendre|autonom|g[ée]r[ée] la famille",
          "Sortir de la pauvreté": r"pauvre|mis[eè]re|d[ée]velopp",
          "Scolarité des enfants": r"[ée]col|scolar|minerval|enfant",
          "Santé / soins": r"soin|sant[ée]|m[ée]dic|h[ôo]pital",
          "Rapidité du cycle": r"rapide|court|peu de temps|vite|mois",
          "Accroître la production": r"production|rendement|semence|intrant|engrais"}
for k, p in SOUHAITS.items(): d["s_" + k] = d["souhait_txt"].str.lower().str.contains(p).astype(int)
for k, p in MOTIFS.items(): d["mo_" + k] = d["motivation_txt"].str.lower().str.contains(p).astype(int)

# ---- Contrôles qualité
d["dup_nom_village"] = d.assign(k=d.nom_chef.str.lower().str.replace(r"\s+", " ", regex=True)).duplicated(["k", "village"], keep=False)
d["tel_fictif"] = d.telephone.map(lambda t: bool(re.fullmatch(r"(\d)\1{2}0{6}|0+|nan|", t)))
tel_counts = d.telephone.map(d.telephone.value_counts())
d["tel_partage"] = (tel_counts > 1) & ~d.tel_fictif
d["duree_suspecte"] = d.duree_min < 5
d["gps_imprecis"] = d.gps_precision_m > 50
flags = ["dup_nom_village", "tel_fictif", "duree_suspecte", "gps_imprecis", "taille_incoherente", "sup_aberrante"]
d["nb_alertes"] = d[flags].sum(axis=1)

# ---- Score de vulnérabilité (0-8), critères pondérés à 1
d["v_femme"] = (d.sexe == "Femme").astype(int)
d["v_handicap"] = (d.handicapes > 0).astype(int)
d["v_sans_terre"] = (d.possede_terre == "Non").astype(int)
d["v_retour_recent"] = d.duree_retour.isin(["Moins de 6 mois", "6 à 12 mois"]).astype(int)
d["v_grande_taille"] = (d.taille_menage >= 9).astype(int)
d["v_non_membre_op"] = (d.membre_op == "Non").astype(int)
d["v_petite_surface"] = ((d.superficie_totale_ha.fillna(0) < 0.25)).astype(int)
d["v_accueil_lourd"] = (d.nb_menages_accueillis >= 2).astype(int)
VCRIT = [c for c in d if c.startswith("v_")]
d["score_vuln"] = d[VCRIT].sum(axis=1)
d["niveau_vuln"] = pd.cut(d.score_vuln, [-1, 2, 4, 9], labels=["Faible", "Modérée", "Élevée"]).astype(str)

# ---- Typologie des systèmes de production (k-means)
feat = [c for c in d if c.startswith("c_")] + ["e_Cobaye", "e_Lapin", "e_Poule", "e_Chèvre", "e_Porc"]
X = d[feat].fillna(0).copy(); X["terre"] = (d.possede_terre == "Oui").astype(int); X["surf"] = d.superficie_totale_ha.fillna(0).clip(0, 2)
Xs = StandardScaler().fit_transform(X)
km = KMeans(n_clusters=4, n_init=20, random_state=42).fit(Xs)
d["_cl"] = km.labels_
prof = X.assign(cl=km.labels_).groupby("cl").mean()
d.drop(columns=["_cl"], inplace=True)

def label_cluster(r):
    top_c = [c[2:] for c in r[[c for c in feat if c.startswith("c_")]].sort_values(ascending=False).index[:3]]
    return top_c
names = {}
for cl, r in prof.iterrows(): names[cl] = r
cl_desc = {cl: {"n": int((km.labels_ == cl).sum()), **{k: round(float(v), 3) for k, v in r.items()}} for cl, r in prof.iterrows()}
d["profil_id"] = km.labels_

# ---- Tests d'association (chi²) et V de Cramér
def cramer(a, b):
    t = pd.crosstab(a, b); chi2, p, dof, _ = chi2_contingency(t)
    n = t.values.sum(); v = np.sqrt(chi2 / (n * (min(t.shape) - 1)))
    return {"chi2": round(chi2, 1), "p": float(p), "v": round(float(v), 3), "table": t.to_dict()}
tests = {
    "Sexe × Possession de terre": cramer(d.sexe, d.possede_terre),
    "Sexe × Membre OP": cramer(d.sexe, d.membre_op),
    "Territoire × Statut du ménage": cramer(d.territoire, d.statut),
    "Territoire × Possession de terre": cramer(d.territoire, d.possede_terre),
    "Statut × Possession de terre": cramer(d.statut, d.possede_terre),
    "Âge × Membre OP": cramer(d.age, d.membre_op),
    "Durée du retour × Possession de terre": cramer(d.duree_retour.dropna(), d.loc[d.duree_retour.notna(), "possede_terre"]),
}

# ---- Nom des profils (règles sur les centres de classes, indépendantes de l'ordre k-means)
pc = prof[[c for c in feat if c.startswith("c_")]]
lab = {}
lab[pc["c_Riz"].idxmax()] = "Riziculteurs diversifiés"
lab[pc["c_Pomme de terre"].idxmax()] = "Maraîchers pomme de terre"
rest = [i for i in pc.index if i not in lab]
div = pc.loc[rest].sum(axis=1)
lab[div.idxmax()] = "Vivriers diversifiés + élevage"
lab[div.idxmin()] = "Petits producteurs peu diversifiés"
d["profil"] = d.profil_id.map(lab)
cl_desc = {lab[k]: v for k, v in cl_desc.items()}

d.to_pickle(os.path.join(OUT, "_base.pkl"))

# ---- Base nettoyée (Excel) : données, contrôles qualité, dictionnaire
base = d[d.consentement != "Non"].copy()
qual = d.groupby("enqueteur").agg(fiches=("id", "size"), duree_mediane_min=("duree_min", "median"),
                                  pct_duree_suspecte=("duree_suspecte", "mean"), pct_gps_imprecis=("gps_imprecis", "mean"),
                                  pct_taille_incoherente=("taille_incoherente", "mean"), alertes_moy=("nb_alertes", "mean")).reset_index()
with pd.ExcelWriter(os.path.join(OUT, "KYF_base_nettoyee.xlsx")) as xw:
    base.drop(columns=["profil_id"]).to_excel(xw, sheet_name="Base nettoyée", index=False)
    d[d.nb_alertes > 0][["id", "enqueteur", "groupement", "village", "nom_chef", "telephone"] + flags + ["nb_alertes"]].to_excel(xw, sheet_name="Fiches à vérifier", index=False)
    qual.round(3).to_excel(xw, sheet_name="Qualité enquêteurs", index=False)
    pd.DataFrame({"Règle": [
        "4 fiches sans consentement exclues de la base analysée",
        "3 fiches de l'ancienne version du formulaire réintégrées dans les colonnes principales",
        "Groupements et villages harmonisés (orthographe, ponctuation, variantes)",
        "Taille du ménage = somme hommes + femmes + garçons + filles quand le détail existe",
        "Superficies > 5 ha considérées comme aberrantes et mises à vide",
        "Durée d'entretien < 5 min signalée comme suspecte ; précision GPS > 50 m signalée",
        "Doublons signalés (même nom + même village), aucune fiche supprimée",
        "Score de vulnérabilité : 1 point par critère (femme cheffe, handicap, sans terre, retour < 12 mois, ménage ≥ 9 personnes, non membre OP, surface < 0,25 ha, accueille ≥ 2 ménages). Faible 0-2, Modérée 3-4, Élevée ≥ 5",
        "Profils de production : k-means (4 classes) sur cultures, élevage, accès et surface de terre",
    ]}).to_excel(xw, sheet_name="Règles de nettoyage", index=False)

# ---- Données du tableau de bord (anonymisées : ni nom, ni téléphone, ni GPS individuel)
def bits(prefix):
    cs = [c for c in base if c.startswith(prefix)]
    return [c[len(prefix):] for c in cs], base[cs].fillna(0).astype(int).astype(str).agg("".join, axis=1).tolist()
dims = {k: sorted(base[k].dropna().astype(str).unique().tolist()) for k in
        ["territoire", "groupement", "village", "sexe", "age", "statut", "duree_retour", "membre_op", "type_structure",
         "possede_terre", "loue_terre", "niveau_vuln", "profil", "enqueteur"]}
rows = []
bitsets = {p: bits(p) for p in ["c_", "m_", "e_", "a_", "p_", "r_", "f_", "s_", "mo_", "v_"]}
for i, (_, r) in enumerate(base.iterrows()):
    row = [dims[k].index(str(r[k])) if pd.notna(r[k]) else -1 for k in dims]
    row += [None if pd.isna(r.superficie_totale_ha) else round(float(r.superficie_totale_ha), 3),
            int(r.taille_menage) if pd.notna(r.taille_menage) else None, int(r.handicapes),
            int(r.score_vuln), r.date.strftime("%Y-%m-%d"), round(float(r.duree_min), 1), int(r.nb_alertes),
            int(np.nansum([r.garcons, r.filles])) if pd.notna(r.garcons) or pd.notna(r.filles) else None]
    row += [bitsets[p][1][i] for p in bitsets]
    rows.append(row)
g = base[(base.gps_precision_m <= 50) & base.lat.between(-1, 1) & base.lon.between(28.5, 30.5)]
vill = g.groupby("village").agg(lat=("lat", "median"), lon=("lon", "median"), n=("id", "size"),
                               vuln=("score_vuln", "mean"), terr=("territoire", "first")).reset_index()
vill = vill[vill.n >= 3].round(4)
dash = {"dims": dims, "fields": list(dims) + ["surf", "taille", "hand", "score", "date", "duree", "alertes", "enfants"] + [p for p in bitsets],
        "bitlabels": {p: bitsets[p][0] for p in bitsets}, "rows": rows,
        "villages": vill.to_dict("records"),
        "tests": {k: {kk: vv for kk, vv in v.items() if kk != "table"} for k, v in tests.items()},
        "clusters": cl_desc, "n_brut": int(len(d)), "n_exclus_consent": int((d.consentement == "Non").sum()),
        "qualite": {f: int(d[f].sum()) for f in flags + ["tel_partage"]}}
json.dump(dash, open(os.path.join(OUT, "dashboard_data.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), default=str)
json.dump({"clusters": cl_desc, "tests": {k: {kk: vv for kk, vv in v.items() if kk != "table"} for k, v in tests.items()}},
          open(os.path.join(OUT, "_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("ok", d.shape)

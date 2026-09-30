# -*- coding: utf-8 -*-
"""Étape 2 : export anonymisé pour l'application Streamlit.

Lit data/interim/_base.pkl (produit par scripts/nettoyage.py) et écrit data/menages_kyf.csv.
Retirés : noms, téléphones, coordonnées GPS, réponses libres, identifiants KoBo, noms des enquêteurs
(remplacés par un code). Les villages de moins de 10 ménages sont regroupés sous « Autres villages ».
"""
import os
import re
import unicodedata

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_pickle(os.path.join(ROOT, "data", "interim", "_base.pkl"))
d = d[d.consentement != "Non"].sort_values("date").reset_index(drop=True)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# Codes enquêteurs, du plus grand au plus petit nombre de fiches
codes = {e: f"E{i:02d}" for i, e in enumerate(d.enqueteur.value_counts().index, 1)}

vc = d.village.value_counts()
out = pd.DataFrame({
    "id": range(1, len(d) + 1),
    "date": d.date.dt.strftime("%Y-%m-%d"),
    "territoire": d.territoire,
    "groupement": d.groupement,
    "village": d.village.where(d.village.map(vc) >= 10, "Autres villages"),
    "sexe": d.sexe,
    "age": d.age,
    "statut": d.statut,
    "duree_retour": d.duree_retour,
    "nb_menages_accueillis": d.nb_menages_accueillis,
    "membre_op": d.membre_op,
    "type_structure": d.type_structure,
    "taille_menage": d.taille_menage,
    "hommes": d.hommes, "femmes": d.femmes, "garcons": d.garcons, "filles": d.filles,
    "handicapes": d.handicapes,
    "possede_terre": d.possede_terre,
    "loue_terre": d.loue_terre,
    "superficie_ha": d.superficie_ha,
    "superficie_louee_ha": d.superficie_louee_ha,
    "superficie_totale_ha": d.superficie_totale_ha,
    "eleve": d.eleve,
    "score_vuln": d.score_vuln,
    "niveau_vuln": d.niveau_vuln,
    "profil": d.profil,
    "enqueteur": d.enqueteur.map(codes),
    "duree_min": d.duree_min,
    "gps_precis": ~d.gps_imprecis,
})
for flag in ["duree_suspecte", "gps_imprecis", "taille_incoherente", "sup_aberrante", "dup_nom_village", "tel_partage"]:
    out["alerte_" + flag] = d[flag].astype(int)
out["nb_alertes"] = d.nb_alertes

PREFIX = {"c_": "culture_", "m_": "maraich_", "e_": "elevage_", "a_": "activite_", "r_": "rentable_",
          "f_": "frein_", "s_": "souhait_", "mo_": "motif_", "v_": "critere_"}
for col in d.columns:
    for p, new in PREFIX.items():
        if col.startswith(p):
            out[new + slug(col[len(p):])] = d[col].fillna(0).astype(int)
            break

for c in ["taille_menage", "hommes", "femmes", "garcons", "filles", "handicapes", "nb_menages_accueillis"]:
    out[c] = out[c].astype("Int64")

path = os.path.join(ROOT, "data", "menages_kyf.csv")
out.to_csv(path, index=False, encoding="utf-8")
print(f"{len(out)} ménages, {out.shape[1]} colonnes → {path}")

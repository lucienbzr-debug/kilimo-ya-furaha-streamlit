"""Chargement des données anonymisées, libellés et fonctions de calcul partagées par les pages."""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "menages_kyf.csv"

ORDER = {
    "age": ["18 à 25 ans", "26 à 35 ans", "36 à 40 ans", "Plus de 41 ans"],
    "duree_retour": ["Moins de 6 mois", "6 à 12 mois", "1 à 2 ans", "plus de 2 ans"],
    "niveau_vuln": ["Faible", "Modérée", "Élevée"],
    "statut": ["Ménage retourné", "Famille d'accueil", "Autre (ni retourné ni accueil)"],
    "profil": ["Maraîchers pomme de terre", "Petits producteurs peu diversifiés",
               "Vivriers diversifiés + élevage", "Riziculteurs diversifiés"],
}

LABELS = {
    "culture": {"haricot": "Haricot", "mais": "Maïs", "maraichage": "Maraîchage", "manioc": "Manioc", "arachide": "Arachide",
                "soja": "Soja", "pomme_de_terre": "Pomme de terre", "riz": "Riz", "autres_cultures": "Autres cultures"},
    "maraich": {"oignon_blanc": "Oignon blanc", "poireau": "Poireau", "chou": "Chou", "epinard": "Épinard", "tomate": "Tomate",
                "aubergine_violette": "Aubergine violette", "amarante": "Amarante", "aubergine_verte": "Aubergine verte",
                "oignon_rouge": "Oignon rouge", "poivron": "Poivron", "morelle": "Morelle (mboga buchungu)"},
    "elevage": {"cobaye": "Cobaye", "poule": "Poule", "lapin": "Lapin", "chevre": "Chèvre", "porc": "Porc", "canard": "Canard", "mouton": "Mouton"},
    "activite": {"agriculture": "Agriculture", "elevage": "Élevage", "commerce": "Service / commerce", "transformation": "Transformation agricole"},
    "frein": {"manque_de_moyens": "Manque de moyens", "manque_de_formation": "Manque de formation", "acces_au_marche": "Accès au marché", "autres": "Autres"},
    "souhait": {"maraichage": "Maraîchage", "commerce_transformation": "Commerce / transformation", "haricot": "Haricot", "mais": "Maïs",
                "elevage_general": "Élevage", "pomme_de_terre": "Pomme de terre", "arachide": "Arachide", "soja": "Soja", "riz": "Riz", "manioc": "Manioc"},
    "motif": {"generer_des_revenus": "Générer des revenus", "ameliorer_les_conditions_de_vie": "Améliorer les conditions de vie",
              "nourrir_le_menage": "Nourrir le ménage", "scolarite_des_enfants": "Scolarité des enfants", "sortir_de_la_pauvrete": "Sortir de la pauvreté",
              "accroitre_la_production": "Accroître la production", "sante_soins": "Santé / soins", "rapidite_du_cycle": "Rapidité du cycle"},
    "critere": {"femme": "Femme cheffe de ménage", "petite_surface": "Moins de 0,25 ha exploité", "non_membre_op": "Non membre d'une organisation",
                "sans_terre": "Pas de terre en propriété", "retour_recent": "Retour depuis moins de 12 mois", "grande_taille": "Ménage de 9 personnes ou plus",
                "handicap": "Personne handicapée", "accueil_lourd": "Accueille 2 ménages ou plus"},
}

ALERTES = {"alerte_tel_partage": "Téléphone partagé entre ménages", "alerte_gps_imprecis": "GPS imprécis (plus de 50 m)",
           "alerte_taille_incoherente": "Taille du ménage incohérente", "alerte_duree_suspecte": "Entretien de moins de 5 minutes",
           "alerte_dup_nom_village": "Doublon probable (même nom, même village)", "alerte_sup_aberrante": "Superficie aberrante (plus de 5 ha)"}

FILTERS = [("territoire", "Territoire"), ("groupement", "Groupement"), ("sexe", "Sexe du chef de ménage"), ("age", "Âge du chef de ménage"),
           ("statut", "Statut du ménage"), ("niveau_vuln", "Niveau de vulnérabilité"), ("profil", "Profil de production")]


@st.cache_data(ttl=86400, max_entries=1)
def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["date"])
    for col, cats in ORDER.items():
        df[col] = pd.Categorical(df[col], categories=cats, ordered=True)
    return df


def options(df: pd.DataFrame, col: str) -> list:
    if col in ORDER:
        return ORDER[col]
    return df[col].value_counts().index.tolist()


def share(df: pd.DataFrame, mask) -> float:
    return float(mask.sum()) / len(df) if len(df) else 0.0


def bit_table(df: pd.DataFrame, prefix: str, base: pd.DataFrame | None = None) -> pd.DataFrame:
    """% de ménages pour chaque colonne binaire d'un groupe (culture_, frein_, ...), trié décroissant."""
    base = df if base is None else base
    rows = [{"libelle": lab, "part": base[f"{prefix}_{k}"].mean() if len(base) else 0.0, "menages": int(base[f"{prefix}_{k}"].sum())}
            for k, lab in LABELS[prefix].items() if f"{prefix}_{k}" in base]
    return pd.DataFrame(rows).sort_values("part", ascending=False)


def counts(df: pd.DataFrame, col: str) -> pd.DataFrame:
    s = df[col].value_counts(sort=False) if col in ORDER else df[col].value_counts()
    out = s.rename_axis("libelle").reset_index(name="menages")
    out["part"] = out["menages"] / max(len(df), 1)
    return out

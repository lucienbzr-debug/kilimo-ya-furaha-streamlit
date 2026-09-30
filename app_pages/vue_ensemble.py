import pandas as pd
import streamlit as st

from lib import charts
from lib.data import ORDER, counts, share

df = st.session_state["df"]
if df.empty:
    st.warning("Aucun ménage ne correspond aux filtres. Élargissez la sélection dans la barre latérale.", icon=":material/filter_alt_off:")
    st.stop()

n = len(df)
fr = lambda x, d=0: f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
pc = lambda x: f"{100 * x:.0f} %"

accueil = pc(share(df, df.statut == "Famille d'accueil"))
tiles = [
    ("Ménages identifiés", fr(n), None),
    ("Personnes couvertes", fr(df.taille_menage.sum()), f"{fr(df.taille_menage.mean(), 1)} personnes par ménage en moyenne"),
    ("Femmes cheffes de ménage", pc(share(df, df.sexe == "Femme")), None),
    ("Chefs de 18 à 35 ans", pc(share(df, df.age.isin(ORDER["age"][:2]))), None),
    ("Ménages retournés", pc(share(df, df.statut == "Ménage retourné")), f"{accueil} de familles d'accueil"),
    ("Possèdent une terre", pc(share(df, df.possede_terre == "Oui")), f"{pc(share(df, df.loue_terre == 'Oui'))} louent une terre"),
    ("Surface médiane", f"{fr(df.superficie_totale_ha.median(), 2)} ha", "Surface exploitée, propriété et location cumulées"),
    ("Membres d'une OP", pc(share(df, df.membre_op == "Oui")), "Association, organisation paysanne ou coopérative"),
    ("Score moyen (sur 8)", fr(df.score_vuln.mean(), 1), "Nombre moyen de critères de vulnérabilité"),
    ("Vulnérabilité élevée", pc(share(df, df.niveau_vuln == "Élevée")), f"{fr((df.niveau_vuln == 'Élevée').sum())} ménages avec 5 critères ou plus"),
]
with st.container(horizontal=True):
    for label, value, helptext in tiles:
        st.metric(label, value, help=helptext, border=True, width=180)

with st.expander("Constats clés sur la base complète", icon=":material/lightbulb:", expanded=True):
    st.markdown(
        "- **Une cible féminine et jeune** : 61 % des chefs de ménage sont des femmes et 46 % ont entre 18 et 35 ans.\n"
        "- **Lubero concentre la vulnérabilité** : 24 % de ménages en vulnérabilité élevée contre 3 % à Beni ; 59 % à Buyora/Luotu.\n"
        "- **Des exploitations minuscules** : 0,20 ha exploités en médiane ; 31 % des ménages n'ont pas de terre en propriété.\n"
        "- **Le capital est le premier frein** : 97 % citent le manque de moyens, 66 % le manque de formation."
    )

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.subheader("Ménages par groupement")
        st.altair_chart(charts.hbar(counts(df, "groupement"), value="menages", pct=False), width="stretch")
with c2:
    with st.container(border=True):
        st.subheader("Statut du ménage par territoire")
        t = df.groupby(["territoire", "statut"], observed=True).size().reset_index(name="menages")
        st.altair_chart(charts.stacked(t, "territoire", "statut", ORDER["statut"], ["#2a78d6", "#eb6834", "#1baf7a"]), width="stretch")
        st.caption("Répartition en % des ménages de chaque territoire.")

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.subheader("Âge du chef de ménage")
        st.altair_chart(charts.hbar(counts(df, "age"), sort=ORDER["age"]), width="stretch")
with c2:
    with st.container(border=True):
        st.subheader("Durée depuis le retour")
        ret = df[df.duree_retour.notna()]
        st.altair_chart(charts.hbar(counts(ret, "duree_retour"), sort=ORDER["duree_retour"]), width="stretch")
        st.caption(f"Ménages retournés uniquement ({fr(len(ret))}).")
with c3:
    with st.container(border=True):
        st.subheader("Type d'organisation")
        org = counts(df[df.type_structure.notna()], "type_structure")
        org["part"] = org["menages"] / n
        st.altair_chart(charts.hbar(org), width="stretch")
        st.caption(f"{pc(share(df, df.membre_op == 'Oui'))} des ménages sont membres d'une organisation.")

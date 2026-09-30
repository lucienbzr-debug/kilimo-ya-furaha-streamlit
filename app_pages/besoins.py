import pandas as pd
import streamlit as st

from lib import charts
from lib.data import LABELS, bit_table

df = st.session_state["df"]
if df.empty:
    st.warning("Aucun ménage ne correspond aux filtres.", icon=":material/filter_alt_off:")
    st.stop()

fem, hom = df[df.sexe == "Femme"], df[df.sexe == "Homme"]

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.subheader("Freins au développement d'une activité")
        fr = pd.DataFrame([{"libelle": lab, "a": fem[f"frein_{k}"].mean() if len(fem) else 0, "b": hom[f"frein_{k}"].mean() if len(hom) else 0}
                           for k, lab in LABELS["frein"].items()])
        st.altair_chart(charts.paired(fr, "libelle", "a", "b", "Femmes", "Hommes"), width="stretch")
        st.caption("% des ménages, selon le sexe du chef de ménage.")
with c2:
    with st.container(border=True):
        st.subheader("Activités pratiquées et jugées rentables")
        ac = pd.DataFrame([{"libelle": lab, "a": df[f"activite_{k}"].mean(), "b": df[f"rentable_{k}"].mean()} for k, lab in LABELS["activite"].items()])
        ac = ac.assign(ecart=ac.b - ac.a).sort_values("ecart", ascending=False)
        st.altair_chart(charts.paired(ac, "libelle", "a", "b", "Pratiquée aujourd'hui", "Jugée parmi les plus rentables"), width="stretch")
        st.caption("Élevage, commerce et transformation sont jugés rentables bien plus souvent qu'ils ne sont pratiqués.")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.subheader("Activités que les ménages veulent développer")
        st.altair_chart(charts.hbar(bit_table(df, "souhait").query("menages > 0")), width="stretch")
        st.caption("Réponses libres codées par thème ; un ménage peut citer plusieurs thèmes.")
with c2:
    with st.container(border=True):
        st.subheader("Motivations exprimées")
        st.altair_chart(charts.hbar(bit_table(df, "motif")), width="stretch")
        st.caption("Réponses libres codées par thème.")

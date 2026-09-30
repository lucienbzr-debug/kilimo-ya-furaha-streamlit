"""Tableau de bord de l'identification des ménages bénéficiaires du projet Kilimo ya Furaha (Rikolto RDC)."""
import streamlit as st

from lib.data import FILTERS, load, options

st.set_page_config(page_title="Ménages KYF", page_icon=":material/agriculture:", layout="wide")

df = load()

with st.sidebar:
    st.subheader("Filtres")
    st.caption("Laissez un filtre vide pour inclure toutes les valeurs.")
    sel = df
    for col, label in FILTERS:
        chosen = st.multiselect(label, options(df, col), key=f"f_{col}", placeholder="Tous")
        if chosen:
            sel = sel[sel[col].isin(chosen)]
    st.metric("Ménages sélectionnés", f"{len(sel):,}".replace(",", " "), help=f"Sur {len(df):,} ménages au total".replace(",", " "))
    if st.button("Réinitialiser les filtres", icon=":material/restart_alt:", width="stretch"):
        for col, _ in FILTERS:
            st.session_state[f"f_{col}"] = []
        st.rerun()
    st.caption("Source : base KoBo « KILIMO YA FURAHA_RIKOLTO RDC », export du 30/09/2026. Données anonymisées.")

st.session_state["df"] = sel
st.session_state["df_all"] = df

page = st.navigation(
    [
        st.Page("app_pages/vue_ensemble.py", title="Vue d'ensemble", icon=":material/dashboard:", default=True),
        st.Page("app_pages/vulnerabilite.py", title="Vulnérabilité", icon=":material/crisis_alert:"),
        st.Page("app_pages/production.py", title="Production", icon=":material/agriculture:"),
        st.Page("app_pages/besoins.py", title="Besoins", icon=":material/handshake:"),
        st.Page("app_pages/qualite.py", title="Qualité des données", icon=":material/fact_check:"),
        st.Page("app_pages/methode.py", title="Méthode et données", icon=":material/description:"),
    ],
    position="top",
)

st.caption("Rikolto RDC · Projet Kilimo ya Furaha · Nord-Kivu (Beni, Lubero)")
st.title(page.title)
page.run()

import altair as alt
import pandas as pd
import streamlit as st

from lib import charts
from lib.data import ALERTES

df = st.session_state["df"]
if df.empty:
    st.warning("Aucun ménage ne correspond aux filtres.", icon=":material/filter_alt_off:")
    st.stop()

st.markdown("Aucune fiche n'a été supprimée, sauf les 4 refus de consentement. Les alertes signalent les fiches à vérifier avant la liste finale.")

c1, c2 = st.columns([2, 3])
with c1:
    with st.container(border=True):
        st.subheader("Alertes de qualité")
        al = pd.DataFrame([{"libelle": lab, "menages": int(df[k].sum())} for k, lab in ALERTES.items()])
        st.altair_chart(charts.hbar(al, value="menages", pct=False), width="stretch")
        st.caption("Nombre de fiches concernées dans la sélection.")
with c2:
    with st.container(border=True):
        st.subheader("Fiches collectées par jour")
        days = df.groupby(df.date.dt.date).size().reset_index(name="fiches")
        days["date"] = pd.to_datetime(days["date"])
        st.altair_chart(alt.Chart(days).mark_bar(color=charts.BRAND, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m")), y=alt.Y("fiches:Q", title=None),
            tooltip=[alt.Tooltip("date:T", title="Date", format="%d/%m/%Y"), alt.Tooltip("fiches:Q", title="Fiches")]).properties(height=260), width="stretch")

with st.container(border=True):
    st.subheader("Performance des enquêteurs")
    st.caption("Enquêteurs codés E01 à E21 (du plus grand au plus petit nombre de fiches). « À vérifier » : plus de 20 % d'entretiens de moins de "
               "5 minutes ou plus de 50 % de fiches avec alerte. Une durée médiane de plusieurs heures indique des formulaires envoyés plus tard.")
    e = df.groupby("enqueteur").agg(fiches=("id", "size"), duree=("duree_min", "median"), courts=("alerte_duree_suspecte", "mean"),
                                    gps=("alerte_gps_imprecis", "mean"),
                                    alertes=("nb_alertes", lambda s: (s > 0).mean())).reset_index().sort_values("enqueteur")
    e["statut"] = [("À vérifier" if c > 0.2 or a > 0.5 else "À surveiller" if c > 0.1 or a > 0.35 else "Conforme")
                   for c, a in zip(e.courts, e.alertes)]
    for c in ["courts", "gps", "alertes"]:
        e[c] = 100 * e[c]
    pct = lambda t: st.column_config.ProgressColumn(t, min_value=0, max_value=100, format="%.0f %%")
    st.dataframe(e, hide_index=True, column_config={
        "enqueteur": "Enquêteur", "fiches": st.column_config.NumberColumn("Fiches", format="%d"),
        "duree": st.column_config.NumberColumn("Durée médiane (min)", format="%.1f"), "courts": pct("Entretiens < 5 min"),
        "gps": pct("GPS imprécis"), "alertes": pct("Fiches avec alerte"), "statut": "Statut"})

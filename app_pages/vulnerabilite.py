import pandas as pd
import streamlit as st

from lib import charts
from lib.data import bit_table

df = st.session_state["df"]
if df.empty:
    st.warning("Aucun ménage ne correspond aux filtres.", icon=":material/filter_alt_off:")
    st.stop()

st.markdown("Le score additionne **8 critères**, un point chacun. Niveau **faible** de 0 à 2, **modéré** de 3 à 4, **élevé** à partir de 5. "
            "C'est un outil de pré-sélection, à valider par l'équipe projet.")

c1, c2 = st.columns([3, 2])
with c1:
    with st.container(border=True):
        st.subheader("Répartition des ménages par score")
        sc = df.score_vuln.value_counts().reindex(range(9), fill_value=0).rename_axis("score").reset_index(name="menages")
        sc["niveau"] = pd.cut(sc.score, [-1, 2, 4, 9], labels=list(charts.LEVELS)).astype(str)
        sc["score"] = sc.score.astype(str)
        st.altair_chart(charts.columns(sc, "menages", "score", [str(i) for i in range(9)], colors=charts.LEVELS, color_field="niveau", legend=True),
                        width="stretch")
with c2:
    with st.container(border=True):
        st.subheader("Fréquence des critères")
        st.altair_chart(charts.hbar(bit_table(df, "critere")), width="stretch")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.subheader("Vulnérabilité élevée par groupement")
        g = df.groupby("groupement").agg(menages=("id", "size"), part=("niveau_vuln", lambda s: (s == "Élevée").mean())).reset_index()
        g = g[g.menages >= 10].rename(columns={"groupement": "libelle"})
        top = g.sort_values("part").libelle.iloc[-1] if len(g) else None
        st.altair_chart(charts.hbar(g, highlight=top), width="stretch")
        st.caption("Groupements d'au moins 10 ménages dans la sélection.")
with c2:
    with st.container(border=True):
        st.subheader("Villages classés par score moyen")
        v = (df[df.village != "Autres villages"].groupby(["village", "territoire"]).agg(menages=("id", "size"), score=("score_vuln", "mean"),
             elevee=("niveau_vuln", lambda s: (s == "Élevée").mean())).reset_index())
        v = v[v.menages >= 10].sort_values("score", ascending=False).assign(elevee=lambda x: 100 * x.elevee)
        st.dataframe(v, hide_index=True, height=360, column_config={
            "village": "Village", "territoire": "Territoire", "menages": st.column_config.NumberColumn("Ménages", format="%d"),
            "score": st.column_config.ProgressColumn("Score moyen", min_value=0, max_value=8, format="%.1f"),
            "elevee": st.column_config.NumberColumn("Vuln. élevée", format="%.0f %%")})

with st.container(border=True):
    st.subheader("Synthèse par groupement")
    s = df.groupby("groupement").agg(
        menages=("id", "size"), femmes=("sexe", lambda x: (x == "Femme").mean()), retournes=("statut", lambda x: (x == "Ménage retourné").mean()),
        terre=("possede_terre", lambda x: (x == "Oui").mean()), surface=("superficie_totale_ha", "median"), op=("membre_op", lambda x: (x == "Oui").mean()),
        score=("score_vuln", "mean"), elevee=("niveau_vuln", lambda x: (x == "Élevée").mean()), n_elevee=("niveau_vuln", lambda x: int((x == "Élevée").sum())),
    ).reset_index().sort_values("menages", ascending=False)
    for c in ["femmes", "retournes", "terre", "op", "elevee"]:
        s[c] = 100 * s[c]
    pct = lambda t: st.column_config.NumberColumn(t, format="%.0f %%")
    st.dataframe(s, hide_index=True, column_config={
        "groupement": "Groupement", "menages": st.column_config.NumberColumn("Ménages", format="%d"), "femmes": pct("Femmes cheffes"),
        "retournes": pct("Ménages retournés"), "terre": pct("Possèdent une terre"), "surface": st.column_config.NumberColumn("Surface médiane (ha)", format="%.2f"),
        "op": pct("Membres OP"), "score": st.column_config.NumberColumn("Score moyen", format="%.1f"),
        "elevee": st.column_config.ProgressColumn("Vulnérabilité élevée", min_value=0, max_value=100, format="%.0f %%"),
        "n_elevee": st.column_config.NumberColumn("Ménages très vulnérables", format="%d")})

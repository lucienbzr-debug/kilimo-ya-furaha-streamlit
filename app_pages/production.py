import pandas as pd
import streamlit as st

from lib import charts
from lib.data import ORDER, bit_table

df = st.session_state["df"]
if df.empty:
    st.warning("Aucun ménage ne correspond aux filtres.", icon=":material/filter_alt_off:")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.subheader("Cultures pratiquées")
        st.altair_chart(charts.hbar(bit_table(df, "culture")), width="stretch")
        st.caption("% de l'ensemble des ménages.")
with c2:
    with st.container(border=True):
        st.subheader("Petit élevage")
        st.altair_chart(charts.hbar(bit_table(df, "elevage")), width="stretch")
        st.caption(f"% de l'ensemble des ménages ; {100 * (df.eleve == 'Oui').mean():.0f} % pratiquent le petit élevage.")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.subheader("Cultures maraîchères préférées")
        mar = df[df.culture_maraichage == 1]
        st.altair_chart(charts.hbar(bit_table(df, "maraich", base=mar)), width="stretch")
        st.caption(f"% des {len(mar)} ménages maraîchers.")
with c2:
    with st.container(border=True):
        st.subheader("Surface totale exploitée")
        bins = [0, 0.1, 0.25, 0.5, 1, 99]
        labels = ["Moins de 0,1 ha", "0,1 à 0,25 ha", "0,25 à 0,5 ha", "0,5 à 1 ha", "1 ha et plus"]
        s = pd.cut(df.superficie_totale_ha.dropna(), bins, labels=labels, right=False).value_counts().reindex(labels)
        st.altair_chart(charts.hbar(s.rename_axis("libelle").reset_index(name="menages"), value="menages", pct=False, sort=labels), width="stretch")
        st.caption("Propriété et location cumulées ; nombre de ménages.")
        t = df.groupby(["sexe", "possede_terre"]).size().reset_index(name="menages")
        t["possede_terre"] = t.possede_terre.map({"Oui": "Propriétaire", "Non": "Sans terre en propriété"})
        st.altair_chart(charts.stacked(t, "sexe", "possede_terre", ["Propriétaire", "Sans terre en propriété"], ["#1baf7a", "#eda100"]), width="stretch")

st.subheader("Profils de production")
st.caption("Quatre profils obtenus par classification statistique (k-means) sur les cultures, l'élevage et l'accès à la terre.")
for col, p in zip(st.columns(4), ORDER["profil"]):
    s = df[df.profil == p]
    if s.empty:
        continue
    with col:
        with st.container(border=True, height="stretch"):
            st.markdown(f"**{p}**")
            st.metric(f"Ménages ({100 * len(s) / len(df):.0f} % de la sélection)", f"{len(s)}")
            top = bit_table(s, "culture").query("libelle != 'Autres cultures'").head(3)
            st.markdown("Cultures : " + ", ".join(f"{r.libelle} {100 * r.part:.0f} %" for r in top.itertuples()))
            st.markdown(f"Territoire dominant : {s.territoire.mode().iat[0]}  \n"
                        f"Femmes cheffes : {100 * (s.sexe == 'Femme').mean():.0f} %  \n"
                        f"Propriétaires : {100 * (s.possede_terre == 'Oui').mean():.0f} %  \n"
                        f"Surface médiane : {s.superficie_totale_ha.median():.2f} ha")
            el = (s.niveau_vuln == "Élevée").mean()
            color = "red" if el > 0.15 else "orange" if el > 0.05 else "green"
            st.badge(f"Vulnérabilité élevée : {100 * el:.0f} %", color=color)

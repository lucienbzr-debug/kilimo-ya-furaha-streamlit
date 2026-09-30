import streamlit as st

df = st.session_state["df"]
df_all = st.session_state["df_all"]

with st.container(border=True):
    st.subheader("Source et traitement")
    st.markdown(
        "- **Source** : base KoBoToolbox « KILIMO YA FURAHA_RIKOLTO RDC », collecte du 15 juin au 14 septembre 2026, export du 30/09/2026 (1 967 fiches).\n"
        "- **Exclusions** : 4 ménages ayant refusé l'utilisation de leurs données ; 1 963 ménages analysés.\n"
        "- **Harmonisation** : noms de groupements, villages et enquêteurs corrigés (fautes de frappe, variantes).\n"
        "- **Taille du ménage** : somme hommes + femmes + garçons + filles quand ce détail est rempli.\n"
        "- **Superficies** : valeurs supérieures à 5 ha considérées comme des erreurs de saisie et laissées vides.\n"
        "- **Score de vulnérabilité** : 1 point par critère (femme cheffe de ménage, personne handicapée, pas de terre en propriété, "
        "retour depuis moins de 12 mois, 9 personnes ou plus, non membre d'une organisation, moins de 0,25 ha exploité, accueil de 2 ménages ou plus).\n"
        "- **Profils de production** : classification k-means en 4 classes sur les cultures, l'élevage et l'accès à la terre.\n"
        "- **Réponses libres** : activités souhaitées et motivations codées par mots-clés."
    )

with st.container(border=True):
    st.subheader("Protection des données")
    st.markdown(
        "Ce jeu de données ne contient **ni nom, ni numéro de téléphone, ni coordonnée GPS, ni réponse libre**. "
        "Les enquêteurs sont désignés par un code et les villages de moins de 10 ménages sont regroupés sous « Autres villages ». "
        "La base nominative reste en interne chez Rikolto RDC."
    )

with st.container(border=True):
    st.subheader("Données de la sélection")
    st.caption(f"{len(df)} ménages sur {len(df_all)}, selon les filtres de la barre latérale.")
    st.dataframe(df, hide_index=True, height=320)
    st.download_button("Télécharger la sélection (CSV)", df.to_csv(index=False).encode("utf-8"), file_name="menages_kyf_selection.csv",
                       mime="text/csv", icon=":material/download:")

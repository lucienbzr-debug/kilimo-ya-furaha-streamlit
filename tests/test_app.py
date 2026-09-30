"""Tests de fumée : chaque page s'affiche sans erreur, avec et sans filtre. Lancer : python -m pytest tests"""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["app_pages/vue_ensemble.py", "app_pages/vulnerabilite.py", "app_pages/production.py",
         "app_pages/besoins.py", "app_pages/qualite.py", "app_pages/methode.py"]


def app():
    return AppTest.from_file("../streamlit_app.py", default_timeout=60)


@pytest.mark.parametrize("page", PAGES)
def test_page_sans_filtre(page):
    at = app().run()
    at.switch_page(page).run()
    assert not at.exception


@pytest.mark.parametrize("page", PAGES)
def test_page_filtre_lubero(page):
    at = app().run()
    at.multiselect(key="f_territoire").select("Lubero").run()
    at.switch_page(page).run()
    assert not at.exception


def test_indicateurs_base_complete():
    at = app().run()
    m = {x.label: x.value for x in at.metric}
    assert m["Ménages identifiés"] == "1 963"
    assert m["Femmes cheffes de ménage"] == "61 %"
    assert m["Vulnérabilité élevée"] == "10 %"

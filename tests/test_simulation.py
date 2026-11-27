"""Validation du moteur, des statistiques, de la configuration et des exports."""

import json
import xml.etree.ElementTree as ET

import pytest

from simulateur_trafic.core.simulateur import Simulateur
from simulateur_trafic.models import Intersection, ReseauRoutier, Vehicule
from simulateur_trafic.out.affichage import Affichage


@pytest.mark.parametrize("tours", [-1, 1.5, True, "3"])
def test_tours_invalides(reseau, tours):
    with pytest.raises(ValueError):
        Simulateur(reseau=reseau).lancer_simulation(tours, afficher=False)


@pytest.mark.parametrize("pas", [0, -1, float("nan"), float("inf")])
def test_pas_invalide(reseau, pas):
    with pytest.raises(ValueError):
        Simulateur(reseau=reseau).lancer_simulation(1, pas, afficher=False)


@pytest.mark.parametrize("frequence", [0, -1, True, 1.5])
def test_frequence_invalide(reseau, frequence):
    with pytest.raises(ValueError):
        Simulateur(reseau=reseau).lancer_simulation(0, afficher=False, afficher_chaque=frequence)


@pytest.mark.parametrize("duree", [0, -1, float("nan"), float("inf")])
def test_duree_feu_invalide(duree):
    with pytest.raises(ValueError):
        Intersection("B", duree_vert=duree)


def test_zero_tour_et_reseau_vide(reseau):
    s = Simulateur(reseau=reseau)
    bilan = s.lancer_simulation(0, afficher=False)
    assert bilan["temps_s"] == 0
    assert bilan["temps_parcours_moyen_s"] is None
    assert len(s.historique) == 1


def test_continuation(reseau):
    s = Simulateur(reseau=reseau)
    s.lancer_simulation(2, 0.5, afficher=False)
    s.lancer_simulation(2, 0.5, afficher=False)
    assert reseau.temps == 2
    assert len(s.historique) == 5


def test_entree_inexistante_config(tmp_path):
    fichier = tmp_path / "invalide.json"
    fichier.write_text(json.dumps({"intersections": [], "routes": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        ReseauRoutier.depuis_json(fichier)


def test_fichier_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        Simulateur(tmp_path / "absent.json")


def test_config_json_invalide(tmp_path):
    fichier = tmp_path / "invalide.json"
    fichier.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        Simulateur(fichier)


def test_congestion_detectee(reseau):
    route = reseau.routes["AB"]
    for i in range(3):
        v = Vehicule(str(i), itineraire=["AB"])
        reseau.ajouter_vehicule(v)
        route.ajouter_vehicule(v)
        v.position = 50 - i * 10
    assert "AB" in Simulateur(reseau=reseau).analyseur.zones_congestion()


def test_exports_json_csv_svg(reseau, tmp_path):
    reseau.ajouter_vehicule(Vehicule("V1", 36, ["AB", "BC"]))
    s = Simulateur(reseau=reseau)
    s.lancer_simulation(20, 1, afficher=False)
    chemins = s.exporter(tmp_path, graphiques=False)
    assert len(chemins) == 4
    assert all(p.is_file() and p.stat().st_size for p in chemins)
    donnees = json.loads((tmp_path / "resultats.json").read_text(encoding="utf-8"))
    assert donnees["bilan"]["vehicules_termines"] == 1
    assert donnees["bilan"]["distance_totale_m"] == 200
    for fichier in (Affichage._courbes_svg(s.historique, tmp_path / "courbes.svg"),
                    Affichage._carte_svg(reseau, tmp_path / "carte.svg")):
        assert ET.parse(fichier).getroot().tag.endswith("svg")

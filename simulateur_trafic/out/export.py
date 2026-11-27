"""Exporte les états, le bilan et les trajets aux formats JSON et CSV."""

import csv
import json
from pathlib import Path

from ..models.reseau import ReseauRoutier


class Export:
    """Regroupe les écritures de données JSON et CSV."""
    @staticmethod
    def sauvegarder(dossier: Path, historique: list[dict], bilan: dict,
                    reseau: ReseauRoutier) -> list[Path]:
        """Écrit les quatre fichiers resultats.json, historique.csv, routes.csv et trajets.csv.

        Args:
            dossier (Path): Dossier de destination ; créé si nécessaire.
            historique (list[dict]): Liste chronologique des instantanés de statistiques.
            bilan (dict): Dictionnaire des indicateurs cumulés à exporter ou à afficher.
            reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.

        Returns:
            list[Path]: Chemins des quatre fichiers de données créés.

        Raises:
            OSError: Si un fichier ne peut pas être écrit.
        """
        dossier.mkdir(parents=True, exist_ok=True)
        fichiers = [dossier / nom for nom in (
            "resultats.json", "historique.csv", "routes.csv", "trajets.csv")]
        with fichiers[0].open("w", encoding="utf-8") as flux:
            json.dump({"bilan": bilan, "historique": historique}, flux, ensure_ascii=False, indent=2)
        colonnes = ["temps_s", "vehicules_actifs", "vehicules_termines", "vehicules_en_attente",
                    "vitesse_moyenne_kmh", "temps_parcours_moyen_s", "zones_congestion"]
        with fichiers[1].open("w", newline="", encoding="utf-8-sig") as flux:
            writer = csv.DictWriter(flux, fieldnames=colonnes)
            writer.writeheader()
            for etat in historique:
                ligne = {cle: etat[cle] for cle in colonnes}
                ligne["zones_congestion"] = ";".join(ligne["zones_congestion"])
                writer.writerow(ligne)
        with fichiers[2].open("w", newline="", encoding="utf-8-sig") as flux:
            writer = csv.DictWriter(flux, fieldnames=["temps_s", "route", "nombre_vehicules",
                                                     "vitesse_moyenne_kmh", "taux_occupation"])
            writer.writeheader()
            for etat in historique:
                for nom, donnees in etat["routes"].items():
                    writer.writerow({"temps_s": etat["temps_s"], "route": nom, **donnees})
        with fichiers[3].open("w", newline="", encoding="utf-8-sig") as flux:
            writer = csv.DictWriter(flux, fieldnames=["identifiant", "type", "itineraire", "depart_prevu_s",
                                                     "depart_reel_s", "arrivee_s", "temps_parcours_s",
                                                     "distance_m", "statut"])
            writer.writeheader()
            for v in reseau.vehicules.values():
                statut = "termine" if v.termine else ("en_cours" if v.route_actuelle else "en_attente")
                writer.writerow({"identifiant": v.identifiant, "type": type(v).__name__,
                                 "itineraire": ";".join(v.itineraire), "depart_prevu_s": v.depart_prevu,
                                 "depart_reel_s": v.heure_depart, "arrivee_s": v.heure_arrivee,
                                 "temps_parcours_s": v.temps_parcours,
                                 "distance_m": v.distance_parcourue, "statut": statut})
        return fichiers

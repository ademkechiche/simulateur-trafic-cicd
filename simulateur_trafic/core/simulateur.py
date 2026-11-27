"""Exécute les tours de simulation et coordonne analyse, affichage et exports."""

from pathlib import Path

from .analyseur import Analyseur
from ..models.reseau import ReseauRoutier
from ..out.affichage import Affichage
from ..out.export import Export
from ..models.validation import nombre_fini


class Simulateur:
    """Coordonne la configuration, la boucle temporelle, l’historique et les exports."""
    def __init__(self, fichier_config: str | Path | None = None,
                 reseau: ReseauRoutier | None = None):
        """Initialise les attributs et vérifie les paramètres de construction.

        Args:
            fichier_config (str | Path | None): Chemin JSON ; None sélectionne la configuration fournie avec le package.
            reseau (ReseauRoutier | None): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.

        Returns:
            None: L’instance est initialisée.

        Raises:
            ValueError: Si une valeur métier ne respecte pas les bornes ou les contraintes.
            TypeError: Si un paramètre numérique n’est pas un réel.
        """
        if fichier_config is not None and reseau is not None:
            raise ValueError("Fournir une configuration ou un réseau, un seul des deux.")
        if reseau is None:
            config = Path(fichier_config) if fichier_config is not None else (
                Path(__file__).resolve().parents[1] / "data" / "config_reseau.json")
            reseau = ReseauRoutier.depuis_json(config)
        self.reseau = reseau
        self.analyseur = Analyseur(reseau)
        self.historique: list[dict] = []

    def lancer_simulation(self, n_tours: int = 60, delta_t: float = 60,
                         afficher: bool = True, afficher_chaque: int = 10) -> dict:
        """Exécute les tours demandés, mémorise chaque état et renvoie le bilan.

        Args:
            n_tours (int): Nombre entier positif ou nul de tours supplémentaires à exécuter.
            delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.
            afficher (bool): Active l’affichage console des états et du bilan.
            afficher_chaque (int): Fréquence entière strictement positive d’affichage, exprimée en tours.

        Returns:
            dict: Bilan du réseau après les tours demandés.

        Raises:
            ValueError: Si les tours, la durée ou la fréquence sont invalides.
            TypeError: Si la durée n’est pas un réel.
        """
        if isinstance(n_tours, bool) or not isinstance(n_tours, int) or n_tours < 0:
            raise ValueError("n_tours doit être un entier positif ou nul.")
        delta_t = nombre_fini(delta_t, "delta_t", strict=True)
        if (isinstance(afficher_chaque, bool) or not isinstance(afficher_chaque, int)
                or afficher_chaque <= 0):
            raise ValueError("afficher_chaque doit être un entier strictement positif.")
        self.reseau.injecter_vehicules()
        if not self.historique:
            self.historique.append(self.analyseur.instantane())
        for tour in range(1, n_tours + 1):
            self.reseau.avancer(delta_t)
            etat = self.analyseur.instantane()
            self.historique.append(etat)
            if afficher and (tour % afficher_chaque == 0 or tour == n_tours):
                Affichage.afficher_etat(etat)
        bilan = self.analyseur.bilan()
        if afficher:
            Affichage.afficher_bilan(bilan)
        return bilan

    def exporter(self, dossier: str | Path, graphiques: bool = True) -> list[Path]:
        """Crée le dossier de sortie et exporte le bilan, les historiques et les graphiques demandés.

        Args:
            dossier (str | Path): Dossier de destination ; créé si nécessaire.
            graphiques (bool): Active les graphiques SVG et les PNG si Matplotlib est disponible.

        Returns:
            list[Path]: Chemins des fichiers effectivement écrits.

        Raises:
            OSError: Si le dossier ou un fichier de sortie ne peut pas être écrit.
        """
        dossier = Path(dossier)
        dossier.mkdir(parents=True, exist_ok=True)
        fichiers = Export.sauvegarder(dossier, self.historique, self.analyseur.bilan(), self.reseau)
        if graphiques:
            fichiers.extend(Affichage.generer_graphiques(self.historique, self.reseau, dossier))
        return fichiers

"""Affiche les états console et produit les graphiques SVG ou PNG et la carte."""

from html import escape
from pathlib import Path

from ..models.reseau import ReseauRoutier


class Affichage:
    """Regroupe l’affichage console et la génération des représentations graphiques."""
    @staticmethod
    def afficher_etat(etat: dict) -> None:
        """Affiche une ligne résumant le trafic à un instant donné.

        Args:
            etat (dict): Dictionnaire des statistiques instantanées.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.
        """
        print(f"t = {etat['temps_s'] / 60:6.1f} min | "
              f"actifs : {etat['vehicules_actifs']:3d} | "
              f"arrivés : {etat['vehicules_termines']:3d} | "
              f"en attente : {etat['vehicules_en_attente']:3d} | "
              f"vitesse : {etat['vitesse_moyenne_kmh']:5.1f} km/h | "
              f"congestion : {', '.join(etat['zones_congestion']) or 'aucune'}")

    @staticmethod
    def afficher_bilan(bilan: dict) -> None:
        """Affiche les indicateurs de durée, de distance, de parcours et d’attente.

        Args:
            bilan (dict): Dictionnaire des indicateurs cumulés à exporter ou à afficher.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.
        """
        print("\nBILAN DE LA SIMULATION")
        print(f"Durée : {bilan['temps_s'] / 60:.1f} min")
        print(f"Trajets terminés : {bilan['vehicules_termines']}/{bilan['nombre_vehicules_total']}")
        print(f"Distance totale : {bilan['distance_totale_m'] / 1000:.2f} km")
        for cle, titre, unite in (
            ("temps_parcours_moyen_s", "Temps moyen des trajets terminés", "s"),
            ("vitesse_moyenne_trajets_kmh", "Vitesse moyenne des trajets terminés", "km/h"),
            ("attente_entree_moyenne_s", "Attente moyenne avant entrée", "s"),
        ):
            valeur = bilan[cle]
            print(f"{titre} : {valeur:.2f} {unite}" if valeur is not None else f"{titre} : indisponible")

    @staticmethod
    def generer_graphiques(historique: list[dict], reseau: ReseauRoutier,
                          dossier: Path) -> list[Path]:
        """SVG sans dépendance ; deux PNG supplémentaires si matplotlib est installé.

        Args:
            historique (list[dict]): Liste chronologique des instantanés de statistiques.
            reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.
            dossier (Path): Dossier de destination ; créé si nécessaire.

        Returns:
            list[Path]: Deux SVG et, si Matplotlib est disponible, deux PNG.

        Raises:
            OSError: Si un fichier de sortie ne peut pas être écrit.
        """
        dossier.mkdir(parents=True, exist_ok=True)
        fichiers = [Affichage._courbes_svg(historique, dossier / "statistiques.svg"),
                    Affichage._carte_svg(reseau, dossier / "carte_reseau.svg")]
        try:
            import matplotlib
        except ImportError:
            return fichiers
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        temps = [etat["temps_s"] / 60 for etat in historique]
        fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True, layout="constrained")
        for cle, titre, couleur in (
            ("vehicules_actifs", "Véhicules actifs", "#2563eb"),
            ("vehicules_en_attente", "Véhicules en attente (départs futurs inclus)", "#b45309"),
            ("vehicules_termines", "Trajets terminés", "#16a34a"),
        ):
            axes[0].plot(temps, [e[cle] for e in historique], label=titre, color=couleur)
        axes[0].set_ylabel("Véhicules")
        axes[0].legend(fontsize=8)
        axes[1].plot(temps, [e["vitesse_moyenne_kmh"] for e in historique], color="#7c3aed")
        axes[1].set_ylabel("Vitesse active (km/h)")
        axes[2].plot(temps, [len(e["zones_congestion"]) for e in historique], color="#dc2626")
        axes[2].set_ylabel("Routes congestionnées")
        axes[2].set_xlabel("Temps (minutes)")
        for axe in axes:
            axe.grid(alpha=0.2)
        fig.suptitle("Évolution du trafic")
        sortie = dossier / "statistiques.png"
        fig.savefig(sortie, dpi=150)
        plt.close(fig)
        fichiers.append(sortie)

        fig, axe = plt.subplots(figsize=(10, 6), layout="constrained")
        for route in reseau.routes.values():
            a, b = reseau.intersections[route.depart], reseau.intersections[route.arrivee]
            axe.annotate("", xy=(b.x, b.y), xytext=(a.x, a.y),
                         arrowprops={"arrowstyle": "->", "lw": 2, "color": "#64748b", "shrinkB": 14})
            axe.text((a.x + b.x) / 2, (a.y + b.y) / 2 + 0.09,
                     f"{route.nom}\n{route.longueur:g} m / {route.limite_vitesse:g} km/h",
                     ha="center", fontsize=8, bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85})
        for noeud in reseau.intersections.values():
            axe.scatter(noeud.x, noeud.y, s=380, color="#2563eb", zorder=3)
            axe.text(noeud.x, noeud.y, noeud.identifiant, color="white", ha="center", va="center", zorder=4)
        axe.set_title("Réseau routier : sens de circulation et limites")
        axe.margins(0.2)
        axe.set_aspect("equal")
        axe.axis("off")
        sortie = dossier / "carte_reseau.png"
        fig.savefig(sortie, dpi=150)
        plt.close(fig)
        fichiers.append(sortie)
        return fichiers

    @staticmethod
    def _courbes_svg(historique: list[dict], fichier: Path) -> Path:
        """Écrit trois courbes SVG à partir des états observés, sans dépendance externe.

        Args:
            historique (list[dict]): Liste chronologique des instantanés de statistiques.
            fichier (Path): Chemin du fichier JSON de configuration.

        Returns:
            Path: Chemin du graphique SVG créé.

        Raises:
            OSError: Si le fichier ne peut pas être écrit.
        """
        elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="760" viewBox="0 0 1000 760">',
                    '<rect width="1000" height="760" fill="#f8fafc"/>',
                    '<g font-family="Arial, sans-serif" fill="#0f172a">',
                    '<text x="55" y="36" font-size="24">Évolution du trafic routier</text>']
        duree = max((e["temps_s"] for e in historique), default=1) or 1
        for indice, (cle, titre, couleur) in enumerate((
            ("vehicules_actifs", "Véhicules actifs", "#2563eb"),
            ("vitesse_moyenne_kmh", "Vitesse moyenne des véhicules actifs (km/h)", "#7c3aed"),
            ("congestion", "Nombre de routes congestionnées", "#dc2626"),
        )):
            haut = 85 + indice * 220
            valeurs = [len(e["zones_congestion"]) if cle == "congestion" else e[cle] for e in historique]
            maximum = max(valeurs, default=1) or 1
            elements.append(f'<text x="60" y="{haut - 15}" font-size="17">{titre}</text>')
            for fraction in (0, 0.5, 1):
                y = haut + 140 * (1 - fraction)
                elements.append(f'<path d="M 85 {y} H 950" stroke="#cbd5e1" fill="none"/>')
                elements.append(f'<text x="75" y="{y + 5}" text-anchor="end" font-size="12">{maximum * fraction:.1f}</text>')
            points = " ".join(f"{85 + e['temps_s'] / duree * 865:.2f},{haut + 140 * (1 - v / maximum):.2f}"
                              for e, v in zip(historique, valeurs))
            if points:
                elements.append(f'<polyline points="{points}" fill="none" stroke="{couleur}" stroke-width="2.5"/>')
            for fraction in (0, 0.25, 0.5, 0.75, 1):
                x = 85 + fraction * 865
                elements.append(f'<text x="{x}" y="{haut + 163}" text-anchor="middle" font-size="12">{duree * fraction / 60:.1f}</text>')
            elements.append(f'<text x="500" y="{haut + 188}" text-anchor="middle" font-size="12">Temps (minutes)</text>')
        elements.append('</g></svg>')
        fichier.write_text("\n".join(elements), encoding="utf-8")
        return fichier

    @staticmethod
    def _carte_svg(reseau: ReseauRoutier, fichier: Path) -> Path:
        """Écrit une carte SVG schématique des routes et des intersections.

        Args:
            reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.
            fichier (Path): Chemin du fichier JSON de configuration.

        Returns:
            Path: Chemin de la carte SVG créée.

        Raises:
            OSError: Si le fichier ne peut pas être écrit.
        """
        noeuds = list(reseau.intersections.values())
        xmin = min((n.x for n in noeuds), default=0)
        ymin = min((n.y for n in noeuds), default=0)
        dx = max((n.x for n in noeuds), default=1) - xmin or 1
        dy = max((n.y for n in noeuds), default=1) - ymin or 1
        positions = {n.identifiant: (110 + (n.x - xmin) / dx * 780, 480 - (n.y - ymin) / dy * 360)
                     for n in noeuds}
        elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600">',
                    '<rect width="1000" height="600" fill="#f8fafc"/>',
                    '<defs><marker id="fleche" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>',
                    '<g font-family="Arial, sans-serif" fill="#0f172a">',
                    '<text x="50" y="40" font-size="24">Réseau routier : sens de circulation</text>']
        for route in reseau.routes.values():
            x1, y1 = positions[route.depart]
            x2, y2 = positions[route.arrivee]
            norme = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1
            finx, finy = x2 - (x2 - x1) / norme * 23, y2 - (y2 - y1) / norme * 23
            elements.append(f'<path d="M {x1} {y1} L {finx} {finy}" stroke="#64748b" stroke-width="3" marker-end="url(#fleche)"/>')
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            elements.append(f'<rect x="{x - 91}" y="{y - 40}" width="182" height="37" rx="4" fill="#f8fafc"/>')
            elements.append(f'<text x="{x}" y="{y - 25}" text-anchor="middle" font-size="14">{escape(route.nom)}</text>')
            elements.append(f'<text x="{x}" y="{y - 9}" text-anchor="middle" font-size="12">{route.longueur:g} m / {route.limite_vitesse:g} km/h</text>')
        for nom, (x, y) in positions.items():
            elements.append(f'<circle cx="{x}" cy="{y}" r="21" fill="#2563eb"/>')
            elements.append(f'<text x="{x}" y="{y + 5}" fill="white" text-anchor="middle" font-size="15">{escape(nom)}</text>')
        elements.append('<text x="50" y="570" font-size="13">Schéma topologique ; les coordonnées ne représentent pas des distances réelles.</text></g></svg>')
        fichier.write_text("\n".join(elements), encoding="utf-8")
        return fichier

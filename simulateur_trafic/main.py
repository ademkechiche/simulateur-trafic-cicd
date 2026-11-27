"""Point d'entrée : python -m simulateur_trafic ou python simulateur_trafic/main.py."""

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulateur_trafic.core.simulateur import Simulateur


def main() -> int:
    """Analyse les arguments CLI, exécute la simulation et produit les fichiers de résultats.

    Returns:
        int: Zéro en cas de succès ; argparse provoque SystemExit en cas d’erreur.
    """
    racine = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="TP Python - Simulateur de trafic routier")
    parser.add_argument("--config", type=Path, default=racine / "data" / "config_reseau.json",
                        help="Configuration JSON du réseau")
    parser.add_argument("--tours", type=int, default=60, help="Nombre de tours (défaut : 60)")
    parser.add_argument("--delta-t", type=float, default=60, help="Secondes par tour (défaut : 60)")
    parser.add_argument("--sortie", type=Path, default=Path.cwd() / "resultats", help="Dossier des résultats")
    parser.add_argument("--afficher-chaque", type=int, default=10, help="Fréquence des lignes console")
    parser.add_argument("--sans-graphiques", action="store_true", help="Exporter seulement CSV et JSON")
    parser.add_argument("--silencieux", action="store_true", help="Masquer l'affichage console")
    args = parser.parse_args()
    try:
        simulateur = Simulateur(fichier_config=args.config)
        simulateur.lancer_simulation(args.tours, args.delta_t,
                                    afficher=not args.silencieux, afficher_chaque=args.afficher_chaque)
        fichiers = simulateur.exporter(args.sortie, graphiques=not args.sans_graphiques)
    except (OSError, ValueError, KeyError, TypeError) as erreur:
        parser.exit(1, f"Erreur : {erreur}\n")
    if not args.silencieux:
        print("\nFichiers générés :")
        for fichier in fichiers:
            print(f"  {fichier.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validation commune des nombres réels finis et des identifiants métier."""

from math import isfinite
from numbers import Real


def nombre_fini(valeur: float, nom: str, minimum: float = 0, strict: bool = False) -> float:
    """Convertit un réel fini respectant une borne en float.

    Args:
        valeur (float): Nombre à valider ; les booléens sont refusés.
        nom (str): Nom du paramètre affiché dans l'erreur.
        minimum (float): Borne inférieure autorisée.
        strict (bool): Si vrai, exclut la borne inférieure.

    Returns:
        float: Valeur finie validée.

    Raises:
        TypeError: Si la valeur n'est pas un réel ou est un booléen.
        ValueError: Si la valeur est infinie, NaN ou hors de la borne.
    """
    if isinstance(valeur, bool) or not isinstance(valeur, Real):
        raise TypeError(f"{nom} doit être un nombre réel.")
    resultat = float(valeur)
    if not isfinite(resultat) or resultat < minimum or (strict and resultat == minimum):
        comparaison = "strictement supérieur" if strict else "supérieur ou égal"
        raise ValueError(f"{nom} doit être fini et {comparaison} à {minimum}.")
    return resultat

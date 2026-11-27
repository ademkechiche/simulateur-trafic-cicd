"""Feux de circulation avec un cycle rouge, vert et orange."""

from math import isfinite


class TrafficLight:
    """Un feu initialement rouge, dont les durées sont exprimées en secondes."""

    STATES = ("RED", "GREEN", "ORANGE")

    def __init__(
        self,
        light_id: str,
        red_duration: float = 30,
        green_duration: float = 30,
        orange_duration: float = 5,
    ):
        if not isinstance(light_id, str) or not light_id.strip():
            raise ValueError("light_id doit être une chaîne non vide.")

        self.light_id = light_id
        self.red_duration = self._validate_time(red_duration, "red_duration")
        self.green_duration = self._validate_time(green_duration, "green_duration")
        self.orange_duration = self._validate_time(orange_duration, "orange_duration")
        self.reset()

    @staticmethod
    def _validate_time(value, name: str, allow_zero: bool = False) -> float:
        """Refuse les valeurs non numériques, non finies ou hors limites."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} doit être un nombre réel.")
        if not isfinite(value):
            raise ValueError(f"{name} doit être fini.")
        if value < 0 or (value == 0 and not allow_zero):
            condition = "positif ou nul" if allow_zero else "strictement positif"
            raise ValueError(f"{name} doit être {condition}.")
        return float(value)

    @property
    def state(self) -> str:
        """État courant, limité à RED, GREEN et ORANGE."""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        if value not in self.STATES:
            raise ValueError("state doit être RED, GREEN ou ORANGE.")
        # Toute entrée dans un état commence avec un compteur nul.
        self._state = value
        self.timer = 0.0

    def change_state(self) -> None:
        """Passe à l'état suivant et réinitialise le compteur."""
        index = self.STATES.index(self.state)
        self.state = self.STATES[(index + 1) % len(self.STATES)]

    def update(self, elapsed_time: float) -> None:
        """Avance le feu, en conservant le temps restant après chaque transition.

        Un appel peut traverser plusieurs états. Par exemple, avec des durées
        rouge=3, vert=2 et orange=1, update(4) atteint le vert avec timer=1.
        """
        elapsed_time = self._validate_time(
            elapsed_time, "elapsed_time", allow_zero=True
        )
        durations = {
            "RED": self.red_duration,
            "GREEN": self.green_duration,
            "ORANGE": self.orange_duration,
        }
        self.timer += elapsed_time
        while self.timer >= durations[self.state]:
            remaining = self.timer - durations[self.state]
            self.change_state()
            self.timer = remaining

    def can_pass(self) -> bool:
        """Autorise le passage uniquement au vert."""
        return self.state == "GREEN"

    def reset(self) -> None:
        """Replace le feu au rouge avec un compteur nul."""
        self.state = "RED"

    def get_state(self) -> str:
        """Renvoie l'état actuel du feu."""
        return self.state

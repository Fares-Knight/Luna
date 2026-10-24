"""Coordination d'une partie locale, indépendante de Pygame."""

from random import Random

from luna.domain.models import GameState, Phase, Position
from luna.domain.rules import apply_cut, cut_error, cut_position_error, has_valid_cut
from luna.domain.scoring import resolve_remaining
from luna.domain.setup import create_game


class GameController:
    def __init__(self, rng: Random | None = None):
        self.rng = rng if rng is not None else Random()
        self.state: GameState
        self.message = ""
        self.new_game()

    def new_game(self) -> None:
        """Prépare un état jouable avant de remplacer la partie précédente."""
        for _ in range(20):
            candidate = create_game(self.rng)
            if has_valid_cut(candidate):
                self.state = candidate
                self.message = "Nouvelle partie : Joueur 1 commence."
                return
        raise RuntimeError("Impossible de préparer une partie jouable après 20 tentatives.")

    def preview_error(
        self, first_id: int, second_id: int, position: Position | None = None
    ) -> str | None:
        if position is None:
            return cut_error(self.state, first_id, second_id)
        return cut_position_error(self.state, first_id, second_id, position)

    def play_cut(self, first_id: int, second_id: int, position: Position) -> bool:
        try:
            apply_cut(self.state, first_id, second_id, position)
        except ValueError as error:
            self.message = str(error)
            return False
        if self.state.phase is Phase.DISTRIBUTION:
            resolve_remaining(self.state, self.rng)
            assert self.state.result is not None
            result = self.state.result
            if result.winner_id is None:
                self.message = "Partie nulle : égalité des scores."
            else:
                self.message = f"Joueur {result.winner_id + 1} remporte la partie !"
            if result.random_awards:
                self.message += f" {len(result.random_awards)} fleur(s) attribuée(s) par tirage au sort."
        elif not has_valid_cut(self.state):
            self.new_game()
            self.message = (
                "Partie annulée : aucune coupe possible. "
                "Nouvelle disposition, Joueur 1 recommence."
            )
        else:
            self.message = f"Au tour de Joueur {self.state.current_player_id + 1}."
        return True

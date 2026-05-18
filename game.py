import random
from itertools import combinations


class FifteenGame:
    """
    Players alternate picking numbers 1-9 from a shared pool.
    First player whose collection contains ANY 3 numbers summing to 15 wins.
    Each number can only be picked once.
    """

    RULES = """GAME: Fifteen
- Numbers 1-9 are available in a shared pool
- Players alternate picking one number per turn (each number can only be picked once)
- First player whose collection contains ANY 3 numbers that sum to 15 wins
- If all 9 numbers are taken with no winner, it's a draw
- You are playing as the Team. The Bot plays against you."""

    def __init__(self):
        self.available = list(range(1, 10))
        self.team_picks: list[int] = []
        self.bot_picks: list[int] = []

    @staticmethod
    def _has_fifteen(picks: list[int]) -> bool:
        return any(sum(c) == 15 for c in combinations(picks, 3)) if len(picks) >= 3 else False

    def status(self) -> str:
        if self._has_fifteen(self.team_picks):
            return "org_wins"
        if self._has_fifteen(self.bot_picks):
            return "bot_wins"
        if not self.available:
            return "draw"
        return "ongoing"

    def team_move(self, number: int) -> bool:
        if number not in self.available:
            return False
        self.available.remove(number)
        self.team_picks.append(number)
        return True

    def bot_move(self) -> int:
        # Win if possible
        for n in self.available:
            if self._has_fifteen(self.bot_picks + [n]):
                return self._commit_bot(n)
        # Block team win
        for n in self.available:
            if self._has_fifteen(self.team_picks + [n]):
                return self._commit_bot(n)
        # Otherwise random
        return self._commit_bot(random.choice(self.available))

    def _commit_bot(self, n: int) -> int:
        self.available.remove(n)
        self.bot_picks.append(n)
        return n

    def display(self) -> str:
        avail = " ".join(str(n) for n in sorted(self.available)) or "(none left)"
        team = " ".join(str(n) for n in self.team_picks) or "(none)"
        bot = " ".join(str(n) for n in self.bot_picks) or "(none)"
        return (
            f"Available: [ {avail} ]\n"
            f"  Your picks: [ {team} ]\n"
            f"  Bot picks:  [ {bot} ]"
        )

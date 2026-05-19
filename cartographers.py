import random
from copy import deepcopy
from itertools import product

EMPTY    = "."
FOREST   = "F"
VILLAGE  = "V"
FARM     = "A"
WATER    = "W"
WASTELAND = "X"
MOUNTAIN = "M"

TERRAIN_NAMES = {EMPTY:"Empty", FOREST:"Forest", VILLAGE:"Village",
                 FARM:"Farm", WATER:"Water", WASTELAND:"Wasteland", MOUNTAIN:"Mountain"}

DECK = [
    {"id": 1,  "shape": [(0,0),(0,1),(1,0)],            "terrain": FOREST,  "coin": False, "time": 1},
    {"id": 2,  "shape": [(0,0),(0,1),(0,2)],             "terrain": FARM,    "coin": False, "time": 1},
    {"id": 3,  "shape": [(0,0),(0,1),(1,1),(2,1)],       "terrain": VILLAGE, "coin": True,  "time": 1},
    {"id": 4,  "shape": [(0,0),(0,1),(1,1),(1,2)],       "terrain": WATER,   "coin": False, "time": 1},
    {"id": 5,  "shape": [(0,0)],                         "terrain": FOREST,  "coin": True,  "time": 1},
    {"id": 6,  "shape": [(0,0),(1,0),(2,0),(2,1)],       "terrain": FARM,    "coin": False, "time": 1},
    {"id": 7,  "shape": [(0,0),(0,1),(1,0),(1,1)],       "terrain": VILLAGE, "coin": False, "time": 1},
    {"id": 8,  "shape": [(0,0),(1,0)],                   "terrain": WATER,   "coin": True,  "time": 1},
    {"id": 9,  "shape": [(0,0),(0,1),(0,2),(1,1)],       "terrain": FOREST,  "coin": False, "time": 1},
    {"id": 10, "shape": [(0,0),(1,0),(1,1)],             "terrain": FARM,    "coin": True,  "time": 1},
    {"id": 11, "shape": [(0,0),(0,1),(1,0)],             "terrain": WATER,   "coin": False, "time": 1},
    {"id": 12, "shape": [(0,0),(1,0),(1,1),(1,2)],       "terrain": FOREST,  "coin": False, "time": 1},
    {"id": 13, "shape": [(0,0),(0,1)],                   "terrain": VILLAGE, "coin": True,  "time": 1},
    {"id": 14, "shape": [(0,0),(0,1),(0,2),(1,0)],       "terrain": FARM,    "coin": False, "time": 1},
    {"id": 15, "shape": [(0,0),(1,0),(2,0)],             "terrain": WATER,   "coin": False, "time": 1},
    {"id": 16, "shape": [(0,0),(0,1),(1,1),(2,1),(2,0)], "terrain": VILLAGE, "coin": False, "time": 1},
    {"id": 17, "shape": [(0,0),(1,0),(1,1),(2,0)],       "terrain": FOREST,  "coin": True,  "time": 1},
    {"id": 18, "shape": [(0,0),(0,1),(1,0),(2,0)],       "terrain": FARM,    "coin": False, "time": 1},
]

MOUNTAIN_CELLS = {(1, 9), (5, 5), (9, 1)}

SEASONS = [
    {"name": "Spring", "threshold": 4,  "objectives": ["A", "B"]},
    {"name": "Summer", "threshold": 4,  "objectives": ["B", "C"]},
    {"name": "Autumn", "threshold": 6,  "objectives": ["C", "D"]},
    {"name": "Winter", "threshold": 6,  "objectives": ["D", "A"]},
]


def rotate_shape(shape, times=1):
    s = list(shape)
    for _ in range(times):
        s = [(-c, r) for r, c in s]
    return _normalise(s)

def flip_shape(shape):
    return _normalise([(r, -c) for r, c in shape])

def _normalise(shape):
    min_r = min(r for r, c in shape)
    min_c = min(c for r, c in shape)
    return [(r - min_r, c - min_c) for r, c in shape]

def all_orientations(shape):
    seen, result = set(), []
    for flipped in [shape, flip_shape(shape)]:
        for rot in range(4):
            s = tuple(sorted(rotate_shape(flipped, rot)))
            if s not in seen:
                seen.add(s)
                result.append(list(s))
    return result


class CartographersGame:
    RULES = """GAME: Cartographers
You are mapping an 11x11 grid. Each turn a terrain card is revealed.
Place its shape (in any rotation/flip) onto empty cells of the grid.
Maximise your score across 4 seasonal scoring phases.

TERRAIN TYPES: Forest(F), Village(V), Farm(A), Water(W), Wasteland(X)
MOUNTAINS(M) are fixed at (1,9), (5,5), (9,1) — cannot be overwritten.

SCORING OBJECTIVES:
  A — SENTINEL WOOD:  +1 per Forest in leftmost or rightmost column
  B — CANAL LAKE:     +1 per Water adjacent to at least one Farm
  C — GREENBOUGH:     +1 per row containing at least one Forest
  D — MAGES VALLEY:   +2 per Water adjacent to a Mountain cell

SEASONS: Spring(A+B), Summer(B+C), Autumn(C+D), Winter(D+A)
Each objective scores in two seasons — placement decisions compound.

ACTIONS: Propose a placement as:
  PLACE: row col orientation_index
  (orientation_index 0-7 indexes available rotations/flips)
Or: WASTELAND: row col  (if no valid placement exists)"""

    def __init__(self):
        self.grid = [[EMPTY] * 11 for _ in range(11)]
        for (r, c) in MOUNTAIN_CELLS:
            self.grid[r][c] = MOUNTAIN

        self.deck          = deepcopy(DECK)
        random.shuffle(self.deck)
        self.discard: list = []

        self.season_idx    = 0
        self.season_time   = 0
        self.current_card  = None
        self.coins         = 0
        self.season_scores: list[int] = []
        self.history: list[dict]      = []

    # ── Card draw ────────────────────────────────────────────────────────
    def draw_card(self):
        if not self.deck:
            self.deck = deepcopy(DECK)
            random.shuffle(self.deck)
        self.current_card = self.deck.pop(0)
        return self.current_card

    def season_complete(self) -> bool:
        return self.season_time >= SEASONS[self.season_idx]["threshold"]

    # ── Placement helpers ─────────────────────────────────────────────────
    def valid_placements(self, shape: list) -> list[tuple[int, int]]:
        """Return all (row, col) anchor positions where shape fits."""
        positions = []
        for r in range(11):
            for c in range(11):
                cells = [(r + dr, c + dc) for dr, dc in shape]
                if all(0 <= rr < 11 and 0 <= cc < 11 and self.grid[rr][cc] == EMPTY
                       for rr, cc in cells):
                    positions.append((r, c))
        return positions

    def place(self, shape: list, terrain: str, anchor_r: int, anchor_c: int) -> bool:
        cells = [(anchor_r + dr, anchor_c + dc) for dr, dc in shape]
        if not all(0 <= r < 11 and 0 <= c < 11 and self.grid[r][c] == EMPTY for r, c in cells):
            return False
        for r, c in cells:
            self.grid[r][c] = terrain
        return True

    def place_wasteland(self, r: int, c: int) -> bool:
        if self.grid[r][c] != EMPTY:
            return False
        self.grid[r][c] = WASTELAND
        return True

    # ── Card play ─────────────────────────────────────────────────────────
    def play_card(self, orientation_idx: int, anchor_r: int, anchor_c: int) -> dict:
        card   = self.current_card
        shapes = all_orientations(card["shape"])
        if orientation_idx >= len(shapes):
            orientation_idx = 0
        shape = shapes[orientation_idx]

        result = {"card_id": card["id"], "terrain": card["terrain"], "events": []}

        if not self.place(shape, card["terrain"], anchor_r, anchor_c):
            # fallback: place wasteland at anchor
            self.place_wasteland(anchor_r, anchor_c)
            result["events"].append(f"Invalid placement; placed WASTELAND at ({anchor_r},{anchor_c}).")
        else:
            result["events"].append(f"Placed {TERRAIN_NAMES[card['terrain']]} at ({anchor_r},{anchor_c}) orientation {orientation_idx}.")
            if card["coin"]:
                self.coins += 1
                result["events"].append("Earned 1 coin.")

        self.season_time += card["time"]
        self.discard.append(card)
        self.history.append(result)

        if self.season_complete():
            pts = self._score_season()
            self.season_scores.append(pts)
            result["events"].append(f"{SEASONS[self.season_idx]['name']} ends — scored {pts} points.")
            self.season_idx  += 1
            self.season_time  = 0
            self.deck = deepcopy(DECK)
            random.shuffle(self.deck)
            self.current_card = None

        return result

    # ── Scoring ───────────────────────────────────────────────────────────
    def _neighbours(self, r: int, c: int) -> list[tuple[int, int]]:
        return [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                if 0 <= r+dr < 11 and 0 <= c+dc < 11]

    def _score_objective(self, obj: str) -> int:
        g = self.grid
        if obj == "A":
            return sum(1 for r in range(11) if g[r][0] == FOREST or g[r][10] == FOREST)
        if obj == "B":
            pts = 0
            for r in range(11):
                for c in range(11):
                    if g[r][c] == WATER:
                        if any(g[nr][nc] == FARM for nr, nc in self._neighbours(r, c)):
                            pts += 1
            return pts
        if obj == "C":
            return sum(1 for r in range(11) if any(g[r][c] == FOREST for c in range(11)))
        if obj == "D":
            pts = 0
            for r in range(11):
                for c in range(11):
                    if g[r][c] == WATER:
                        if any(g[nr][nc] == MOUNTAIN for nr, nc in self._neighbours(r, c)):
                            pts += 2
            return pts
        return 0

    def _score_season(self) -> int:
        objs = SEASONS[self.season_idx]["objectives"]
        return sum(self._score_objective(o) for o in objs)

    def total_score(self) -> int:
        return sum(self.season_scores) + self.coins

    def status(self) -> str:
        if self.season_idx >= 4:
            return "complete"
        return "ongoing"

    # ── Display ───────────────────────────────────────────────────────────
    def display(self) -> str:
        season = SEASONS[min(self.season_idx, 3)]
        lines = [
            f"Season: {season['name']}  (time {self.season_time}/{season['threshold']})  "
            f"Coins: {self.coins}  Score so far: {self.total_score()}",
            f"Objectives this season: {' + '.join(season['objectives'])}",
            "",
        ]
        # grid
        lines.append("     " + " ".join(str(c).rjust(2) for c in range(11)))
        for r in range(11):
            row = " ".join(self.grid[r][c].center(2) for c in range(11))
            lines.append(f"  {r:2d} {row}")
        lines.append("")
        if self.current_card:
            c = self.current_card
            orientations = all_orientations(c["shape"])
            lines.append(f"Current card: {TERRAIN_NAMES[c['terrain']]}  coin={c['coin']}  "
                         f"orientations available: {len(orientations)}")
            lines.append(f"  Shape (orientation 0): {orientations[0]}")
        if self.season_scores:
            lines.append(f"Season scores so far: {self.season_scores}")
        return "\n".join(lines)

    # ── Action parsing ────────────────────────────────────────────────────
    def execute(self, action_tuple: tuple) -> dict:
        action, orientation_idx, r, c = action_tuple
        if action == "WASTELAND":
            ok = self.place_wasteland(r, c)
            return {"events": [f"Placed WASTELAND at ({r},{c})." if ok else f"Invalid wasteland cell ({r},{c})."]}
        return self.play_card(orientation_idx, r, c)

    def parse_action(self, text: str) -> tuple[str, int, int, int]:
        """Returns (action, orientation_idx, row, col)."""
        import re
        m = re.search(r"PLACE:\s*(\d+)\s+(\d+)\s+(\d+)", text, re.IGNORECASE)
        if m:
            return "PLACE", int(m.group(3)), int(m.group(1)), int(m.group(2))
        m2 = re.search(r"WASTELAND:\s*(\d+)\s+(\d+)", text, re.IGNORECASE)
        if m2:
            return "WASTELAND", 0, int(m2.group(1)), int(m2.group(2))
        # fallback: pick first valid placement of orientation 0
        if self.current_card:
            shapes = all_orientations(self.current_card["shape"])
            for r, c in product(range(11), range(11)):
                cells = [(r+dr, c+dc) for dr, dc in shapes[0]]
                if all(0<=rr<11 and 0<=cc<11 and self.grid[rr][cc]==EMPTY for rr,cc in cells):
                    return "PLACE", 0, r, c
        return "WASTELAND", 0, 0, 0

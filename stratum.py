import random


class StratumGame:
    RULES = """GAME: Stratum
You are excavating 5 archaeological columns (0–4).
Each column has a hidden collapse threshold (3–7 depth units).
If you dig a column to or past its threshold, it COLLAPSES and scores 0.

ACTIONS (choose one per turn):
  DIG(col, intensity)  — dig column col by 1, 2, or 3 depth units
  SHORE(col)           — add a brace to col, raising its effective threshold by 1
  BRACE(col)           — spend a brace token to reveal if col is STABLE or NEAR COLLAPSE

SCORING (after 10 turns):
  Each surviving (non-collapsed) column scores depth² points.
  Collapsed columns score 0.
  Target: beat 60 points.

SIGNALS:
  A column RUMBLES when depth reaches threshold-1 (one step from collapse).
  A column COLLAPSES when depth reaches threshold."""

    def __init__(self):
        self.thresholds = [random.randint(3, 7) for _ in range(5)]
        self.depths     = [0] * 5
        self.collapsed  = [False] * 5
        self.shores     = [0] * 5   # extra threshold from SHORE actions
        self.brace_tokens = 3
        self.turn         = 0
        self.max_turns    = 10
        self.history: list[dict] = []

    def effective_threshold(self, col: int) -> int:
        return self.thresholds[col] + self.shores[col]

    def status(self) -> str:
        if self.turn >= self.max_turns:
            return "complete"
        return "ongoing"

    def score(self) -> int:
        return sum(d ** 2 for d, c in zip(self.depths, self.collapsed) if not c)

    def act(self, action: str, col: int, intensity: int = 1) -> dict:
        """Execute an action. Returns a result dict with outcome details."""
        action = action.upper()
        result = {"action": action, "col": col, "intensity": intensity, "events": []}

        if col < 0 or col > 4:
            result["events"].append(f"Invalid column {col}.")
            return result

        if action == "DIG":
            if self.collapsed[col]:
                result["events"].append(f"Column {col} is already collapsed — cannot dig.")
                return result
            self.depths[col] += intensity
            result["events"].append(f"Column {col} dug to depth {self.depths[col]}.")
            eff = self.effective_threshold(col)
            if self.depths[col] >= eff:
                self.collapsed[col] = True
                result["events"].append(f"Column {col} COLLAPSES! (threshold was {eff})")
            elif self.depths[col] == eff - 1:
                result["events"].append(f"Column {col} RUMBLES. (one step from collapse)")

        elif action == "SHORE":
            if self.collapsed[col]:
                result["events"].append(f"Column {col} is already collapsed — cannot shore.")
                return result
            self.shores[col] += 1
            result["events"].append(f"Column {col} shored. Effective threshold now {self.effective_threshold(col)}.")

        elif action == "BRACE":
            if self.brace_tokens <= 0:
                result["events"].append("No brace tokens remaining.")
                return result
            self.brace_tokens -= 1
            eff = self.effective_threshold(col)
            if self.depths[col] >= eff - 1:
                result["events"].append(f"Column {col}: NEAR COLLAPSE (depth {self.depths[col]}, threshold ~{eff}).")
            else:
                result["events"].append(f"Column {col}: STABLE (depth {self.depths[col]}, threshold >{self.depths[col] + 1}).")

        else:
            result["events"].append(f"Unknown action: {action}")
            return result

        self.turn += 1
        self.history.append(result)
        return result

    def display(self) -> str:
        lines = [f"Turn {self.turn}/{self.max_turns}   Brace tokens: {self.brace_tokens}   Score so far: {self.score()}"]
        lines.append("")
        header = "  Col:  " + "  ".join(f"  {i}  " for i in range(5))
        lines.append(header)

        depth_row = "  Depth: " + "  ".join(f"  {self.depths[i]}  " for i in range(5))
        lines.append(depth_row)

        status_row = "  State: " + "  ".join(
            " [X] " if self.collapsed[i] else f" [{self.depths[i]}d] "
            for i in range(5)
        )
        lines.append(status_row)

        shore_row = "  Shore: " + "  ".join(f" +{self.shores[i]}  " for i in range(5))
        lines.append(shore_row)
        lines.append("")
        lines.append(f"  Current score (if game ended now): {self.score()}")
        return "\n".join(lines)

    def execute(self, action_tuple: tuple) -> dict:
        action, col, intensity = action_tuple
        return self.act(action, col, intensity)

    def parse_action(self, text: str) -> tuple[str, int, int]:
        """Parse ACTION: DIG/SHORE/BRACE col [intensity] from agent text."""
        import re
        m = re.search(r"ACTION:\s*(DIG|SHORE|BRACE)\s*(\d)\s*(?:intensity\s*)?(\d)?", text, re.IGNORECASE)
        if m:
            action    = m.group(1).upper()
            col       = int(m.group(2))
            intensity = int(m.group(3)) if m.group(3) else 1
            return action, col, intensity

        # fallback: look for any DIG/SHORE/BRACE + digit
        m2 = re.search(r"\b(DIG|SHORE|BRACE)\b.*?(\d)", text, re.IGNORECASE)
        if m2:
            action = m2.group(1).upper()
            col    = int(m2.group(2))
            m3 = re.search(r"\bintensity\s*(\d)\b|\bby\s*(\d)\b", text, re.IGNORECASE)
            intensity = int(m3.group(1) or m3.group(2)) if m3 else 1
            intensity = min(max(intensity, 1), 3)
            return action, col, intensity

        # last resort: DIG col 0 intensity 1
        return "DIG", 0, 1

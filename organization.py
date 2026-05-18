import re
import anthropic
import json

from agents import Agent
from doctrine import Doctrine


class Organization:
    def __init__(self, name: str, agents: list[Agent], goal: str):
        self.name = name
        self.agents = agents
        self.goal = goal
        self.doctrine = Doctrine(name)
        self._client = anthropic.Anthropic()

    def run(self, rounds: int = 3):
        print(f"\n{'='*60}")
        print(f"  {self.name}")
        print(f"  Goal: {self.goal}")
        print(f"{'='*60}")

        transcript_lines: list[str] = []
        doctrine_context = self.doctrine.to_context()

        for round_num in range(1, rounds + 1):
            print(f"\n--- Round {round_num} ---")
            transcript = "\n".join(transcript_lines) if transcript_lines else "(conversation just started)"

            for agent in self.agents:
                prompt = (
                    f"Team conversation so far:\n\n{transcript}\n\n"
                    f"It's your turn. Respond as {agent.name}."
                )
                response = agent.run(prompt, doctrine_context, self.goal)
                transcript_lines.append(f"{agent.name}: {response}")
                print(f"\n[{agent.name}]\n{response}")

        print("\n--- Scribe synthesizing doctrine ---")
        new_entries = self._synthesize("\n".join(transcript_lines))

        if new_entries:
            self.doctrine.add(new_entries)
            print(f"\n{len(new_entries)} new doctrine entries:")
            for e in self.doctrine.entries[-len(new_entries):]:
                print(f"  • [{e.learned_by}] {e.principle}")
        else:
            print("No new entries extracted.")

        print(f"\nDoctrine saved → {self.doctrine.path}")

    def play_game(self, game, verbose: bool = True) -> str:
        """Play one game session. Agents discuss each move; doctrine updated after."""
        doctrine_context = self.doctrine.to_context()
        move_log: list[str] = []
        full_transcript: list[str] = []

        print(f"\n{game.RULES}\n")

        while game.status() == "ongoing":
            state = game.display()
            print(f"\n{state}")

            history = "\n".join(full_transcript) if full_transcript else "(game just started)"
            prompt = (
                f"{game.RULES}\n\n"
                f"Current state:\n{state}\n\n"
                f"Available numbers: {sorted(game.available)}\n\n"
                f"Discussion so far:\n{history}\n\n"
                f"Discuss briefly, then end your message with: PICK: <number>"
            )

            discussion: list[str] = []
            for agent in self.agents:
                context = prompt if not discussion else "\n".join(discussion)
                response = agent.run(context, doctrine_context, self.goal)
                line = f"{agent.name}: {response}"
                discussion.append(line)
                full_transcript.append(line)
                if verbose:
                    print(f"\n[{agent.name}] {response}")

            move = self._parse_move(" ".join(discussion), game.available)
            game.team_move(move)
            move_log.append(f"Team→{move}")
            print(f"\n>>> Team picks: {move}")

            if game.status() != "ongoing":
                break

            bot = game.bot_move()
            move_log.append(f"Bot→{bot}")
            print(f">>> Bot picks:  {bot}")

        outcome = game.status()
        label = {"org_wins": "WIN ✓", "bot_wins": "LOSS ✗", "draw": "DRAW —"}[outcome]
        print(f"\n{'='*40}\nResult: {label}\nMoves: {', '.join(move_log)}\n{'='*40}")

        # Post-game debrief
        debrief = (
            f"Game over — {label}.\n"
            f"Move sequence: {', '.join(move_log)}\n\n"
            f"Discuss: what worked, what failed, what should we do differently next game?"
        )
        full_transcript.append(debrief)

        for agent in self.agents:
            response = agent.run("\n".join(full_transcript), doctrine_context, self.goal)
            line = f"{agent.name}: {response}"
            full_transcript.append(line)
            if verbose:
                print(f"\n[{agent.name} debrief] {response}")

        new_entries = self._synthesize("\n".join(full_transcript))
        if new_entries:
            self.doctrine.add(new_entries)
            print(f"\n+{len(new_entries)} doctrine entries saved.")

        return outcome

    def _parse_move(self, text: str, available: list[int]) -> int:
        match = re.search(r"PICK:\s*(\d+)", text, re.IGNORECASE)
        if match:
            n = int(match.group(1))
            if n in available:
                return n
        for n in sorted(available, reverse=True):
            if str(n) in text.split():
                return n
        return available[0]

    def _synthesize(self, transcript: str) -> list[dict]:
        prompt = f"""You are a Scribe for "{self.name}".

Read this conversation and extract 2-4 concrete organizational principles — tribal knowledge about what worked, what tensions produced good results, and what agent combinations or behaviors proved effective.

Return ONLY valid JSON:
{{
  "entries": [
    {{
      "principle": "one clear sentence",
      "learned_by": "agent name or 'Organization'",
      "context": "when this applies (one short phrase)"
    }}
  ]
}}

Conversation:
{transcript}"""

        response = self._client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = next(block.text for block in response.content if block.type == "text")

        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end]).get("entries", [])
        except (json.JSONDecodeError, ValueError):
            return []

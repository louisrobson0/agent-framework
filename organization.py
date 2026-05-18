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

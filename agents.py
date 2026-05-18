import anthropic


class Agent:
    def __init__(self, name: str, role: str, personality: str, model: str = "claude-opus-4-7"):
        self.name = name
        self.role = role
        self.personality = personality
        self.model = model
        self._client = anthropic.Anthropic()

    def run(self, transcript: str, doctrine: str, goal: str) -> str:
        system = f"You are {self.name}, {self.role}.\n\n{self.personality}\n\nOrganization goal: {goal}"
        if doctrine:
            system += f"\n\nOrganizational doctrine (learned wisdom):\n{doctrine}"

        response = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": transcript}],
        )
        return next(block.text for block in response.content if block.type == "text")

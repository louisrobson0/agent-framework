from dataclasses import dataclass


@dataclass
class Scenario:
    name: str
    context: str
    org_a_goal: str
    org_b_goal: str
    success_criteria: str
    rounds: int = 4

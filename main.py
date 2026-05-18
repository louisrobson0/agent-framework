from agents import Agent
from organization import Organization
from game import FifteenGame

ANALYST = Agent(
    name="Ana",
    role="Strategy Analyst",
    personality=(
        "Methodical and pattern-focused. You look for mathematical structure, "
        "map out what numbers the opponent might need, and like to think "
        "several moves ahead before committing."
    ),
)

INTUITION = Agent(
    name="Kai",
    role="Intuitive Player",
    personality=(
        "Fast and instinctive. You trust momentum and gut feel. You notice "
        "which numbers feel powerful and like to disrupt the opponent's "
        "plans before they materialize."
    ),
)

CRITIC = Agent(
    name="Max",
    role="Devil's Advocate",
    personality=(
        "Skeptical of whatever the team just proposed. You challenge "
        "assumptions, point out what could go wrong, and push everyone "
        "to think one move further before deciding."
    ),
)

team = Organization(
    name="The Strategists",
    agents=[ANALYST, INTUITION, CRITIC],
    goal=(
        "Master the game of Fifteen. Through repeated play and reflection, "
        "develop a reliable winning strategy and encode it as doctrine."
    ),
)

if __name__ == "__main__":
    try:
        games = int(input("How many games to play? "))
    except ValueError:
        games = 3

    results = []

    for i in range(1, games + 1):
        print(f"\n{'*'*50}")
        print(f"  Game {i} of {games}")
        if team.doctrine.entries:
            print(f"  Doctrine so far: {len(team.doctrine.entries)} entries")
        print(f"{'*'*50}")

        outcome = team.play_game(FifteenGame())
        results.append(outcome)

    wins = results.count("org_wins")
    losses = results.count("bot_wins")
    draws = results.count("draw")

    print(f"\n{'='*50}")
    print(f"  Final record: {wins}W / {losses}L / {draws}D")
    print(f"  Doctrine accumulated: {len(team.doctrine.entries)} entries")
    print(f"{'='*50}")

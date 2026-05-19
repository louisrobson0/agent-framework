from agents import Agent
from organization import Organization
from game import FifteenGame
from stratum import StratumGame
from cartographers import CartographersGame

ANALYST = Agent(
    name="Alice",
    role="Strategy Analyst",
    personality=(
        "Methodical and pattern-focused. You enumerate options, estimate probabilities, "
        "and minimise variance. You want full information before committing to a move."
    ),
)

BOLD = Agent(
    name="Bob",
    role="Bold Player",
    personality=(
        "Fast and aggressive. You maximise expected value and accept tail risk. "
        "You'd rather push hard and occasionally fail than play timid and leave points on the table."
    ),
)

SKEPTIC = Agent(
    name="Carol",
    role="Devil's Advocate",
    personality=(
        "Skeptical of whatever the team just proposed. You challenge assumptions, "
        "point out what could go wrong, and push everyone to think one step further before deciding."
    ),
)

GAMES = {
    "1": ("Fifteen (vs bot)",     "fifteen"),
    "2": ("Stratum (excavation)", "stratum"),
    "3": ("Cartographers (map)",  "cartographers"),
}

GOALS = {
    "fifteen":      "Master the game of Fifteen. Develop a reliable winning strategy.",
    "stratum":      "Master Stratum. Learn when to dig aggressively versus play safe. Beat 60 points.",
    "cartographers":"Master Cartographers. Learn how to place terrain efficiently for maximum score. Beat 30 points.",
}

if __name__ == "__main__":
    print("\nChoose a game:")
    for k, (label, _) in GAMES.items():
        print(f"  {k}. {label}")
    choice = input("Enter 1, 2, or 3: ").strip()
    _, game_key = GAMES.get(choice, ("", "stratum"))

    team = Organization(
        name="The Strategists",
        agents=[ANALYST, BOLD, SKEPTIC],
        goal=GOALS[game_key],
    )

    try:
        games = int(input("How many games to play? "))
    except ValueError:
        games = 3

    scores = []

    for i in range(1, games + 1):
        print(f"\n{'*'*50}")
        print(f"  Game {i} of {games}  [{game_key.upper()}]")
        if team.doctrine.entries:
            print(f"  Doctrine so far: {len(team.doctrine.entries)} entries")
        print(f"{'*'*50}")

        if game_key == "fifteen":
            outcome = team.play_game(FifteenGame())
            scores.append(outcome)
        elif game_key == "stratum":
            score = team.play_solo_game(StratumGame())
            scores.append(score)
        elif game_key == "cartographers":
            score = team.play_solo_game(CartographersGame())
            scores.append(score)

    print(f"\n{'='*50}")
    if game_key == "fifteen":
        wins   = scores.count("org_wins")
        losses = scores.count("bot_wins")
        draws  = scores.count("draw")
        print(f"  Final record: {wins}W / {losses}L / {draws}D")
    else:
        target = 60 if game_key == "stratum" else 30
        beats  = sum(1 for s in scores if s >= target)
        print(f"  Scores: {scores}")
        print(f"  Beat target ({target}): {beats}/{games} games")
    print(f"  Doctrine accumulated: {len(team.doctrine.entries)} entries")
    print(f"{'='*50}")

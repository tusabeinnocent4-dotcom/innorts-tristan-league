import json
import os

DATA_FILE = "league_data.json"
TEAM_COUNT = 12


def create_empty_data():
    return {"teams": [], "fixtures": []}


def save_data(data):
    """Save league information so it is available next time."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_data():
    """Load saved league information, or start a new league."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict) and "teams" in data and "fixtures" in data:
                return data
        except (json.JSONDecodeError, OSError):
            print("The saved data file could not be read. Starting a new league.")
    return create_empty_data()


def register_teams(data):
    if data["fixtures"]:
        print("Fixtures already exist. Start a new league file to change the teams.")
        return

    teams = []
    print("\nEnter the names of your 12 teams.")
    while len(teams) < TEAM_COUNT:
        name = input(f"Team {len(teams) + 1}: ").strip()
        if not name:
            print("Team name cannot be empty.")
        elif name.casefold() in [team.casefold() for team in teams]:
            print("That team name has already been entered.")
        else:
            teams.append(name)

    data["teams"] = teams
    save_data(data)
    print("All 12 teams have been saved.")


def generate_fixtures(data):
    teams = data["teams"]
    if len(teams) != TEAM_COUNT:
        print("Please register exactly 12 teams first.")
        return
    if data["fixtures"]:
        print("Fixtures have already been generated.")
        return

    # Circle method: 12 teams make 11 rounds, with 6 matches per round.
    rotation = teams[:]
    first_leg = []
    for round_number in range(TEAM_COUNT - 1):
        round_matches = []
        for i in range(TEAM_COUNT // 2):
            team_a = rotation[i]
            team_b = rotation[TEAM_COUNT - 1 - i]

            # Alternate home advantage to keep the schedule balanced.
            if (round_number + i) % 2 == 0:
                home, away = team_a, team_b
            else:
                home, away = team_b, team_a

            round_matches.append({
                "matchday": round_number + 1,
                "home": home,
                "away": away,
                "home_goals": None,
                "away_goals": None,
                "played": False
            })
        first_leg.extend(round_matches)

        # Keep the first team fixed and rotate the other eleven teams.
        rotation = [rotation[0], rotation[-1]] + rotation[1:-1]

    # Second leg: reverse home and away for every first-leg fixture.
    second_leg = []
    for match in first_leg:
        second_leg.append({
            "matchday": match["matchday"] + (TEAM_COUNT - 1),
            "home": match["away"],
            "away": match["home"],
            "home_goals": None,
            "away_goals": None,
            "played": False
        })

    data["fixtures"] = first_leg + second_leg
    save_data(data)
    print("Fixtures generated: 22 matchdays, 6 matches per matchday, 132 matches total.")


def show_fixtures(data, played_filter=None):
    if not data["fixtures"]:
        print("No fixtures yet. Register teams and generate fixtures first.")
        return

    if played_filter is None:
        matches = data["fixtures"]
        heading = "ALL FIXTURES"
    elif played_filter:
        matches = [m for m in data["fixtures"] if m["played"]]
        heading = "COMPLETED MATCHES"
    else:
        matches = [m for m in data["fixtures"] if not m["played"]]
        heading = "REMAINING MATCHES"

    print(f"\n{heading}")
    current_day = None
    for index, match in enumerate(matches, start=1):
        if match["matchday"] != current_day:
            current_day = match["matchday"]
            print(f"\n--- MATCHDAY {current_day} ---")

        if match["played"]:
            score = f'{match["home_goals"]} - {match["away_goals"]}'
            status = "PLAYED"
        else:
            score = "vs"
            status = "UPCOMING"

        print(f'{match["home"]}  {score}  {match["away"]} [{status}]')

    print(f"\nMatches shown: {len(matches)}")


def show_one_matchday(data):
    if not data["fixtures"]:
        print("Generate fixtures first.")
        return

    try:
        matchday = int(input("Enter matchday (1-22): "))
    except ValueError:
        print("Please enter a whole number.")
        return

    if not 1 <= matchday <= 22:
        print("Matchday must be between 1 and 22.")
        return

    matches = [m for m in data["fixtures"] if m["matchday"] == matchday]
    print(f"\n--- MATCHDAY {matchday} ---")
    for match in matches:
        if match["played"]:
            print(f'{match["home"]} {match["home_goals"]} - '
                  f'{match["away_goals"]} {match["away"]}')
        else:
            print(f'{match["home"]} vs {match["away"]}  [Not played]')


def enter_result(data):
    if not data["fixtures"]:
        print("Generate fixtures first.")
        return

    remaining = [m for m in data["fixtures"] if not m["played"]]
    if not remaining:
        print("All matches have been played.")
        return

    print("\nUNPLAYED FIXTURES")
    for number, match in enumerate(remaining, start=1):
        print(f'{number}. MD {match["matchday"]}: '
              f'{match["home"]} vs {match["away"]}')

    try:
        choice = int(input("Choose a fixture number (0 to cancel): "))
    except ValueError:
        print("Please enter a whole number.")
        return

    if choice == 0:
        return
    if not 1 <= choice <= len(remaining):
        print("That fixture number is not valid.")
        return

    match = remaining[choice - 1]
    try:
        home_goals = int(input(f'Goals scored by {match["home"]}: '))
        away_goals = int(input(f'Goals scored by {match["away"]}: '))
        if home_goals < 0 or away_goals < 0:
            print("Goals cannot be negative.")
            return
    except ValueError:
        print("Goals must be whole numbers.")
        return

    match["home_goals"] = home_goals
    match["away_goals"] = away_goals
    match["played"] = True
    save_data(data)
    print(f'Result saved: {match["home"]} {home_goals} - '
          f'{away_goals} {match["away"]}')
    print("The league table will update automatically.")


def calculate_table(data):
    table = {}
    for team in data["teams"]:
        table[team] = {
            "P": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0
        }

    for match in data["fixtures"]:
        if not match["played"]:
            continue

        home = table[match["home"]]
        away = table[match["away"]]
        hg = match["home_goals"]
        ag = match["away_goals"]

        home["P"] += 1
        away["P"] += 1
        home["GF"] += hg
        home["GA"] += ag
        away["GF"] += ag
        away["GA"] += hg

        if hg > ag:
            home["W"] += 1
            home["Pts"] += 3
            away["L"] += 1
        elif hg < ag:
            away["W"] += 1
            away["Pts"] += 3
            home["L"] += 1
        else:
            home["D"] += 1
            away["D"] += 1
            home["Pts"] += 1
            away["Pts"] += 1

    for stats in table.values():
        stats["GD"] = stats["GF"] - stats["GA"]

    # Premier League style: points, goal difference, then goals scored.
    return sorted(
        table.items(),
        key=lambda item: (
            item[1]["Pts"], item[1]["GD"], item[1]["GF"], item[0].casefold()
        ),
        reverse=True
    )


def show_table(data):
    if len(data["teams"]) != TEAM_COUNT:
        print("Please register all 12 teams first.")
        return

    standings = calculate_table(data)

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    GOLD = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    RED = "\033[91m"
    DIM = "\033[90m"

    width = 105
    line = "═" * width
    thin = "─" * width

    print()
    print(f"{GOLD}╔{line}╗{RESET}")
    print(f"{GOLD}║{RESET}{BOLD}{CYAN}{'🏆  INNORTS TRISTAN LEAGUE — OFFICIAL STANDINGS':^{width}}{RESET}{GOLD}║{RESET}")
    print(f"{GOLD}║{RESET}{WHITE}{'THE BEAUTIFUL GAME • 12 TEAMS • HOME & AWAY':^{width}}{RESET}{GOLD}║{RESET}")
    print(f"{GOLD}╠{line}╣{RESET}")

    header = (
        f"{'POS':>3}  {'CLUB':<23} {'P':>3} {'W':>3} {'D':>3} "
        f"{'L':>3} {'GF':>4} {'GA':>4} {'GD':>4} {'PTS':>4}"
    )
    print(f"{GOLD}║{RESET} {BOLD}{WHITE}{header:<{width-2}}{RESET}{GOLD}║{RESET}")
    print(f"{GOLD}╟{thin}╢{RESET}")

    for position, (team, stats) in enumerate(standings, start=1):
        if position == 1:
            colour, marker = GOLD, "👑"
        elif position <= 4:
            colour, marker = GREEN, "★"
        elif position >= 11:
            colour, marker = RED, "!"
        else:
            colour, marker = WHITE, " "

        row = (
            f"{position:>3}  {team[:23]:<23} "
            f'{stats["P"]:>3} {stats["W"]:>3} {stats["D"]:>3} '
            f'{stats["L"]:>3} {stats["GF"]:>4} {stats["GA"]:>4} '
            f'{stats["GD"]:>4} {stats["Pts"]:>4}'
        )
        print(f"{GOLD}║{RESET} {colour}{marker} {row:<{width-4}}{RESET} {GOLD}║{RESET}")

    print(f"{GOLD}╠{line}╣{RESET}")
    played_count = sum(1 for match in data["fixtures"] if match["played"])
    total_count = len(data["fixtures"])
    remaining_count = total_count - played_count

    footer1 = f"  FOOTBALL MATCHES PLAYED: {played_count}/{total_count}"
    footer2 = f"  MATCHES REMAINING: {remaining_count}"
    footer3 = "  SCORING: WIN = 3 PTS  |  DRAW = 1 PT  |  LOSS = 0 PTS"
    print(f"{GOLD}║{RESET}{CYAN}{footer1:<{width}}{RESET}{GOLD}║{RESET}")
    print(f"{GOLD}║{RESET}{BLUE}{footer2:<{width}}{RESET}{GOLD}║{RESET}")
    print(f"{GOLD}║{RESET}{WHITE}{footer3:<{width}}{RESET}{GOLD}║{RESET}")
    print(f"{GOLD}╚{line}╝{RESET}")
    print(f"{DIM}  POS = Position | P = Played | W = Won | D = Drawn | L = Lost{RESET}")
    print(f"{DIM}  GF = Goals For | GA = Goals Against | GD = Goal Difference | PTS = Points{RESET}")


def print_menu():
    print("\n" + "=" * 44)
    print("       FOOTBALL LEAGUE MANAGER")
    print("=" * 44)
    print("1. Register 12 teams")
    print("2. Generate home-and-away fixtures")
    print("3. View all fixtures")
    print("4. View fixtures by matchday")
    print("5. Enter a match result")
    print("6. View league table")
    print("7. View completed matches")
    print("8. View remaining matches")
    print("9. Save league data")
    print("10. Exit")
    print("=" * 44)


def main():
    data = load_data()
    print("Welcome to the 12-Team Football League Manager!")
    if data["teams"]:
        print(f'Loaded saved league with {len(data["teams"])} team(s).')
    if data["fixtures"]:
        played = sum(1 for match in data["fixtures"] if match["played"])
        print(f'Loaded {len(data["fixtures"])} fixtures; {played} played.')

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            register_teams(data)
        elif choice == "2":
            generate_fixtures(data)
        elif choice == "3":
            show_fixtures(data)
        elif choice == "4":
            show_one_matchday(data)
        elif choice == "5":
            enter_result(data)
        elif choice == "6":
            show_table(data)
        elif choice == "7":
            show_fixtures(data, played_filter=True)
        elif choice == "8":
            show_fixtures(data, played_filter=False)
        elif choice == "9":
            save_data(data)
            print(f"League data saved to {DATA_FILE}.")
        elif choice == "10":
            save_data(data)
            print("League saved. Goodbye!")
            break
        else:
            print("Invalid choice. Please choose a number from 1 to 10.")


if __name__ == "__main__":
    main()

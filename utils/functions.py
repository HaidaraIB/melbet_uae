from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
from groups.group_preferences.constants import BRANDS, LEAGUES


def generate_infographic(team1: str, stats1: dict, team2: str, stats2: dict) -> BytesIO:
    # Collect all common keys
    labels = list(stats1.keys())

    values1 = []
    values2 = []
    for label in labels:
        val1 = stats1.get(label, 0) or 0
        val2 = stats2.get(label, 0) or 0

        # Handle percentage values
        if isinstance(val1, str) and val1.endswith("%"):
            val1 = float(val1.strip("%")) / 100
        if isinstance(val2, str) and val2.endswith("%"):
            val2 = float(val2.strip("%")) / 100

        try:
            values1.append(float(val1))
            values2.append(float(val2))
        except (ValueError, TypeError):
            values1.append(0.0)
            values2.append(0.0)

    x = range(len(labels))
    # Dynamic figure size with minimum height
    fig_height = max(6, 0.5 * len(labels) + 2)
    plt.figure(figsize=(12, fig_height))

    bar1 = plt.barh(
        x,
        values1,
        height=0.4,
        label=team1,
        color="#1f77b4",
    )
    bar2 = plt.barh(
        [i + 0.4 for i in x],
        values2,
        height=0.4,
        label=team2,
        color="#d62728",
    )

    plt.yticks([i + 0.2 for i in x], labels)
    plt.xlabel("Value")
    plt.title("Match Statistics")
    plt.legend()

    # Determine a good position for the text labels
    max_value = max(max(values1), max(values2)) if values1 or values2 else 1
    text_offset = max_value * 0.05  # 5% of max value as offset

    # Add value labels
    for bars in [bar1, bar2]:
        for bar in bars:
            plt.text(
                bar.get_width() + text_offset,
                bar.get_y() + bar.get_height() / 2,
                (
                    f"{bar.get_width():.1f}"
                    if isinstance(bar.get_width(), float)
                    else f"{int(bar.get_width())}"
                ),
                va="center",
                fontsize=8,
                color="black",
            )

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=120)
    plt.close()
    buf.seek(0)
    return buf


def draw_double_lineup_image(
    home_team: str,
    away_team: str,
    formation_home: str,
    formation_away: str,
    coach_home: str,
    coach_away: str,
    players_home: list[dict],
    players_away: list[dict],
) -> BytesIO:

    # Change figure size to accommodate vertical layout
    fig, ax = plt.subplots(figsize=(10, 16))  # Taller figure for vertical layout

    # خلفية الملعب
    ax.set_facecolor("#065C32")
    ax.set_xticks([])
    ax.set_yticks([])

    # Vertical pitch dimensions (now 100 tall, 70 wide)
    pitch_width = 70
    pitch_height = 100

    # حدود الملعب (vertical)
    pitch = Rectangle(
        xy=(15, 0),  # Shifted right to center in the figure
        width=pitch_width,
        height=pitch_height,
        fill=False,
        edgecolor="white",
        lw=2,
    )
    ax.add_patch(pitch)

    # منتصف الملعب وخط المنتصف (now horizontal)
    ax.plot(
        [15, 15 + pitch_width],  # Horizontal line across width
        [pitch_height / 2, pitch_height / 2],
        color="white",
        lw=2,
    )
    center_circle = Arc(
        xy=(15 + pitch_width / 2, pitch_height / 2),  # Center point
        width=20,
        height=20,
        angle=90,  # Rotated 90 degrees for vertical pitch
        theta1=0,
        theta2=360,
        color="white",
        lw=2,
    )
    ax.add_patch(center_circle)
    ax.plot(
        15 + pitch_width / 2,
        pitch_height / 2,
        marker="o",
        color="white",
    )

    # أسماء الفرق والتشكيلات (now stacked vertically)
    ax.text(
        x=15 + pitch_width / 2,
        y=pitch_height + 8,
        s=f"{home_team} ({formation_home})",
        ha="center",
        va="top",
        fontsize=16,
        color="white",
        weight="bold",
    )
    ax.text(
        x=15 + pitch_width / 2,
        y=-8,
        s=f"{away_team} ({formation_away})",
        ha="center",
        va="bottom",
        fontsize=16,
        color="white",
        weight="bold",
    )

    # أسماء المدربين (moved to sides)
    ax.text(
        x=5,
        y=pitch_height / 2,
        s=f"Coach: {coach_home}",
        ha="left",
        va="center",
        fontsize=12,
        color="white",
        style="italic",
        rotation=90,
    )
    ax.text(
        x=15 + pitch_width + 5,
        y=pitch_height / 2,
        s=f"Coach: {coach_away}",
        ha="right",
        va="center",
        fontsize=12,
        color="white",
        style="italic",
        rotation=270,
    )

    # شعار 888STARZ بشكل واضح (centered)
    ax.text(
        x=15 + pitch_width / 2,
        y=pitch_height / 2,
        s="TipsterHub",
        ha="center",
        va="center",
        fontsize=50,
        color="orange",
        weight="bold",
        alpha=0.2,
    )

    def plot_team(
        y_min: float,
        y_max: float,
        formation: str,
        players: list[dict],
        team_color: str,
        reverse=False,
    ):
        if reverse:
            players = list(reversed(players))
            formation_numbers = list(map(int, reversed(formation.split("-"))))
            formation_numbers.append(1)
        else:
            formation_numbers = list(map(int, formation.split("-")))
            formation_numbers.insert(0, 1)
        total_lines = len(formation_numbers)
        y_spacing = (y_max - y_min) / (total_lines - 1)
        current_player = 0

        for line_idx, players_in_line in enumerate(formation_numbers):
            y = y_min + line_idx * y_spacing
            x_spacing = pitch_width / (players_in_line + 1)

            for i in range(players_in_line):
                if current_player >= len(players):
                    break
                x = 15 + (i + 1) * x_spacing

                shadow = Circle(
                    xy=(x + 0.3, y - 0.3),
                    radius=3,
                    color="black",
                    alpha=0.3,
                )
                player_circle = Circle(
                    xy=(x, y),
                    radius=3,
                    color=team_color,
                    ec="white",
                    lw=1.5,
                )

                ax.add_patch(shadow)
                ax.add_patch(player_circle)

                ax.text(
                    x=x,
                    y=y,
                    s=players[current_player]["number"],
                    fontsize=9,
                    ha="center",
                    va="center",
                    color="white",
                    weight="bold",
                )

                ax.text(
                    x=x,
                    y=y - 4,
                    s=players[current_player]["name"],
                    fontsize=7,
                    ha="center",
                    va="top",
                    color="white",
                )

                current_player += 1

    # المضيف
    plot_team(
        y_min=pitch_height / 2 + 10,
        y_max=pitch_height - 10,
        formation=formation_home,
        players=players_home,
        team_color="#1f77b4",
        reverse=True,
    )

    # الضيف
    plot_team(
        y_min=10,
        y_max=pitch_height / 2 - 10,
        formation=formation_away,
        players=players_away,
        team_color="#d62728",
        reverse=False,
    )

    plt.xlim(0, 15 + pitch_width + 15)
    plt.ylim(-15, pitch_height + 15)

    # حفظ الصورة
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_enhanced_poster_prompt(
    match_title: str,
    league_name: str,
    match_datetime: str,
    stats_summary: str,
    brands: list[str],
    team_colors: str = None,
) -> str:
    league_block = f"🏆 Tournament: {league_name}\n🕒 Kick-off: {match_datetime}\n"
    stats_block = f"📊 Key Stats: {stats_summary}\n🎨 Team Colors: {team_colors}\n"

    base_prompt = (
        f"Design a premium Telegram sports betting poster (1280x720), "
        f"featuring the match: {match_title}.\n"
        f"{league_block}"
        f"{stats_block}"
        "🎯 Design Requirements:\n"
        "- Display real club logos in top corners.\n"
        "- Use glowing infographics for stats (possession, shots, xG).\n"
        "- Center the pitch in 3D style with visible player formations.\n"
        "- Surrounding: vibrant crowd, depth lights, stadium motion.\n"
        "- Fonts: clean, modern, no hallucinated symbols or fake words.\n"
        "- No placeholder numbers. Respect real context.\n"
    )

    if len(brands) == 1:
        brand = BRANDS[brands[0]]
        base_prompt += (
            f"🔻 Branding:\n"
            f"- Add logo: {brand['logo_prompt']}\n"
            f"- Use brand colors: {', '.join(brand['brand_colors'])}\n"
            f"- Add slogan: \"{brand['slogan']}\" at the bottom in small font.\n"
        )
    else:
        base_prompt += (
            f"🔻 Multi-brand layout:\n"
            "- Split the poster visually (vertical or horizontal).\n"
        )
        for b in brands:
            brand = BRANDS[b]
            base_prompt += (
                f"--- {brand['display_name']} ---\n"
                f"- Logo prompt: {brand['logo_prompt']}\n"
                f"- Colors: {', '.join(brand['brand_colors'])}\n"
                f"- Slogan: \"{brand['slogan']}\"\n"
            )

    base_prompt += (
        "\n💡 Keep overall layout premium, bold, and ready for sports Telegram groups."
    )
    return base_prompt


def filter_fixtures(fixtures: list, sport: str = "football"):
    league_ids = [l["id"] for l in LEAGUES[sport].values()]
    return [fix for fix in fixtures if fix["league_id"] in league_ids]


def format_basketball_stats(stats):
    return (
        f"Record: {stats['games']['wins']['all']['total']}-{stats['games']['loses']['all']['total']} | "
        f"PPG: {stats['points']['for']['average']['all']} | "
        f"PAPG: {stats['points']['against']['average']['all']} | "
        f"Home: {stats['games']['wins']['home']['total']}-{stats['games']['loses']['home']['total']} | "
        f"Away: {stats['games']['wins']['away']['total']}-{stats['games']['loses']['away']['total']}"
    )


def format_football_stats(stats):
    return (
        f"Form: {stats['form']} | "
        f"Record: {stats['fixtures']['wins']['total']}-{stats['fixtures']['draws']['total']}-{stats['fixtures']['loses']['total']} | "
        f"GF: {stats['goals']['for']['total']['total']} ({stats['goals']['for']['average']['total']}/game) | "
        f"GA: {stats['goals']['against']['total']['total']} ({stats['goals']['against']['average']['total']}/game) | "
        f"CS: {stats['clean_sheet']['total']}"
    )


def format_american_football_stats(stats):
    team_stats = stats[0]["statistics"]
    return (
        f"Yards: {team_stats['yards']['total']} | "
        f"Pass: {team_stats['passing']['comp_att']} | "
        f"Rush: {team_stats['rushings']['attempts']} for {team_stats['rushings']['total']} | "
        f"3rd Down: {team_stats['first_downs']['third_down_efficiency']} | "
        f"TO: {team_stats['turnovers']['total']} | "
        f"Poss: {team_stats['posession']['total']}"
    )


def format_hockey_stats(stats):
    return (
        f"Record: {stats['games']['wins']['all']['total']}-{stats['games']['loses']['all']['total']} | "
        f"GF: {stats['goals']['for']['total']['all']} ({stats['goals']['for']['average']['all']}/game) | "
        f"GA: {stats['goals']['against']['total']['all']} ({stats['goals']['against']['average']['all']}/game) | "
        f"Home: {stats['games']['wins']['home']['total']}-{stats['games']['loses']['home']['total']} | "
        f"Away: {stats['games']['wins']['away']['total']}-{stats['games']['loses']['away']['total']}"
    )


def format_last_matches(matches, team_id, sport):
    if not matches or not isinstance(matches, list) or len(matches) == 0:
        return "No recent matches"

    last_5 = matches[:5]
    results = []
    goals_for = 0
    goals_against = 0
    overtime_games = 0

    for match in last_5:
        if sport == "football":
            # Football specific handling
            is_home = match["teams"]["home"]["id"] == team_id
            team_goals = match["goals"]["home"] if is_home else match["goals"]["away"]
            opp_goals = match["goals"]["away"] if is_home else match["goals"]["home"]

        elif sport == "basketball":
            # Basketball specific handling
            is_home = match["teams"]["home"]["id"] == team_id
            team_goals = match["scores"]["home" if is_home else "away"]["total"]
            opp_goals = match["scores"]["away" if is_home else "home"]["total"]
            if (
                match["scores"]["home"]["over_time"]
                or match["scores"]["away"]["over_time"]
            ):
                overtime_games += 1

        elif sport == "american-football":
            # American football specific handling
            is_home = match["teams"]["home"]["id"] == team_id
            team_goals = match["scores"]["home" if is_home else "away"]["total"]
            opp_goals = match["scores"]["away" if is_home else "home"]["total"]
            if match["status"]["short"] in ["AOT", "OT"]:
                overtime_games += 1

        elif sport == "hockey":
            # Hockey specific handling
            is_home = match["teams"]["home"]["id"] == team_id
            team_goals = match["scores"]["home"] if is_home else match["scores"]["away"]
            opp_goals = match["scores"]["away"] if is_home else match["scores"]["home"]
            if match["periods"]["overtime"]:
                overtime_games += 1
        if team_goals is not None and opp_goals is not None:
            # Determine result
            if team_goals > opp_goals:
                result = "W"
            elif team_goals == opp_goals:
                result = "D"
            else:
                result = "L"

            results.append(result)
            goals_for += team_goals
            goals_against += opp_goals

    # Build summary string
    summary = f"Form: {' '.join(results)} | GF: {goals_for} | GA: {goals_against}"

    # Add averages if we have matches
    if len(last_5) > 0:
        avg_for = goals_for / len(last_5)
        avg_against = goals_against / len(last_5)
        summary += f" | Avg: {avg_for:.1f}-{avg_against:.1f}"

    # Add overtime info if any games went to OT
    if overtime_games > 0:
        summary += f" | OT: {overtime_games}"

    return summary


def structure_team_standing(data: dict, sport: str):
    if not data:
        return {}
    team_standing = {}
    if sport == "football":
        team_standing["rank"] = data[0]["league"]["standings"][0][0]["rank"]
        team_standing["points"] = data[0]["league"]["standings"][0][0]["points"]
    elif sport == "basketball":
        team_standing["rank"] = data[0][0]["position"]
        team_standing["points"] = data[0][0]["points"]["for"]
    elif sport == "american_football":
        team_standing["rank"] = data[0]["position"]
        team_standing["points"] = data[0]["points"]["for"]
    elif sport == "hockey":
        team_standing["rank"] = data[0][0]["position"]
        team_standing["points"] = data[0][0]["points"]
    return team_standing


def structure_fixtures(sport: str, data: list[dict], fix_num: int = None):
    data = data[:fix_num] if fix_num else data
    fixtures = []
    if sport == "football":
        for item in data:
            fixture = item["fixture"]
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": fixture["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": fixture["venue"]["name"],
                    "date": fixture["date"],
                    "sport": sport,
                    "goals": item.get("goals", None),
                }
            )

    elif sport == "basketball":
        for item in data:
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": item["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": item["venue"],
                    "date": item["date"],
                    "sport": sport,
                    "goals": item.get("scores", None),
                }
            )

    elif sport == "american_football":
        for item in data:
            teams = item["teams"]
            fixture = item["game"]
            fixtures.append(
                {
                    "fixture_id": fixture["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": fixture["venue"]["name"],
                    "date": item["date"],
                    "goals": item.get("scores", None),
                }
            )

    elif sport == "hockey":
        for item in data:
            teams = item["teams"]
            fixtures.append(
                {
                    "fixture_id": item["id"],
                    "home_id": teams["home"]["id"],
                    "away_id": teams["away"]["id"],
                    "home_name": teams["home"]["name"],
                    "away_name": teams["away"]["name"],
                    "season": item["league"]["season"],
                    "league_id": item["league"]["id"],
                    "league_name": item["league"]["name"],
                    "venue": "N/A",
                    "date": item["date"],
                    "sport": sport,
                    "goals": item.get("scores", None),
                }
            )
    return fixtures


def summarize_odds(odds: list[dict]):
    summaries = []
    printed = set()
    for provider in odds:
        for bet in provider.get("bookmakers", []):
            for market in bet.get("bets", []):
                name = market.get("name", "")
                if name not in printed:
                    printed.add(name)
                    values = " | ".join(
                        [f"{o['value']}: {o['odd']}" for o in market.get("values", [])]
                    )
                    summaries.append(f"{name}: {values}")
    result = "\n".join(summaries)
    return result

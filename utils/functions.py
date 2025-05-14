from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.axes import Axes


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

    # شعار MELBET بشكل واضح (centered)
    ax.text(
        x=15 + pitch_width / 2,
        y=pitch_height / 2,
        s="MELBET",
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

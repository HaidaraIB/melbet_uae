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
    home_team,
    away_team,
    formation_home,
    formation_away,
    coach_home,
    coach_away,
    players_home,
    players_away,
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
        (15, 0),  # Shifted right to center in the figure
        pitch_width,
        pitch_height,
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
        (15 + pitch_width / 2, pitch_height / 2),  # Center point
        20,
        20,
        angle=90,  # Rotated 90 degrees for vertical pitch
        theta1=0,
        theta2=360,
        color="white",
        lw=2,
    )
    ax.add_patch(center_circle)
    ax.plot(15 + pitch_width / 2, pitch_height / 2, marker="o", color="white")

    # أسماء الفرق والتشكيلات (now stacked vertically)
    ax.text(
        15 + pitch_width / 2,
        pitch_height + 8,
        f"{home_team} ({formation_home})",
        ha="center",
        va="top",
        fontsize=16,
        color="white",
        weight="bold",
    )
    ax.text(
        15 + pitch_width / 2,
        -8,
        f"{away_team} ({formation_away})",
        ha="center",
        va="bottom",
        fontsize=16,
        color="white",
        weight="bold",
    )

    # أسماء المدربين (moved to sides)
    ax.text(
        5,
        pitch_height / 2,
        f"Coach: {coach_home}",
        ha="left",
        va="center",
        fontsize=12,
        color="white",
        style="italic",
        rotation=90,
    )
    ax.text(
        15 + pitch_width + 5,
        pitch_height / 2,
        f"Coach: {coach_away}",
        ha="right",
        va="center",
        fontsize=12,
        color="white",
        style="italic",
        rotation=270,
    )

    # شعار MELBET بشكل واضح (centered)
    ax.text(
        15 + pitch_width / 2,
        pitch_height / 2,
        "MELBET",
        ha="center",
        va="center",
        fontsize=50,
        color="orange",
        weight="bold",
        alpha=0.2,
    )

    def plot_team(y_min, y_max, formation, players, team_color, reverse=False):
        formation_numbers = list(map(int, formation.split("-")))
        if not reverse:
            formation_numbers.insert(0, 1)
        else:
            formation_numbers.append(1)
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

                shadow = Circle((x + 0.3, y - 0.3), 3, color="black", alpha=0.3)
                player_circle = Circle((x, y), 3, color=team_color, ec="white", lw=1.5)

                ax.add_patch(shadow)
                ax.add_patch(player_circle)

                ax.text(
                    x,
                    y,
                    players[current_player]["number"],
                    fontsize=9,
                    ha="center",
                    va="center",
                    color="white",
                    weight="bold",
                )

                ax.text(
                    x,
                    y - 4,
                    players[current_player]["name"],
                    fontsize=7,
                    ha="center",
                    va="top",
                    color="white",
                )

                current_player += 1

    # الآن التطبيق بوضوح على الفريقين:

    pitch_height = 100
    pitch_width = 70

    # المضيف (بدون عكس)
    plot_team(
        pitch_height / 2 + 10,
        pitch_height - 10,
        "-".join(list(reversed(formation_home.split("-")))),
        list(reversed(players_home)),
        "#1f77b4",
        reverse=True,
    )

    # الضيف (بعكس الترتيب)
    plot_team(
        10,
        pitch_height / 2 - 10,
        formation_away,
        players_away,
        "#d62728",
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

from io import BytesIO
import matplotlib.pyplot as plt


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


def draw_lineup_image(team_name: str, formation: str, players: list) -> BytesIO:
    _, ax = plt.subplots(figsize=(6, 9))
    ax.set_facecolor("#0B6623")  # لون الملعب (أخضر)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # عنوان الفريق والتشكيلة
    ax.text(
        50,
        98,
        f"{team_name} ({formation})",
        ha="center",
        va="top",
        fontsize=14,
        color="white",
        weight="bold",
    )

    # ✅ كلمة MELBET بالخلفية كعلامة مائية شفافة
    ax.text(
        50,
        50,
        "MELBET",
        ha="center",
        va="center",
        fontsize=50,
        color="white",
        alpha=0.08,
        weight="bold",
        rotation=30,
    )

    # توزيع اللاعبين بناءً على التشكيلة
    formation_parts = list(map(int, formation.split("-")))
    total_lines = len(formation_parts) + 1
    y_positions = list(
        reversed([10 + i * (80 // (total_lines - 1)) for i in range(total_lines)])
    )

    player_index = 0

    # حارس مرمى
    ax.text(
        50,
        y_positions[0],
        f"{players[player_index]['number']} - {players[player_index]['name']}",
        ha="center",
        va="center",
        fontsize=10,
        color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc="black", ec="white"),
    )
    player_index += 1

    # الخطوط الأخرى
    for line_idx, count in enumerate(formation_parts):
        x_spacing = 100 // (count + 1)
        y = y_positions[line_idx + 1]
        for i in range(count):
            if player_index >= len(players):
                break
            x = (i + 1) * x_spacing
            ax.text(
                x,
                y,
                f"{players[player_index]['number']} - {players[player_index]['name']}",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                bbox=dict(boxstyle="round,pad=0.2", fc="black", ec="white"),
            )
            player_index += 1

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf

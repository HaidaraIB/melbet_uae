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

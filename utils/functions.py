from io import BytesIO
import matplotlib.pyplot as plt


def generate_infographic(team1: str, stats1: dict, team2: str, stats2: dict):
    labels = ["Possession", "Shots", "Passes", "Corners", "Yellow Cards"]
    values1 = [
        stats1.get("Ball Possession", 0),
        stats1.get("Total Shots", 0),
        stats1.get("Total passes", 0),
        stats1.get("Corner Kicks", 0),
        stats1.get("Yellow Cards", 0),
    ]
    values2 = [
        stats2.get("Ball Possession", 0),
        stats2.get("Total Shots", 0),
        stats2.get("Total passes", 0),
        stats2.get("Corner Kicks", 0),
        stats2.get("Yellow Cards", 0),
    ]
    x = range(len(labels))
    plt.figure(figsize=(10, 5))
    bar1 = plt.bar(
        x,
        values1,
        width=0.4,
        label=team1,
        align="center",
        color="#1f77b4",
    )
    bar2 = plt.bar(
        [i + 0.4 for i in x],
        values2,
        width=0.4,
        label=team2,
        align="center",
        color="#d62728",
    )
    plt.xticks([i + 0.2 for i in x], labels)
    plt.legend()
    plt.title("Match Statistics")
    # عرض القيم فوق الأعمدة
    for bar in bar1 + bar2:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval + (max(values1 + values2) * 0.02),
            str(yval),
            ha="center",
            va="bottom",
            fontsize=9,
            color="black",
        )
    plt.tight_layout()

    # Save to BytesIO instead of disk
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf

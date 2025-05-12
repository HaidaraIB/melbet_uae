from io import BytesIO
import matplotlib.pyplot as plt


def generate_infographic(team1: str, stats1: dict, team2: str, stats2: dict) -> BytesIO:
    # جمع كل المفاتيح المشتركة
    labels = list(stats1.keys())

    values1 = []
    values2 = []
    for label in labels:
        val1 = stats1[label] or 0
        val2 = stats2[label] or 0

        # تحويل إلى أرقام إن كانت نسب مئوية
        if isinstance(val1, str) and val1.endswith("%"):
            val1 = val1.strip("%")
        if isinstance(val2, str) and val2.endswith("%"):
            val2 = val2.strip("%")

        values1.append(float(val1))
        values2.append(float(val2))

    x = range(len(labels))
    plt.figure(figsize=(12, 0.5 * len(labels) + 2))  # حجم ديناميكي حسب عدد الإحصائيات

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
    plt.xlabel("القيمة")
    plt.title("Match Statistics")
    plt.legend()

    # إضافة القيم بجانب كل عمود
    for bars in [bar1, bar2]:
        for bar in bars:
            plt.text(
                bar.get_width() + 1,
                bar.get_y() + bar.get_height() / 2,
                f"{int(bar.get_width())}",
                va="center",
                fontsize=8,
                color="black",
            )

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf

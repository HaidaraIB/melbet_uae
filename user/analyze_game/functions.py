def summarize_matches(matches: list[dict]):
    summary = []
    for m in matches:
        summary.append(
            f"{m['home_name']} {m['goals']['home']} - {m['goals']['away']} {m['away_name']} on {m['date']}"
        )
    return "\n".join(summary)


def summarize_injuries(injuries: list[dict], sport: str):
    if not injuries:
        return
    if sport == "football":
        return "\n".join(
            [
                f"{i['player']['name']} ({i['player']['type']}) - {i['player']['reason']}"
                for i in injuries
            ]
        )
    elif sport == "american_football":
        return "\n".join(
            [
                f"{i['player']['name']} ({i['status']}) - {i['description']}"
                for i in injuries
            ]
        )

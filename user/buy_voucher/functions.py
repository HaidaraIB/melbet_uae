from datetime import datetime, timedelta
from common.constants import TIMEZONE
import math


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


def calc_from_to_dates_and_duration_in_days(duration_type: str, duration_value: str):
    now = datetime.now(TIMEZONE)
    if duration_type == "hours":
        hours = duration_value
        duration_in_days = math.ceil(hours / 24)
    else:
        days = duration_value
        duration_in_days = days

    return now, duration_in_days

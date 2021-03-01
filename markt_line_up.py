import json
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_line_up(str):
    return str.replace(
        "\r\n", '').replace(
        "\t", '').replace(
        "Starting Line-up:", '').replace("flat", "").replace(" ", '')


def getPos(str):
    pos = str.replace(
        'top:', '').replace('left:', '').replace('%', '').replace(' ', '')
    return (float(pos) - float(pos) % 10)


def get_minutes(minute_span):
    minutes = ""
    minute_style = minute_span.attrs['style']
    matches = re.match(
        "background-position: -(\d+)px -(\d+)px;", minute_style)
    x = matches[1]
    y = matches[2]
    minute = -1
    if x != 0 and y != 0:
        minute = 10*(int(y)/36) + int(x)/36 + 1
    plus = minute_span.text.replace("\xa0", "").replace("\r\n\t", "")
    minutes = f"{int(minute)}{plus}"
    minutes = minutes
    return minutes


def get_goals(header):
    goals = []
    header_parent = header.parent
    minute_spans = header_parent.findChildren(
        "span", {"class": "sb-sprite-uhr-klein"}, recursive=True)
    goal_info = header_parent.findChildren(
        "a", {"class": "wichtig"}, recursive=True)
    for i in range(len(goal_info)):
        if i % 2 == 0:
            goal_detail = goal_info[i].parent
            goal_detail_text = goal_detail.text.replace(
                "\n", "").replace("\t", "")
            goal_detail_list = goal_detail_text.split("Assist: ")
            scorer_detail = goal_detail_list[0]
            scorer_detail_list = scorer_detail.split(", ")
            scorer = scorer_detail_list[0]
            goal_type = scorer_detail_list[1]
            assist = ""
            assist_type = ""
            if len(goal_detail_list) == 2:
                assist_detail = goal_detail_list[1]
                assist_detail_list = assist_detail.split(
                    ", ")
                if len(assist_detail_list) < 2:
                    assist_detail_list = assist_detail.split(
                        " by ")
                    if len(assist_detail_list) > 1:
                        assist_type = assist_detail_list[0]
                        assist = assist_detail_list[1]
                else:
                    assist = assist_detail_list[0]
                    assist_type = assist_detail_list[1]
            index = 0
            if i > 0:
                index = int(i/2)
            minutes = get_minutes(minute_spans[index])
            goal_detail = {
                "minutes": minutes,
                "scorer": scorer,
                "goal_type": goal_type,
                "assist": assist,
                "assist_type": assist_type
            }
            goals.append(goal_detail)
    return goals


def get_missed_penalty(header):
    missed_penalties = []
    header_parent = header.parent
    minute_spans = header_parent.findChildren(
        "span", {"class": "sb-sprite-uhr-klein"}, recursive=True)
    goal_info = header_parent.findChildren(
        "a", {"class": "wichtig"}, recursive=True)
    for i in range(len(goal_info)):
        if i % 2 == 0:
            scorer_detail = goal_info[i].parent
            scorer_detail_text = scorer_detail.text.replace(
                "\n", "").replace("\t", "")
            scorer_detail_list = scorer_detail_text.split(", ")
            scorer = ""
            reason = ""
            keeper = ""
            keeper_role = ""
            if len(scorer_detail_list) == 1:
                scorer = scorer_detail_list[0]
            else:
                scorer = scorer_detail_list[0]
                reason = scorer_detail_list[1]

                goalkeeper_detail = goal_info[i+1].parent
                goalkeeper_detail_text = goalkeeper_detail.text.replace(
                    "\n", "").replace("\t", "")
                goalkeeper_detail_list = goalkeeper_detail_text.split(", ")
                keeper = goalkeeper_detail_list[0]
                keeper_role = goalkeeper_detail_list[1]

            index = 0
            if i > 0:
                index = int(i/2)
            minutes = get_minutes(minute_spans[index])
            missed_penalty_detail = {
                "minutes": minutes,
                "scorer": scorer,
                "reason": reason,
                "keeper": keeper,
                "keeper_role": keeper_role
            }
            missed_penalties.append(missed_penalty_detail)
    return missed_penalties


def get_subsitutions(header):
    substitutions = []
    header_parent = header.parent
    minute_spans = header_parent.findChildren(
        "span", {"class": "sb-sprite-uhr-klein"}, recursive=True)
    changes_info = header_parent.findChildren(
        "span", {"class": "hide-for-small"}, recursive=True)
    for i in range(len(changes_info)):
        changes_reason = changes_info[i]

        changes_reason_text = changes_reason.text.replace(
            ", ", "").replace('\xa0', '')
        if changes_reason_text == '':
            changes_reason_text = "Tactical"
        minutes = get_minutes(minute_spans[i])
        reason = {"minutes": minutes, "reason": changes_reason_text}
        substitutions.append(reason)
    return substitutions


def get_cards(header):
    cards = []
    header_parent = header.parent
    minute_spans = header_parent.findChildren(
        "span", {"class": "sb-sprite-uhr-klein"}, recursive=True)
    card_info = header_parent.findChildren(
        "div", {"class": "sb-aktion-aktion"}, recursive=True)
    for i in range(len(card_info)):
        minutes = get_minutes(minute_spans[i])
        res = "Foul"
        card_reason = card_info[i]
        card_reason_text = card_reason.text.replace(
            ", ", "").replace('\xa0', '').replace("\n", "").replace("\t", "")

        card_reason_list = card_reason_text.split("card ")

        if card_reason_list != None and len(card_reason_list) > 1:
            res = card_reason_list[1].strip()

        reason = {"minutes": minutes, "reason": res}

        cards.append(reason)
    return cards


def get_start_up(mac_id):

    headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

    page = f"https://www.transfermarkt.com/spielbericht/index/spielbericht/{mac_id}"
    pageTree = requests.get(page, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    rn = pageSoup.find_all("div", {"class": "rn"})

    style = pageSoup.find_all(
        "div", {"class": "aufstellung-spieler-container"})

    starting_line_up = pageSoup.find_all(
        "div", {"class": "aufstellung-unterueberschrift"})

    host_players = []
    guest_players = []

    host_line_up = get_line_up(starting_line_up[0].text)
    guest_line_up = get_line_up(starting_line_up[1].text)

    for i in range(11):
        player = style[i].findChildren("a", recursive=True)[0].text
        x = getPos(style[i].attrs['style'].split(';')[0])
        y = getPos(style[i].attrs['style'].split(';')[1])
        host_players.append({
            "player": player,
            "number": rn[i].text,
            "pos": {
                "px": int(x),
                "py": int(y)
            }})
        player = style[i+11].findChildren("a", recursive=True)[0].text
        x = getPos(style[i+11].attrs['style'].split(';')[0])
        y = getPos(style[i+11].attrs['style'].split(';')[1])
        guest_players.append({
            "player": player,
            "number": rn[i+11].text,
            "pos": {
                "px": int(x),
                "py": int(y)
            }})

    headers = pageSoup.find_all("div", {"class": "header"})

    goals = []
    missed_penalties = []
    substitutions = []
    cards = []
    for header in headers:
        h2 = header.findChildren("h2", recursive=False)
        if h2[0].text == "Goals":
            goals = get_goals(header)
        elif h2[0].text == "missed penalties":
            missed_penalties = get_missed_penalty(header)
        elif h2[0].text == "Substitutions":
            substitutions = get_subsitutions(header)
        elif h2[0].text == "Cards":
            cards = get_cards(header)

    df = pd.DataFrame.from_dict({
        "host": [
            {"players": host_players,
             "line_up": host_line_up
             }
        ],
        "guest": [
            {
                "players": guest_players,
                "line_up": guest_line_up
            }
        ],

        "goals": [
            goals
        ],
        "missed_penalties": [missed_penalties],
        "substitutions": [substitutions],
        "cards": [cards]
    })

    data = df.to_dict(orient="records")[0]
    return data

    # with open("test.json", 'w+', encoding='utf-8') as fw:
    #    df.to_json(fw, orient='records', force_ascii=False, lines=True)

   # return result


#data = get_start_up(3221072)

# host = data['host']
# players = data['host']['players']
# for item in players:
#    print(item['number'])
#    print(item['pos'])

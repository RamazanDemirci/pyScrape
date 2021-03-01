import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from transfermarkt_line_up import *


player_pre_str_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptKadrolar_ctl"
player_pre_str_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptKadrolar_ctl"
goal_pre_str_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptGoller_ctl"
goal_pre_str_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptGoller_ctl"
card_pre_str_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptKartlar_ctl"
card_pre_str_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptKartlar_ctl"
out_str_pre_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptCikanlar_ctl"
player_out_str_post = "_lblCikan"
minutes_out_str_post = "_oc"
out_str_pre_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptCikanlar_ctl"

in_str_pre_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptGirenler_ctl"
player_in_str_post = "_lblGiren"
minutes_in_str_post = "_og"
in_str_pre_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptGirenler_ctl"

repeat_pattern_str = "ctl00_MPane_m_29_194_ctnr_m_29_194_MacBilgiDisplay1_dtMacBilgisi"

host_logo_str = f"{repeat_pattern_str}_imgTakim1Logo"
guest_logo_str = f"{repeat_pattern_str}_imgTakim2Logo"

base_url = "http://localhost:8000"
#base_url = "http://176.240.51.73:9000"


host_team_info = {}
guest_team_info = {}


def title(str):
    output = ""
    str_list = str.split(" ")
    for item in str_list:
        tmp = item.capitalize()
        output = f'{output} {tmp}'
    return output.strip()


def getTeamInfo(league, season, host_name):
    team_info = {}
    host_name = host_name.replace(
        "A.Ş.", "").replace("FK", "").replace("FUTBOL KULÜBÜ", "").lower().strip()
    payload = {
        "name": host_name,
    }
    response = requests.get(f'{base_url}/api/teams', data=payload)
    if response.status_code == 200:
        data = response.json()
        team_info = data
    else:
        #print(f"Please enter the team name : name is {host_name}")
        #team = str(input())
        #team = team.title()
        print(f"Please enter the team alias : name is {host_name}")
        alias = str(input())
        alias = title(alias)
        team_info = {
            "name": host_name,
            "alias": alias,
            "logo": "",
            "season": season,
            "league": league
        }

        requests.post(f'{base_url}/api/teams', json=team_info)
    return team_info


def getPersonAlias(person_title, name, belongTo):

    if len(name) > 20:
        alias = ""
        name = title(name.strip())
        payload = {
            "name": name,
        }
        response = requests.get(f'{base_url}/api/persons', data=payload)

        if response.status_code == 200:
            data = response.json()
            alias = data["alias"]
        else:
            print("Player name No found in DB")
            name = title(name)
            alias = name.strip()
            asl = alias.split(" ")
            word_count = len(asl)
            next_alias = ""
            for i in range(word_count):
                if len(next_alias) < 18:
                    alias = next_alias
                else:
                    break

                next_alias = f"{asl[word_count - 1 - i]} {next_alias}"

            # print(
            #    f"Please enter the alias for title:'{title}''  name : '{name}' alias : '{current_alias}''")
            #in_str = str(input())
            # if in_str != "":
            #    alias = in_str

            payload = {
                "name": name,
                "alias": alias,
                "title": title(person_title),
                "team": title(belongTo)
            }

            requests.post(f'{base_url}/api/persons', json=payload)
        return alias
    return name


def get_players(pageSoup, player_pre_str, line_up, team_name):
    players = []

    for i in range(11):
        player_index = f'{(i+1):02}'
        id_str = f"{player_pre_str}{player_index}_formaNo"
        player_str = f"{player_pre_str}{player_index}_lnkOyuncu"
        forma_no = pageSoup.find("span", {"id": id_str}).text.replace(".", "")
        player_name = pageSoup.find("a", {"id": player_str}).text
        pos = {}
        for item in line_up:
            if int(forma_no) == int(item['number']):
                pos = item['pos']
                break
        if len(pos) == 0:
            for node in line_up:
                left = node['player'].strip().replace('İ', 'I').lower()
                right = player_name.strip().replace('İ', 'I').lower()
                if left in right:
                    pos = node['pos']
                    break

        player_alias = getPersonAlias('player', player_name, team_name)

        players.append({"forma_no": int(forma_no),
                        "name": title(player_alias), "pos": pos})
    return players


def getGoalType(t):
    if t == 'P':
        return "Penalty"
    elif t == 'F':
        return "Foot"
    elif t == 'H':
        return "Head"
    elif t == 'K':
        return "Own"
    elif t == 'S':
        return "Serial_Penalty"


def get_goals(pageSoup, goal_pre_str, goal_info_list):
    goals = []

    goal_post_str = "_lblGol"

    for i in range(15):
        goal_index = f'{(i+1):02}'
        goal_str = f"{goal_pre_str}{goal_index}{goal_post_str}"
        goal = pageSoup.find("a", {"id": goal_str})
        if(goal == None):
            break

        # matches = re.match(r"(\w+|\W+),(\d+).dk \((\w|\W)\)", goal.text)
        matches = re.match("(.+),(.+) \((.)\)", goal.text)

        if(matches == None):
            print("ERROR: bkz : get_goals")
        # minutes = int(get_minutes(matches[2])
        minutes = matches[2].replace(".dk", "")

        goal_type_detail = ""
        assist = ""
        assist_type = ""
        for item in goal_info_list:
            if item["minutes"] == minutes:
                goal_type_detail = item["goal_type"]
                assist = item["assist"]
                assist_type = item["assist_type"]

        goals.append({"player": title(matches[1]),
                      "minutes": minutes,
                      "goal_type": getGoalType(matches[3]),
                      "goal_type_detail": goal_type_detail,
                      "assist": assist,
                      "assist_type": assist_type})
    return goals


def get_card_type(t):
    if t == 'Sarı Kart':
        return 'Yellow'
    elif t == 'Çift Sarı Kart':
        return 'Red'
    elif t == 'Kırmızı Kart':
        return 'Red'


def get_minutes(card_minutes_text):
    minutes = 0
    matches = re.match("(\d+).dk", card_minutes_text)
    if(matches == None):
        matches = re.match("(\d+)\+(\d+).dk", card_minutes_text)
        minutes = int(matches[1]) + int(matches[2])
    else:
        minutes = int(matches[1])
    return minutes


def get_cards(pageSoup, team_info, card_pre_str, card_info_list):
    cards = []

    for i in range(15):
        card_index = f'{(i+1):02}'
        card_player_str = f"{card_pre_str}{card_index}_lblKart"
        card_minutes_str = f"{card_pre_str}{card_index}_d"
        card_type_str = f"{card_pre_str}{card_index}_k"

        card_player = pageSoup.find("a", {"id": card_player_str})
        if(card_player == None):
            break
        card_minutes = pageSoup.find("span", {"id": card_minutes_str})
        card_type = pageSoup.find("img", {"id": card_type_str}).attrs['alt']

        # minutes = get_minutes(card_minutes.text)
        minutes = card_minutes.text.replace(".dk", "")
        reason = ""
        for item in card_info_list:
            if item["minutes"] == minutes:
                reason = item["reason"]

        player_alias = getPersonAlias(
            'player', card_player.text, team_info['name'])

        if reason == "":
            reason = "Foul"

        cards.append({"player": title(player_alias),
                      "minutes": minutes,
                      "card_type": get_card_type(card_type),
                      "reason": reason})
    return cards


def get_changes(pageSoup, team_info, pre_string, player_post_string, minutes_post_string, changes_info_list):
    result = []
    for i in range(15):
        index = f'{(i+1):02}'
        player_str = f"{pre_string}{index}{player_post_string}"
        minutes_str = f"{pre_string}{index}{minutes_post_string}"
        player = pageSoup.find("a", {"id": player_str})
        if(player == None):
            break
        minutes = pageSoup.find("span", {"id": minutes_str})

        # minute = get_minutes(minutes.text)
        reason = ""
        minute = minutes.text.replace(".dk", "")
        for item in changes_info_list:
            if item["minutes"] == minute:
                reason = item["reason"]

        if reason == '':
            reason = "Tactical"

        player_alias = getPersonAlias(
            'player', player.text, team_info['name'])

        result.append({"player": title(player_alias),
                       "minutes": minute,
                       "reason": reason})
    return result


def get_logo(pageSoup, logo_str, team_info):
    link = pageSoup.find("a", {"id": logo_str})
    src = link.next.attrs['src']

    logo = requests.get(src).content

    headers = {
        'Content-Type': 'multipart/form-data',
        'Accept': 'application/json'
    }

    files = {"logo": logo,
             'Content-Type': 'image/png',
             'Content-Length': 1
             }
    data = {'filename': team_info["alias"]}

    r = requests.post(f"{base_url}/api/upload/logo",
                      data=data, files=files)
    payload = {
        "name": team_info["name"],
        "alias": team_info["alias"],
        "logo": team_info["alias"],
        "season": team_info["season"],
        "league": team_info["league"],
    }

    requests.put(f'{base_url}/api/teams', json=payload)


def get_match(mac_id, line_up):
    headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
    page = f"https://www.tff.org/Default.aspx?pageId=29&macId={mac_id}"
    pageTree = requests.get(page, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    _league = "Süper Lig"
    _season = "2019"
    # _season = pageSoup.find("span", {
    #    "id": f"{repeat_pattern_str}_lblOrganizasyonAdi"})

    stadium = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_lnkStad"}).text.replace(" -", "")
    stadium = title(stadium.split("stadium")[0])
    match_date_time = pageSoup.find(
        "span", {"id": f"{repeat_pattern_str}_lblTarih"}).text
    match_date = match_date_time.split(" - ")[0]
    match_time = match_date_time.split(" - ")[1]

    payload = {
        "stadium": stadium,
        "match_date": match_date,
        "match_time": match_time
    }

    response = requests.get(f'{base_url}/api/match_exist', data=payload)

    if response.status_code != 200:
        return

    referee = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl00_lnkHakem"}).text.replace("(Hakem)", "")
    referee = getPersonAlias(
        "Referee", referee, "Federation")
    referee_assist_1st = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl01_lnkHakem"}).text.replace("(1. Yardımcı Hakem)", "")
    referee_assist_1st = getPersonAlias(
        "Referee", referee_assist_1st, "Federation")
    referee_assist_2nd = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl02_lnkHakem"}).text.replace("(2. Yardımcı Hakem)", "")
    referee_assist_2nd = getPersonAlias(
        "Referee", referee_assist_2nd, "Federation")
    #referee_4th = pageSoup.find("a", {"id": f"{repeat_pattern_str}_rpt_ctl03_lnkHakem"}).text.replace("(Dördüncü Hakem)", "")
    #referee_VAR = pageSoup.find("a", {"id": f"{repeat_pattern_str}_rpt_ctl04_lnkHakem"}).text.replace("(VAR)", "")
    #referee_VAR_assist = pageSoup.find("a", {"id": f"{repeat_pattern_str}_rpt_ctl05_lnkHakem"}).text.replace("(AVAR)", "")

    host_name = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_lnkTakim1"}).text
    host_team_info = getTeamInfo(_league, _season, host_name)
    host_score = pageSoup.find(
        "span", {"id": f"{repeat_pattern_str}_lblTakim1Skor"}).text

    guest_name = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_lnkTakim2"}).text
    guest_team_info = getTeamInfo(_league, _season, guest_name)
    guest_score = pageSoup.find(
        "span", {"id": f"{repeat_pattern_str}_Label12"}).text

    if host_team_info["logo"] == "":
        get_logo(pageSoup, host_logo_str, host_team_info)
    if guest_team_info["logo"] == "":
        get_logo(pageSoup, guest_logo_str,
                 guest_team_info)

    host_coach = pageSoup.find(
        "a", {"id": "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptTeknikKadro_ctl01_lnkTeknikSorumlu"}).text
    guest_coach = pageSoup.find(
        "a", {"id": "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptTeknikKadro_ctl01_lnkTeknikSorumlu"}).text

    host_line_up = line_up['host']['players']
    host_players = get_players(
        pageSoup, player_pre_str_host, host_line_up, host_team_info["alias"])

    guest_line_up = line_up['guest']['players']
    guest_players = get_players(
        pageSoup, player_pre_str_guest, guest_line_up, guest_team_info["alias"])

    missed_penalties = line_up['missed_penalties']

    host_goals = get_goals(pageSoup, goal_pre_str_host, line_up['goals'])
    guest_goals = get_goals(pageSoup, goal_pre_str_guest, line_up['goals'])

    host_cards = get_cards(pageSoup, host_team_info,
                           card_pre_str_host, line_up['cards'])
    guest_cards = get_cards(pageSoup, guest_team_info,
                            card_pre_str_guest, line_up['cards'])

    host_out = get_changes(pageSoup, host_team_info,
                           out_str_pre_host, player_out_str_post, minutes_out_str_post, line_up['substitutions'])
    guest_out = get_changes(pageSoup, guest_team_info,
                            out_str_pre_guest, player_out_str_post, minutes_out_str_post, line_up['substitutions'])

    host_in = get_changes(pageSoup, host_team_info,
                          in_str_pre_host, player_in_str_post, minutes_in_str_post, line_up['substitutions'])
    guest_in = get_changes(pageSoup, guest_team_info,
                           in_str_pre_guest, player_in_str_post, minutes_in_str_post, line_up['substitutions'])

    df = pd.DataFrame.from_dict({
        "league": _league,
        "season": title(_season),
        "stadium": title(stadium),
        "match_date": match_date,
        "match_time": match_time,
        "referee": title(referee),
        "referee_assist_1st": title(referee_assist_1st),
        "referee_assist_2nd": title(referee_assist_2nd),
        # "referee_4th": referee_4th.title(),
        # "referee_VAR": referee_VAR.title(),
        # "referee_VAR_assist": referee_VAR_assist.title(),
        # "missed_penalties": [missed_penalties],
        "host": [{
            "name": title(host_name),
            "score": host_score,
            "coach": title(host_coach),
            "goals": host_goals,
            "cards": host_cards,
            "changes_in": host_in,
            "changes_out": host_out,
            "players": host_players,
            "logo": title(host_name),
            "line_up": line_up['host']["line_up"]}],
        "guest": [{
            "name": title(guest_name),
            "score": guest_score,
            "coach": title(guest_coach),
            "goals": guest_goals,
            "cards": guest_cards,
            "changes_in": guest_in,
            "changes_out": guest_out,
            "players": guest_players,
            "logo": title(guest_name),
            "line_up": line_up['guest']["line_up"]}]})

    data = df.to_dict(orient="records")[0]
    #requests.post('http://localhost:8008/api/matches', json=data)
    requests.post(f'{base_url}/api/matches', json=data)

    # with open(mac_id + '.json', 'w', encoding='utf-8') as fw:
    #    df.to_json(fw, orient="records", force_ascii=False, lines=True)

    # with open('deneme.json', 'w+', encoding='utf-8') as fw:
    #    json.dump(data, fw, ensure_ascii=False)


transfermarkt_ids = ["3221066", "3221067", "3221068", "3221069",
                     "3221070", "3221071", "3221072", "3221073", "3221074"]
tff_ids = ["207159", "207162", "207158", "207157",
           "207160", "207154", "207155", "207156", "207161"]

#tff_ids = ["207154"]
#transfermarkt_ids = ["3221071"]

percent = 0

for i in range(len(tff_ids)):
    line_up = get_start_up(transfermarkt_ids[i])
    get_match(tff_ids[i], line_up)
    percent = percent + 10
    print(f"{percent}%")
percent = percent + 10
print(f"100%")

#r = requests.get(f'{base_url}/api/entry')

# extracting data in json format

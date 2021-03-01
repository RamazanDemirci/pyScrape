import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from transfermarkt_line_up import *


def get_players(pageSoup, player_pre_str, line_up):
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

        players.append({"forma_no": int(forma_no),
                        "name": player_name.title(), "pos": pos})
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


def get_goals(pageSoup, goal_pre_str):
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
        goals.append({"player": matches[1].title(),
                      "minutes": minutes,
                      "goal_type": getGoalType(matches[3])})
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


def get_cards(pageSoup, card_pre_str):
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

        cards.append({"player": card_player.text.title(),
                      "minutes": minutes,
                      "card_type": get_card_type(card_type)})
    return cards


def get_changes(pageSoup, pre_string, player_post_string, minutes_post_string):
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
        minute = minutes.text.replace(".dk", "")
        result.append({"player": player.text.title(),
                       "minutes": minute})
    return result


def get_logo(pageSoup, logo_str, file_name):
    file_name = file_name.replace(" A.Ş.", "")
    file_name = file_name.replace(" FUTBOL KULÜBÜ", "")
    file_name = file_name+".png"
    if os.path.isfile(f'logo/{file_name}.png'):
        return

    link = pageSoup.find(
        "a", {"id": logo_str})
    src = link.next.attrs['src']

    logo = requests.get(src).content

    # with open(f"logo/{file_name}.png", "wb") as f:
    #    f.write(requests.get(src).content)

    headers = {
        'Content-Type': 'multipart/form-data',
        'Accept': 'application/json'
    }

    filesa = open(
        'C:\\Users\\tr1d5042\\Google Drive\\Tutorials\\Python\\transfermrkt\\logo\\ALANYASPOR.png', 'rb')
    files = {"logo": logo,
             'Content-Type': 'image/png',
             'Content-Length': 1
             }
    data = {'filename': file_name}

    r = requests.post("http://localhost:8008/api/upload/logo",
                      data=data, files=files)
    return file_name


def get_match(mac_id, line_up):
    headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
    page = f"https://www.tff.org/Default.aspx?pageId=29&macId={mac_id}"
    pageTree = requests.get(page, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    repeat_pattern_str = "ctl00_MPane_m_29_194_ctnr_m_29_194_MacBilgiDisplay1_dtMacBilgisi"

    _season = pageSoup.find("span", {
        "id": f"{repeat_pattern_str}_lblOrganizasyonAdi"})

    stadium = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_lnkStad"}).text.replace(" -", "")
    match_date_time = pageSoup.find(
        "span", {"id": f"{repeat_pattern_str}_lblTarih"}).text
    match_date = match_date_time.split(" - ")[0]
    match_time = match_date_time.split(" - ")[1]

    referee = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl00_lnkHakem"}).text.replace("(Hakem)", "")
    referee_assist_1st = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl01_lnkHakem"}).text.replace("(1. Yardımcı Hakem)", "")
    referee_assist_2nd = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl02_lnkHakem"}).text.replace("(2. Yardımcı Hakem)", "")
    referee_4th = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl03_lnkHakem"}).text.replace("(Dördüncü Hakem)", "")
    referee_VAR = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl04_lnkHakem"}).text.replace("(VAR)", "")
    referee_VAR_assist = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_rpt_ctl05_lnkHakem"}).text.replace("(AVAR)", "")

    host_name = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_lnkTakim1"}).text
    host_score = pageSoup.find(
        "span", {"id": f"{repeat_pattern_str}_lblTakim1Skor"}).text

    # ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptKadrolar_ctl01_formaNo
    guest_name = pageSoup.find(
        "a", {"id": f"{repeat_pattern_str}_lnkTakim2"}).text
    guest_score = pageSoup.find(
        "span", {"id": f"{repeat_pattern_str}_Label12"}).text

    host_logo_str = f"{repeat_pattern_str}_imgTakim1Logo"
    guest_logo_str = f"{repeat_pattern_str}_imgTakim2Logo"

    host_logo = get_logo(pageSoup, host_logo_str, host_name)
    print("get_logo : ", host_logo)
    guest_logo = get_logo(pageSoup, guest_logo_str, guest_name)
    print("get_logo : ", guest_logo)

    host_coach = pageSoup.find(
        "a", {"id": "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptTeknikKadro_ctl01_lnkTeknikSorumlu"}).text
    guest_coach = pageSoup.find(
        "a", {"id": "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptTeknikKadro_ctl01_lnkTeknikSorumlu"}).text

    player_pre_str_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptKadrolar_ctl"
    player_pre_str_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptKadrolar_ctl"

    host_line_up = line_up['host']['players']
    host_players = get_players(pageSoup, player_pre_str_host, host_line_up)

    guest_line_up = line_up['guest']['players']
    guest_players = get_players(pageSoup, player_pre_str_guest, guest_line_up)

    goal_pre_str_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptGoller_ctl"
    goal_pre_str_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptGoller_ctl"

    host_goals = get_goals(pageSoup, goal_pre_str_host)
    guest_goals = get_goals(pageSoup, goal_pre_str_guest)

    card_pre_str_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptKartlar_ctl"
    card_pre_str_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptKartlar_ctl"

    host_cards = get_cards(pageSoup, card_pre_str_host)
    guest_cards = get_cards(pageSoup, card_pre_str_guest)

    out_str_pre_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptCikanlar_ctl"
    player_out_str_post = "_lblCikan"
    minutes_out_str_post = "_oc"
    out_str_pre_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptCikanlar_ctl"

    in_str_pre_host = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptGirenler_ctl"
    player_in_str_post = "_lblGiren"
    minutes_in_str_post = "_og"
    in_str_pre_guest = "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptGirenler_ctl"

    host_out = get_changes(pageSoup,
                           out_str_pre_host, player_out_str_post, minutes_out_str_post)
    guest_out = get_changes(pageSoup,
                            out_str_pre_guest, player_out_str_post, minutes_out_str_post)

    host_in = get_changes(pageSoup,
                          in_str_pre_host, player_in_str_post, minutes_in_str_post)
    guest_in = get_changes(pageSoup,
                           in_str_pre_guest, player_in_str_post, minutes_in_str_post)

    country = "Türkiye"
    country_code = "TR"
    league = "Süper Lig"
    season = "2019"
    season_alias = _season.text.replace(
        " Sezonu (Profesyonel Takım) ", "").replace("Süper Lig ", "")

    df = pd.DataFrame.from_dict({
        "country": country,
        "country_code": country_code,
        "league": league,
        "season": season.title(),
        "stadium": stadium.title(),
        "season_alias": season_alias.title(),
        "match_date": match_date,
        "match_time": match_time,
        "referee": referee.title(),
        "referee_assist_1st": referee_assist_1st.title(),
        "referee_assist_2nd": referee_assist_2nd.title(),
        "referee_4th": referee_4th.title(),
        "referee_VAR": referee_VAR.title(),
        "referee_VAR_assist": referee_VAR_assist.title(),
        "host": [{
            "name": host_name.title(),
            "score": host_score,
            "coach": host_coach.title(),
            "goals": host_goals,
            "cards": host_cards,
            "changes_in": host_in,
            "changes_out": host_out,
            "players": host_players,
            "logo": host_logo,
            "line_up": line_up['host']["line_up"]}],
        "guest": [{
            "name": guest_name.title(),
            "score": guest_score,
            "coach": guest_coach.title(),
            "goals": guest_goals,
            "cards": guest_cards,
            "changes_in": guest_in,
            "changes_out": guest_out,
            "players": guest_players,
            "logo": guest_logo,
            "line_up": line_up['guest']["line_up"]}]})

    with open(mac_id + '.json', 'w', encoding='utf-8') as fw:
        df.to_json(fw, orient="records", force_ascii=False, lines=True)

    #data = df.to_dict(orient="records")[0]
    #requests.post('http://localhost:8008/api/matches', json=data)

    # with open('deneme.json', 'w+', encoding='utf-8') as fw:
    #    json.dump(data, fw, ensure_ascii=False)


#line_up = get_start_up(3221071)
#get_match("207154", line_up)

# tff_ids = ["207154", "207155", "207156", "207157", "207158",
#           "207159", "207160", "207161", "207162"]
# transfermarkt_ids = ["3221066", "3221067", "3221068", "3221069",
#                     "3221070", "3221071", "3221072", "3221073", "3221074"]


#transfermarkt_ids = ["3221066", "3221067", "3221068", "3221069", "3221070", "3221071", "3221072", "3221073", "3221074"]

#tff_ids = ["207159", "207162", "207158", "207157", "207160", "207154", "207155", "207156", "207161"]

tff_ids = ["207159"]
transfermarkt_ids = ["3221066"]

for i in range(len(tff_ids)):
    print(f"{i} : ")
    line_up = get_start_up(transfermarkt_ids[i])
    get_match(tff_ids[i], line_up)

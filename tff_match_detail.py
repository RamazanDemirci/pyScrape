import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from markt_line_up import *

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


class Scrape():
    def __init__(self):
        pass

    def getPersonAlias(self, person_title, name, belongTo):

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

    def get_players(self, pageSoup, player_pre_str, line_up, team_name):
        players = []

        for i in range(11):
            player_index = f'{(i+1):02}'
            id_str = f"{player_pre_str}{player_index}_formaNo"
            player_str = f"{player_pre_str}{player_index}_lnkOyuncu"
            forma_no = pageSoup.find(
                "span", {"id": id_str}).text.replace(".", "")
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

            player_alias = self.getPersonAlias(
                'player', player_name, team_name)

            players.append({"forma_no": int(forma_no),
                            "name": title(player_alias), "pos": pos})
        return players

    def getGoalType(self, t):
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

    def get_goals(self, pageSoup, goal_pre_str, goal_info_list):
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
                          "goal_type": self.getGoalType(matches[3]),
                          "goal_type_detail": goal_type_detail,
                          "assist": assist,
                          "assist_type": assist_type})
        return goals

    def get_card_type(self, t):
        if t == 'Sarı Kart':
            return 'Yellow'
        elif t == 'Çift Sarı Kart':
            return 'Red'
        elif t == 'Kırmızı Kart':
            return 'Red'

    def get_minutes(self, card_minutes_text):
        minutes = 0
        matches = re.match("(\d+).dk", card_minutes_text)
        if(matches == None):
            matches = re.match("(\d+)\+(\d+).dk", card_minutes_text)
            minutes = int(matches[1]) + int(matches[2])
        else:
            minutes = int(matches[1])
        return minutes

    def get_cards(self, pageSoup, team_name, card_pre_str, card_info_list):
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
            card_type = pageSoup.find(
                "img", {"id": card_type_str}).attrs['alt']

            # minutes = get_minutes(card_minutes.text)
            minutes = card_minutes.text.replace(".dk", "")
            reason = ""
            for item in card_info_list:
                if item["minutes"] == minutes:
                    reason = item["reason"]

            player_alias = self.getPersonAlias(
                'player', card_player.text, team_name)

            if reason == "":
                reason = "Foul"

            cards.append({"player": title(player_alias),
                          "minutes": minutes,
                          "card_type": self.get_card_type(card_type),
                          "reason": reason})
        return cards

    def get_changes(self, pageSoup, team_name, pre_string, player_post_string, minutes_post_string, changes_info_list):
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

            player_alias = self.getPersonAlias(
                'player', player.text, team_name)

            result.append({"player": title(player_alias),
                           "minutes": minute,
                           "reason": reason})
        return result

    def get_logo(self, pageSoup, logo_str, team_info):
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

    def get_match(self, fixture):
        print(f'get_match : host:{fixture["host"]}, guest:{fixture["guest"]}')
        line_up = get_start_up(fixture["markt_id"])
        headers = {'User-Agent':
                   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
        page = f'https://www.tff.org/Default.aspx?pageId=29&macId={fixture["tff_id"]}'
        pageTree = requests.get(page, headers=headers)
        pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

        payload = {
            "stadium": fixture["stadium"],
            "match_date": fixture["date"],
            "match_time": fixture["time"]
        }

        response = requests.get(f'{base_url}/api/match_exist', data=payload)

        if response.status_code != 200:
            return

        referee = pageSoup.find(
            "a", {"id": f"{repeat_pattern_str}_rpt_ctl00_lnkHakem"}).text.replace("(Hakem)", "")
        referee = self.getPersonAlias(
            "Referee", referee, "Federation")
        referee_assist_1st = pageSoup.find(
            "a", {"id": f"{repeat_pattern_str}_rpt_ctl01_lnkHakem"}).text.replace("(1. Yardımcı Hakem)", "")
        referee_assist_1st = self.getPersonAlias(
            "Referee", referee_assist_1st, "Federation")
        referee_assist_2nd = pageSoup.find(
            "a", {"id": f"{repeat_pattern_str}_rpt_ctl02_lnkHakem"}).text.replace("(2. Yardımcı Hakem)", "")
        referee_assist_2nd = self.getPersonAlias(
            "Referee", referee_assist_2nd, "Federation")

        host_coach = pageSoup.find(
            "a", {"id": "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim1_rptTeknikKadro_ctl01_lnkTeknikSorumlu"}).text
        guest_coach = pageSoup.find(
            "a", {"id": "ctl00_MPane_m_29_194_ctnr_m_29_194_grdTakim2_rptTeknikKadro_ctl01_lnkTeknikSorumlu"}).text

        host_line_up = line_up['host']['players']
        host_players = self.get_players(
            pageSoup, player_pre_str_host, host_line_up, fixture["host"])

        guest_line_up = line_up['guest']['players']
        guest_players = self.get_players(
            pageSoup, player_pre_str_guest, guest_line_up, fixture["guest"])

        host_goals = self.get_goals(
            pageSoup, goal_pre_str_host, line_up['goals'])
        guest_goals = self.get_goals(
            pageSoup, goal_pre_str_guest, line_up['goals'])

        host_cards = self.get_cards(
            pageSoup, fixture["host"], card_pre_str_host, line_up['cards'])
        guest_cards = self.get_cards(
            pageSoup, fixture["guest"], card_pre_str_guest, line_up['cards'])

        host_out = self.get_changes(pageSoup, fixture["host"],
                                    out_str_pre_host, player_out_str_post, minutes_out_str_post, line_up['substitutions'])
        guest_out = self.get_changes(pageSoup, fixture["guest"],
                                     out_str_pre_guest, player_out_str_post, minutes_out_str_post, line_up['substitutions'])

        host_in = self.get_changes(pageSoup, fixture["host"],
                                   in_str_pre_host, player_in_str_post, minutes_in_str_post, line_up['substitutions'])
        guest_in = self.get_changes(pageSoup, fixture["guest"],
                                    in_str_pre_guest, player_in_str_post, minutes_in_str_post, line_up['substitutions'])

        if host_cards is None:
            host_cards = []
        if guest_cards is None:
            guest_cards = []
        if host_goals is None:
            host_goals = []
        if guest_goals is None:
            guest_goals = []
        if host_out is None:
            host_out = []
        if guest_out is None:
            guest_out = []
        if host_in is None:
            host_in = []
        if guest_in is None:
            guest_in = []

        df = pd.DataFrame.from_dict({
            "league": fixture["league"],
            "season": fixture["season"],
            "week": fixture["week"],
            "stadium": fixture["stadium"],
            "match_date": fixture["date"],
            "match_time": fixture["time"],
            "referee": title(referee),
            "referee_assist_1st": title(referee_assist_1st),
            "referee_assist_2nd": title(referee_assist_2nd),
            "missed_penalties": [line_up['missed_penalties']],
            "host": [{
                "name": fixture["host"],
                "score": fixture["h_score"],
                "coach": title(host_coach),
                "logo": fixture["host"],
                "line_up": line_up['host']["line_up"],
                "goals": host_goals,
                "cards": host_cards,
                "changes_in": host_in,
                "changes_out": host_out,
                "players": host_players,
            }],
            "guest": [{
                "name": fixture["guest"],
                "score": fixture["g_score"],
                "coach": title(guest_coach),
                "logo": fixture["guest"],
                "line_up": line_up['guest']["line_up"],
                "goals": guest_goals,
                "cards": guest_cards,
                "changes_in": guest_in,
                "changes_out": guest_out,
                "players": guest_players,
            }]})

        data = df.to_dict(orient="records")[0]
        #requests.post('http://localhost:8008/api/matches', json=data)
        requests.post(f'{base_url}/api/matches', json=data)

        # with open("matches.json", 'w', encoding='utf-8') as wf:
        #    json.dump(data, wf, ensure_ascii=False)
        print("...")

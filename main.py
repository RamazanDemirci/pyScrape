from tff_match_detail import Scrape
import time
import multiprocessing
import requests
from selenium import webdriver
from time import sleep

from bs4 import BeautifulSoup, element
import json
from utils import *
from operator import itemgetter

url = "https://www.4devs.com.br/gerador_de_cpf"
url_tff = "https://www.tff.org/Default.aspx?pageID=322"

rp = "ctl00_MPane_m_322_1480_ctnr_m_322_1480"

prev_standings = {}


session = None


def set_global_session():
    global session
    if not session:
        session = requests.Session()


def scrape_data(match):
    scrape = Scrape()
    print(f'tff_id : {match["tff_id"]}, markt_id : {match["markt_id"]}')
    scrape.get_match(match)


def download_all_sites(fixture):
    with multiprocessing.Pool(initializer=set_global_session) as pool:
        pool.map(scrape_data, fixture)


def get_empty_standing(team_name):
    standing = {}
    standing['team'] = team_name
    standing['playedGames'] = 0
    standing['goalsFor'] = 0
    standing['goalsAgainst'] = 0
    standing['goalDifference'] = 0
    standing['won'] = 0
    standing['points'] = 0
    standing['draw'] = 0
    standing['lost'] = 0
    standing['position'] = 0
    return standing


base_url = "http://localhost:8000"


def get_match_result(h_score, g_score):
    result = 0
    if h_score > g_score:
        result = 1
    elif h_score == g_score:
        result = 0
    elif h_score < g_score:
        result = 2
    return result


def update_standing(is_host, prev_standing, h_score, g_score, result):
    if is_host is False:
        tmp = h_score
        h_score = g_score
        g_score = tmp

    prev_standing['playedGames'] = prev_standing['playedGames'] + 1
    prev_standing['goalsFor'] = prev_standing['goalsFor'] + int(h_score)
    prev_standing['goalsAgainst'] = prev_standing['goalsAgainst'] + \
        int(g_score)
    prev_standing['goalDifference'] = prev_standing['goalsFor'] - \
        prev_standing['goalsAgainst']

    if result == 1:
        if is_host is True:
            prev_standing['won'] = prev_standing['won'] + 1
            prev_standing['points'] = prev_standing['points'] + 3
        else:
            prev_standing['lost'] = prev_standing['lost'] + 1
    elif result == 0:
        prev_standing['draw'] = prev_standing['draw'] + 1
        prev_standing['points'] = prev_standing['points'] + 1
    elif result == 2:
        if is_host is False:
            prev_standing['won'] = prev_standing['won'] + 1
            prev_standing['points'] = prev_standing['points'] + 3
        else:
            prev_standing['lost'] = prev_standing['lost'] + 1
    return prev_standing


def order_standing(detail):
    # newlist = sorted(standing_list, key=itemgetter(
    #    'points', 'goalDifference', 'team'), reverse=True)
    prev_standings['detail'] = sorted(sorted(detail, key=lambda x: (x['team'])), key=lambda x: (
        x['points'], x['goalDifference']), reverse=True)

    for i in range(0, len(prev_standings['detail'])):
        prev_standings['detail'][i]['position'] = i+1


def create_standing(week_fixture):
    prev_standings['league'] = week_fixture[0]['league']
    prev_standings['season'] = week_fixture[0]['season']
    prev_standings['week'] = week_fixture[0]['week']
    for match in week_fixture:
        result = get_match_result(match['h_score'], match['g_score'])

        for prev_standing in prev_standings['detail']:
            if match['host'] == prev_standing['team']:
                prev_standing = update_standing(
                    True, prev_standing, match["h_score"], match["g_score"], result)
            elif match['guest'] == prev_standing['team']:
                prev_standing = update_standing(
                    False, prev_standing, match["h_score"], match["g_score"], result)

        if len(prev_standings['detail']) < 18:
            host_exist = False
            guest_exist = False
            prev_standings['week'] = 0
            for prev_standing in prev_standings['detail']:
                if match['host'] == prev_standing['team']:
                    host_exist = True
                elif match['host'] == prev_standing['team']:
                    guest_exist = True

            if host_exist == False:
                standing = get_empty_standing(match['host'])
                prev_standings['detail'].append(standing)
            if guest_exist == False:
                standing = get_empty_standing(match['guest'])
                prev_standings['detail'].append(standing)
    if prev_standings['detail'][0]['playedGames'] == 0:
        order_standing(prev_standings['detail'])
        # post zeroed standing
        requests.post(f'{base_url}/api/standing', json=prev_standings)
        create_standing(week_fixture)   # call for first week again
    else:
        order_standing(prev_standings['detail'])
        requests.post(f'{base_url}/api/standing', json=prev_standings)


season_index = 1
league_index = 0
league_text = 'Süper Lig'
season_text = "2019"

week_index = 0
teams = []


def nextPage(driver):
    global season_index
    global league_index
    global week_index

    cbSeason = driver.find_element_by_id(f'{rp}_rdbSezonSec_index')
    cbLeague = driver.find_element_by_id(f'{rp}_rdcmbLigler_index')
    cbWeek = driver.find_element_by_id(f'{rp}_hafta_index')

    driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);",
                          cbSeason,
                          "value",
                          season_index)

    driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);",
                          cbLeague,
                          "value",
                          league_index)

    driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);",
                          cbWeek,
                          "value",
                          week_index)

    driver.execute_script(
        f"document.getElementById('{rp}_btnSave2').click()")


def get_fixture(driver):
    fixture = []
    soup = BeautifulSoup(driver.page_source)

    result = soup.find(
        "span", {"id": f"{rp}_grdSonuc_ctl01_ctl04_Label9"})

    if result is None:
        table = soup.find("table", {"id": f"{rp}_grdSonuc_ctl01"})
        tbody = table.contents[4]
        if len(tbody.contents) > 0:
            rows = tbody.contents
            for row in rows:
                if type(row) == element.Tag:
                    cols = row.contents
                    week = {}
                    for i in range(len(cols)):
                        if type(cols[i]) is element.Tag:
                            if i == 1:
                                tff_match_id = cols[i].contents[1].attrs['href'].split("macId=")[
                                    1]
                                week["tff_id"] = tff_match_id
                            if i == 3:
                                score_list = cols[i].text.replace(
                                    "\n", "").split("-")
                                week["h_score"] = score_list[0]
                                week["g_score"] = score_list[1]
                            elif i == 2:
                                host = cols[i].text.replace("\n", "")
                                week["host"] = get_team_alias(
                                    league_text, season_text, teams, host)
                            elif i == 4:
                                guest = cols[i].text.replace("\n", "")
                                week["guest"] = get_team_alias(
                                    league_text, season_text, teams, guest)
                            elif i == 5:
                                week["date"] = cols[i].text.replace(
                                    "\n", "")
                            elif i == 6:
                                week["time"] = cols[i].text.replace(
                                    "\n", "")
                            elif i == 7:
                                stadium = cols[i].text.replace(
                                    "\n", "")
                                week["stadium"] = get_stadium(stadium)
                            elif i == 8:
                                week["league"] = league_text
                                week["season"] = season_text
                                week["week"] = week_index
                    fixture.append(week)
                    print(week)
    return fixture


def get_last_standing_index():
    global prev_standings
    payload = {
        "league": "Süper Lig",
        "season": "2019",
    }

    response = requests.get(f'{base_url}/api/standing_all', data=payload)
    res_dict = json.loads(response.content.decode("UTF-8"))
    max_week = max(res_dict, key=itemgetter("week"))

    # for item in res_dict:
    #    if item["week"] == 30:
    #        max_week = item
    #        break

    prev_standings = max_week

    return max_week['week']+1


def get_tff():
    global season_index
    global league_index
    global week_index
    global season_text

    driver = webdriver.Chrome()
    driver.get(url_tff)

    dd = driver.find_element_by_id(f'{rp}_rdbSezonSec')
    seasonCont = driver.find_element_by_id(f'{rp}_rdbSezonSec_DropDown')

    all_options = seasonCont.find_elements_by_tag_name("div")

    prev_standings['detail'] = []

    last_week_index = get_last_standing_index()

    for index in range(last_week_index, 35):  # loop week
        week_index = index
        nextPage(driver)
        sleep(1)
        cbSeason = driver.find_element_by_id(f'{rp}_rdbSezonSec_index')
        cbSeason_text = driver.find_element_by_id(f'{rp}_rdbSezonSec_text')
        cbWeek = driver.find_element_by_id(f'{rp}_hafta_index')
        cbWeek_text = driver.find_element_by_id(f'{rp}_hafta_text')
        season_text = cbSeason_text.get_attribute('value').split('-')[0]

        print(
            f"{season_index}({season_text}) : {league_index}({league_text}) : {week_index}")

        fixture = get_fixture(driver)

        if len(fixture) > 0:
            fixture_updated = get_markt(season_text, index, fixture)
            download_all_sites(fixture_updated)
            # for match in fixture_updated:
            #    scrape_data(match)
            create_standing(fixture)


def get_markt(season_id, week_id, fixture):
    url_markt = f'https://www.transfermarkt.com.tr/super-lig/spieltagtabelle/wettbewerb/TR1?saison_id={season_id}&spieltag={week_id}'

    headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.107 Safari/537.36'}
    pageTree = requests.get(url_markt, headers=headers)
    soup = BeautifulSoup(pageTree.content, 'html.parser')

    match_id_tags = soup.findChildren(
        "span", {"class": f"matchresult"}, recursive=True)

    markt_fixture = []
    for item in match_id_tags:
        link = item.parent
        match_id = ""
        if link.name == "span":
            match_id = link.attrs['id'].replace('ergebnis_', '')
            td = link.parent
        else:
            match_id = link.attrs['href'].replace(
                '/spielbericht/index/spielbericht/', '')
            td = link.parent.parent
        tr = td.parent
        _host = tr.contents[9].contents[3]
        _guest = tr.contents[19].contents[1]

        markt_match = {
            "host": _host.text,
            "guest": _guest.text,
            "markt_id": match_id,
        }
        markt_fixture.append(markt_match)

    for markt in markt_fixture:
        for item in fixture:
            host = item["host"].replace("spor", "")
            guest = item["guest"].replace("spor", "")
            if host in markt["host"]:
                if guest in markt["guest"]:
                    item["markt_id"] = markt["markt_id"]
                    print(
                        f"{item['tff_id']} - {item['markt_id']}- {item['host']} -- {item['guest']}")

    return fixture


if __name__ == "__main__":
    start_time = time.time()

    get_tff()

    duration = time.time() - start_time
    print(f"Downloaded {duration} seconds")

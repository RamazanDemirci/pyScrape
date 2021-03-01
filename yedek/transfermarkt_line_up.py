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


def get_start_up(mac_id):

    headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

    page = f"https://www.transfermarkt.com/spielbericht/index/spielbericht/{mac_id}"
    pageTree = requests.get(page, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    rn = pageSoup.find_all("div", {"class": "rn"})

    style = pageSoup.find_all(
        "div", {"class": "aufstellung-spieler-container"})
    ss = style[0].attrs['style'].split(';')
    f1 = ss[0].replace('top:', '').replace('left:', '').replace('%', '')
    s2 = ss[1].replace('top:', '').replace('left:', '').replace('%', '')

    starting_line_up = pageSoup.find_all(
        "div", {"class": "aufstellung-unterueberschrift"})

    host_players = []
    host_rn = []
    host_pos_left = []
    host_pos_top = []
    guest_players = []
    guest_rn = []
    guest_pos_left = []
    guest_pos_top = []

    host_line_up = get_line_up(starting_line_up[0].text)
    guest_line_up = get_line_up(starting_line_up[1].text)

    for i in range(11):
        x = getPos(style[i].attrs['style'].split(';')[0])
        y = getPos(style[i].attrs['style'].split(';')[1])
        host_players.append({"number": rn[i].text,
                             "pos": {
            "px": x,
            "py": y
        }})
        x = getPos(style[i+11].attrs['style'].split(';')[0])
        y = getPos(style[i+11].attrs['style'].split(';')[1])
        guest_players.append({
            "number": rn[i+11].text,
            "pos": {
                "px": x,
                "py": y
            }})

    df = pd.DataFrame({"host": [{"players": host_players, "line_up": host_line_up}],
                       "guest": [{"players": guest_players, "line_up": guest_line_up}]})

    # print(df.head())

    # with open('df.json', 'w', encoding='utf-8') as fw:
    #    df.to_json(fw, orient="records", force_ascii=False)

    data = df.to_dict(orient="records")[0]
    return data


#data = get_start_up(3221073)
#host = data['host']
#players = data['host']['players']
# for item in players:
#    print(item['number'])
#    print(item['pos'])

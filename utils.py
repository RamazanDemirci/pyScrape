import requests

base_url = "http://localhost:8000"


def title(str):
    output = ""
    str_list = str.split(" ")
    for item in str_list:
        tmp = item.capitalize()
        output = f'{output} {tmp}'
    return output.strip()


def get_stadium(stadium_name):
    stadium = title(stadium_name.split(" -")[0])
    stadium = title(stadium.split("Stad")[0])
    return stadium


def team_cg(team_name):
    return team_name.replace(
        "A.Ş.", "").replace("FK", "").replace("FUTBOL KULÜBÜ", "").lower().strip()


def get_team_alias(league, season, teams, team_name):
    team_name = team_cg(team_name)
    team_alias = ''
    if len(teams) > 0:
        for team in teams:
            if team_name == team['name']:
                team_alias = team['alias']

    if team_alias == '':
        team_info = getTeamInfo(league, season, team_name)
        teams.append(team_info)
        team_alias = team_info['alias']
    return team_alias


def getTeamInfo(league, season, host_name):
    team_info = {}
    host_name = team_cg(host_name)
    payload = {
        "name": host_name,
    }
    response = requests.get(f'{base_url}/api/teams', data=payload)
    if response.status_code == 200:
        data = response.json()
        team_info = data
    else:
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

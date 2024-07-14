import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests

valid_positions = ['QB', 'RB', 'WR', 'TE']


# function that returns a player's game log in a given season
# player: player's full name (e.g. Tom Brady)
# position: abbreviation (QB, RB, WR, TE only)
def get_player_game_log(player: str, position: str, season: int, player_url: str = None) -> pd.DataFrame:
    """A function to retrieve a player's game log in a given season.

    Returns a pandas DataFrame of a NFL player's game log in a given season, including position-specific statistics.

    Args:
        player (str): A NFL player's full name, as it appears on Pro Football Reference
        position (str): The position the player plays. Must be 'QB', 'RB', 'WR', or 'TE'
        season (int): The season of the game log you are trying to retrieve

    Returns:
        pandas.DataFrame: Each game is a row of the DataFrame

    """

    # position arg must be formatted properly
    if position not in valid_positions:
        raise Exception('Invalid position: "position" arg must be "QB", "RB", "WR", or "TE"')


    new_player_url = None

    if not player_url:
        # make request to find proper href
        r1 = make_request_list(player, position, season)
        player_list = get_soup(r1)

        # find href
        href = get_href(player, position, season, player_list)

        # make HTTP request and extract HTML
        new_player_url = build_gamelog_url(href)
        player_url = new_player_url

    # Make gamelog request
    r2 = make_request_player(player_url, season)

    # parse HTML using BeautifulSoup
    game_log = get_soup(r2)

    # generating the appropriate game log format according to position
    if 'QB' in position:
        return qb_game_log(game_log), new_player_url
    elif 'WR' in position or 'TE' in position:
        return wr_game_log(game_log, season), new_player_url
    elif 'RB' in position:
        return rb_game_log(game_log), new_player_url


# helper function that gets the player's href
def get_href(player: str, position: str, season: int, player_list: BeautifulSoup) -> str:
    players = player_list.find('div', id='div_players').find_all('p')
    for p in players:
        seasons = p.text.split(' ')
        seasons = seasons[len(seasons) - 1].split('-')
        if season >= int(seasons[0]) and season <= int(seasons[1]) and str.lower(player) in str.lower(p.text) and (position in p.text or (True if position == 'RB' and 'FB' in p.text else False) or (True if position == 'RB' and 'WR' in p.text else False)) : # check if FB vs RB
            return p.find('a').get('href').replace('.htm', '')
    raise Exception('Cannot find a ' + position + ' named ' + player + ' from ' + str(season))


# helper function that makes a HTTP request over a list of players with a given last initial
def make_request_list(player: str, position: str, season: int):
    name_split = player.split(' ')
    last_initial = name_split[1][0]
    url = 'https://www.pro-football-reference.com/players/%s/' % (last_initial)
    return requests.get(url)


def build_gamelog_url(href: str):
    return 'https://www.pro-football-reference.com%s/gamelog/' % (href)

# helper function that makes a HTTP request for a given player's game log
def make_request_player(url: str, season: int):
    return requests.get(url + '%s/' % season)


# helper function that takes a requests.Response object and returns a BeautifulSoup object
def get_soup(request):
    return BeautifulSoup(request.text, 'html.parser')


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a QB game log
def qb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant QB stats, in my opinion. Could adjust if necessary
    data = {
        'date': [],
        'week': [],
        'age': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'started': [],
        'cmp': [],
        'att': [],
        'cmp_perc': [],
        'pass_yds': [],
        'pass_td': [],
        'int': [],
        'rating': [],
        'sacked': [],
        'rush_att': [],
        'rush_yds': [],
        'rush_td': [],
        'fumbles': [],
        'snaps': [],
        'snap_pct': [],
        'inactive': []
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x == 'COVID-19 List':
            to_ignore.append(i)

    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            data['age'].append(float(table_rows[i].find('td', {'data-stat': 'age'}).text or 0))
            data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            data['team_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            )
            data['opp_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            )

            data['started'].append(None)

            #10

            data['cmp'].append(None)
            data['att'].append(None)
            data['cmp_perc'].append(None)
            data['pass_yds'].append(None)
            data['pass_td'].append(None)
            data['int'].append(None)
            data['rating'].append(None)
            data['sacked'].append(None)

            #18
            data['rush_att'].append(None)
            data['rush_yds'].append(None)
            data['rush_td'].append(None)
            data['fumbles'].append(None)
            data['snaps'].append(None)
            data['snap_pct'].append(None)

            data['inactive'].append(True)


        if i not in to_ignore:
            try: 
                data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
                data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text or 0))
                data['age'].append(float(table_rows[i].find('td', {'data-stat': 'age'}).text or 0))
                data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
                data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
                data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
                data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
                data['team_pts'].append(
                    int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
                )
                data['opp_pts'].append(
                    int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
                )

                #started logic
                if not table_rows[i].find('td', {'data-stat': 'gs'}).text:
                    started = False
                else:
                    started = True
                data['started'].append(started)

                #10

                if not table_rows[i].find('td', {'data-stat': 'pass_cmp'}):
                    data['cmp'].append(int(0))
                    data['att'].append(int(0))
                    data['cmp_perc'].append(float(0))
                    data['pass_yds'].append(int(0))
                    data['pass_td'].append(int(0))
                    data['int'].append(int(0))
                    data['rating'].append(float(0))
                    data['sacked'].append(int(0))
                else:
                    data['cmp'].append(int(table_rows[i].find('td', {'data-stat': 'pass_cmp'}).text or 0))
                    data['att'].append(int(table_rows[i].find('td', {'data-stat': 'pass_att'}).text or 0))
                    data['cmp_perc'].append(float(table_rows[i].find('td', {'data-stat': 'pass_cmp_perc'}).text or 0))
                    data['pass_yds'].append(int(table_rows[i].find('td', {'data-stat': 'pass_yds'}).text or 0))
                    data['pass_td'].append(int(table_rows[i].find('td', {'data-stat': 'pass_td'}).text or 0))
                    data['int'].append(int(table_rows[i].find('td', {'data-stat': 'pass_int'}).text or 0))
                    data['rating'].append(float(table_rows[i].find('td', {'data-stat': 'pass_rating'}).text or 0))
                    data['sacked'].append(int(table_rows[i].find('td', {'data-stat': 'pass_sacked'}).text or 0))

                #18

                if not table_rows[i].find('td', {'data-stat': 'rush_att'}):
                    data['rush_att'].append(0)
                    data['rush_yds'].append(0)
                    data['rush_td'].append(0)
                else:
                    data['rush_att'].append(int(table_rows[i].find('td', {'data-stat': 'rush_att'}).text or 0))
                    data['rush_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rush_yds'}).text or 0))
                    data['rush_td'].append(int(table_rows[i].find('td', {'data-stat': 'rush_td'}).text or 0))

                #21

                if not table_rows[i].find('td', {'data-stat': 'fumbles_lost'}):
                    data['fumbles'].append(0)
                else:
                    data['fumbles'].append(int(table_rows[i].find('td', {'data-stat': 'fumbles_lost'}).text or 0))


                data['snaps'].append(int(table_rows[i].find('td', {'data-stat': 'offense'}).text or 0))
                data['snap_pct'].append(float(table_rows[i].find('td', {'data-stat': 'off_pct'}).text.replace('%', '') or 0))
            
                data['inactive'].append(False)
                #25
            except Exception as e:
                print(e)

    print(data)
    return pd.DataFrame(data=data)


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a WR/TE game log
def wr_game_log(soup: BeautifulSoup, season: int) -> pd.DataFrame:
    # Most relevant WR stats, in my opinion.
    # Could adjust if necessary (maybe figure out how to incorporate rushing stats?)

    data = {
        'date': [],
        'week': [],
        'age': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'started': [],
        'rush_att': [],
        'rush_yds': [],
        'yds_per_att': [],
        'rush_td': [],
        'tgt': [],
        'rec': [],
        'rec_yds': [],
        'rec_td': [],
        'yds_per_rec': [],
        'ctch_perc': [],
        'yds_per_tgt': [],
        'fumbles': [],
        'snaps': [],
        'snap_pct': [],
        'inactive': []
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x =='COVID-19 List':
            to_ignore.append(i)

    # adding data to data dictionray
    for i in range(len(table_rows)):
        if i in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            data['age'].append(float(table_rows[i].find('td', {'data-stat': 'age'}).text or 0))
            data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            data['team_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            )
            data['opp_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            )
            data['started'].append(None)
#10
            data['rush_att'].append(None)
            data['rush_yds'].append(None)
            data['yds_per_att'].append(None)
            data['rush_td'].append(None)

            data['tgt'].append(None)
            data['rec'].append(None)
            data['rec_yds'].append(None)
            data['rec_td'].append(None)
            data['yds_per_rec'].append(None)
            data['ctch_perc'].append(None)
            data['yds_per_tgt'].append(None)
            data['fumbles'].append(None)
            data['snaps'].append(None)
            data['snap_pct'].append(None)
            
            data['inactive'].append(True)


        if i not in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            data['age'].append(float(table_rows[i].find('td', {'data-stat': 'age'}).text or 0))
            data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            data['team_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            )
            data['opp_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            )

            #started logic
            if not table_rows[i].find('td', {'data-stat': 'gs'}).text:
                started = False
            else:
                started = True

            data['started'].append(started)
#10
            if not table_rows[i].find('td', {'data-stat': 'rush_att'}):
                data['rush_att'].append(int(0))
                data['rush_yds'].append(int(0))
                data['yds_per_att'].append(float(0))
                data['rush_td'].append(int(0))
            else:
                data['rush_att'].append(int(table_rows[i].find('td', {'data-stat': 'rush_att'}).text or 0))
                data['rush_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rush_yds'}).text or 0))
                data['yds_per_att'].append(float(table_rows[i].find('td', {'data-stat': 'rush_yds_per_att'}).text or 0))
                data['rush_td'].append(int(table_rows[i].find('td', {'data-stat': 'rush_td'}).text or 0))

            if not table_rows[i].find('td', {'data-stat': 'targets'}):
                data['tgt'].append(int(0))
                data['rec'].append(int(0))
                data['rec_yds'].append(int(0))
                data['rec_td'].append(int(0))
                data['yds_per_rec'].append(float(0))
                data['ctch_perc'].append(float(0))
                data['yds_per_tgt'].append(float(0))
            else:
                data['tgt'].append(int(table_rows[i].find('td', {'data-stat': 'targets'}).text or 0))
                data['rec'].append(int(table_rows[i].find('td', {'data-stat': 'rec'}).text or 0))
                data['rec_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yds'}).text or 0))
                data['rec_td'].append(int(table_rows[i].find('td', {'data-stat': 'rec_td'}).text or 0))
                data['yds_per_rec'].append(float(table_rows[i].find('td', {'data-stat': 'rec_yds_per_rec'}).text or 0))
                data['ctch_perc'].append(float(table_rows[i].find('td', {'data-stat': 'catch_pct'}).text.replace('%', '') or 0))
                data['yds_per_tgt'].append(float(table_rows[i].find('td', {'data-stat': 'rec_yds_per_tgt'}).text or 0))

            if not table_rows[i].find('td', {'data-stat': 'fumbles_lost'}):
                data['fumbles'].append(int(0))
            else:
                data['fumbles'].append(int(table_rows[i].find('td', {'data-stat': 'fumbles_lost'}).text or 0))

            data['snaps'].append(int(table_rows[i].find('td', {'data-stat': 'offense'}).text or 0))
            data['snap_pct'].append(float(table_rows[i].find('td', {'data-stat': 'off_pct'}).text.replace('%', '') or 0))

            data['inactive'].append(False)
    return pd.DataFrame(data=data)


def rb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant RB stats, in my opinion. Could adjust if necessary
    data = {
        'date': [],
        'week': [],
        'age': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'started': [],
        'rush_att': [],
        'rush_yds': [],
        'yds_per_att': [],
        'rush_td': [],
        'tgt': [],
        'rec': [],
        'rec_yds': [],
        'rec_td': [],
        'yds_per_rec': [],
        'ctch_perc': [],
        'yds_per_tgt': [],
        'fumbles': [],
        'snaps': [],
        'snap_pct': [],
        'inactive': []
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x == 'COVID-19 List':
            to_ignore.append(i)

    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            data['age'].append(float(table_rows[i].find('td', {'data-stat': 'age'}).text or 0))
            data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            data['team_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            )
            data['opp_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            )
            data['started'].append(False)

            data['rush_att'].append(None)
            data['rush_yds'].append(None)
            data['yds_per_att'].append(None)
            data['rush_td'].append(None)

            data['tgt'].append(None)
            data['rec'].append(None)
            data['rec_yds'].append(None)
            data['rec_td'].append(None)
            data['yds_per_rec'].append(None)
            data['ctch_perc'].append(None)
            data['yds_per_tgt'].append(None)
            data['fumbles'].append(None)
            data['snaps'].append(None)
            data['snap_pct'].append(None)
            
            elements = table_rows[i].find_all('td')
            x = elements[len(elements) - 1].text
            data['inactive'].append(True)

        if i not in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            data['age'].append(float(table_rows[i].find('td', {'data-stat': 'age'}).text or 0))
            data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            data['team_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            )
            data['opp_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            )

            #started logic
            if not table_rows[i].find('td', {'data-stat': 'gs'}).text:
                started = False
            else:
                started = True

            data['started'].append(started)

            if not table_rows[i].find('td', {'data-stat': 'rush_att'}):
                data['rush_att'].append(int(0))
                data['rush_yds'].append(int(0))
                data['yds_per_att'].append(float(0))
                data['rush_td'].append(int(0))
            else:
                data['rush_att'].append(int(table_rows[i].find('td', {'data-stat': 'rush_att'}).text or 0))
                data['rush_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rush_yds'}).text or 0))
                data['yds_per_att'].append(float(table_rows[i].find('td', {'data-stat': 'rush_yds_per_att'}).text or 0))
                data['rush_td'].append(int(table_rows[i].find('td', {'data-stat': 'rush_td'}).text or 0))

            if not table_rows[i].find('td', {'data-stat': 'targets'}):
                data['tgt'].append(int(0))
                data['rec'].append(int(0))
                data['rec_yds'].append(int(0))
                data['rec_td'].append(int(0))
                data['yds_per_rec'].append(float(0))
                data['ctch_perc'].append(float(0))
                data['yds_per_tgt'].append(float(0))
            else:
                data['tgt'].append(int(table_rows[i].find('td', {'data-stat': 'targets'}).text or 0))
                data['rec'].append(int(table_rows[i].find('td', {'data-stat': 'rec'}).text or 0))
                data['rec_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yds'}).text or 0))
                data['rec_td'].append(int(table_rows[i].find('td', {'data-stat': 'rec_td'}).text or 0))
                data['yds_per_rec'].append(float(table_rows[i].find('td', {'data-stat': 'rec_yds_per_rec'}).text or 0))
                data['ctch_perc'].append(float(table_rows[i].find('td', {'data-stat': 'catch_pct'}).text.replace('%', '') or 0))
                data['yds_per_tgt'].append(float(table_rows[i].find('td', {'data-stat': 'rec_yds_per_tgt'}).text or 0))

            if not table_rows[i].find('td', {'data-stat': 'fumbles_lost'}):
                data['fumbles'].append(int(0))
            else:
                data['fumbles'].append(int(table_rows[i].find('td', {'data-stat': 'fumbles_lost'}).text or 0))

            data['snaps'].append(int(table_rows[i].find('td', {'data-stat': 'offense'}).text or 0))
            data['snap_pct'].append(float(table_rows[i].find('td', {'data-stat': 'off_pct'}).text.replace('%', '') or 0))
            data['inactive'].append(False)
            
    return pd.DataFrame(data=data)


def main():
    print(get_player_game_log('Jonathan Taylor', 'RB', 2021))


if __name__ == '__main__':
    main()

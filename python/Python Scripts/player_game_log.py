import math
import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
from enums.data_stat_type import Data_Stat_Type

valid_positions = ['QB', 'RB', 'WR', 'TE']

# Sections of the table:
data_stat = 'data-stat'

# data columns from website
date = 'date'
week_num = 'week_num'
age = 'age'
team = 'team_name_abbr'
game_location = 'game_location'
opp_name = 'opp_name_abbr'
result = 'game_result'
is_starter = 'is_starter'
pass_cmp = 'pass_cmp'
pass_att = 'pass_att'
pass_cmp_perc = 'pass_cmp_pct'
pass_yds = 'pass_yds'
pass_td = 'pass_td'
pass_int = 'pass_int'
pass_rating = 'pass_rating'
pass_sacked = 'pass_sacked'
### NOT INCLUDED YET, BUT EXISTS:
pass_yds_per_att = 'pass_yds_per_att'

rush_att = 'rush_att'
rush_yds = 'rush_yds'
rush_yds_per_att = 'rush_yds_per_att'
rush_td = 'rush_td'
fumbles = 'fumbles_lost'
snap_count = 'snap_counts_offense'
snap_count_perc = 'snap_counts_off_pct'

targets = 'targets'
rec = 'rec'
rec_yds = 'rec_yds'
rec_td = 'rec_td'
yds_per_rec = 'rec_yds_per_rec'
catch_perc = 'catch_pct'
yds_per_tgt = 'rec_yds_per_tgt'


inactive_statuses = [
    'Inactive' ,
    'Did Not Play',
    'Injured Reserve',
    'COVID-19 List'
]

# function that returns a player's game log in a given season
# player: player's full name (e.g. Tom Brady)
# position: abbreviation (QB, RB, WR, TE only)
def get_player_game_log(player: str, position: str, season: int, player_url: str = None, profootball_position: str = None) -> pd.DataFrame:
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
        r1 = make_request_list(player, profootball_position or position, season)
        player_list = get_soup(r1)

        # find href
        href = get_href(player, profootball_position or position, season, player_list)

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
    elif 'TE' in position:
        return te_game_log(game_log), new_player_url


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

def getValue(tableRow, data_stat_value, type):
    match type:
        case Data_Stat_Type.INT:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return math.nan
            return int(tableRow.find('td', {data_stat: data_stat_value}).text or 0)
        case Data_Stat_Type.FLOAT:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return math.nan
            return float(tableRow.find('td', {data_stat: data_stat_value}).text or 0)
        case Data_Stat_Type.RESULT:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return math.nan
            return tableRow.find('td', {data_stat: data_stat_value}).text.split(' ')[0]
        case Data_Stat_Type.TEAM_PTS:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return math.nan
            return int(tableRow.find('td', {data_stat: data_stat_value}).text.split(' ')[1].split('-')[0])
        case Data_Stat_Type.OPP_PTS:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return math.nan
            return int(tableRow.find('td', {data_stat: data_stat_value}).text.split(' ')[1].split('-')[1])
        case Data_Stat_Type.BOOLEAN:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return pd.NA
            if not tableRow.find('td', {data_stat: data_stat_value}).text:
                return False
            if tableRow.find('td', {data_stat: data_stat_value}).text in inactive_statuses:
                return False
            return True
        case _:
            if not tableRow.find('td', {data_stat: data_stat_value}):
                return pd.NA
            return tableRow.find('td', {data_stat: data_stat_value}).text

def fetch_week_info(data, table_row):
    data['date'].append(getValue(table_row, date, None, None))
    data['week'].append(getValue(table_row, week_num, Data_Stat_Type.INT, 0))
    data['age'].append(getValue(table_row, age, Data_Stat_Type.FLOAT, 0))
    data['team'].append(getValue(table_row, team, None, None))
    data['game_location'].append(getValue(table_row, game_location, None, None))
    data['opp'].append(getValue(table_row, opp_name, None, None))
    data['result'].append(getValue(table_row, result, Data_Stat_Type.RESULT, None))
    data['team_pts'].append(getValue(table_row, result, Data_Stat_Type.TEAM_PTS, None))
    data['opp_pts'].append(getValue(table_row, result, Data_Stat_Type.OPP_PTS, None))
    data['started'].append(getValue(table_row, is_starter, Data_Stat_Type.BOOLEAN, None))


def fetch_passing(data, table_row):
    data['cmp'].append(getValue(table_row, pass_cmp, Data_Stat_Type.INT, 0))
    data['att'].append(getValue(table_row, pass_att, Data_Stat_Type.INT, 0))
    data['cmp_perc'].append(getValue(table_row, pass_cmp_perc, Data_Stat_Type.FLOAT, 0))
    data['pass_yds'].append(getValue(table_row, pass_yds, Data_Stat_Type.INT, 0))
    data['pass_td'].append(getValue(table_row, pass_td, Data_Stat_Type.INT, 0))
    data['int'].append(getValue(table_row, pass_int, Data_Stat_Type.INT, 0))
    data['rating'].append(getValue(table_row, pass_rating, Data_Stat_Type.FLOAT, 0))
    data['sacked'].append(getValue(table_row, pass_sacked, Data_Stat_Type.INT, 0))

def fetch_rushing(data, table_row):
    data['rush_att'].append(getValue(table_row, rush_att, Data_Stat_Type.INT, 0))
    data['rush_yds'].append(getValue(table_row, rush_yds, Data_Stat_Type.INT, 0))
    data['rush_td'].append(getValue(table_row, rush_td, Data_Stat_Type.INT, 0))
    data['yds_per_att'].append(getValue(table_row, rush_yds_per_att, Data_Stat_Type.INT, 0))

def fetch_fumble_snaps(data, table_row):
    data['fumbles'].append(getValue(table_row, fumbles, Data_Stat_Type.INT, 0))
    data['snaps'].append(getValue(table_row, snap_count, Data_Stat_Type.INT, 0))
    data['snap_pct'].append(getValue(table_row, snap_count_perc, Data_Stat_Type.FLOAT, 0))

def fetch_receiving(data, table_row):
    data['tgt'].append(getValue(table_row, targets, Data_Stat_Type.INT, 0))
    data['rec'].append(getValue(table_row, rec, Data_Stat_Type.INT, 0))
    data['rec_yds'].append(getValue(table_row, rec_yds, Data_Stat_Type.INT, 0))
    data['rec_td'].append(getValue(table_row, rec_td, Data_Stat_Type.INT, 0))
    data['yds_per_rec'].append(getValue(table_row, yds_per_rec, Data_Stat_Type.FLOAT, 0))
    data['ctch_perc'].append(getValue(table_row, catch_perc, Data_Stat_Type.FLOAT, 0))
                # data['ctch_perc'].append(float(table_rows[i].find('td', {data_stat: catch_perc}).text.replace('%', '') or 0))
    data['yds_per_tgt'].append(getValue(table_row, yds_per_tgt, Data_Stat_Type.FLOAT, 0))

# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a QB game log
def qb_game_log(soup: BeautifulSoup) -> pd.DataFrame:

    information = [
        [ 'date', date, None ],
        [ 'week', week_num, Data_Stat_Type.INT],
        [ 'age', age, None ],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp_name, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS],
        [ 'started', is_starter, Data_Stat_Type.BOOLEAN ],
        [ 'cmp', pass_cmp, Data_Stat_Type.INT],
        [ 'att', pass_att, Data_Stat_Type.INT],
        [ 'cmp_perc', pass_cmp_perc, Data_Stat_Type.FLOAT],
        [ 'pass_yds', pass_yds, Data_Stat_Type.INT],
        [ 'pass_td', pass_td, Data_Stat_Type.INT],
        [ 'int', pass_int, Data_Stat_Type.INT],
        [ 'rating', pass_rating, Data_Stat_Type.FLOAT],
        [ 'sacked', pass_sacked, Data_Stat_Type.INT],
        [ 'rush_att', rush_att, Data_Stat_Type.INT],
        [ 'rush_yds', rush_yds, Data_Stat_Type.INT],
        [ 'rush_td', rush_td, Data_Stat_Type.INT],
        [ 'fumbles', fumbles, Data_Stat_Type.INT ],
        [ 'snaps', snap_count, Data_Stat_Type.FLOAT ],
        [ 'snap_pct', snap_count_perc, Data_Stat_Type.FLOAT ],
    ]

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
        'inactive': [],
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    to_skip = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if len(elements) < 5:
            ## a line saying a player was moved will have 4 elements, skip this row
            to_skip.append(i)
        if x in inactive_statuses:
            to_ignore.append(i)


    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i in to_skip:
            continue
        if i in to_ignore:
            data['inactive'].append(True)
        else:
            data['inactive'].append(False)



        try: 
            for column in information:
                data_frame_column = column[0]
                web_column = column[1]
                type_ = column[2]

                data[data_frame_column].append(getValue(table_rows[i], web_column, type_))

          
        except Exception as e:
            print(e)

    print(data)
    return pd.DataFrame(data=data)


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a WR/TE game log
def wr_game_log(soup: BeautifulSoup, season: int) -> pd.DataFrame:
    # Most relevant WR stats, in my opinion.
    # Could adjust if necessary (maybe figure out how to incorporate rushing stats?)

    information = [
        [ 'date', date, None ],
        [ 'week', week_num, Data_Stat_Type.INT],
        [ 'age', age, Data_Stat_Type.INT],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp_name, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS],
        [ 'started', is_starter, Data_Stat_Type.BOOLEAN ],
        [ 'rush_att', rush_att, Data_Stat_Type.INT],
        [ 'rush_yds', rush_yds, Data_Stat_Type.INT],
        [ 'yds_per_att', rush_yds_per_att, Data_Stat_Type.FLOAT ],
        [ 'rush_td', rush_td, Data_Stat_Type.INT],
        [ 'tgt', targets, Data_Stat_Type.FLOAT ],
        [ 'rec', rec, Data_Stat_Type.FLOAT ],
        [ 'rec_yds', rec_yds, Data_Stat_Type.FLOAT ],
        [ 'rec_td', rec_td, Data_Stat_Type.FLOAT ],
        [ 'yds_per_rec', yds_per_rec, Data_Stat_Type.FLOAT ],
        [ 'ctch_perc', catch_perc, Data_Stat_Type.FLOAT ],
        [ 'yds_per_tgt', yds_per_tgt, Data_Stat_Type.FLOAT ],
        [ 'fumbles', fumbles, Data_Stat_Type.FLOAT ],
        [ 'snaps', snap_count, Data_Stat_Type.FLOAT ],
        [ 'snap_pct', snap_count_perc, Data_Stat_Type.FLOAT ],
    ]

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
        'inactive': [],
    }

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
            data['inactive'].append(True)
        else:
            data['inactive'].append(False)


        for column in information:
            data_frame_column = column[0]
            web_column = column[1]
            type_ = column[2]

            data[data_frame_column].append(getValue(table_rows[i], web_column, type_))

    print(data)
    return pd.DataFrame(data=data)


def rb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant RB stats, in my opinion. Could adjust if necessary
    information = [
        [ 'date', date, None ],
        [ 'week', week_num, Data_Stat_Type.INT],
        [ 'age', age, Data_Stat_Type.INT],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp_name, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS],
        [ 'started', is_starter, Data_Stat_Type.BOOLEAN ],
        [ 'rush_att', rush_att, Data_Stat_Type.INT],
        [ 'rush_yds', rush_yds, Data_Stat_Type.INT],
        [ 'yds_per_att', rush_yds_per_att, Data_Stat_Type.FLOAT ],
        [ 'rush_td', rush_td, Data_Stat_Type.INT],
        [ 'tgt', targets, Data_Stat_Type.FLOAT ],
        [ 'rec', rec, Data_Stat_Type.FLOAT ],
        [ 'rec_yds', rec_yds, Data_Stat_Type.FLOAT ],
        [ 'rec_td', rec_td, Data_Stat_Type.FLOAT ],
        [ 'yds_per_rec', yds_per_rec, Data_Stat_Type.FLOAT ],
        [ 'ctch_perc', catch_perc, Data_Stat_Type.FLOAT ],
        [ 'yds_per_tgt', yds_per_tgt, Data_Stat_Type.FLOAT ],
        [ 'fumbles', fumbles, Data_Stat_Type.FLOAT ],
        [ 'snaps', snap_count, Data_Stat_Type.FLOAT ],
        [ 'snap_pct', snap_count_perc, Data_Stat_Type.FLOAT ],
    ]

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
        'inactive': [],
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x == 'COVID-19 List' or x is None:
            to_ignore.append(i)

    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i in to_ignore:
            data['inactive'].append(True)
        else:
            data['inactive'].append(False)

        # if i not in to_ignore:
        for column in information:
            data_frame_column = column[0]
            web_column = column[1]
            type_ = column[2]

            data[data_frame_column].append(getValue(table_rows[i], web_column, type_))
            
    return pd.DataFrame(data=data)

def te_game_log(soup: BeautifulSoup) -> pd.DataFrame:

    information = [
        [ 'date', date, None],
        [ 'week', week_num, Data_Stat_Type.INT],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp_name, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS ],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS ],
        [ 'started', is_starter, Data_Stat_Type.BOOLEAN ],
        [ 'rush_att', rush_att, Data_Stat_Type.INT ],
        [ 'rush_yds', rush_yds, Data_Stat_Type.INT ],
        [ 'yds_per_att', rush_yds_per_att, Data_Stat_Type.FLOAT ],
        [ 'rush_td', rush_td, Data_Stat_Type.INT ],
        [ 'tgt', targets, Data_Stat_Type.FLOAT ],
        [ 'rec', rec, Data_Stat_Type.FLOAT ],
        [ 'rec_yds', rec_yds, Data_Stat_Type.FLOAT ],
        [ 'rec_td', rec_td, Data_Stat_Type.FLOAT ],
        [ 'yds_per_rec', yds_per_rec, Data_Stat_Type.FLOAT ],
        [ 'ctch_perc', catch_perc, Data_Stat_Type.FLOAT ],
        [ 'yds_per_tgt', yds_per_tgt, Data_Stat_Type.FLOAT ],
        [ 'fumbles', fumbles, Data_Stat_Type.FLOAT ],
        [ 'snaps', snap_count, Data_Stat_Type.FLOAT ],
        [ 'snap_pct', snap_count_perc, Data_Stat_Type.FLOAT ],
    ]
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
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x == 'COVID-19 List' or x is None:
            to_ignore.append(i)

    # adding data to data dictionray
    for i in range(len(table_rows)):
        if i in to_ignore:
            data['inactive'].append(True)
        else:
            data['inactive'].append(False)

        if i not in to_ignore:
            for column in information:
                data_frame_column = column[0]
                web_column = column[1]
                type_ = column[2]

                data[data_frame_column].append(getValue(table_rows[i], web_column, type_))

    return pd.DataFrame(data=data)



def main():
    print(get_player_game_log('Jonathan Taylor', 'RB', 2021))


if __name__ == '__main__':
    main()

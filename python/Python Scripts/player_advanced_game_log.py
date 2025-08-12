import math
import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
from enums.data_stat_type import Data_Stat_Type

valid_positions = ['QB', 'RB', 'WR', 'TE']

# Sections of the table:
data_stat = 'data-stat'


# data_Stats
## week info
game_date = 'date'
week_num = 'team_game_num_season'
team = 'team_name_abbr'
game_location = 'game_location'
opp = 'opp_name_abbr'
opp_name = 'opp_name_abbr'
result = 'game_result'

## pass info
pass_cmp = 'pass_cmp'
pass_att = 'pass_att'
pass_first_down = 'pass_first_down'
pass_first_down_pct = 'pass_first_down_pct'
pass_target_yds = 'pass_target_yds'
pass_tgt_yds_per_att = 'pass_tgt_yds_per_att'
pass_air_yds = 'pass_air_yds'
pass_air_yds_per_cmp = 'pass_air_yds_per_cmp'
pass_air_yds_per_att = 'pass_air_yds_per_att'
pass_yac = 'pass_yac'
pass_yac_per_cmp = 'pass_yac_per_cmp'
pass_drops = 'pass_drops'
pass_drops_pct = 'pass_drop_pct'
pass_poor_throws = 'pass_poor_throws'
pass_poor_throw_pct = 'pass_poor_throw_pct'
pass_sacked = 'pass_sacked'
pass_blitzed = 'pass_blitzed'
pass_hurried = 'pass_hurried'
pass_hits = 'pass_hits'
pass_pressured = 'pass_pressured'
pass_pressured_pct = 'pass_pressured_pct'
rush_scrambles = 'rush_scrambles'
rush_scrambles_yds_per_att = 'rush_scrambles_yds_per_att'

### Not used:
pass_batted_passes = 'pass_batted_passes'
pass_throwaways = 'pass_throwaways'


# WR Stats:
targets = 'targets'
rec = 'rec'
rec_yds = 'rec_yds'
rec_first_down = 'rec_first_down'
rec_air_yds = 'rec_air_yds'
air_yards_per_rec = 'rec_air_yds_per_rec'
rec_yac = 'rec_yac'
rec_yac_per_rec = 'rec_yac_per_rec'
adot = 'rec_adot'
rec_broken_tackles = 'rec_broken_tackles'
rec_drops = 'rec_drops'
rec_drop_pct = 'rec_drop_pct'
rec_pass_rating = 'rec_pass_rating'

# RB Stats:
rush_yds_before_contact = 'rush_yds_before_contact'
rush_yds_bc_per_rush = 'rush_yds_bc_per_rush'
rush_yac = 'rush_yac'
rush_yac_per_rush = 'rush_yac_per_rush'
rush_broken_tackles = 'rush_broken_tackles'
rush_broken_tackles_per_rush = 'rush_broken_tackles_per_rush'

inactive_statuses = [
    'Inactive' ,
    'Did Not Play',
    'Injured Reserve',
    'COVID-19 List'
]


# function that returns a player's game log in a given season
# player: player's full name (e.g. Tom Brady)
# position: abbreviation (QB, RB, WR, TE only)
def get_player_advanced_game_log(player: str, position: str, season: int, player_url: str = None) -> pd.DataFrame:
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


    # make HTTP request and extract HTML
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
        if season >= int(seasons[0]) and season <= int(seasons[1]) and player in p.text and position in p.text:
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
    return requests.get(url + '%s/advanced' % season)

# helper function that takes a requests.Response object and returns a BeautifulSoup object
def get_soup(request):
    return BeautifulSoup(request.text, 'html.parser')

def getValue(tableRow, data_stat_value, type):
    try:
        tableRowValue = tableRow.find('td', {data_stat: data_stat_value})
        if not tableRowValue:
            match type:
                case Data_Stat_Type.INT:
                    return math.nan
                case Data_Stat_Type.FLOAT:
                    return math.nan
                case Data_Stat_Type.TEAM_PTS:
                    return math.nan
                case Data_Stat_Type.OPP_PTS:
                    return math.nan
                case _:
                    return pd.NA

        match type:
            case Data_Stat_Type.INT:
                return int(tableRowValue.text or 0)
            case Data_Stat_Type.FLOAT:
                return float(tableRowValue.text or 0)
            case Data_Stat_Type.RESULT:
                return tableRowValue.text.split(' ')[0]
            case Data_Stat_Type.TEAM_PTS:
                return int(tableRowValue.text.split(' ')[1].split('-')[0])
            case Data_Stat_Type.OPP_PTS:
                return int(tableRowValue.text.split(' ')[1].split('-')[1])
            case Data_Stat_Type.BOOLEAN:
                if not tableRowValue.text:
                    return False
                if tableRowValue.text in inactive_statuses:
                    return False
                return True
            case _:
                return tableRow.find('td', {data_stat: data_stat_value}).text
        
    except Exception as e:
        print(e)


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a QB game log
def qb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant QB stats, in my opinion. Could adjust if necessary
    information = [
        [ 'date', game_date, None ],
        [ 'week', week_num, Data_Stat_Type.INT],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp_name, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS],
        ['cmp', pass_cmp, Data_Stat_Type.INT ],
        ['att', pass_att, Data_Stat_Type.INT ],
        ['first_down', pass_first_down, Data_Stat_Type.INT ],
        ['first_down_pct', pass_first_down_pct, Data_Stat_Type.FLOAT ],
        ['pass_target_yds', pass_target_yds, Data_Stat_Type.FLOAT ],
        ['pass_target_yds_per_att', pass_tgt_yds_per_att, Data_Stat_Type.FLOAT ],
        ['pass_air_yds', pass_air_yds, Data_Stat_Type.INT ],
        ['pass_air_yds_per_cmp', pass_air_yds_per_cmp, Data_Stat_Type.FLOAT ],
        ['pass_air_yds_per_att', pass_air_yds_per_att, Data_Stat_Type.FLOAT ],
        ['pass_yac', pass_yac, Data_Stat_Type.FLOAT ],
        ['pass_yac_per_cmp', pass_yac_per_cmp, Data_Stat_Type.FLOAT ],
        ['pass_drops', pass_drops, Data_Stat_Type.INT ],
        ['pass_drop_pct', pass_drops_pct, Data_Stat_Type.FLOAT ],
        ['pass_poor_throws', pass_poor_throws, Data_Stat_Type.INT ],
        ['pass_poor_throws_pct', pass_poor_throw_pct, Data_Stat_Type.FLOAT ],
        ['pass_sacked', pass_sacked, Data_Stat_Type.INT ],
        ['pass_blitzed', pass_blitzed, Data_Stat_Type.INT ],
        ['pass_hurried', pass_hurried, Data_Stat_Type.INT ],
        ['pass_hits', pass_hits, Data_Stat_Type.INT ],
        ['pass_pressured', pass_pressured, Data_Stat_Type.INT ],
        ['pass_pressured_pct', pass_pressured_pct, Data_Stat_Type.FLOAT ],
        ['rush_scrambles', rush_scrambles, Data_Stat_Type.INT ],
        ['rush_scrambles_yds_per_att', rush_scrambles_yds_per_att, Data_Stat_Type.FLOAT ],
    ]

    data = {
        'date': [],
        'week': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'cmp': [],
        'att': [],
        'first_down': [],
        'first_down_pct': [],
        'pass_target_yds': [],
        'pass_target_yds_per_att': [],
        'pass_air_yds': [],
        'pass_air_yds_per_cmp': [],
        'pass_air_yds_per_att': [],
        'pass_yac': [],
        'pass_yac_per_cmp': [],
        'pass_drops': [],
        'pass_drop_pct': [],
        'pass_poor_throws': [],
        'pass_poor_throws_pct': [],
        'pass_sacked': [],
        'pass_blitzed': [],
        'pass_hurried': [],
        'pass_hits': [],
        'pass_pressured': [],
        'pass_pressured_pct': [],
        'rush_scrambles': [],
        'rush_scrambles_yds_per_att': [],
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
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x == 'COVID-19 List':
            to_ignore.append(i)

    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i in to_skip:
            continue

        if i not in to_ignore:
            for column in information:
                data_frame_column = column[0]
                web_column = column[1]
                type_ = column[2]

                data[data_frame_column].append(getValue(table_rows[i], web_column, type_))

        
    return pd.DataFrame(data=data)


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a WR/TE game log
def wr_game_log(soup: BeautifulSoup, season: int) -> pd.DataFrame:
    # Most relevant WR stats, in my opinion.
    # Could adjust if necessary (maybe figure out how to incorporate rushing stats?)

    information = [
        [ 'date', game_date, None ],
        [ 'week', week_num, Data_Stat_Type.INT],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS ],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS ],
        [ 'tgt', targets, Data_Stat_Type.INT ],
        [ 'rec', rec, Data_Stat_Type.INT ],
        [ 'rec_yds', rec_yds, Data_Stat_Type.INT ],
        [ 'rec_first_down', rec_first_down, Data_Stat_Type.INT ],
        [ 'air_yds', rec_air_yds, Data_Stat_Type.INT ],
        [ 'air_yds_per_rec', air_yards_per_rec, Data_Stat_Type.FLOAT ],
        [ 'yac', rec_yac, Data_Stat_Type.INT ],
        [ 'yac_per_rec', rec_yac_per_rec, Data_Stat_Type.FLOAT ],
        [ 'adot', adot, Data_Stat_Type.FLOAT ],
        [ 'broken_tackles', rec_broken_tackles, Data_Stat_Type.INT ],
        [ 'drops', rec_drops, Data_Stat_Type.INT ],
        [ 'drop_perc', rec_drop_pct, Data_Stat_Type.FLOAT ],
        [ 'rec_pass_rating', rec_pass_rating, Data_Stat_Type.FLOAT ]
    ]


    data = {
        'date': [],
        'week': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'tgt': [],
        'rec': [],
        'rec_yds': [],
        'rec_first_down': [],
        'air_yds': [],
        'air_yds_per_rec': [],
        'yac': [],
        'yac_per_rec': [],
        'adot': [],
        'broken_tackles': [],
        'drops': [],
        'drop_perc': [],
        'rec_pass_rating': []
    }  # type: dict

    table_rows = soup.find('table', id='adv_rushing_and_receiving').find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    to_skip = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if len(elements) < 5:
            ## a line saying a player was moved will have 4 elements, skip this row
            to_skip.append(i)
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve'  or x == 'COVID-19 List':
            to_ignore.append(i)

    # adding data to data dictionray
    for i in range(len(table_rows)):
        if i in to_skip:
            continue

        if i not in to_ignore:
            for column in information:
                data_frame_column = column[0]
                web_column = column[1]
                type_ = column[2]

                data[data_frame_column].append(getValue(table_rows[i], web_column, type_))
        # if i not in to_ignore:
        #     for column in information:
        #         data_frame_column = column[0]
        #         web_column = column[1]
        #         type_ = column[2]

        #         if not table_rows[i].find('td', {'data-stat': web_column}) or table_rows[i].find('td', {'data-stat': web_column}).text == '':
        #             if type_ == 'float' or type_ == 'int':
        #                 data[data_frame_column].append(int(0))
        #             else:
        #                 data[data_frame_column].append(None)
        #         else:
        #             if data_frame_column == 'team_pts':
        #                 data['team_pts'].append(
        #                     int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
        #                 )
        #             elif data_frame_column == 'opp_pts':
        #                 data['opp_pts'].append(
        #                     int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
        #                 )
        #             else:
        #                 if type_ == 'float':
        #                     data[data_frame_column].append(float(table_rows[i].find('td', {'data-stat': web_column}).text) or 0)
        #                 elif type_ == 'int':
        #                     data[data_frame_column].append(int(table_rows[i].find('td', {'data-stat': web_column}).text) or 0)
        #                 else:
        #                     data[data_frame_column].append(table_rows[i].find('td', {'data-stat': web_column}).text)
                
            # data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            # data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            # data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            # data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            # data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            # data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            # data['team_pts'].append(
            #     int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            # )
            # data['opp_pts'].append(
            #     int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            # )
            
            
            # if not table_rows[i].find('td', {'data-stat': 'targets'}):
            #     data['tgt'].append(0)
            #     data['rec'].append(0)
            #     data['rec_yds'].append(0)
            #     data['rec_td'].append(0)
            #     data['rec_first_down'].append(0)
            #     data['air_yds'].append(0)
            #     data['air_yds_per_rec'].append(0)
            #     data['yac'].append(0)
            #     data['yac_per_rec'].append(0)
            #     data['adot'].append(0)
            #     data['broken_tackles'].append(0)
            #     data['drops'].append(0)
            #     data['drop_perc'].append(0)
            #     data['rec_pass_rating'].append(0)
            # else:
            #     data['tgt'].append(int(table_rows[i].find('td', {'data-stat': 'targets'}).text) or 0)
            #     data['rec'].append(int(table_rows[i].find('td', {'data-stat': 'rec'}).text) or 0)
            #     data['rec_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yds'}).text) or 0)
            #     data['rec_td'].append(int(table_rows[i].find('td', {'data-stat': 'rec_td'}).text) or 0)

            #     if not table_rows[i].find('td', {'data-stat': 'rec_first_down'}) or table_rows[i].find('td', {'data-stat': 'rec_first_down'}).text == '':
            #         data['rec_first_down'].append(int(0))
            #     else:
            #         data['rec_first_down'].append(int(table_rows[i].find('td', {'data-stat': 'rec_first_down'}).text) or 0)

            #     data['air_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_air_yds'}).text) or 0)

            #     if not table_rows[i].find('td', {'data-stat': 'air_yards_per_rec'}) or table_rows[i].find('td', {'data-stat': 'air_yards_per_rec'}).text == '':
            #         data['air_yds_per_rec'].append(int(0))
            #     else:
            #         data['air_yds_per_rec'].append(float(table_rows[i].find('td', {'data-stat': 'rec_air_yds_per_rec'}).text) or 0)

            #     data['yac'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yac'}).text) or 0)

            #     if not table_rows[i].find('td', {'data-stat': 'rec_yac_per_rec'}) or table_rows[i].find('td', {'data-stat': 'rec_yac_per_rec'}).text == '':
            #         data['yac_per_rec'].append(int(0))
            #     else:
            #         data['yac_per_rec'].append(float(table_rows[i].find('td', {'data-stat': 'rec_yac_per_rec'}).text) or 0)

            #     if not table_rows[i].find('td', {'data-stat': 'adot'}) or table_rows[i].find('td', {'data-stat': 'adot'}).text == '':
            #         data['adot'].append(int(0))
            #     else:
            #         data['adot'].append(float(table_rows[i].find('td', {'data-stat': 'rec_adot'}).text) or 0)

            #     data['broken_tackles'].append(int(table_rows[i].find('td', {'data-stat': 'rec_broken_tackles'}).text) or 0)
            #     data['drops'].append(int(table_rows[i].find('td', {'data-stat': 'rec_drops'}).text) or 0)
            #     data['drop_perc'].append(float(table_rows[i].find('td', {'data-stat': 'rec_drop_pct'}).text) or 0)

            #     if not table_rows[i].find('td', {'data-stat': 'rec_pass_rating'}) or table_rows[i].find('td', {'data-stat': 'rec_pass_rating'}).text == '':
            #         data['rec_pass_rating'].append(int(0))
            #     else:
            #         data['rec_pass_rating'].append(float(table_rows[i].find('td', {'data-stat': 'rec_pass_rating'}).text) or 0)

    return pd.DataFrame(data=data)


def rb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant RB stats, in my opinion. Could adjust if necessary

    information = [
        [ 'date', game_date, None ],
        [ 'week', week_num, Data_Stat_Type.INT ],
        [ 'team', team, None ],
        [ 'game_location', game_location, None ],
        [ 'opp', opp_name, None ],
        [ 'result', result, Data_Stat_Type.RESULT ],
        [ 'team_pts', result, Data_Stat_Type.TEAM_PTS ],
        [ 'opp_pts', result, Data_Stat_Type.OPP_PTS ],
        [ 'ybc', rush_yds_before_contact, Data_Stat_Type.INT ],
        [ 'ybc_per_att', rush_yds_bc_per_rush, Data_Stat_Type.FLOAT ],
        [ 'yac', rush_yac, Data_Stat_Type.INT ],
        [ 'yac_per_att', rush_yac_per_rush, Data_Stat_Type.FLOAT ],
        [ 'broken_tkl', rush_broken_tackles, Data_Stat_Type.INT ],
        [ 'att_per_broken_tkl', rush_broken_tackles_per_rush, Data_Stat_Type.FLOAT ],
    ]

    data = {
        'date': [],
        'week': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'ybc': [],
        'ybc_per_att': [],
        'yac': [],
        'yac_per_att': [],
        'broken_tkl': [],
        'att_per_broken_tkl': [],
    }  # type: dict

    table_rows = soup.find('table', id='adv_rushing_and_receiving').find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    to_skip = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if len(elements) < 5:
            ## a line saying a player was moved will have 4 elements, skip this row
            to_skip.append(i)
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve'  or x == 'COVID-19 List':
            to_ignore.append(i)

    # adding data to data dictionray
    for i in range(len(table_rows)):
        if i in to_skip:
            continue

        if i not in to_ignore:
            for column in information:
                data_frame_column = column[0]
                web_column = column[1]
                type_ = column[2]

                data[data_frame_column].append(getValue(table_rows[i], web_column, type_))

    # # adding data to data dictionray
    # for i in range(len(table_rows)):
    #     if i not in to_ignore:
    #         for column in information:
    #             data_frame_column = column[0]
    #             web_column = column[1]
    #             type_ = column[2]

    #             if not table_rows[i].find('td', {'data-stat': web_column}) or table_rows[i].find('td', {'data-stat': web_column}).text == '':
    #                 if type_ == 'float' or type_ == 'int':
    #                     data[data_frame_column].append(int(0))
    #                 else:
    #                     data[data_frame_column].append(None)
    #             else:
    #                 if data_frame_column == 'team_pts':
    #                     data['team_pts'].append(
    #                         int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
    #                     )
    #                 elif data_frame_column == 'opp_pts':
    #                     data['opp_pts'].append(
    #                         int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
    #                     )
    #                 else:
    #                     if type_ == 'float':
    #                         data[data_frame_column].append(float(table_rows[i].find('td', {'data-stat': web_column}).text) or 0)
    #                     elif type_ == 'int':
    #                         data[data_frame_column].append(int(table_rows[i].find('td', {'data-stat': web_column}).text) or 0)
    #                     else:
    #                         data[data_frame_column].append(table_rows[i].find('td', {'data-stat': web_column}).text) 

    # data = {
    #     'date': [],
    #     'week': [],
    #     'team': [],
    #     'game_location': [],
    #     'opp': [],
    #     'result': [],
    #     'team_pts': [],
    #     'opp_pts': [],
    #     'rush_att': [],
    #     'rush_yds': [],
    #     'rush_td': [],
    #     'tgt': [],
    #     'rec_yds': [],
    #     'rec_td': [],
    # }  # type: dict

    # table_rows = soup.find('tbody').find_all('tr')

    # # ignore inactive or DNP games
    # to_ignore = []
    # for i in range(len(table_rows)):
    #     elements = table_rows[i].find_all('td')
    #     x = elements[len(elements) - 1].text
    #     if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve' or x == 'COVID-19 List':
    #         to_ignore.append(i)

    # # adding data to data dictionary
    # for i in range(len(table_rows)):
    #     if i not in to_ignore:
    #         data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
    #         data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
    #         data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
    #         data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
    #         data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
    #         data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
    #         data['team_pts'].append(
    #             int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
    #         )
    #         data['opp_pts'].append(
    #             int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
    #         )
    #         data['rush_att'].append(int(table_rows[i].find('td', {'data-stat': 'rush_att'}).text))
    #         data['rush_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rush_yds'}).text))
    #         data['rush_td'].append(int(table_rows[i].find('td', {'data-stat': 'rush_td'}).text))
    #         data['tgt'].append(int(table_rows[i].find('td', {'data-stat': 'targets'}).text))
    #         data['rec_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yds'}).text))
    #         data['rec_td'].append(int(table_rows[i].find('td', {'data-stat': 'rec_td'}).text))

    return pd.DataFrame(data=data)

def find_attribute(object, attribute: str):
    if hasattr(object, attribute):
        return object.text.replace('%', '')
    else:
        return None 

def main():
    print(get_player_advanced_game_log('Jonathan Taylor', 'RB', 2021))


if __name__ == '__main__':
    main()

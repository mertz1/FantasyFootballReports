import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests

valid_positions = ['QB', 'RB', 'WR', 'TE']


# function that returns a player's game log in a given season
# player: player's full name (e.g. Tom Brady)
# position: abbreviation (QB, RB, WR, TE only)
def get_player_advanced_game_log(player: str, position: str, season: int) -> pd.DataFrame:
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

    # make request to find proper href
    r1 = make_request_list(player, position, season)
    player_list = get_soup(r1)

    # find href
    href = get_href(player, position, season, player_list)

    # make HTTP request and extract HTML
    r2 = make_request_player(href, season)

    # parse HTML using BeautifulSoup
    game_log = get_soup(r2)

    # generating the appropriate game log format according to position
    if 'QB' in position:
        return qb_game_log(game_log)
    elif 'WR' in position or 'TE' in position:
        return wr_game_log(game_log, season)
    elif 'RB' in position:
        return rb_game_log(game_log)


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


# helper function that makes a HTTP request for a given player's game log
def make_request_player(href: str, season: int):
    url = 'https://www.pro-football-reference.com%s/gamelog/%s/advanced' % (href, season)
    return requests.get(url)


# helper function that takes a requests.Response object and returns a BeautifulSoup object
def get_soup(request):
    return BeautifulSoup(request.text, 'html.parser')


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a QB game log
def qb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant QB stats, in my opinion. Could adjust if necessary
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
        'pass_yds': [],
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
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve':
            to_ignore.append(i)

    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i not in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
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
            data['cmp'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_cmp'}),'text') or 0))
            data['att'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_att'}), 'text') or 0))
            data['pass_yds'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_yds'}), 'text') or 0))
            data['first_down'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'first_down'}), 'text') or 0))
            data['first_down_pct'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'first_down_pct'}), 'text') or 0))
            data['pass_target_yds'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_target_yds'}), 'text') or 0))
            data['pass_target_yds_per_att'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_target_yds_per_att'}), 'text') or 0))
            data['pass_air_yds'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_air_yds'}), 'text') or 0))
            data['pass_air_yds_per_cmp'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_air_yds_per_cmp'}), 'text') or 0))
            data['pass_air_yds_per_att'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_air_yds_per_att'}), 'text') or 0))
            data['pass_yac'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_yac'}), 'text') or 0))
            data['pass_yac_per_cmp'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_yac_per_cmp'}), 'text') or 0))
            data['pass_drops'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_drops'}), 'text') or 0))
            data['pass_drop_pct'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_drop_pct'}), 'text') or 0))
            data['pass_poor_throws'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_poor_throws'}), 'text') or 0))
            data['pass_poor_throws_pct'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_poor_throws_pct'}), 'text') or 0))
            data['pass_sacked'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_sacked'}), 'text') or 0))
            data['pass_blitzed'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_blitzed'}), 'text') or 0))
            data['pass_hurried'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_hurried'}), 'text') or 0))
            data['pass_hits'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_hits'}), 'text') or 0))
            data['pass_pressured'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_pressured'}), 'text') or 0))
            data['pass_pressured_pct'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'pass_pressured_pct'}), 'text') or 0))
            data['rush_scrambles'].append(int(find_attribute(table_rows[i].find('td', {'data-stat': 'rush_scrambles'}), 'text') or 0))
            data['rush_scrambles_yds_per_att'].append(float(find_attribute(table_rows[i].find('td', {'data-stat': 'rush_scrambles_yds_per_att'}), 'text') or 0))

    return pd.DataFrame(data=data)


# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing a WR/TE game log
def wr_game_log(soup: BeautifulSoup, season: int) -> pd.DataFrame:
    # Most relevant WR stats, in my opinion.
    # Could adjust if necessary (maybe figure out how to incorporate rushing stats?)

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
        'rec_td': [],
        'snap_pct': [],
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve':
            to_ignore.append(i)

    # adding data to data dictionray
    for i in range(len(table_rows)):
        if i not in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
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
            data['tgt'].append(int(table_rows[i].find('td', {'data-stat': 'targets'}).text))
            data['rec'].append(int(table_rows[i].find('td', {'data-stat': 'rec'}).text))
            data['rec_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yds'}).text))
            data['rec_td'].append(int(table_rows[i].find('td', {'data-stat': 'rec_td'}).text))
            if season > 2011:
                data['snap_pct'].append(float(int(table_rows[i].find('td', {'data-stat': 'off_pct'}).text[:-1]) / 100))
            else:
                data['snap_pct'].append('Not Available')

    return pd.DataFrame(data=data)


def rb_game_log(soup: BeautifulSoup) -> pd.DataFrame:
    # Most relevant RB stats, in my opinion. Could adjust if necessary
    data = {
        'date': [],
        'week': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'rush_att': [],
        'rush_yds': [],
        'rush_td': [],
        'tgt': [],
        'rec_yds': [],
        'rec_td': [],
    }  # type: dict

    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve':
            to_ignore.append(i)

    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i not in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
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
            data['rush_att'].append(int(table_rows[i].find('td', {'data-stat': 'rush_att'}).text))
            data['rush_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rush_yds'}).text))
            data['rush_td'].append(int(table_rows[i].find('td', {'data-stat': 'rush_td'}).text))
            data['tgt'].append(int(table_rows[i].find('td', {'data-stat': 'targets'}).text))
            data['rec_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rec_yds'}).text))
            data['rec_td'].append(int(table_rows[i].find('td', {'data-stat': 'rec_td'}).text))

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

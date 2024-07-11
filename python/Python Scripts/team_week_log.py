import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests

valid_teams = ['DET','DEN','CHI','HOU','NYJ','IND','LVR','LAR','LAC','SFO','ATL','CLE','PIT','BAL','DAL','GNB','BUF','TEN','WAS','ARI','NYG','NWE','TAM','CIN','MIN','NOR','JAX','CAR','SEA','PHI','KAN','MIA']
lower_teams = [x.lower() for x in valid_teams]

season = 2022
href = 'https://www.pro-football-reference.com/teams/%s/%s.htm'

def get_all_team_logs():
    for team in lower_teams:
        # Http request:
        url = href % (team, season)
        html_request = requests.get(url)

        html = BeautifulSoup(html_request.text, 'html.parser')

        # Find the Game Results
        games_table = html.find('table', attrs={"id": "games"}).find('tbody')
        games_list = games_table.findAll('tr')
        print(games_list)

        # Build data frame expected
        data = {
            'week_num',
            'game_day_of_week',
            'game_date',
            'game_time',
            'boxscore_word',
            'game_outcome',
            'overtime',
            'team_record',
            'game_location',
            'opp',
            'pts_off',
            'pts_def',
            'first_down_off',
            'yards_off',
            'pass_yds_off',
            'rush_yds_off',
            'to_off',
            'first_down_def',
            'yards_def',
            'pass_yds_def',
            'rush_yds_def',
            'to_def',
            'exp_pts_off',
            'exp_pts_def',
            'exp_pts_st'
        }

        # ignore inactive or DNP games
        to_ignore = []
        exit_inc = 999

        for i in range(len(games_list)):
            elements = games_list[i].find_all('td')
            x = elements[len(elements) - 1].text
            if x == 'Bye Week':
                to_ignore.append(i)
            if x == 'Playoffs':
                exit_inc = i

        for i in range(len(games_list)):
            if i == exit_inc:
                break
            if i not in to_ignore:
                try: 




        # Build ignore_week_iterator:
            # Ignore Bye Week
            # Ignore Playoffs

        # Add valid weeks to dataframe

        # return




get_all_team_logs()





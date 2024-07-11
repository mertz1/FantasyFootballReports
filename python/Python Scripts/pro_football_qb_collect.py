##https://www.footballdb.com/players/justin-jefferson-jeffeju01/gamelogs/2022
import time
from player_game_log import get_player_game_log as pgl
import psycopg2
import requests
import pandas as pd
import sys
from sqlalchemy import create_engine
import numpy as np
import re


def update_sql_isloaded(cursor, name):
    statement = 'UPDATE profootball_qb_loaded SET isloaded = true WHERE name = \'' + re.sub("'", "''", name) + '\''

    cursor.execute(statement)


def update_player_url(cursor, name, url):
    statement = 'UPDATE footballdb_players SET url = \'' + url + '\' WHERE \"Name\" = \'' + re.sub("'", "''", name) + '\''

    cursor.execute(statement)

#game_log = pgl.get_player_game_log(player = 'Josh Allen', position = 'QB', season = 2022)
#print(game_log)

# url = 'https://www.footballdb.com/players/justin-jefferson-jeffeju01/gamelogs/2022'
# html = requests.get(url).content
# df_list = pd.read_html(html)

# print(df_list)

#game_log = pgl.get_player_game_log(player = 'Justin Fields', position = 'QB', season = 2022)

season = 2023
position = 'QB'


###
# Error File:
#sys.stdout = open(position + "_" + str(season) + "_output.txt", 'a')

engine = create_engine('postgresql+psycopg2://postgres:password\
@localhost:5432/fantasyfootball')

conn = psycopg2.connect(database="fantasyfootball",
                        host="localhost",
                        user="postgres",
                        password="password",
                        port="5432")

cursor = conn.cursor()

cursor.execute("SELECT fdp.* FROM footballdb_players fdp " +
               " join qb_weekly qw on qw.name = fdp.\"Name\" and fdp.\"Position\" = '" + position + "'"
               " join profootball_qb_loaded fdpl on fdpl.name = fdp.\"profootball_name\""
               " where qw.year = " + str(season) + 
               " and fdpl.\"year\" = " + str(season) + " and (isloaded = false or isloaded is null) "
               " group by fdp.\"Id\", fdp.\"Name\" having count(*) > 0;")

#print(cursor.fetchone())

all_players = cursor.fetchall()


for player in all_players:
    try:
        player_name = player[4]
        player_url = player[6]
        sys.stdout.write('loading ' + player_name + '\n')


        qb_is_loaded = pd.read_sql('select * from profootball_qb_loaded where name = \'' + re.sub("'", "''", player_name) + '\' and year = ' + str(season) + ';', con=engine)
        if not qb_is_loaded.empty and qb_is_loaded.loc[0,'isloaded']:
            continue

        # if already exists:
        ### TODO!!!! IF DOING AN ACTIVE SEASON, DON'T JUST SKIP IF DATA EXISTS!
        existing_values = pd.read_sql('select * from profootball_qb where name = \'' + re.sub("'", "''", player_name) + '\' and year = ' + str(season) + ';', con=engine)
        print(existing_values)

        ## Comment this out if doing current season
        '''
        if not existing_values.empty:  # 4 is the profootball name
            qb_is_loaded['isloaded'] = True
            #qb_is_loaded.to_sql('profootball_qb_loaded', engine, if_exists='replace', index=False)
            update_sql_isloaded(cursor, player_name)
            conn.commit()
            continue
        '''
        # END COMMENT IF DOING CURRENT SEASON

        game_log, url = pgl(player = player_name, position = 'QB', season = season, player_url= player_url)
        
        if url:
            update_player_url(cursor, player_name, url)

        game_log['name'] = player_name
        game_log['year'] = season
        game_log.set_index(['name', 'date'])
        print(game_log)


        existing_values.set_index(['name', 'date'])


        dfnew  = pd.merge(game_log, existing_values, how='left', indicator='Exist')
        dfnew  = dfnew .loc[dfnew ['Exist'] != 'both']
        dfnew.drop(columns=['Exist'], inplace=True) 
        print(dfnew)

        #mixed_data = pd.concat([game_log, existing_values], axis=0, join='left')
        #print(mixed_data)


        #duplicates = set(existing_values.index).intersection(game_log.index)
        #non_duplicates = game_log.merge(existing_values, indicator=True, how='outer', on=['name', 'date']).query('_merge=="left_only"').drop('_merge', axis=1)
        #print(non_duplicates)
        # add duplicate rows to game_log
        #game_log = game_log.append(duplicates)
        # add duplicates column
        #game_log['Duplicated'] = game_log.duplicated(keep=False) # keep=False marks the duplicated row with a True
        #game_log = game_log[~game_log['Duplicated']] # selects only rows which are not duplicated
        #del game_log['Duplicated'] # delete the indicator column

        #game_log = game_log.drop(duplicates, axis=0)
        #print(game_log)

        dfnew.to_sql('profootball_qb', engine, if_exists='append', index=False)
        sys.stdout.write(player_name + " loaded" + '\n')
        
        # update qb_is_loaded table
#        qb_is_loaded['isloaded'] = True
        update_sql_isloaded(cursor, player_name)
        conn.commit()
        time.sleep(2)
    except Exception as e:
        print(e)
        sys.stdout.write("ERROR:" + player_name + " does not exist for QBs" + '\n')
        raise

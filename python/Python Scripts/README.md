Database Connection:
- localhost:5432
- password

Schema:
- database: "fantasyfootball"
- schema: "public"
- tables:





Upload Data Steps:
- For each position, for each week:
  - open up existing data sheet from "C:\Users\micha\Documents\Fantasy Football\footballdb data" to get the proper headers
  - add data from [here](https://www.footballdb.com/fantasy-football/index.html?pos=QB&yr=2023&wk=18&key=48ca46aa7d721af4d58dccc0c249a1c4) to excel file

- Import Data (Using DBeaver, not PGAdmin):
  - load excel file into "footballdb_weekly_{position}"
  
  - Run "update_all_tables(year, month, month)
    - updates all the tables given the time frame
      - calls "upd_{pos}_weekly"
        - upades the position weekly table with player_id and other metadata
      - calls "prep_profootball_{pos}_loaded"
        - marks the players that need to be loaded for that time frame from profootballdb scrape
        
- run python scripts to scrape data for:
  - WR
  - RB
  - QB
  - QB_Advanced

  - if a player DNE for that position, can mark the "ignoreLoad" in the players table

- run the post upload scripts
  - post_qb_autoload
  - post_wr_autoload
  - post_rb_autoload

  
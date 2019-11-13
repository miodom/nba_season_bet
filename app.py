from flask import Flask, render_template
import pandas as pd
from nba_api.stats.endpoints import leaguestandings, leaguegamefinder, playernextngames

app = Flask(__name__)

# ids of players playing in given teams (here butler, derozan, oladipo and griffin)
team_ids = {'heat': {'id': 1610612748, 'abbreviation': 'MIA', 'player_id': 202710},
            'spurs': {'id': 1610612759, 'abbreviation': 'SAS', 'player_id': 201942},
            'pacers': {'id': 1610612754, 'abbreviation': 'IND', 'player_id': 203506},
            'pistons': {'id': 1610612765, 'abbreviation': 'DET', 'player_id': 201933}}


def get_teams_stats():
    team_stats = leaguestandings.LeagueStandings(timeout=60).get_dict()['resultSets'][0]

    team_stats_list = team_stats['rowSet']
    headers = team_stats['headers']

    team_stats_dict = {}

    for elem in team_stats_list:
        team = elem[4]
        if team == 'Heat':
            team_stats_dict['heat'] = dict(zip(headers, elem))
        elif team == 'Spurs':
            team_stats_dict['spurs'] = dict(zip(headers, elem))
        elif team == 'Pacers':
            team_stats_dict['pacers'] = dict(zip(headers, elem))
        elif team == 'Pistons':
            team_stats_dict['pistons'] = dict(zip(headers, elem))

    return team_stats_dict


def get_team_prev_games(team, n=5):
    gamelog = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_ids[team]['id'],
                                                season_nullable='2019-20', timeout=60).get_dict()['resultSets'][0]

    games = gamelog['rowSet']
    headers = gamelog['headers']

    last_games = []

    for game in games[:n]:
        game_dict = dict(zip(headers, game))
        score = '{}-{}'.format(game_dict['PTS'], int(game_dict['PTS'] - game_dict['PLUS_MINUS']))
        last_games.append('{} | {} | {} ({})'.format(game_dict['GAME_DATE'],
                                                     game_dict['MATCHUP'],
                                                     score,
                                                     game_dict['WL']))

    return last_games


def get_previous_games(n=5):
    gamelog = leaguegamefinder.LeagueGameFinder(season_nullable='2019-20', timeout=60).get_dict()['resultSets'][0]

    games = gamelog['rowSet']
    headers = gamelog['headers']

    df = pd.DataFrame(games, columns=headers)
    df = df[['TEAM_ID', 'GAME_DATE', 'MATCHUP', 'PTS', 'PLUS_MINUS', 'WL']]

    previous_games = {}

    for team in team_ids.keys():
        team_previous_games = []
        team_last_games_df = df[df['TEAM_ID'] == team_ids[team]['id']][:n]
        team_last_games_df['OPP_PTS'] = team_last_games_df['PTS'] - team_last_games_df['PLUS_MINUS']
        team_last_games_df = team_last_games_df.astype({'OPP_PTS': int})
        for index, row in team_last_games_df.iterrows():
            team_previous_games.append('{} | {} | {}-{} ({})'.format(row['GAME_DATE'],
                                                                     row['MATCHUP'],
                                                                     row['PTS'],
                                                                     row['OPP_PTS'],
                                                                     row['WL']))
        previous_games[team] = team_previous_games

    return previous_games


def get_players_next_games(team, n=5):
    player_next_games = playernextngames.PlayerNextNGames(player_id=team_ids[team]['player_id'],
                                                          number_of_games=n, timeout=60).get_dict()['resultSets'][0]

    games = player_next_games['rowSet']
    headers = player_next_games['headers']

    next_games = []

    for game in games:
        game_dict = dict(zip(headers, game))
        if game_dict['HOME_TEAM_ABBREVIATION'] == team_ids[team]['abbreviation']:
            matchup = '{} vs. {}'.format(game_dict['HOME_TEAM_ABBREVIATION'], game_dict['VISITOR_TEAM_ABBREVIATION'])
            opponent_record = game_dict['VISITOR_WL']
        else:
            matchup = '{} @ {}'.format(game_dict['VISITOR_TEAM_ABBREVIATION'], game_dict['HOME_TEAM_ABBREVIATION'])
            opponent_record = game_dict['HOME_WL']

        next_games.append('{} {} | {} ({})'.format(game_dict['GAME_DATE'], game_dict['GAME_TIME'], matchup, opponent_record))

    return next_games


@app.route('/')
def main_page():
    from time import perf_counter
    start = perf_counter()
    team_stats = get_teams_stats()
    prev_games_df = get_previous_games()

    result_dict = {team: {'record': team_stats[team]['Record'],
                          'win_percentage': round(team_stats[team]['WinPCT'] * 100, 1),
                          'games_played': team_stats[team]['WINS'] + team_stats[team]['LOSSES'],
                          'games_left': 82 - (team_stats[team]['WINS'] + team_stats[team]['LOSSES']),
                          'last_games': prev_games_df[team],
                          'next_games': get_players_next_games(team, n=5)}
                   for team in ['heat', 'spurs', 'pacers', 'pistons']}
    end = perf_counter()
    print(end - start)
    return render_template('/template.html', data=result_dict)


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
from flask import Flask, render_template
from nba_api.stats.endpoints import leaguestandings, leaguegamefinder, playernextngames

app = Flask(__name__)

team_ids = {'heat': 1610612748, 'spurs': 1610612759, 'pacers': 1610612754, 'pistons': 1610612765}
team_abr = {'heat': 'MIA', 'spurs': 'SAS', 'pacers': 'IND', 'pistons': 'DET'}

# ids of players playing in given teams (here butler, derozan, oladipo and griffin)
player_ids = {'heat': 202710, 'spurs': 201942, 'pacers': 203506, 'pistons': 201933}


def get_teams_stats():
    team_stats = leaguestandings.LeagueStandings().get_dict()['resultSets'][0]

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
    gamelog = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_ids[team],
                                                season_nullable='2019-20').get_dict()['resultSets'][0]

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


def get_players_next_games(team, n=5):
    player_next_games = playernextngames.PlayerNextNGames(player_id=player_ids[team],
                                                          number_of_games=n).get_dict()['resultSets'][0]

    games = player_next_games['rowSet']
    headers = player_next_games['headers']

    next_games = []

    for game in games:
        game_dict = dict(zip(headers, game))
        if game_dict['HOME_TEAM_ABBREVIATION'] == team_abr[team]:
            matchup = '{} vs. {}'.format(game_dict['HOME_TEAM_ABBREVIATION'], game_dict['VISITOR_TEAM_ABBREVIATION'])
            opponent_record = game_dict['VISITOR_WL']
        else:
            matchup = '{} @ {}'.format(game_dict['VISITOR_TEAM_ABBREVIATION'], game_dict['HOME_TEAM_ABBREVIATION'])
            opponent_record = game_dict['HOME_WL']

        next_games.append('{} {} | {} ({})'.format(game_dict['GAME_DATE'], game_dict['GAME_TIME'], matchup, opponent_record))

    return next_games


@app.route('/')
def main_page():
    team_stats = get_teams_stats()
    result_dict = {team: {'record': team_stats[team]['Record'],
                          'win_percentage': round(team_stats[team]['WinPCT'] * 100, 1),
                          'games_played': team_stats[team]['WINS'] + team_stats[team]['LOSSES'],
                          'games_left': 82 - (team_stats[team]['WINS'] + team_stats[team]['LOSSES']),
                          'last_games': get_team_prev_games(team, n=5),
                          'next_games': get_players_next_games(team, n=5)}
                   for team in ['heat', 'spurs', 'pacers', 'pistons']}
    return render_template('/template.html', data=result_dict)

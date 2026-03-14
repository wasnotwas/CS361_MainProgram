import json
from datetime import datetime, timezone

def get_match_details(game_id):
    
    # gather game data for game
    with open('data/games.json') as f:
        games = json.load(f)

    # gather teams data for game
    with open('data/teams.json') as f:
        teams = {team['id']: team for team in json.load(f)}

    # gather venue data for game
    with open('data/venues.json') as f:
        venues = {venue['id']: venue for venue in json.load(f)}

    # gather data for specific game with game_id for game data
    with open('data/game_results.json') as f:
        results = {result['game_id']: result for result in json.load(f)}

    # gather data for specific game with game_id for game lineup
    with open('data/game_lineup.json') as f:
        lineups = json.load(f)['game_lineups']

    # gather data for specific game with game_id for players
    with open('data/player.json') as f:
        players = {player['player_id']: player for player in json.load(f)['players']}

    # gather data for specific game with game_id
    game = next((g for g in games if g['id'] == str(game_id)), None)
    if not game:
        return None  # Game not found

    # get team and venue name
    home_team = teams.get(game['home_team_id'], {})
    away_team = teams.get(game['away_team_id'], {})
    venue = venues.get(game['venue_id'], {})

    # get gametime and format
    utc_time = datetime.fromisoformat(game['datetime']).replace(tzinfo=timezone.utc)
    formatted_datetime = utc_time.strftime('%A, %B %d, %Y at %I:%M %p')

    # get score
    result = results.get(str(game_id))
    score = None
    if result:
        score = {
            'home': result['final_score']['home'],
            'away': result['final_score']['away'],
            'winner_id': result.get('winning_team_id')
        }

    # build lineups with player names, jerseys and positions
    def build_lineup(team_id):
        team_lineup = next(
            (l for l in lineups if l['game_id'] == int(game_id) and l['team_id'] == int(team_id)),
            None
        )
        if not team_lineup:
            return None

        player_list = []
        for entry in sorted(team_lineup['lineup'], key=lambda x: x['field_position']):
            player = players.get(entry['player_id'])
            if player:
                player_list.append({
                    'name': f"{player['first_name']} {player['last_name'] or ''}".strip(),
                    'jersey_number': player['jersey_number'],
                    'position': player['primary_position'],
                    'field_position': entry['field_position']
                })

        return {
            'formation': team_lineup['formation'],
            'players': player_list
        }

    # put all data in one dictionary
    match_details = {
        'game_id': game['id'],
        'game_label': game.get('game_label'),
        'status': game.get('status'),
        'datetime': formatted_datetime,
        'venue': venue.get('name'),
        'venue_city': venue.get('city'),
        'venue_country': venue.get('country'),
        'venue_latitude': venue.get('latitude'),
        'venue_longitude': venue.get('longitude'),
        'home_team': {
            'id': game['home_team_id'],
            'name': home_team.get('name'),
            'lineup': build_lineup(game['home_team_id'])
        },
        'away_team': {
            'id': game['away_team_id'],
            'name': away_team.get('name'),
            'lineup': build_lineup(game['away_team_id'])
        },
        'score': score
    }

    return match_details
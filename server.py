from flask import Flask, request, render_template
import json
from datetime import datetime, timezone

app = Flask(__name__)

# function to read in the data for all teams
def read_in_teams():
    with open('data/teams.json') as f:
        teams = json.load(f)
        return teams

#function to write the updated data for all teams
def write_to_teams_data(new_team_data):
    with open('data/teams.json', 'w') as file:
        json.dump(new_team_data, file)

# function to read in the data for all venues
def read_in_venues():
    with open('data/venues.json') as f:
        venues = json.load(f)
        return venues

#function to write the updated data for all venues
def write_to_venues_data(new_venue_data):
    with open('data/venues.json', 'w') as file:
        json.dump(new_venue_data, file)

# function to read in the data for all games
def read_in_games():
    with open('data/games.json') as f:
        games = json.load(f)
        return games

#function to write the updated data for all games
def write_to_games(new_game_data):
    with open('data/games.json', 'w') as file:
        json.dump(new_game_data, file)

# function to read in the data for all game data
def read_in_game_data():
    with open('data/game_results.json') as f:
        game_results = json.load(f)
        return game_results

#function to write the updated data for all game data
def write_to_game_data(new_game_results):
    with open('data/game_results.json', 'w') as file:
        json.dump(new_game_results, file)

# function to find a specific set of games.
# there are several parameters (all scheduled games, all completed games, games for a specific teamID)
def get_games(status=None, team_id=None):
    # status is an optional parameter ('scheduled', 'completed', or None)
    # team_id is an optional parameter to filter games where this team is home or away
    
    # list to hold filtered games
    filtered_games = []

    # loop through all games and filter by status and/or team_id
    for game in games:
        # check status filter
        if status is not None and game['status'] != status:
            continue
        
        # check team_id filter (home or away)
        if team_id is not None and game['home_team_id'] != team_id and game['away_team_id'] != team_id:
            continue
        
        filtered_games.append(game)

    # list to hold the game info (teams who are playing, venue, game date)
    game_data = []

    # loop through filtered list and merge required data from teams and venues
    for game in filtered_games:
        # switch datetime string to datetime object
        utc_time = datetime.fromisoformat(game['datetime'])
        # Add UTC timezone if missing or if there is an offset appended (this will help with sort later)
        utc_time = utc_time.replace(tzinfo=timezone.utc)  

        # dictionary of individual game data
        individual_game = {
            'id': game['id'],
            'datetime': utc_time.strftime('%A, %B %d, %Y at %I:%M %p'),
            'datetime_sort': utc_time, 
            'home_team': teams_dict[game['home_team_id']]['name'],
            'away_team': teams_dict[game['away_team_id']]['name'],
            'game_label': game['game_label'],
            'venue': venues_dict[game['venue_id']]['name'],
            'city': venues_dict[game['venue_id']]['city'],
            'country': venues_dict[game['venue_id']]['country']
        }

        # add individual game back into list
        game_data.append(individual_game)
    
    # Sort list with earlist game first by sorting on the datatime object from each game:
    def get_datetime(x):
        return x['datetime_sort']
    game_data.sort(key=get_datetime)

    return game_data

# the home page includes a list of all upcoming games
@app.route('/')
def home_page():
    # run function to get all scheduled games
    upcoming_game_data = get_games("scheduled")

    return render_template('index.html', games=upcoming_game_data)

# the games page includes a list of all games (past and present) for this season
@app.route('/games')
def list_games():
    # run function to get all scheduled games
    all_game_data = get_games()

    return render_template('list_games.html', games=all_game_data)

# list all teams
@app.route('/teams')
def list_teams():
    return render_template('list_teams.html', ListofTeams=teams)

# list info for a specific game
@app.route('/game_detail')
def game_detail():
    return render_template('game_detail.html')

# admin: add a new team form
@app.route('/admin/add_team')
def admin_add_team_form():
    return render_template('admin/admin_add_team.html', ListofTeams=teams)

# admin: add a new venue form
@app.route('/admin/add_venue')
def admin_add_venue_form():
    return render_template('admin/admin_add_venue.html', ListofVenues=venues)

# admin: add team to database
@app.post('/admin/create_new_team')
def create_new_team():
    # convert form data into varables
    team_name = request.form.get('Team_Name')
    team_countryID = request.form.get('countryID')
    id = max(int(team['id']) for team in teams)+1
    #put new team data into a new list
    new_team = {'id': str(id), 'name': team_name, 'country': team_countryID}
    # add to teams list
    teams.append(new_team)
    write_to_teams_data(teams)
    return f'sucessfully added {team_name} {team_countryID} {id}'

@app.get('/teams/<id>')
def read_single_team(id):
    for team in teams:
        if team['id']==id:
            return team
        
    return "That team doesn't exist"

if __name__ == '__main__':
    #load teams data from file
    teams = read_in_teams()

    #load games from file
    games = read_in_games()

    #load game data from file
    game_data = read_in_game_data()

    #load venue data from file
    venues = read_in_venues()

    #create a dictionary of teams
    teams_dict = {}
    for team in teams:
        team_id = team['id']
        teams_dict[team_id] = team

    #create a dictionary of venues
    venues_dict = {}
    for venue in venues:
        venue_id = venue['id']
        venues_dict[venue_id] = venue

    app.run(debug=True)

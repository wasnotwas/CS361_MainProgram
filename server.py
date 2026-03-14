from flask import Flask, request, render_template
import json
import requests
from datetime import datetime, timezone
from match_data import get_match_details
from dotenv import load_dotenv
import os

load_dotenv()

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
# you can use "status" to find all, just scheduled, or just completed games and you can find games for a specific teamID)
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
        # Add UTC timezone
        utc_time = utc_time.replace(tzinfo=timezone.utc)  

        # dictionary of individual game data
        individual_game = {
            'id': game['id'],
            'datetime': utc_time.strftime('%A, %B %d, %Y at %I:%M %p'),
            'datetime_sort': utc_time, 
            'home_team': teams_dict[game['home_team_id']]['name'],
            'home_team_id': game['home_team_id'],
            'away_team': teams_dict[game['away_team_id']]['name'],
            'away_team_id': game['away_team_id'],
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

@app.route('/match_details')
def match_details():
    game_id = request.args.get('id')
    if not game_id:
        return "No game ID provided"
 
    # Grab match details
    details = get_match_details(game_id)
    if not details:
        return "Game not found"
 
    # Get Current Weather details from OpenWeatherMap.org
    weather = None
    venue_latitude = details.get('venue_latitude')
    venue_longitude = details.get('venue_longitude')
 
    
    """
    # Test Weather Data
    weather = {
                    'main': "Clouds", #str
                    'temp': 12.51, #float
                    'humidity': 90, #int
                    'wind_speed': 3.81, #float
                    'code': 200 #int
                }
    """
    #real weather call
 
    if venue_latitude and venue_longitude:
            try:
                weather_url = (
                    f"https://api.openweathermap.org/data/2.5/weather"
                    f"?lat={venue_latitude}&lon={venue_longitude}&units=metric"
                    f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
                )
                weather_response = requests.get(weather_url, timeout=5)
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    weather = {
                        'main': weather_data['weather'][0]['main'],
                        'temp': weather_data['main']['temp'],
                        'humidity': weather_data['main']['humidity'],
                        'wind_speed': weather_data['wind']['speed'],
                        'code': weather_data['cod']
                    }
                            
            except Exception as e:
                print(f"Weather API error: {e}")
                weather = None
    
    # BIG POOL MICROSERVER API Call: Convert wind speed to from Metric to imperial
    wind_speed_mph = None
    wind_speed_kmh = weather['wind_speed']
    try:
        ws_response = requests.get(
            f"http://127.0.0.1:6060/mtok/?speed={wind_speed_kmh}",
            timeout=5
        )
        if ws_response.status_code == 200:
            wind_speed_mph = ws_response.json()['result']
    except Exception as e:
        print(f"Wind speed conversion API error: {e}")
 
    # SMALL POOL Microservice API Call: Convert temperature to Fahrenheit
    temp_F = None
    try:
        temp_response = requests.get(
            f"http://127.0.0.1:8080/ctof/?temp={weather['temp']}",
            timeout=5
        )
        if temp_response.status_code == 200:
            temp_F = temp_response.json()['result']
    except Exception as e:
        print(f"Temp conversion API error: {e}")
 
    # BIG POOL MICROSERVICE API CALL: Calculate heat index
    heat_index_F = None
    if temp_F is not None:
        try:
            hi_response = requests.get(
                f"http://127.0.0.1:7070/heatindex?temperature_f={temp_F}&humidity={weather['humidity']}",
                timeout=5
            )
            if hi_response.status_code == 200:
                heat_index_F = hi_response.json()['heat_index']
        except Exception as e:
            print(f"Heat index API error: {e}")

    # BIG POOL Microservice API Call: Find Weather term
    weather_term = weather['main'].upper()
    try:
        temp_response = requests.get(
            f"http://127.0.0.1:4040/definition/?term={weather_term}",
            timeout=5
        )
        if temp_response.status_code == 200:
            weather_term = temp_response.json()['definition']
    except Exception as e:
        print(f"Terms API error: {e}")


    return render_template(
        'match_details.html',
        match=details,
        weather=weather,
        wind_speed_mph=wind_speed_mph,
        temp_F=round(temp_F,2),
        heat_index_F=heat_index_F,
        weather_define=weather_term
    )

# the games page includes a list of all games (past and present) for this season
@app.route('/games')
def list_games():
    # run function to get all scheduled games
    all_game_data = get_games()

    return render_template('list_games.html', games=all_game_data)

# Profile setup
@app.route('/profile_setup')
def profile_setup():
    return render_template('profile_set_up.html', ListofTeams=teams)

# list all teams
@app.route('/teams')
def list_teams():
    team_id = request.args.get('id')
    
    if team_id:
        all_game_data = get_games(None, team_id)
        return render_template('list_teams.html', ListofTeams=teams, ListofGames=all_game_data)
    else:
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

# admin: add a new venue form
@app.route('/admin/add_game')
def admin_add_game_form():
    ListofGames_data=get_games()
    return render_template('admin/admin_add_game.html', ListofGames=ListofGames_data, ListofTeams=teams, ListofVenues=venues)

# admin: add game to database
@app.post('/admin/create_new_game')
def create_new_game():
    # convert form data into varables
    game_home_team = request.form.get('home_teamID')
    game_away_team = request.form.get('away_teamID')
    game_venue = request.form.get('venueID')
    game_timezone = 'blank' #request.form.get('timezone')
    game_label = request.form.get('game_label')
    game_status = request.form.get('game_status')
    game_datetime = request.form.get('game_datetime')
    id = max(int(game['id']) for game in games)+1
    
    #put new game data into a new list
    new_game = {'id': str(id), 'home_team_id': game_home_team, 'away_team_id': game_away_team, 'venue_id': game_venue, 'timezone': game_timezone, 'datetime': game_datetime, 'game_label': game_label, 'status': game_status}

    # add to games list
    games.append(new_game)
    write_to_games(games)
    return f'sucessfully added {game_home_team} {game_away_team} {game_datetime} <a href="/">home</a>'


# admin: add venue to database
@app.post('/admin/create_new_venue')
def create_new_venue():
    # convert form data into varables
    venue_name = request.form.get('Venue_Name')
    venue_city = request.form.get('Venue_City')
    venue_country = request.form.get('countryID')
    venue_timezone = request.form.get('timezone')
    id = max(int(venue['id']) for venue in venues)+1
    
    #put new venue data into a new list
    new_venue = {'id': str(id), 'name': venue_name, 'city': venue_city, 'country': venue_country, 'timezone': venue_timezone}
    
    # add to teams list
    venues.append(new_venue)
    write_to_venues_data(venues)
    return f'sucessfully added {venue_name} {venue_country} {id} <a href="/">home</a>'


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
    return f'sucessfully added {team_name} {team_countryID} {id} <a href="/">home</a>'

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

from flask import Flask, request, render_template
import json


app = Flask(__name__)

def read_in_teams():
    with open('data/teams.json') as f:
        teams = json.load(f)
        return teams

def write_to_teams_data(new_team_data):
    with open('data/teams.json', 'w') as file:
        json.dump(new_team_data, file)

@app.route('/')
def home_page():
    return render_template('index.html', team_name="West Ham")

# list of all upcoming games
@app.route('/games')
def list_games():
    return render_template('list_games.html')

# list info for a specific game
@app.route('/game_detail')
def game_detail():
    return render_template('game_detail.html')

# admin: add a new team form
@app.route('/admin/add_team')
def admin_add_team_form():
    return render_template('admin/admin_add_team.html')

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

@app.get('/teams')
def list_teams():
    return teams

@app.get('/teams/<id>')
def read_single_team(id):
    for team in teams:
        if team['id']==id:
            return team
        
    return "That team doesn't exist"

if __name__ == '__main__':
    #load data
    teams = read_in_teams()
    app.run(debug=True)

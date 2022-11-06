import os
from flask import Flask, g, session, redirect, request, url_for, jsonify
from flask_cors import CORS, cross_origin
from requests_oauthlib import OAuth2Session
import mysql.connector as mysql
import json
import secrets


OAUTH2_CLIENT_ID = "1036701946108715048"
OAUTH2_CLIENT_SECRET = "JCYXn-DK8R0WXWyMVgV9B4iCV9jZwoch"
OAUTH2_REDIRECT_URI = 'http://server.pauli1panter.de:5004/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token

def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)

@app.route("/server/get/info")
def serverinfo():
    gid = request.args.get('guild_id')
    with open("config.json") as config:
        config = json.load(config)
    db = mysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database="testdb1",
    )
    cursor = db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM servers WHERE server='{gid}'")
    f = cursor.fetchone()
    return json.dumps(f)

@app.route("/session/get")
def getsession():
    access_token = request.args.get('access_token')
    expires_at = request.args.get('expires_at')
    expires_in = request.args.get('expires_in')
    refresh_token = request.args.get('refresh_token')
    scope = ["guilds", "guilds.join", "email", "connections", "identify"]
    token_type = "Bearer"
    data = {"access_token": access_token, "expires_at": expires_at, "expires_in": expires_in, "refresh_token": refresh_token, "scope": scope, "token_type": token_type}
    discord = make_session(token=data)
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    return guilds

@app.route("/token/check")
def checktoken():
    token = request.args.get('token')
    with open("config.json") as config:
        config = json.load(config)
    db = mysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database="oauth2",
    )
    cursor = db.cursor(buffered=True)
    cursor.execute(f"SELECT id FROM tokens WHERE token='{token}'")
    f = cursor.fetchone()
    if f == None:
        jsonData = {"code":"false"}
        return json.dumps(jsonData)
    else:
        cursor.execute(f"DELETE FROM tokens WHERE token='{token}'")
        db.commit()
        cursor.execute(f"SELECT authtoken FROM authtokens WHERE token='{token}'")
        f2 = cursor.fetchone()
        cursor.execute(f"DELETE FROM authtokens WHERE token='{token}'")
        db.commit()
        jsonData = {"code": "true", "sessiontoken": f2[0]}
        return json.dumps(jsonData)
@app.route('/')
def index():
    scope = request.args.get(
        'scope',
        'identify email connections guilds guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('.me'))

@app.route('/change/settings')
def change_settings():
    access_token = request.args.get('access_token')
    expires_at = request.args.get('expires_at')
    expires_in = request.args.get('expires_in')
    refresh_token = request.args.get('refresh_token')
    gid = request.args.get('gid')
    module = request.args.get('module')
    value = request.args.get('value')
    scope = ["guilds", "guilds.join", "email", "connections", "identify"]
    token_type = "Bearer"
    data = {"access_token": access_token, "expires_at": expires_at, "expires_in": expires_in,
            "refresh_token": refresh_token, "scope": scope, "token_type": token_type}
    discord = make_session(token=data)
    user = discord.get(API_BASE_URL + '/users/@me').json()
    with open("config.json") as config:
        config = json.load(config)
    db = mysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database="testdb1",
    )
    cursor = db.cursor(buffered=True)
    token = secrets.token_hex(80)
    cursor.execute(f"UPDATE servers set {module}='{value}' WHERE server='{gid}'")
    db.commit()
    cdata = {"code": "success"}
    return cdata

@app.route('/redirect/servers')
def redirect_to_servers():
    access_token = request.args.get('access_token')
    expires_at = request.args.get('expires_at')
    expires_in = request.args.get('expires_in')
    refresh_token = request.args.get('refresh_token')
    gid = request.args.get('gid')
    scope = ["guilds", "guilds.join", "email", "connections", "identify"]
    token_type = "Bearer"
    data = {"access_token": access_token, "expires_at": expires_at, "expires_in": expires_in,
            "refresh_token": refresh_token, "scope": scope, "token_type": token_type}
    discord = make_session(token=data)
    user = discord.get(API_BASE_URL + '/users/@me').json()
    with open("config.json") as config:
        config = json.load(config)
    db = mysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database="oauth2",
    )
    cursor = db.cursor(buffered=True)
    token = secrets.token_hex(80)
    cursor.execute(f"INSERT INTO tokens(id, token) VALUES('{user['id']}', '{token}')")
    db.commit()
    v = "'"
    n = '"'
    cursor.execute(f"INSERT INTO authtokens(token, authtoken) VALUES('{token}', '{str(session.get('oauth2_token')).replace(v, n)}')")
    db.commit()
    return redirect("http://server.pauli1panter.de/interface/servers?token=" + token + "&&guild_id=" + gid)

@app.route('/me')
def me():

    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
    with open("config.json") as config:
        config = json.load(config)
    db = mysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database="oauth2",
    )
    cursor = db.cursor(buffered=True)
    #for g in guilds:
    #    if g["owner"] == True:
    #        cursor.execute(f"SELECT servername FROM servers WHERE server='{g['id']}'")
    #        f = cursor.fetchone()
    #        if f == None:
    #            pass
    #        else:
    #            pass
    token = secrets.token_hex(80)
    cursor.execute(f"INSERT INTO tokens(id, token) VALUES('{user['id']}', '{token}')")
    db.commit()
    v = "'"
    n = '"'
    cursor.execute(f"INSERT INTO authtokens(token, authtoken) VALUES('{token}', '{str(session.get('oauth2_token')).replace(v, n)}')")
    db.commit()
    return redirect("http://server.pauli1panter.de/interface?token=" + token)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    app.run(port="5004",host="0.0.0.0")

from imports import *
from predefines import *

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

CLIENT_ID = '1370521645495881789'
CLIENT_SECRET = '-wTpQHOjKPPE0U7ELMv6XqFnSlFVeqkj'
REDIRECT_URI = 'http://localhost:5000/callback'

@app.route("/")
def home():
    guild_id = "656863051802476548"
    settings = load_settings_json("guild_settings").get(guild_id, {})

    return render_template('home.html', user=session.get("user"), settings=settings)

@app.route('/pfl')
def pfl_page():
    guild_id = "1068670713529106432"
    settings = load_settings_json("guild_settings").get(guild_id, {})

    return render_template('pfl.html', user=session.get("user"), settings=settings)

@app.route('/pbl')
def pbl_page():
    guild_id = "1240014143784747018"
    settings = load_settings_json("guild_settings").get(guild_id, {})

    return render_template('pbl.html', user=session.get("user"), settings=settings)

@app.route('/pbul')
def pbul_page():
    guild_id = "1364650269652025354"
    settings = load_settings_json("guild_settings").get(guild_id, {})

    return render_template('pbul.html', user=session.get("user"), settings=settings)

@app.route("/login")
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify") 

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    access_token = r.json()["access_token"]

    user_data = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"}).json()
    session["user"] = {
        "username": f'{user_data["username"]}',
        "avatar_url": f'https://cdn.discordapp.com/avatars/{user_data["id"]}/{user_data["avatar"]}.png'
    }
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)



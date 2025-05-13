from imports import *
from predefines import *
from functions import *

def download_file(service, file_id, dest_path):
    temp_path = dest_path + ".tmp"
    request = service.files().get_media(fileId=file_id)
    with open(temp_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    os.replace(temp_path, dest_path)  # Atomic overwrite
    size = os.path.getsize(dest_path)
    print(f"[DOWNLOAD] Saved '{dest_path}' ({size} bytes)")

def sync_from_drive():
    drive_service = build('drive', 'v3', credentials=credentials)

    print("[SYNC] Starting sync from Google Drive...")

    # Find 'settings' folder
    results = drive_service.files().list(
        q="name='settings' and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    if not folders:
        print("[SYNC] Settings folder not found.")
        return
    folder_id = folders[0]['id']
    print(f"[SYNC] Found settings folder with ID: {folder_id}")

    # Download all files in the settings folder
    files = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name)"
    ).execute().get('files', [])

    print(f"[SYNC] Found {len(files)} files in 'settings' folder.")
    for f in files:
        print(f"  - {f['name']}")


    os.makedirs('settings', exist_ok=True)

    for f in files:
        dest_path = os.path.join('settings', f['name'])
        print(f"[SYNC] Downloading file: {f['name']} to {dest_path}")
        download_file(drive_service, f['id'], dest_path)

    # Download main_database.db
    db_files = drive_service.files().list(
        q="name='main_database.db'",
        fields="files(id, name)"
    ).execute().get('files', [])
    if db_files:
        print("[SYNC] Downloading main_database.db")
        download_file(drive_service, db_files[0]['id'], 'main_database.db')
    else:
        print("[SYNC] main_database.db not found on Drive.")

    print("[SYNC] Sync complete.\n")

def start_auto_sync():
    def loop():
        while True:
            sync_from_drive()
            time.sleep(1800)  # Every 30 minutes
    threading.Thread(target=loop, daemon=True).start()

start_auto_sync()

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

CLIENT_ID = '1370521645495881789'
CLIENT_SECRET = 'X94AVQ6FXxIhD7SO-xrG-9_5n1o9NFiv'
REDIRECT_URI = 'https://providencerosports.com/callback'

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



@app.route("/<league>/stats/<section>")
def unified_league_stats(league, section):
    guild_map = {
        "pfl": "1068670713529106432",
        "pbl": "1240014143784747018",
        "pbul": "1364650269652025354"
    }

    title_map = {
        "season": "Season Stats",
        "all_time": "All-Time Stats"
    }

    if league not in guild_map or section not in title_map:
        return "Invalid league or section", 404

    return render_league_stats(guild_map[league], section, title_map[section])

@app.route("/login")
def login():
    return redirect(
        f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope=identify+email+guilds"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify email guilds"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    r.raise_for_status()

    access_token = r.json()["access_token"]
    user_data = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    session["user"] = {
        "username": user_data["username"],
        "avatar_url": f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        "id": user_data["id"]
    }
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    discord_id = str(session["user"]["id"])
    user_data = load_user_data(discord_id)

    return render_template("profile.html", user=session["user"], user_data=user_data)

@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.utcfromtimestamp(value).strftime('%b %d, %Y')

if __name__ == "__main__":
    app.run(debug=True)

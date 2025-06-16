from imports import *
from predefines import *
from functions import *

prs_guild_id = 656863051802476548

def download_file(service, file_id, dest_path):
    temp_path = dest_path + ".tmp"
    request = service.files().get_media(fileId=file_id)
    with open(temp_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    os.replace(temp_path, dest_path)
    size = os.path.getsize(dest_path)
    print(f"[DOWNLOAD] Saved '{dest_path}' ({size} bytes)")

def sync_from_drive():
    drive_service = build('drive', 'v3', credentials=credentials)

    print("[SYNC] Starting sync from Google Drive...")

    settings_results = drive_service.files().list(
        q="name='settings' and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    settings_folders = settings_results.get('files', [])
    if settings_folders:
        settings_folder_id = settings_folders[0]['id']
        print(f"[SYNC] Found settings folder with ID: {settings_folder_id}")

        settings_files = drive_service.files().list(
            q=f"'{settings_folder_id}' in parents",
            fields="files(id, name)"
        ).execute().get('files', [])

        print(f"[SYNC] Found {len(settings_files)} files in 'settings' folder.")
        os.makedirs('settings', exist_ok=True)
        for f in settings_files:
            dest_path = os.path.join('settings', f['name'])
            print(f"[SYNC] Downloading file: {f['name']} to {dest_path}")
            download_file(drive_service, f['id'], dest_path)
    else:
        print("[SYNC] Settings folder not found.")

    db_files = drive_service.files().list(
        q="name='main_database.db'",
        fields="files(id, name)"
    ).execute().get('files', [])
    if db_files:
        print("[SYNC] Downloading main_database.db")
        download_file(drive_service, db_files[0]['id'], 'main_database.db')
    else:
        print("[SYNC] main_database.db not found on Drive.")

    databases_results = drive_service.files().list(
        q="name='databases' and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    databases_folders = databases_results.get('files', [])
    if databases_folders:
        databases_folder_id = databases_folders[0]['id']
        print(f"[SYNC] Found databases folder with ID: {databases_folder_id}")

        databases_files = drive_service.files().list(
            q=f"'{databases_folder_id}' in parents",
            fields="files(id, name)"
        ).execute().get('files', [])

        print(f"[SYNC] Found {len(databases_files)} files in 'databases' folder.")
        os.makedirs('databases', exist_ok=True)
        for f in databases_files:
            dest_path = os.path.join('databases', f['name'])
            print(f"[SYNC] Downloading file: {f['name']} to {dest_path}")
            download_file(drive_service, f['id'], dest_path)
    else:
        print("[SYNC] databases folder not found.")

    print("[SYNC] Sync complete.\n")

def start_auto_sync():
    sync_from_drive()

    def loop():
        while True:
            try:
                now = datetime.utcnow()
                seconds_until_next_hour = ((60 - now.minute - 1) * 60) + (60 - now.second)
                print(f"[SYNC] Waiting {seconds_until_next_hour} seconds until the next full hour...")
                time.sleep(seconds_until_next_hour)

                print("[SYNC] Attempting sync...")
                sync_from_drive()

            except Exception as e:
                print(f"[SYNC ERROR] {e}")
                traceback.print_exc()
                time.sleep(300)  # Wait 5 min before retrying to avoid a tight error loop

    threading.Thread(target=loop, daemon=True).start()

    threading.Thread(target=loop, daemon=True).start()

start_auto_sync()

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

CLIENT_ID = '1370521645495881789'
CLIENT_SECRET = 'X94AVQ6FXxIhD7SO-xrG-9_5n1o9NFiv'
REDIRECT_URI = 'https://providencerosports.com/callback'

@app.route("/")
def home():
    league_ids = load_settings_json("guild_ids").get("league_ids", [])
    league_data = []
    for league_id in league_ids:
        league_id = str(league_id)
        settings = load_settings_json("guild_settings").get(league_id)
        if settings:
            league_data.append({
                "url": f"/{settings['info']['league_name'].lower()}",
                "name": settings['info']['league_name'],
                "game_name": settings['info']['game_name'],
                "color": f"{settings['info']['league_color']}",
                "cover": settings['info']['game_cover']
            })
    return render_template('home.html', user=session.get("user"), league_data=league_data)

@app.route("/ads.txt")
def serve_ads_txt():
    return send_from_directory(os.path.join(app.root_path), "ads.txt")

@app.route("/<league>")
def dynamic_league_page(league):
    league_ids = load_settings_json("guild_ids").get("league_ids", [])
    guild_settings = load_settings_json("guild_settings")

    for league_id in league_ids:
        settings = guild_settings.get(str(league_id))
        if settings and settings['info']['league_name'].lower() == league:
            settings["info"]["guild_id"] = league_id
            return render_template("league.html", user=session.get("user"), settings=settings)


    return render_template("404.html"), 404

@app.route("/<league>/stats/<section>")
def unified_league_stats(league, section):
    guild_ids = load_settings_json("guild_ids").get("league_ids", [])
    settings_data = load_settings_json("guild_settings")

    for gid in guild_ids:
        settings = settings_data.get(str(gid))
        if settings and settings['info']['league_name'].lower() == league:
            if section not in ["season", "all_time"]:
                return "Invalid section", 404
            title_map = {
                "season": "Season Stats",
                "all_time": "All-Time Stats"
            }
            return render_league_stats(str(gid), section, title_map[section])

    return "Invalid league or section", 404

@app.route("/<league>/league_regulations")
def game_rules_page(league):
    guild_ids = load_settings_json("guild_ids").get("league_ids", [])
    guild_settings = load_settings_json("guild_settings")
    game_rules_data = load_settings_json("game_rules")

    for gid in guild_ids:
        settings = guild_settings.get(str(gid))
        if settings and settings['info']['league_name'].lower() == league:
            rules = game_rules_data.get(str(gid), {})
            parsed_sections = []
            for i, (section_key, section_data) in enumerate(rules.items(), start=1):
                section_title = section_key.replace("_", " ").title()
                section_rules = [
                    f"{i}.{str(j+1).zfill(2)}: {rule}"
                    for j, rule in enumerate(section_data['rules'])
                ]
                parsed_sections.append((section_title, section_rules))
            return render_template("league_regulations.html", settings=settings, sections=parsed_sections)
    return render_template("404.html"), 404

@app.route("/<league>/standings")
def league_standings_page(league):
    guild_ids = load_settings_json("guild_ids").get("league_ids", [])
    settings_data = load_settings_json("guild_settings")
    standings_data = load_database_json("standings_database")
    league_status = load_settings_json("league_status")
    team_data = load_database_json("team_database")

    for gid in guild_ids:
        settings = settings_data.get(str(gid))
        if settings and settings['info']['league_name'].lower() == league:
            settings["info"]["guild_id"] = gid

            current_series = league_status.get(str(gid), {}).get("series", 0)

            labels = {
                "season": "Season",
                "series1": "Series 1",
                "series2": "Series 2",
                "series3": "Series 3",
                "series4": "Series 4",
                "series5": "Playoffs"
            }

            filtered_labels = {}
            for key, label in labels.items():
                if key == "season":
                    filtered_labels[key] = label
                elif key.startswith("series"):
                    number = key[6:]
                    if number.isdigit() and int(number) <= current_series:
                        filtered_labels[key] = label

            standings_sections = []
            for section_key, label in filtered_labels.items():
                rows = []
                for team_name, team_data in standings_data.get(str(gid), {}).items():
                    section = team_data.get(section_key)
                    if section:
                        rows.append([
                            team_name,
                            section.get("division", "-"),
                            section.get("rank", "-"),
                            section.get("seed", "-"),
                            section.get("wins", 0),
                            section.get("losses", 0),
                            section.get("pd", 0),
                            section.get("points", 0)
                        ])
                if rows:
                    rows.sort(key=lambda x: (int(x[2]) if str(x[2]).isdigit() else 999))
                    standings_sections.append({
                        "label": label,
                        "headers": ["Team", "Division", "Rank", "Seed", "Wins", "Losses", "Points", "PD"],
                        "rows": rows
                    })

            return render_template("standings.html", settings=settings, user=session.get("user"), standings_sections=standings_sections)

    return render_template("404.html"), 404

@app.route("/rosports_standards")
def rosports_standards_page():
    guild_settings = load_settings_json("guild_settings").get(str(prs_guild_id))
    rosports_standards = load_settings_json("rosports_standards")

    if rosports_standards:
        parsed_sections = []
        for i, (section_key, section_data) in enumerate(rosports_standards.items(), start=1):
            section_title = section_key.replace("_", " ").title()
            section_rules = [
                f"{i}.{str(j+1).zfill(2)}: {rule}"
                for j, rule in enumerate(section_data['rules'])
            ]
            parsed_sections.append((section_title, section_rules))
        return render_template("rosports_standards.html", settings=guild_settings, sections=parsed_sections)
    return render_template("404.html"), 404

@app.route("/<league>/donator_benefits")
def benefits_perks_page(league):
    guild_ids = load_settings_json("guild_ids").get("league_ids", [])
    guild_settings = load_settings_json("guild_settings")
    all_perks = load_settings_json("benefits_perks")

    for guild_id in guild_ids:
        settings = guild_settings.get(str(guild_id))
        if settings and settings["info"]["league_name"].lower() == league:
            perks = all_perks.get(str(guild_id), {})
            default_perks = perks.get("default", {})
            combined_perks = {}
            for level in ("donator1", "donator2", "donator3"):
                combined_perks[level] = dict(perks.get(level, {}))
                combined_perks[level].update(default_perks)
            return render_template("donator_benefits.html", settings=settings, combined_perks=combined_perks)
    return render_template("404.html"), 404

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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/images/<path:filename>")
def serve_images(filename):
    return send_from_directory(os.path.join(app.root_path, "images"), filename)

if __name__ == "__main__":
    app.run(debug=True)

from imports import *

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
encoded = os.environ["GOOGLE_CREDENTIALS_BASE64"]
decoded_json = base64.b64decode(encoded).decode("utf-8")
credentials_info = json.loads(decoded_json)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
gc = gspread.authorize(credentials)


def load_settings_json(name):
    path = os.path.join("settings", f"{name}.json")
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}
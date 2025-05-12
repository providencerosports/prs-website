from imports import *
from predefines import *

def list_to_string(lst):
    return ",".join(map(str, lst))

def string_to_list(string):
    if not string:
        return []

    return string.split(',')

def load_user_data(member_id):
    main_db_conn = sqlite3.connect('main_database.db')
    main_db_cursor = main_db_conn.cursor()

    list_columns = ['past_users', 'alt_discords']

    try:
        main_db_cursor.execute('PRAGMA table_info(user_data);')
        columns_info = main_db_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        column_types = {col[1]: col[2].upper() for col in columns_info}

        main_db_cursor.execute('SELECT * FROM user_data WHERE member_id = ?', (member_id,))
        data = main_db_cursor.fetchone()

        if data:
            data_dict = dict(zip(column_names, data))

            for column in data_dict:
                value = data_dict[column]

                if column in list_columns:
                    if isinstance(value, str):
                        data_dict[column] = string_to_list(value) if value.strip() else []
                    else:
                        data_dict[column] = []
                elif value is None and column_types.get(column) == "INTEGER":
                    data_dict[column] = 0

            return data_dict

        return {
            column: [] if column in list_columns else (
                0 if column_types.get(column) == "INTEGER" else None
            )
            for column in column_names
        }

    except sqlite3.Error as e:
        print(f"Error loading user data: {e}")
        return None

    finally:
        main_db_conn.close()


def render_league_stats(guild_id: str, section: str, title: str):
    with threading.Lock():
        main_db_conn = sqlite3.connect("main_database.db")
        main_db_cursor = main_db_conn.cursor()

        main_db_cursor.execute("""
            SELECT DISTINCT stat_category
            FROM stats_database
            WHERE guild_id = ? AND section = ?
        """, (guild_id, section))
        categories = [row[0] for row in main_db_cursor.fetchall()]
        if not categories:
            return "No stats available."

        selected_category = request.args.get("category") or categories[0]
        sort_by = request.args.get("sort")
        direction = request.args.get("dir", "desc")

        main_db_cursor.execute("""
            SELECT stat_name, order_index
            FROM stats_database
            WHERE guild_id = ? AND section = ? AND stat_category = ?
            GROUP BY stat_name
            ORDER BY order_index ASC
        """, (guild_id, section, selected_category))
        headers_raw = main_db_cursor.fetchall()

        stat_headers = []
        default_sort_by = headers_raw[0][0] if headers_raw else None
        for i, (name, index) in enumerate(headers_raw):
            stat_headers.append({"stat_name": name, "order_index": index})
            if i == 0:
                stat_headers.append({"stat_name": "username", "order_index": -1})

        if not sort_by:
            sort_by = default_sort_by
            direction = "asc"

        main_db_cursor.execute("""
            SELECT username, stat_name, stat_value
            FROM stats_database
            WHERE guild_id = ? AND section = ? AND stat_category = ?
        """, (guild_id, section, selected_category))
        raw_data = main_db_cursor.fetchall()

        user_stats = {}
        for username, stat_name, stat_value in raw_data:
            if username not in user_stats:
                user_stats[username] = {}
            user_stats[username][stat_name] = stat_value

        stats_data = []
        for username, stats in user_stats.items():
            row = {
                "username": username,
                "stats": []
            }
            for h in stat_headers:
                stat_name = h["stat_name"]
                if stat_name == "username":
                    row["stats"].append(username)
                else:
                    row["stats"].append(stats.get(stat_name, ""))
            stats_data.append(row)

        if sort_by:
            idx = next((i for i, h in enumerate(stat_headers) if h["stat_name"] == sort_by), None)
            if idx is not None:
                def parse(v):
                    try:
                        v = v.replace(',', '') if isinstance(v, str) else v
                        return float(v.strip('%')) if isinstance(v, str) and '%' in v else float(v)
                    except:
                        return float('-inf') if direction == 'desc' else float('inf')
                stats_data.sort(key=lambda x: parse(x["stats"][idx]), reverse=(direction == "desc"))

        sort_column_index = idx

        settings = load_settings_json("guild_settings").get(guild_id)
        league_name = settings["info"]["league_name"]
        league_color = f"#{settings['info']['league_color'].lstrip('#')}"

        main_db_conn.close()

    return render_template(
        "league_stats.html",
        categories=categories,
        selected_category=selected_category,
        stat_headers=stat_headers,
        stats_data=stats_data,
        user=session.get("user"),
        sort_by=sort_by,
        direction=direction,
        sort_column_index=sort_column_index,
        title=title,
        league_name=league_name,
        league_color=league_color
    )
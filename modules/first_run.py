from modules import db
from modules.connections import database_file as database_file
import os


async def add_admins(self):
    if not db.query("SELECT * FROM admins"):
        app_info = await self.application_info()
        if app_info.team:
            for team_member in app_info.team.members:
                db.query(["INSERT INTO admins VALUES (?, ?)", [str(team_member.id), "1"]])
                print(f"Added {team_member.name} to admin list")
        else:
            db.query(["INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"]])
            print(f"Added {app_info.owner.name} to admin list")


def create_tables():
    if not os.path.exists(database_file):
        db.query("CREATE TABLE config (setting, parent, value, flag)")
        db.query("CREATE TABLE admins (user_id, permissions)")

        db.query("CREATE TABLE rssfeed_tracklist (url)")
        db.query("CREATE TABLE rssfeed_channels (url, channel_id)")
        db.query("CREATE TABLE rssfeed_history (url, entry_id)")

        db.query("CREATE TABLE rankfeed_channel_list (channel_id)")
        db.query("CREATE TABLE rankfeed_history (mapset_id)")

        db.query("CREATE TABLE usereventfeed_tracklist (osu_id)")
        db.query("CREATE TABLE usereventfeed_channels (osu_id, channel_id)")
        db.query("CREATE TABLE usereventfeed_history (osu_id, event_id, timestamp)")

        db.query("CREATE TABLE groupfeed_channel_list (channel_id)")
        db.query("CREATE TABLE groupfeed_members (osu_id, username, group_id)")
        db.query("CREATE TABLE groupfeed_json_data (group_id, contents)")

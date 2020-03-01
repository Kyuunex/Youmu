import sqlite3
from modules.connections import database_file as database_file
import os


async def add_admins(self):
    async with await self.db.execute("SELECT * FROM admins") as cursor:
        admin_list = await cursor.fetchall()

    if not admin_list:
        app_info = await self.application_info()
        if app_info.team:
            for team_member in app_info.team.members:
                await self.db.execute("INSERT INTO admins VALUES (?, ?)", [str(team_member.id), "1"])
                print(f"Added {team_member.name} to admin list")
        else:
            await self.db.execute("INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"])
            print(f"Added {app_info.owner.name} to admin list")
        await self.db.commit()


def create_tables():
    if not os.path.exists(database_file):
        conn = sqlite3.connect(database_file)
        c = conn.cursor()
        c.execute("CREATE TABLE config (setting, parent, value, flag)")
        c.execute("CREATE TABLE admins (user_id, permissions)")

        c.execute("CREATE TABLE rssfeed_tracklist (url)")
        c.execute("CREATE TABLE rssfeed_channels (url, channel_id)")
        c.execute("CREATE TABLE rssfeed_history (url, entry_id)")

        c.execute("CREATE TABLE rankfeed_channel_list (channel_id)")
        c.execute("CREATE TABLE rankfeed_history (mapset_id)")

        c.execute("CREATE TABLE usereventfeed_tracklist (osu_id)")
        c.execute("CREATE TABLE usereventfeed_channels (osu_id, channel_id)")
        c.execute("CREATE TABLE usereventfeed_history (osu_id, event_id, timestamp)")

        c.execute("CREATE TABLE groupfeed_channel_list (channel_id)")
        c.execute("CREATE TABLE groupfeed_group_members (osu_id, group_id)")
        c.execute("CREATE TABLE groupfeed_member_info (osu_id, username, country)")
        conn.commit()
        conn.close()

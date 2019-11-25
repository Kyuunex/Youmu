#!/usr/bin/env python3

from discord.ext import commands
import os

from modules import db

from modules.connections import database_file as database_file
from modules.connections import bot_token as bot_token

command_prefix = "."
app_version = "a20191125"
client = commands.Bot(command_prefix=command_prefix,
                      description=f"Youmu {app_version}")

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

initial_extensions = [
    "cogs.BotManagement",
    "cogs.GroupFeed",
    "cogs.RankFeed",
    "cogs.RSSFeed",
    "cogs.UserEventFeed",
]

if __name__ == "__main__":
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            print(e)


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")
    if not db.query("SELECT * FROM admins"):
        app_info = await client.application_info()
        db.query(["INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"]])
        print(f"Added {app_info.owner.name} to admin list")


client.run(bot_token)

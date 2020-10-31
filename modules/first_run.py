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
                await self.db.execute("INSERT INTO admins VALUES (?, ?)", [int(team_member.id), 1])
                print(f"Added {team_member.name} to admin list")
        else:
            await self.db.execute("INSERT INTO admins VALUES (?, ?)", [int(app_info.owner.id), 1])
            print(f"Added {app_info.owner.name} to admin list")
        await self.db.commit()


def ensure_tables():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS "admins" (
        "user_id"    INTEGER NOT NULL UNIQUE,
        "permissions"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "config" (
        "setting"    TEXT,
        "parent"    TEXT,
        "value"    TEXT,
        "flag"    TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "groupfeed_channel_list" (
        "channel_id"    INTEGER NOT NULL UNIQUE
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "groupfeed_group_members" (
        "osu_id"    INTEGER NOT NULL,
        "group_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "groupfeed_member_info" (
        "osu_id"    INTEGER NOT NULL UNIQUE,
        "username"    TEXT NOT NULL,
        "country"    TEXT NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "ignored_users" (
        "user_id"    INTEGER NOT NULL UNIQUE,
        "reason"    TEXT NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "rankfeed_channel_list" (
        "channel_id"    INTEGER NOT NULL UNIQUE
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "rankfeed_history" (
        "mapset_id"    INTEGER NOT NULL UNIQUE
    )
    """)
    c.execute("""CREATE TABLE IF NOT EXISTS "rssfeed_channels" (
        "url"    TEXT NOT NULL,
        "channel_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "rssfeed_history" (
        "url"    TEXT NOT NULL,
        "entry_id"    TEXT NOT NULL UNIQUE
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "rssfeed_tracklist" (
        "url"    TEXT NOT NULL UNIQUE
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "usereventfeed_channels" (
        "osu_id"    INTEGER NOT NULL,
        "channel_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "usereventfeed_history" (
        "osu_id"    INTEGER NOT NULL,
        "event_id"    INTEGER NOT NULL UNIQUE,
        "timestamp"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "usereventfeed_tracklist" (
        "osu_id"    INTEGER NOT NULL UNIQUE
    )
    """)
    conn.commit()
    conn.close()

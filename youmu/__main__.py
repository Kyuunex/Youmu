#!/usr/bin/env python3

from discord.ext import commands
import aiosqlite
import os

from aioosuapi import aioosuapi
from aioosuwebapi import aioosuwebapi

from youmu.modules import first_run
from youmu.manifest import VERSION
from youmu.manifest import CONTRIBUTORS

from youmu.modules.storage_management import database_file as database_file
from youmu.modules.connections import bot_token as bot_token
from youmu.modules.connections import osu_api_key as osu_api_key
from youmu.modules.connections import client_id as client_id
from youmu.modules.connections import client_secret as client_secret

if os.environ.get('YOUMU_PREFIX'):
    command_prefix = os.environ.get('YOUMU_PREFIX')
else:
    command_prefix = "'"

first_run.ensure_tables()

initial_extensions = [
    "youmu.cogs.BotManagement",
    "youmu.cogs.GroupFeed",
    "youmu.cogs.RankFeed",
    "youmu.cogs.RSSFeed",
    "youmu.cogs.UserEventFeed",
]


class Youmu(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_tasks = []

        self.app_version = VERSION
        self.project_contributors = CONTRIBUTORS

        self.description = f"Youmu {self.app_version}"
        self.database_file = database_file
        self.osu = aioosuapi(osu_api_key)
        self.osuweb = aioosuwebapi(client_id, client_secret)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(e)

    async def start(self, *args, **kwargs):
        self.db = await aiosqlite.connect(self.database_file)

        await super().start(*args, **kwargs)

    async def close(self):
        # Cancel all Task object generated by cogs.
        # This prevents any task still running due to having long sleep time.
        for task in self.background_tasks:
            task.cancel()

        # Close osu web api session
        await self.osuweb.close()

        # Close connection to the database
        if self.db:
            await self.db.close()

        # Run actual discord.py close.
        # await super().close()

        # for now let's just quit() since the thing above does not work :c
        quit()

    async def on_ready(self):
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("------")
        await first_run.add_admins(self)


client = Youmu(command_prefix=command_prefix)
client.run(bot_token)
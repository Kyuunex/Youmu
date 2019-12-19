import time
import asyncio
from discord.ext import commands

from modules import db
from modules import permissions
from modules.connections import osuweb as osuweb
import osuwebembed


class RankFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.rankfeed_background_loop())

    @commands.command(name="rankfeed_add", brief="Add a rankfeed in the current channel", description="")
    @commands.check(permissions.is_admin)
    async def add(self, ctx):
        fresh_entries = await osuweb.get_latest_ranked_beatmapsets()
        if fresh_entries:
            for mapset_metadata in fresh_entries["beatmapsets"]:
                mapset_id = mapset_metadata["id"]
                if not db.query(["SELECT mapset_id FROM rankfeed_history WHERE mapset_id = ?", [str(mapset_id)]]):
                    db.query(["INSERT INTO rankfeed_history VALUES (?)", [str(mapset_id)]])
            if not db.query(["SELECT * FROM rankfeed_channel_list WHERE channel_id = ?", [str(ctx.channel.id)]]):
                db.query(["INSERT INTO rankfeed_channel_list VALUES (?)", [str(ctx.channel.id)]])
                await ctx.send(":ok_hand:")

    @commands.command(name="rankfeed_remove", brief="Remove a rankfeed from the current channel", description="")
    @commands.check(permissions.is_admin)
    async def remove(self, ctx):
        db.query(["DELETE FROM rankfeed_channel_list WHERE channel_id = ?", [str(ctx.channel.id)]])
        await ctx.send(":ok_hand:")

    async def rankfeed_background_loop(self):
        print("RankFeed Loop launched!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(10)
                rankfeed_channel_list = db.query("SELECT channel_id FROM rankfeed_channel_list")
                if rankfeed_channel_list:
                    if db.query("SELECT mapset_id FROM rankfeed_history"):
                        print(time.strftime("%X %x %Z")+" | performing rankfeed check")
                        fresh_entries = await osuweb.get_latest_ranked_beatmapsets()
                        if fresh_entries:
                            for mapset_metadata in fresh_entries["beatmapsets"]:
                                mapset_id = mapset_metadata["id"]
                                if mapset_metadata["status"] == "loved":
                                    continue
                                if not db.query(["SELECT mapset_id FROM rankfeed_history "
                                                 "WHERE mapset_id = ?",
                                                 [str(mapset_id)]]):
                                    embed = await osuwebembed.beatmapset(mapset_metadata, color=0xffc85a)
                                    if embed:
                                        for rankfeed_channel_id in rankfeed_channel_list:
                                            channel = self.bot.get_channel(int(rankfeed_channel_id[0]))
                                            if channel:
                                                await channel.send(embed=embed)
                                            else:
                                                db.query(["DELETE FROM rankfeed_channel_list "
                                                          "WHERE channel_id = ?",
                                                          [str(rankfeed_channel_id[0])]])
                                                print(f"channel with id {rankfeed_channel_id[0]} no longer exists "
                                                      "so I am removing it from the list")
                                        db.query(["INSERT INTO rankfeed_history VALUES (?)", [str(mapset_id)]])
                        print(time.strftime("%X %x %Z")+" | finished rankfeed check")
                    else:
                        print("no maps in history so i stop so i don't spam")
                await asyncio.sleep(1600)
            except Exception as e:
                print(time.strftime("%X %x %Z"))
                print("in rankfeed_background_loop")
                print(e)
                await asyncio.sleep(3600)


def setup(bot):
    bot.add_cog(RankFeed(bot))

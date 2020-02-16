import time
import asyncio
from discord.ext import commands

from modules import permissions
from modules.connections import osuweb as osuweb
import osuwebembed


class RankFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.background_tasks.append(
            self.bot.loop.create_task(self.rankfeed_background_loop())
        )

    @commands.command(name="rankfeed_add", brief="Add a rankfeed in the current channel", description="")
    @commands.check(permissions.is_admin)
    async def add(self, ctx):
        fresh_entries = await osuweb.get_latest_ranked_beatmapsets()
        if fresh_entries:
            for mapset_metadata in fresh_entries["beatmapsets"]:
                mapset_id = mapset_metadata["id"]
                async with await self.bot.db.execute("SELECT mapset_id FROM rankfeed_history WHERE mapset_id = ?",
                                                     [str(mapset_id)]) as cursor:
                    check_one = await cursor.fetchall()
                if not check_one:
                    await self.bot.db.execute("INSERT INTO rankfeed_history VALUES (?)", [str(mapset_id)])
            async with await self.bot.db.execute("SELECT * FROM rankfeed_channel_list WHERE channel_id = ?",
                                                 [str(ctx.channel.id)]) as cursor:
                check_two = await cursor.fetchall()
            if not check_two:
                await self.bot.db.execute("INSERT INTO rankfeed_channel_list VALUES (?)", [str(ctx.channel.id)])
                await ctx.send(":ok_hand:")
            await self.bot.db.commit()

    @commands.command(name="rankfeed_remove", brief="Remove a rankfeed from the current channel", description="")
    @commands.check(permissions.is_admin)
    async def remove(self, ctx):
        await self.bot.db.execute("DELETE FROM rankfeed_channel_list WHERE channel_id = ?", [str(ctx.channel.id)])
        await self.bot.db.commit()
        await ctx.send(":ok_hand:")

    async def rankfeed_background_loop(self):
        print("RankFeed Loop launched!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(10)
                async with await self.bot.db.execute("SELECT channel_id FROM rankfeed_channel_list") as cursor:
                    rankfeed_channel_list = await cursor.fetchall()
                if rankfeed_channel_list:
                    async with await self.bot.db.execute("SELECT mapset_id FROM rankfeed_history") as cursor:
                        rankfeed_history_check = await cursor.fetchall()
                    if rankfeed_history_check:
                        print(time.strftime("%X %x %Z") + " | performing rankfeed check")
                        fresh_entries = await osuweb.get_latest_ranked_beatmapsets()
                        if fresh_entries:
                            for mapset_metadata in fresh_entries["beatmapsets"]:
                                mapset_id = mapset_metadata["id"]
                                if mapset_metadata["status"] == "loved":
                                    continue
                                async with await self.bot.db.execute("SELECT mapset_id FROM rankfeed_history "
                                                                     "WHERE mapset_id = ?",
                                                                     [str(mapset_id)]) as cursor:
                                    in_rankfeed_history_check = await cursor.fetchall()
                                if not in_rankfeed_history_check:
                                    embed = await osuwebembed.beatmapset(mapset_metadata, color=0xffc85a)
                                    if embed:
                                        for rankfeed_channel_id in rankfeed_channel_list:
                                            channel = self.bot.get_channel(int(rankfeed_channel_id[0]))
                                            if channel:
                                                await channel.send(embed=embed)
                                            else:
                                                await self.bot.db.execute("DELETE FROM rankfeed_channel_list "
                                                                          "WHERE channel_id = ?",
                                                                          [str(rankfeed_channel_id[0])])
                                                await self.bot.db.commit()
                                                print(f"channel with id {rankfeed_channel_id[0]} no longer exists "
                                                      "so I am removing it from the list")
                                        await self.bot.db.execute("INSERT INTO rankfeed_history VALUES (?)",
                                                                  [str(mapset_id)])
                                        await self.bot.db.commit()
                        print(time.strftime("%X %x %Z") + " | finished rankfeed check")
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

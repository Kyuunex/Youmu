import asyncio
import time
import discord
from discord.ext import commands
from modules import permissions
from modules import wrappers
from modules.connections import osu as osu
import osuembed


class UserEventFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.background_tasks.append(
            self.bot.loop.create_task(self.usereventfeed_background_loop())
        )

    @commands.command(name="uef_track", brief="Track mapping activity of a specified user", description="")
    @commands.check(permissions.is_admin)
    async def track(self, ctx, user_id):
        channel = ctx.channel
        user = await osu.get_user(u=user_id)
        if user:
            async with await self.bot.db.execute("SELECT * FROM usereventfeed_tracklist WHERE osu_id = ?",
                                                 [str(user.id)]) as cursor:
                check_is_already_tracked = await cursor.fetchall()
            if not check_is_already_tracked:
                await self.bot.db.execute("INSERT INTO usereventfeed_tracklist VALUES (?)", [str(user.id)])

            for event in user.events:
                async with await self.bot.db.execute("SELECT * FROM usereventfeed_history WHERE event_id = ?",
                                                     [str(event.id)]) as cursor:
                    check_is_already_in_history = await cursor.fetchall()
                if not check_is_already_in_history:
                    await self.bot.db.execute("INSERT INTO usereventfeed_history VALUES (?, ?, ?)",
                                              [str(user.id), str(event.id), str(int(time.time()))])

            async with await self.bot.db.execute("SELECT * FROM usereventfeed_channels "
                                                 "WHERE channel_id = ? AND osu_id = ?",
                                                 [str(channel.id), str(user.id)]) as cursor:
                check_is_channel_already_tracked = await cursor.fetchall()
            if not check_is_channel_already_tracked:
                await self.bot.db.execute("INSERT INTO usereventfeed_channels VALUES (?, ?)",
                                          [str(user.id), str(channel.id)])
                await channel.send(f"Tracked `{user.name}` in this channel")
            else:
                await channel.send(f"User `{user.name}` is already tracked in this channel")
            await self.bot.db.commit()

    @commands.command(name="uef_untrack", brief="Stop tracking the mapping activity of the specified user",
                      description="")
    @commands.check(permissions.is_admin)
    async def untrack(self, ctx, user_id):
        channel = ctx.channel
        user = await osu.get_user(u=user_id)
        if user:
            user_id = user.id
            user_name = user.name
        else:
            user_name = user_id
        await self.bot.db.execute("DELETE FROM usereventfeed_channels "
                                  "WHERE osu_id = ? AND channel_id = ? ",
                                  [str(user_id), str(channel.id)])
        await self.bot.db.commit()
        await channel.send(f"`{user_name}` is no longer tracked in this channel")

    @commands.command(name="uef_tracklist",
                      brief="Show a list of all users' mapping activity being tracked and where",
                      description="")
    @commands.check(permissions.is_admin)
    async def tracklist(self, ctx, everywhere=None):
        channel = ctx.channel
        async with await self.bot.db.execute("SELECT * FROM usereventfeed_tracklist") as cursor:
            tracklist = await cursor.fetchall()
        if tracklist:
            buffer = ":notepad_spiral: **Track list**\n\n"
            for one_entry in tracklist:
                async with await self.bot.db.execute("SELECT channel_id FROM usereventfeed_channels WHERE osu_id = ?",
                                                     [str(one_entry[0])]) as cursor:
                    destination_list = await cursor.fetchall()
                destination_list_str = ""
                for destination_id in destination_list:
                    destination_list_str += f"<#{destination_id[0]}> "
                if (str(channel.id) in destination_list_str) or everywhere:
                    buffer += f"osu_id: `{one_entry[0]}` | channels: {destination_list_str}\n"
            embed = discord.Embed(color=0xff6781)
            await wrappers.send_large_embed(channel, embed, buffer)

    async def usereventfeed_background_loop(self):
        print("UEF Loop launched!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(10)
                async with await self.bot.db.execute("SELECT osu_id FROM usereventfeed_tracklist") as cursor:
                    tracklist = await cursor.fetchall()
                if tracklist:
                    print(time.strftime("%X %x %Z") + " | performing user event check")
                    for user_id in tracklist:
                        await self.prepare_to_check(user_id[0])
                    print(time.strftime("%X %x %Z") + " | finished user event check")
                await asyncio.sleep(1200)
            except Exception as e:
                print(time.strftime("%X %x %Z"))
                print("in usereventfeed_background_loop")
                print(e)
                await asyncio.sleep(7200)

    async def prepare_to_check(self, user_id):
        user = await osu.get_user(u=user_id, event_days="2")
        if user:
            async with await self.bot.db.execute("SELECT channel_id FROM usereventfeed_channels "
                                                 "WHERE osu_id = ?",
                                                 [str(user.id)]) as cursor:
                channel_list = await cursor.fetchall()
            if channel_list:
                final_channel_list = []
                for channel in channel_list:
                    final_channel_list.append(int(channel[0]))
                await self.check_events(final_channel_list, user)
            else:
                await self.bot.db.execute("DELETE FROM usereventfeed_tracklist WHERE osu_id = ?", [str(user.id)])
                await self.bot.db.commit()
                print(f"{user.id} is not tracked in any channel so I am untracking them")
        else:
            print(f"{user_id} is restricted, untracking everywhere")
            await self.bot.db.execute("DELETE FROM usereventfeed_tracklist WHERE osu_id = ?", [str(user.id)])
            await self.bot.db.execute("DELETE FROM usereventfeed_channels WHERE osu_id = ?", [str(user.id)])
            await self.bot.db.commit()

    async def check_events(self, channel_list, user):
        print(time.strftime("%X %x %Z") + f" | currently checking {user.name}")
        for event in user.events:
            async with await self.bot.db.execute("SELECT event_id FROM usereventfeed_history WHERE event_id = ?",
                                                 [str(event.id)]) as cursor:
                check_is_entry_in_history = await cursor.fetchall()
            if not check_is_entry_in_history:
                await self.bot.db.execute("INSERT INTO usereventfeed_history VALUES (?, ?, ?)",
                                          [str(user.id), str(event.id), str(int(time.time()))])
                await self.bot.db.commit()
                event_color = await self.get_event_color(event.display_text)
                if event_color:
                    result = await osu.get_beatmapset(s=event.beatmapset_id)
                    embed = await osuembed.beatmapset(result, event_color)
                    if embed:
                        display_text = event.display_text.replace("@", "")
                        print(display_text)
                        for channel_id in channel_list:
                            channel = self.bot.get_channel(int(channel_id))
                            await channel.send(display_text, embed=embed)

    async def get_event_color(self, string):
        if "has submitted" in string:
            return 0x2a52b2
        elif "has updated" in string:
            # return 0xb2532a
            return None
        elif "qualified" in string:
            return 0x2ecc71
        elif "has been revived" in string:
            return 0xff93c9
        elif "has been deleted" in string:
            return 0xf2d7d5
        else:
            return None


def setup(bot):
    bot.add_cog(UserEventFeed(bot))

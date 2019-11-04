import asyncio
import time
import discord
from discord.ext import commands
from modules import db
from modules import permissions
from modules.connections import osu as osu
import osuembed


class UserEventFeed(commands.Cog, name="UserEventFeed"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.usereventfeed_background_loop())

    @commands.command(name="uef_track", brief="Track mapping activity of a specified user", description="")
    @commands.check(permissions.is_admin)
    async def track(self, ctx, user_id):
        channel = ctx.channel
        user = await osu.get_user(u=user_id)
        if user:
            if not db.query(["SELECT * FROM usereventfeed_tracklist WHERE osu_id = ?", [str(user.id)]]):
                db.query(["INSERT INTO usereventfeed_tracklist VALUES (?)", [str(user.id)]])

            for event in user.events:
                if not db.query(["SELECT * FROM usereventfeed_history WHERE event_id = ?", [str(event.id)]]):
                    db.query(["INSERT INTO usereventfeed_history VALUES (?, ?, ?)",
                              [str(user.id), str(event.id), str(int(time.time()))]])

            if not db.query(["SELECT * FROM usereventfeed_channels "
                             "WHERE channel_id = ? AND osu_id = ?",
                             [str(channel.id), str(user.id)]]):
                db.query(["INSERT INTO usereventfeed_channels VALUES (?, ?)", [str(user.id), str(channel.id)]])
                await channel.send(content='Tracked `%s` in this channel' % user.name)
            else:
                await channel.send(content='User `%s` is already tracked in this channel' % user.name)

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
        db.query(["DELETE FROM usereventfeed_channels "
                  "WHERE osu_id = ? AND channel_id = ? ",
                  [str(user_id), str(channel.id)]])
        await channel.send(content='`%s` is no longer tracked in this channel' % user_name)

    @commands.command(name="uef_tracklist",
                      brief="Show a list of all users' mapping activity being tracked and where",
                      description="")
    @commands.check(permissions.is_admin)
    async def tracklist(self, ctx, everywhere=None):
        channel = ctx.channel
        tracklist = db.query("SELECT * FROM usereventfeed_tracklist")
        if tracklist:
            for one_entry in tracklist:
                destination_list = db.query(["SELECT channel_id FROM usereventfeed_channels "
                                             "WHERE osu_id = ?",
                                             [str(one_entry[0])]])
                destination_list_str = ""
                for destination_id in destination_list:
                    destination_list_str += ("<#%s> " % (str(destination_id[0])))
                if (str(channel.id) in destination_list_str) or everywhere:
                    await channel.send(content='osu_id: `%s` | channels: %s' % (one_entry[0], destination_list_str))

    async def usereventfeed_background_loop(self):
        print("UEF Loop launched!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(10)
                tracklist = db.query("SELECT osu_id FROM usereventfeed_tracklist")
                if tracklist:
                    print(time.strftime('%X %x %Z') + ' | performing user event check')
                    for user_id in tracklist:
                        await self.prepare_to_check(user_id[0])
                    print(time.strftime('%X %x %Z') + ' | finished user event check')
                await asyncio.sleep(1200)
            except Exception as e:
                print(time.strftime('%X %x %Z'))
                print("in usereventfeed_background_loop")
                print(e)
                await asyncio.sleep(7200)

    async def prepare_to_check(self, user_id):
        user = await osu.get_user(u=user_id, event_days="2")
        if user:
            channel_list = db.query(["SELECT channel_id FROM usereventfeed_channels "
                                     "WHERE osu_id = ?",
                                     [str(user.id)]])
            if channel_list:
                final_channel_list = []
                for channel in channel_list:
                    final_channel_list.append(int(channel[0]))
                await self.check_events(final_channel_list, user)
            else:
                db.query(["DELETE FROM usereventfeed_tracklist WHERE osu_id = ?", [str(user.id)]])
                print("%s is not tracked in any channel so I am untracking them" % (str(user.id)))
        else:
            print("%s is restricted, untracking everywhere" % (str(user_id)))
            db.query(["DELETE FROM usereventfeed_tracklist WHERE osu_id = ?", [str(user.id)]])
            db.query(["DELETE FROM usereventfeed_channels WHERE osu_id = ?", [str(user.id)]])

    async def check_events(self, channel_list, user):
        print(time.strftime('%X %x %Z') + " | currently checking %s" % user.name)
        for event in user.events:
            if not db.query(["SELECT event_id FROM usereventfeed_history WHERE event_id = ?", [str(event.id)]]):
                db.query(["INSERT INTO usereventfeed_history VALUES (?, ?, ?)",
                          [str(user.id), str(event.id), str(int(time.time()))]])
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
        if 'has submitted' in string:
            return 0x2a52b2
        elif 'has updated' in string:
            # return 0xb2532a
            return None
        elif 'qualified' in string:
            return 0x2ecc71
        elif 'has been revived' in string:
            return 0xff93c9
        elif 'has been deleted' in string:
            return 0xf2d7d5
        else:
            return None


def setup(bot):
    bot.add_cog(UserEventFeed(bot))

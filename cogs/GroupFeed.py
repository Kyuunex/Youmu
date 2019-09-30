import json
import time
import asyncio
import discord
from discord.ext import commands
from modules import db
from modules import permissions
from modules.connections import osu as osu
from modules.connections import osuweb as osuweb


class GroupFeed(commands.Cog, name="GroupFeed"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.groupfeed_background_loop())

    @commands.command(name="groupfeed_add", brief="Add a groupfeed in the current channel", description="", pass_context=True)
    async def add(self, ctx):
        if permissions.check(ctx.message.author.id):
            db.query(["INSERT INTO groupfeed_channel_list VALUES (?)", [str(ctx.channel.id)]])
            await ctx.send(":ok_hand:")
        else:
            await ctx.send(embed=permissions.error())

    @commands.command(name="groupfeed_remove", brief="Remove a groupfeed from the current channel", description="", pass_context=True)
    async def remove(self, ctx):
        if permissions.check(ctx.message.author.id):
            db.query(["DELETE FROM groupfeed_channel_list WHERE channel_id = ?", [str(ctx.channel.id)]])
            await ctx.send(":ok_hand:")
        else:
            await ctx.send(embed=permissions.error())

    async def comparelists(self, list1, list2, reverse = False):
        difference = []
        if reverse:
            comparelist1 = list2
            comparelist2 = list1
        else:
            comparelist1 = list1
            comparelist2 = list2
        for i in comparelist1:
            if not i in comparelist2:
                difference.append(i)
        return difference

    async def compare(self, result, lookupvalue, tablename, lookupkey, updatedb = True, reverse = False):
        if not db.query(["SELECT %s FROM %s WHERE %s = ?" % (lookupkey, tablename, lookupkey), [lookupvalue]]):
            db.query(["INSERT INTO %s VALUES (?,?)" % (tablename), [lookupvalue, json.dumps(result)]])
            return None
        else:
            if result:
                localdata = json.loads((db.query(["SELECT contents FROM %s WHERE %s = ?" % (tablename, lookupkey), [lookupvalue]]))[0][0])
                comparison = await self.comparelists(result, localdata, reverse)
                if updatedb:
                    db.query(["UPDATE %s SET contents = ? WHERE %s = ?" % (tablename, lookupkey), [json.dumps(result), lookupvalue]])
                if comparison:
                    return comparison
                else:
                    return None
            else:
                print('in compare groupfeed connection problems?')
                return None

    async def get_changes(self, group_members, group_id):
        changes = []
        userlist = []
        for i in group_members:
            userlist.append(str(i["id"]))
        check_additions = await self.compare(userlist, group_id, 'groupfeed_json_data', 'group_id', False, False)
        check_removals = await self.compare(userlist, group_id, 'groupfeed_json_data', 'group_id', True, True)
        if check_additions:
            for new_user in check_additions:
                changes.append(["added", new_user, "Someone"])
        if check_removals:
            for removed_user in check_removals:
                changes.append(["removed", removed_user, "Someone"])
        return changes

    async def execute_event(self, groupfeed_channel_list, event, group_id, group_name):
        if event[0] == "removed":
            print("groupfeed | %s | removed %s" % (group_name, event[2]))
            description_template = "%s **%s**\nhas been removed from\nthe **%s**"
            color = 0x2c0e6c
        elif event[0] == "added":
            print("groupfeed | %s | added %s" % (group_name, event[2]))
            description_template = "%s **%s**\nhas been added to\nthe **%s**"
            color = 0xffbd0e

        user = await osu.get_user(u=event[1])
        if user:
            flagsign = ":flag_%s:" % (user.country.lower())
            username = user.name
        else:
            flagsign = ":gay_pride_flag:"
            username = event[2]
            #description_template += "\n **%s got restricted btw lol**" % (username)
            description_template = "%s **%s**\n**has gotten restricted lol**\nand has been removed from\nthe **%s**"
            color = 0x9e0000

        what_group = "[%s](%s)" % (group_name, ("https://osu.ppy.sh/groups/%s" % (group_id)))
        what_user = "[%s](https://osu.ppy.sh/users/%s)" % (username, event[1])

        description = description_template % (flagsign, what_user, what_group)

        embed = await self.group_member(event[1], description, color)
        for groupfeed_channel_id in groupfeed_channel_list:
            channel = self.bot.get_channel(int(groupfeed_channel_id[0]))
            if channel:
                await channel.send(embed=embed)

    async def check_group(self, groupfeed_channel_list, group_id, group_name):
        group_members = await osuweb.groups(group_id)
        if group_members:
            events = await self.get_changes(group_members, group_id)
            if events:
                for event in events:
                    await self.execute_event(groupfeed_channel_list, event, group_id, group_name)
        else:
            print('groupfeed connection problems?')
            return None

    async def groupfeed_background_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(5)
                groupfeed_channel_list = db.query("SELECT channel_id FROM groupfeed_channel_list")
                if groupfeed_channel_list:
                    print(time.strftime('%X %x %Z')+' | performing groupfeed check')
                    await self.check_group(groupfeed_channel_list, "7", "Nomination Assessment Team")
                    await asyncio.sleep(120)
                    await self.check_group(groupfeed_channel_list, "28", "Beatmap Nominators")
                    await asyncio.sleep(5)
                    await self.check_group(groupfeed_channel_list, "32", "Beatmap Nominators (Probationary)")
                    await asyncio.sleep(120)
                    await self.check_group(groupfeed_channel_list, "4", "Global Moderation Team")
                    await asyncio.sleep(120)
                    await self.check_group(groupfeed_channel_list, "11", "Developers")
                    await asyncio.sleep(120)
                    await self.check_group(groupfeed_channel_list, "16", "osu! Alumni")
                    await asyncio.sleep(120)
                    await self.check_group(groupfeed_channel_list, "22", "Support Team")
                    print(time.strftime('%X %x %Z')+' | finished groupfeed check')
                await asyncio.sleep(1600)
            except Exception as e:
                print(time.strftime('%X %x %Z'))
                print("in groupfeed_background_loop")
                print(e)
                await asyncio.sleep(3600)

    async def group_member(self, user_id, description, color):
        embed = discord.Embed(
            description=description,
            color=color
        )
        embed.set_thumbnail(
            url='https://a.ppy.sh/%s' % (user_id)
        )
        return embed

def setup(bot):
    bot.add_cog(GroupFeed(bot))
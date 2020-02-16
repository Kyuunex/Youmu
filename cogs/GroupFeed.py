import json
import time
import asyncio
import discord
from discord.ext import commands
from modules import db
from modules import permissions
from modules.connections import osu as osu
from modules.connections import osuweb as osuweb


class GroupFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.background_tasks.append(
            self.bot.loop.create_task(self.groupfeed_background_loop())
        )

    @commands.command(name="groupfeed_add", brief="Add a groupfeed in the current channel", description="")
    @commands.check(permissions.is_admin)
    async def add(self, ctx):
        await self.bot.db.execute("INSERT INTO groupfeed_channel_list VALUES (?)", [str(ctx.channel.id)])
        await self.bot.db.commit()
        await ctx.send(":ok_hand:")

    @commands.command(name="groupfeed_remove", brief="Remove a groupfeed from the current channel", description="")
    @commands.check(permissions.is_admin)
    async def remove(self, ctx):
        await self.bot.db.execute("DELETE FROM groupfeed_channel_list WHERE channel_id = ?", [str(ctx.channel.id)])
        await self.bot.db.commit()
        await ctx.send(":ok_hand:")

    async def compare_lists(self, list1, list2, reverse=False):
        difference = []
        if reverse:
            compare_list_1 = list2
            compare_list_2 = list1
        else:
            compare_list_1 = list1
            compare_list_2 = list2
        for i in compare_list_1:
            if not i in compare_list_2:
                difference.append(i)
        return difference

    async def compare(self, result, lookup_value, table_name, lookup_key, update_db=True, reverse=False):
        async with await self.bot.db.execute(f"SELECT {lookup_key} FROM {table_name} WHERE {lookup_key} = ?",
                                             [lookup_value]) as cursor:
            idk1 = await cursor.fetchall()
        if not idk1:
            await self.bot.db.execute(f"INSERT INTO {table_name} VALUES (?,?)", [lookup_value, json.dumps(result)])
            await self.bot.db.commit()
            return None
        else:
            if result:
                async with await self.bot.db.execute(f"SELECT contents FROM {table_name} "
                                                     f"WHERE {lookup_key} = ?",
                                                     [lookup_value]) as cursor:
                    idk2 = await cursor.fetchall()
                local_data = json.loads(idk2[0][0])
                comparison = await self.compare_lists(result, local_data, reverse)
                if update_db:
                    await self.bot.db.execute(f"UPDATE {table_name} SET contents = ? WHERE {lookup_key} = ?",
                                              [json.dumps(result), lookup_value])
                    await self.bot.db.commit()
                if comparison:
                    return comparison
                else:
                    return None
            else:
                print("in compare groupfeed connection problems?")
                return None

    async def get_changes(self, group_members, group_id):
        changes = []
        user_list = []
        for i in group_members:
            user_list.append(str(i["id"]))
        check_additions = await self.compare(user_list, group_id, "groupfeed_json_data", "group_id", False, False)
        check_removals = await self.compare(user_list, group_id, "groupfeed_json_data", "group_id", True, True)
        if check_additions:
            for new_user in check_additions:
                changes.append(["added", new_user, "Someone"])
        if check_removals:
            for removed_user in check_removals:
                changes.append(["removed", removed_user, "Someone"])
        return changes

    async def execute_event(self, groupfeed_channel_list, event, group_id, group_name):
        if event[0] == "removed":
            print(f"groupfeed | {group_name} | removed {event[2]}")
            description_template = "%s **%s**\nhas been removed from\nthe **%s**"
            color = 0x2c0e6c
        elif event[0] == "added":
            print(f"groupfeed | {group_name} | added {event[2]}")
            description_template = "%s **%s**\nhas been added to\nthe **%s**"
            color = 0xffbd0e

        user = await osu.get_user(u=event[1])
        if user:
            flag_sign = f":flag_{user.country.lower()}:"
            username = user.name
        else:
            flag_sign = ":gay_pride_flag:"
            username = event[2]
            # description_template += "\n **%s got restricted btw lol**" % username
            description_template = "%s **%s**\n**has gotten restricted lol**\nand has been removed from\nthe **%s**"
            color = 0x9e0000

        what_group = f"[{group_name}](https://osu.ppy.sh/groups/{group_id})"
        what_user = f"[{username}](https://osu.ppy.sh/users/{event[1]})"

        description = description_template % (flag_sign, what_user, what_group)

        embed = await self.group_member(event[1], description, color)
        for groupfeed_channel_id in groupfeed_channel_list:
            channel = self.bot.get_channel(int(groupfeed_channel_id[0]))
            if channel:
                await channel.send(embed=embed)

    async def check_group(self, groupfeed_channel_list, group_id, group_name):
        group_members = await osuweb.get_group_members(group_id)
        if group_members:
            events = await self.get_changes(group_members, group_id)
            if events:
                for event in events:
                    await self.execute_event(groupfeed_channel_list, event, group_id, group_name)
        else:
            print("groupfeed connection problems?")
            return None

    async def groupfeed_background_loop(self):
        print("GroupFeed Loop launched!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(5)
                async with await self.bot.db.execute("SELECT channel_id FROM groupfeed_channel_list") as cursor:
                    groupfeed_channel_list = await cursor.fetchall()
                if groupfeed_channel_list:
                    print(time.strftime("%X %x %Z") + " | performing groupfeed check")
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
                    print(time.strftime("%X %x %Z") + " | finished groupfeed check")
                await asyncio.sleep(1600)
            except Exception as e:
                print(time.strftime("%X %x %Z"))
                print("in groupfeed_background_loop")
                print(e)
                await asyncio.sleep(3600)

    async def group_member(self, user_id, description, color):
        embed = discord.Embed(
            description=description,
            color=color
        )
        embed.set_thumbnail(
            url=f"https://a.ppy.sh/{user_id}"
        )
        return embed


def setup(bot):
    bot.add_cog(GroupFeed(bot))

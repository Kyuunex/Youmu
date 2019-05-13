#!/usr/bin/env python3

import discord
import asyncio
from discord.ext import commands
import os

from modules import permissions
from modules import osuapi
from modules import osuembed
from modules import osuwebapipreview
from modules import dbhandler

from modules import groupfeed
from modules import rankfeed
from modules import usereventfeed

client = commands.Bot(command_prefix='.')
#client.remove_command('help')
appversion = "b20190513"


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    if not os.path.exists('data/maindb.sqlite3'):
        appinfo = await client.application_info()
        await dbhandler.query("CREATE TABLE config (setting, parent, value, flag)")
        await dbhandler.query("CREATE TABLE admins (user_id, permissions)")
        await dbhandler.query("CREATE TABLE rankfeed_channel_list (channel_id)")
        await dbhandler.query("CREATE TABLE rankfeed_ranked_maps (mapset_id)")
        await dbhandler.query("CREATE TABLE user_event_feed_track_list (osu_id, channel_list)")
        await dbhandler.query("CREATE TABLE user_event_feed_json_data (osu_id, contents)")
        await dbhandler.query("CREATE TABLE groupfeed_channel_list (channel_id)")
        await dbhandler.query("CREATE TABLE groupfeed_json_data (feed_type, contents)")
        await dbhandler.query(["INSERT INTO admins VALUES (?, ?)", [str(appinfo.owner.id), "1"]])


@client.command(name="adminlist", brief="Show bot admin list.", description="", pass_context=True)
async def adminlist(ctx):
    await ctx.send(embed=await permissions.adminlist())


@client.command(name="makeadmin", brief="Add a user to bot admin list.", description="", pass_context=True)
async def makeadmin(ctx, user_id: str):
    if await permissions.checkowner(ctx.message.author.id):
        await dbhandler.query(["INSERT INTO admins VALUES (?, ?)", [str(user_id), "0"]])
        await ctx.send(":ok_hand:")
    else:
        await ctx.send(embed=await permissions.ownererror())


@client.command(name="restart", brief="Restart the bot.", description="", pass_context=True)
async def restart(ctx):
    if await permissions.check(ctx.message.author.id):
        await ctx.send("Restarting")
        quit()
    else:
        await ctx.send(embed=await permissions.error())


@client.command(name="gitpull", brief="Update the bot.", description="Grabs the latest version from GitHub.", pass_context=True)
async def gitpull(ctx):
    if await permissions.check(ctx.message.author.id):
        await ctx.send("Fetching the latest version from the repository and updating from version %s" % (appversion))
        os.system('git pull')
        quit()
        # exit()
    else:
        await ctx.send(embed=await permissions.error())


@client.command(name="sql", brief="Executre an SQL query.", description="", pass_context=True)
async def sql(ctx, *, query):
    if await permissions.checkowner(ctx.message.author.id):
        if len(query) > 0:
            response = await dbhandler.query(query)
            await ctx.send(response)
    else:
        await ctx.send(embed=await permissions.ownererror())


@client.command(name="leave", brief="Leave the current guild.", description="", pass_context=True)
async def leave(ctx):
    if await permissions.checkowner(ctx.message.author.id):
        try:
            await ctx.guild.leave()
        except Exception as e:
            await ctx.send(e)
    else:
        await ctx.send(embed=await permissions.ownererror())


@client.command(name="mapset", brief="Show mapset info.", description="", pass_context=True)
async def mapset(ctx, mapset_id: str, text: str = None):
    if await permissions.check(ctx.message.author.id):
        embed = await osuembed.mapset(await osuapi.get_beatmaps(mapset_id))
        if embed:
            await ctx.send(content=text, embed=embed)
            # await ctx.message.delete()
        else:
            await ctx.send(content='`No mapset found with that ID`')
    else:
        await ctx.send(embed=await permissions.error())


@client.command(name="user", brief="Show osu user info.", description="", pass_context=True)
async def user(ctx, *, username):
    embed = await osuembed.osuprofile(await osuapi.get_user(username))
    if embed:
        await ctx.send(embed=embed)
        # await ctx.message.delete()
    else:
        await ctx.send(content='`No user found with that username`')


@client.command(name="groupfeed", brief="Add/remove a groupfeed in the current channel.", description="", pass_context=True)
async def cgroupfeed(ctx, action):
    if await permissions.check(ctx.message.author.id):
        if action == "add":
            await dbhandler.query(["INSERT INTO groupfeed_channel_list VALUES (?)", [str(ctx.channel.id)]])
            await ctx.send(":ok_hand:")
        elif action == "remove":
            await ctx.send("placeholder")
            #TODO: Add groupfeed remove
    else:
        await ctx.send(embed=await permissions.error())


@client.command(name="rankfeed", brief="Add/remove a rankfeed in the current channel.", description="", pass_context=True)
async def crankfeed(ctx, action):
    if await permissions.check(ctx.message.author.id):
        if action == "add":
            await dbhandler.query(["INSERT INTO rankfeed_channel_list VALUES (?)", [str(ctx.channel.id)]])
            await ctx.send(":ok_hand:")
        elif action == "remove":
            await ctx.send("placeholder")
            #TODO: Add rankfeed remove
    else:
        await ctx.send(embed=await permissions.error())


@client.command(name="usereventfeed", brief="Track/untrack mapping activity of a specified user.", description="", pass_context=True)
async def cusereventfeed(ctx, action, osu_id, channels):
    if await permissions.check(ctx.message.author.id):
        if action == "track":
            await dbhandler.query(["INSERT INTO user_event_feed_track_list VALUES (?,?)", [osu_id, channels]])
            await ctx.send(":ok_hand:")
        elif action == "untrack":
            await ctx.send("placeholder")
            #TODO: Add usereventfeed remove
            #TODO: implement csv
    else:
        await ctx.send(embed=await permissions.error())


async def groupfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await groupfeed.main(client)


async def rankfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await rankfeed.main(client)


async def usereventfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await usereventfeed.main(client)


client.loop.create_task(groupfeed_background_loop())
client.loop.create_task(rankfeed_background_loop())
client.loop.create_task(usereventfeed_background_loop())
client.run(open("data/token.txt", "r+").read(), bot=True)

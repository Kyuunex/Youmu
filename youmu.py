#!/usr/bin/env python3

import discord
import asyncio
from discord.ext import commands
import os

from modules import permissions
from osuembed import osuembed
from modules import db
from modules import groupfeed
from modules import rankfeed
from modules import rssfeed
from modules import usereventfeed

from modules.connections import osu as osu
from modules.connections import database_file as database_file
from modules.connections import bot_token as bot_token

client = commands.Bot(command_prefix='.', description='Youmu teaches you how to be a bot master.')
# client.remove_command('help')
appversion = "b20190812"

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
    db.query("CREATE TABLE usereventfeed_history (osu_id, event_id)")

    db.query("CREATE TABLE groupfeed_channel_list (channel_id)")
    db.query("CREATE TABLE groupfeed_members (osu_id, username, group_id)")
    db.query("CREATE TABLE groupfeed_json_data (group_id, contents)")


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    if not db.query("SELECT * FROM admins"):
        appinfo = await client.application_info()
        db.query(["INSERT INTO admins VALUES (?, ?)", [str(appinfo.owner.id), "1"]])
        print("Added %s to admin list" % (appinfo.owner.name))


@client.command(name="adminlist", brief="Show bot admin list", description="", pass_context=True)
async def adminlist(ctx):
    await ctx.send(embed=permissions.get_admin_list())


@client.command(name="makeadmin", brief="Add a user to bot admin list", description="", pass_context=True)
async def makeadmin(ctx, user_id: str):
    if permissions.check_owner(ctx.message.author.id):
        db.query(["INSERT INTO admins VALUES (?, ?)", [str(user_id), "0"]])
        await ctx.send(":ok_hand:")
    else:
        await ctx.send(embed=permissions.error_owner())


@client.command(name="restart", brief="Restart the bot", description="", pass_context=True)
async def restart(ctx):
    if permissions.check(ctx.message.author.id):
        await ctx.send("Restarting")
        quit()
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="update", brief="Update the bot", description="it just does git pull", pass_context=True)
async def update(ctx):
    if permissions.check(ctx.message.author.id):
        await ctx.send("Updating.")
        os.system('git pull')
        quit()
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="sql", brief="Executre an SQL query", description="", pass_context=True)
async def sql(ctx, *, query):
    if permissions.check_owner(ctx.message.author.id):
        if len(query) > 0:
            response = db.query(query)
            await ctx.send(response)
    else:
        await ctx.send(embed=permissions.error_owner())


@client.command(name="leaveguild", brief="Make the bot leave the current guild", description="", pass_context=True)
async def leave(ctx):
    if await permissions.check_owner(ctx.message.author.id):
        try:
            await ctx.guild.leave()
        except Exception as e:
            await ctx.send(e)
    else:
        await ctx.send(embed=await permissions.error_owner())


@client.command(name="mapset", brief="Show mapset info", description="", pass_context=True)
async def mapset(ctx, mapset_id: str):
    result = await osu.get_beatmapset(s=mapset_id)
    embed = await osuembed.beatmapset(result)
    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send(content='`No mapset found with that ID`')


@client.command(name="user", brief="Show osu user info", description="", pass_context=True)
async def user(ctx, *, username):
    result = await osu.get_user(u=username)
    embed = await osuembed.user(result)
    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send(content='`No user found with that username`')


@client.command(name="rankfeedadd", brief="Add a rankfeed in the current channel", description="", pass_context=True)
async def rankfeed_add(ctx):
    if permissions.check(ctx.message.author.id):
        await rankfeed.add(ctx.channel)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="rankfeedremove", brief="Remove a rankfeed from the current channel", description="", pass_context=True)
async def rankfeed_remove(ctx):
    if permissions.check(ctx.message.author.id):
        await rankfeed.remove(ctx.channel)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="groupfeedadd", brief="Add a groupfeed in the current channel", description="", pass_context=True)
async def groupfeed_add(ctx):
    if permissions.check(ctx.message.author.id):
        db.query(["INSERT INTO groupfeed_channel_list VALUES (?)", [str(ctx.channel.id)]])
        await ctx.send(":ok_hand:")
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="groupfeedremove", brief="Remove a groupfeed from the current channel", description="", pass_context=True)
async def groupfeed_remove(ctx):
    if permissions.check(ctx.message.author.id):
        db.query(["DELETE FROM groupfeed_channel_list WHERE channel_id = ?", [str(ctx.channel.id)]])
        await ctx.send(":ok_hand:")
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="ueftrack", brief="Track mapping activity of a specified user", description="", pass_context=True)
async def usereventfeed_track(ctx, user_id):
    if permissions.check(ctx.message.author.id):
        await usereventfeed.track(ctx.channel, user_id)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="uefuntrack", brief="Stop tracking the mapping activity of the specified user", description="", pass_context=True)
async def usereventfeed_untrack(ctx, user_id):
    if permissions.check(ctx.message.author.id):
        await usereventfeed.untrack(ctx.channel, user_id)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="ueftracklist", brief="Show a list of all users' mapping activity being tracked and where", description="", pass_context=True)
async def usereventfeed_tracklist(ctx, everywhere = None):
    if permissions.check(ctx.message.author.id):
        await usereventfeed.print_tracklist(ctx.channel, everywhere)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="rssadd", brief="Subscribe to an RSS feed in the current channel", description="", pass_context=True)
async def rss_add(ctx, *, url):
    if permissions.check(ctx.message.author.id):
        await rssfeed.add(ctx.channel, url)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="rssremove", brief="Unsubscribe to an RSS feed in the current channel", description="", pass_context=True)
async def rss_remove(ctx, *, url):
    if permissions.check(ctx.message.author.id):
        await rssfeed.remove(ctx.channel, url)
    else:
        await ctx.send(embed=permissions.error())


@client.command(name="rsslist", brief="Show a list of all RSS feeds being tracked", description="", pass_context=True)
async def rss_tracklist(ctx, everywhere = None):
    if permissions.check(ctx.message.author.id):
        await rssfeed.print_tracklist(ctx.channel, everywhere)
    else:
        await ctx.send(embed=permissions.error())


async def rankfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await rankfeed.main(client)


async def groupfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await groupfeed.main(client)


async def usereventfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await usereventfeed.main(client)


async def rssfeed_background_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        await rssfeed.main(client)

client.loop.create_task(groupfeed_background_loop())
client.loop.create_task(rankfeed_background_loop())
client.loop.create_task(usereventfeed_background_loop())
client.loop.create_task(rssfeed_background_loop())
client.run(bot_token)

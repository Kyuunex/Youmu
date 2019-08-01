import feedparser
import aiohttp
import time
import asyncio
import discord
import re
from html import unescape

from modules import dbhandler


async def rss_entry_embed(rss_object, color=0xbd3661):
    try:
        if rss_object:
            embed = discord.Embed(
                title=rss_object['title'],
                url=rss_object['link'],
                description=(unescape(re.sub('<[^<]+?>', '', rss_object['summary']))).replace("@", ""),
                color=int(color)
            )
            embed.set_author(
                name=rss_object['author']
            )
            # embed.set_thumbnail(
            #     url=''
            # )
            embed.set_footer(
                text=rss_object['published']
            )
            return embed
        else:
            return None
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in rssfeed.rss_entry_embed")
        print(e)
        return None


async def fetch(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                httpcontents = (await response.text())
                if len(httpcontents) > 4:
                    return httpcontents
                else:
                    return None
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in rankfeed.fetch")
        print(e)
        return None


async def main(client):
    await asyncio.sleep(10)
    rssfeed_entries = await dbhandler.query("SELECT * FROM rssfeed_track_list")
    if rssfeed_entries:
        for rssfeed_entry in rssfeed_entries:
            url = rssfeed_entry[0]
            print("checking %s" % (url))
            online_entries = (feedparser.parse(await fetch(url)))['entries']
            for one_entry in online_entries:
                entry_id = one_entry['id']
                if not await dbhandler.query(["SELECT * FROM rssfeed_posted_entries WHERE url = ? AND posted_entry = ?", [str(url), str(entry_id)]]):
                    for one_channel in rssfeed_entry[1].split(","):
                        channel = client.get_channel(int(one_channel))
                        await channel.send(embed=await rss_entry_embed(one_entry))
                    await dbhandler.query(["INSERT INTO rssfeed_posted_entries VALUES (?, ?)", [str(url), str(entry_id)]])
        print(time.strftime('%X %x %Z'))
        print("finished rss check")
    await asyncio.sleep(1200)


async def add(client, ctx, url):
    online_entries = (feedparser.parse(await fetch(url)))['entries']
    if online_entries:
        trackinfo = await dbhandler.query(["SELECT * FROM rssfeed_track_list WHERE url = ?", [str(url)]])
        if not trackinfo:
            await dbhandler.query(["INSERT INTO rssfeed_track_list VALUES (?, ?)", [url, str(ctx.channel.id)]])
            for one_entry in online_entries:
                entry_id = one_entry['id']
                if not await dbhandler.query(["SELECT * FROM rssfeed_posted_entries WHERE url = ? AND posted_entry = ?", [str(url), str(entry_id)]]):
                    await dbhandler.query(["INSERT INTO rssfeed_posted_entries VALUES (?, ?)", [str(url), str(entry_id)]])
            await ctx.send("added")
        else:
            newcsv = await csv_add(trackinfo[0][1], str(ctx.channel.id))
            await dbhandler.query(["UPDATE rssfeed_track_list SET channel_id = ? WHERE url = ?", [newcsv, str(url)]])
            await ctx.send("added")


async def remove(client, ctx, url):
    trackinfo = await dbhandler.query(["SELECT * FROM rssfeed_track_list WHERE url = ?", [str(url)]])
    if trackinfo:
        newcsv = await csv_remove(trackinfo[0][1], str(ctx.channel.id))
        if newcsv:
            await dbhandler.query(["UPDATE rssfeed_track_list SET channel_id = ? WHERE url = ?", [newcsv, str(url)]])
        else:
            await dbhandler.query(["DELETE FROM rssfeed_track_list WHERE url = ?", [str(url)]])
        await ctx.send("don")


async def tracklist(ctx, everywhere=None):
    tracklist = await dbhandler.query("SELECT * FROM rssfeed_track_list")
    if tracklist:
        for oneentry in tracklist:
            if (str(ctx.channel.id) in oneentry[1]) or (everywhere):
                channellist = await csv_wrap_entries(oneentry[1])
                await ctx.send(content='channels: %s | url: %s' % (channellist, oneentry[0]))


async def csv_add(csv_current_entries, csv_new_entries):
    entry_list = csv_current_entries.split(",")
    for one_new_entry in str(csv_new_entries).split(","):
        if not one_new_entry in entry_list:
            entry_list.append(one_new_entry)
    return ",".join(entry_list)


async def csv_remove(csv_current_entries, csv_new_entries):
    entry_list = csv_current_entries.split(",")
    for one_new_entry in str(csv_new_entries).split(","):
        if one_new_entry in entry_list:
            entry_list.remove(one_new_entry)
    return ",".join(entry_list)


async def csv_wrap_entries(csv_current_entries, wrapper="<#%s>"):
    entry_string = ""
    for one_entry in csv_current_entries.split(","):
        entry_string += ((wrapper+" ") % (one_entry))
    return entry_string

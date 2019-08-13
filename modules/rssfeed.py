import feedparser
import aiohttp
import time
import asyncio
import discord
import re
from html import unescape

from modules import db


async def rss_entry_embed(rss_object, color=0xbd3661):
    if rss_object:
        print(rss_object)
        embed = discord.Embed(
            title=rss_object['title'],
            url=rss_object['link'],
            description=(unescape(re.sub('<[^<]+?>', '', rss_object['summary']))).replace("@", ""),
            color=int(color)
        )
        if 'author' in rss_object:
            embed.set_author(
                name=rss_object['author']
            )
        embed.set_footer(
            text=rss_object['published']
        )
        return embed
    else:
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
    rssfeed_entries = db.query("SELECT url FROM rssfeed_tracklist")
    if rssfeed_entries:
        for rssfeed_entry in rssfeed_entries:
            url = rssfeed_entry[0]
            channel_list = db.query(["SELECT channel_id FROM rssfeed_channels WHERE url = ?", [str(url)]])
            if channel_list:
                print("checking %s" % (url))
                online_entries = (feedparser.parse(await fetch(url)))['entries']
                for one_entry in online_entries:
                    entry_id = one_entry['id']
                    if not db.query(["SELECT * FROM rssfeed_history WHERE url = ? AND entry_id = ?", [str(url), str(entry_id)]]):
                        for one_channel in channel_list:
                            channel = client.get_channel(int(one_channel[0]))
                            await channel.send(embed=await rss_entry_embed(one_entry))
                        #db.query(["INSERT INTO rssfeed_history VALUES (?, ?)", [str(url), str(entry_id)]])
            else:
                db.query(["DELETE FROM rssfeed_tracklist WHERE url = ?", [str(url)]])
                print("%s is not tracked in any channel so I am untracking it" % (str(url)))
        print(time.strftime('%X %x %Z'))
        print("finished rss check")
    await asyncio.sleep(1200)


async def add(channel, url):
    online_entries = (feedparser.parse(await fetch(url)))['entries']
    if online_entries:
        if not db.query(["SELECT * FROM rssfeed_tracklist WHERE url = ?", [str(url)]]):
            db.query(["INSERT INTO rssfeed_tracklist VALUES (?)", [str(url)]])

        for one_entry in online_entries:
            entry_id = one_entry['id']
            if not db.query(["SELECT * FROM rssfeed_history WHERE url = ? AND entry_id = ?", [str(url), str(entry_id)]]):
                db.query(["INSERT INTO rssfeed_history VALUES (?, ?)", [str(url), str(entry_id)]])

        if not db.query(["SELECT * FROM rssfeed_channels WHERE channel_id = ? AND url = ?", [str(channel.id), str(url)]]):
            db.query(["INSERT INTO rssfeed_channels VALUES (?, ?)", [str(url), str(channel.id)]])
            await channel.send(content='Feed `%s` is now tracked in this channel' % (url))
        else:
            await channel.send(content='Feed `%s` is already tracked in this channel' % (url))


async def remove(channel, url):
    db.query(["DELETE FROM rssfeed_channels WHERE url = ? AND channel_id = ? ", [str(url), str(channel.id)]])
    await channel.send(content='Feed `%s` is no longer tracked in this channel' % (url))


async def print_tracklist(channel, everywhere = None):
    tracklist = db.query("SELECT * FROM rssfeed_tracklist")
    if tracklist:
        for one_entry in tracklist:
            destination_list = db.query(["SELECT channel_id FROM rssfeed_channels WHERE url = ?", [str(one_entry[0])]])
            destination_list_str = ""
            for destination_id in destination_list:
                destination_list_str += ("<#%s> " % (str(destination_id[0])))
            if (str(channel.id) in destination_list_str) or (everywhere):
                await channel.send(content='url: `%s` | channels: %s' % (one_entry[0], destination_list_str))

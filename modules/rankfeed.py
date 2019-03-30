import feedparser
import aiohttp
import time
import asyncio

from modules import osuapi
from modules import osuembed
from modules import dbhandler


async def fetch():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://osu.ppy.sh/feed/ranked/") as response:
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
    try:
        await asyncio.sleep(10)
        rankfeedchannellist = await dbhandler.query("SELECT channelid FROM rankfeed_channellist")
        if rankfeedchannellist:
            mapfeed = feedparser.parse(await fetch())
            for maplist in mapfeed['entries']:
                mapsetid = maplist['link'].split('http://osu.ppy.sh/s/')[1]
                lookupmapindb = await dbhandler.query(["SELECT mapsetid FROM rankfeed_rankedmaps WHERE mapsetid = ?", [str(mapsetid), ]])
                if not lookupmapindb:
                    embed = await osuembed.mapset(await osuapi.get_beatmaps(mapsetid))
                    if embed:
                        for rankfeedchannelid in rankfeedchannellist:
                            channel = client.get_channel(int(rankfeedchannelid[0]))
                            await channel.send(embed=embed)
                        await dbhandler.query(["INSERT INTO rankfeed_rankedmaps VALUES (?)", [str(mapsetid)]])
        await asyncio.sleep(1600)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in rankfeed_background_loop")
        print(e)
        await asyncio.sleep(3600)

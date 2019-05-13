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
        rankfeedchannel_list = await dbhandler.query("SELECT channel_id FROM rankfeed_channel_list")
        if rankfeedchannel_list:
            mapfeed = feedparser.parse(await fetch())
            for maplist in mapfeed['entries']:
                mapset_id = maplist['link'].split('http://osu.ppy.sh/s/')[1]
                lookupmapindb = await dbhandler.query(["SELECT mapset_id FROM rankfeed_ranked_maps WHERE mapset_id = ?", [str(mapset_id), ]])
                if not lookupmapindb:
                    embed = await osuembed.mapset(await osuapi.get_beatmaps(mapset_id))
                    if embed:
                        for rankfeedchannel_id in rankfeedchannel_list:
                            channel = client.get_channel(int(rankfeedchannel_id[0]))
                            await channel.send(embed=embed)
                        await dbhandler.query(["INSERT INTO rankfeed_ranked_maps VALUES (?)", [str(mapset_id)]])
        await asyncio.sleep(1600)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in rankfeed_background_loop")
        print(e)
        await asyncio.sleep(3600)

import discord


async def group_member(thumbnail_url, description, color):
    embed = discord.Embed(
        description=description,
        color=color
    )
    embed.set_thumbnail(
        url=thumbnail_url
    )
    return embed

from redbot.core import commands

from .rss import RSS


async def setup(bot: commands.Bot):
    n = RSS(bot)
    await bot.add_cog(n)

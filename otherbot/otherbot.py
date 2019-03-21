import discord

import asyncio

from redbot.core import commands, checks, Config
from redbot.core.utils.predicates import MessagePredicate

from typing import Optional

default_guild = {
    "ping": None,
    "reporting": None,
    "watching": [],
    "online_notify": False,
    "sent_online": False,
}


class Otherbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2730321001, force_registration=True)
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def otherbot(self, ctx):
        """Otherbot configuration options."""
        pass

    @otherbot.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel to report in."""
        await self.config.guild(ctx.guild).reporting.set(channel.id)
        await ctx.send(f"Reporting channel set to: {channel.mention}.")

    @otherbot.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def pingrole(self, ctx, role_name: discord.Role = None):
        """Sets the role to use for pinging. Leave blank to reset it."""
        if not role_name:
            await self.config.guild(ctx.guild).ping.set(None)
            return await ctx.send("Ping role cleared.")
        await self.config.guild(ctx.guild).ping.set(role_name.id)
        pingrole_id = await self.config.guild(ctx.guild).ping()
        pingrole_obj = discord.utils.get(ctx.guild.roles, id=pingrole_id)
        await ctx.send(f"Ping role set to: {pingrole_obj.name}.")

    @otherbot.group()
    @checks.admin_or_permissions(manage_roles=True)
    async def watching(self, ctx):
        """Watching commands."""
        pass

    @watching.command()
    @checks.admin_or_permissions(manage_roles=True)  # TODO : Check if a bot is already stored, then delete it or sent msg to say it already stored
    async def add(self, ctx, online: Optional[bool] = False, bot_user: discord.Member = None):
        """
        Add a bot to watch when it goes offline.

        <online> : Set `True` if you want alerts when bot is back online. Default to False.
        You can change it later by using [p]otherbot watching online command.
        Note : Online alerts is for all bots configured per servers.
        """
        data = await self.config.guild(ctx.guild).all()
        online_notify = await self.config.guild(ctx.guild).online_notify()
        if online == True:
            await self.config.guild(ctx.guild).online_notify.set(True)
        else:
            await self.config.guild(ctx.guild).online_notify.set(False)
        if not bot_user:
            return await ctx.send_help()
        if not bot_user.bot:
            return await ctx.send("User is not a bot.")
        async with self.config.guild(ctx.guild).watching() as watch_list:
            watch_list.append(bot_user.id)
        await ctx.send(f"Now watching: {bot_user.mention}.\nOnline alerts: {online_notify}")
        if not data["reporting"]:
            await self.config.guild(ctx.guild).reporting.set(ctx.message.channel.id)
            await ctx.send(
                f"Reporting channel set to: {ctx.message.channel.mention}. Use `{ctx.prefix}otherbot channel` to change this."
            )

    @watching.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def online(self, ctx, true_or_false: bool = False):
        """Choose if you want alerts when bot is back online."""
        if true_or_false == True:
            await self.config.guild(ctx.guild).online_notify.set(True)
            return await ctx.send("Online alerts sets to `True`.")
        else:
            await self.config.guild(ctx.guild).online_notify.set(False)
            return await ctx.send("Online alerts sets to `False`.")

    @watching.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def clear(self, ctx):
        """Clear existing bots watching."""
        await ctx.send("Are you sure to clear all watched bots ?")
        
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Response timed out.")
        else:
            if pred.result is True:
                await self.config.guild(ctx.guild).watching.clear()
                return await ctx.send("Successfully cleared watched bots.")
            else:
                return await ctx.send("Clear cancelled.")

    @watching.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def list(self, ctx):
        """List existing bots."""
        data = await self.config.guild(ctx.guild).all()
        online_notify = await self.config.guild(ctx.guild).online_notify()
        msg = f"```Online alerts: {online_notify}\n"
        msg += "Watching these bots:\n\n"
        if not data["watching"]:
            msg += "None.```"
        for saved_bot_id in data["watching"]:
            bot_user = await self.bot.get_user_info(saved_bot_id)
            if len(bot_user.name) > 16:
                bot_name = f"{bot_user.name:16}...#{bot_user.discriminator}"
            else:
                bot_name = f"{bot_user.name}#{bot_user.discriminator}"
            msg += f"{bot_name:24} ({bot_user.id})\n"
        msg += "```"
        return await ctx.send(msg)

    async def on_member_update(self, before, after):
        data = await self.config.guild(after.guild).all()
        channel_object = self.bot.get_channel(data["reporting"])
        if after.status == discord.Status.offline and (after.id in data["watching"]):
            await self.config.guild(after.guild).sent_online.set(False)
            if not data["ping"]:
                await channel_object.send(f"{after.mention} is offline. \N{LARGE RED CIRCLE}")
            else:
                await channel_object.send(
                    f'<@&{data["ping"]}>, {after.mention} is offline. \N{LARGE RED CIRCLE}'
                )
        elif (
            data["online_notify"]
            and after.status == discord.Status.online
            and (after.id in data["watching"])
        ):
            await self.config.guild(after.guild).sent_online.set(True)
            if not data["sent_online"]:
                if not data["ping"]:
                    await channel_object.send(
                        f"{after.mention} is back online. \N{WHITE HEAVY CHECK MARK}"
                    )
                else:
                    await channel_object.send(
                        f'<@&{data["ping"]}>, {after.mention} is back online. \N{WHITE HEAVY CHECK MARK}'
                    )
            else:
                pass
        else:
            pass

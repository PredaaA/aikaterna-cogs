import discord

from redbot.core import commands, checks, Config

from datetime import datetime


class Otherbot(commands.Cog):
    __author__ = ["aikaterna", "Predä"]
    __version__ = "0.5.2"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2730321001, force_registration=True)
        self.config.register_guild(
            ping=None, reporting=None, watching=[], online_watching=[],
        )
        self.convert_data = bot.loop.create_task(self.data_convert())

    def cog_unload(self):
        if self.convert_data:
            self.convert_data.cancel()

    async def data_convert(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            raw_data = await self.config.guild(guild).all()
            for k, v in raw_data.items():
                if k == "watching" and not v:
                    continue
                if k == "online_notify" and v is True:
                    await self.config.guild(guild).online_watching.set(raw_data["watching"])
                    for to_del in ["online_notify", "sent_online"]:
                        raw_data.pop(to_del)

    async def get_watching(self, watch_list: list):
        data = []
        for user_id in watch_list:
            user = self.bot.get_user(user_id)
            if not user:
                data.append(user_id)
            else:
                data.append(user.mention)
        return data

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def otherbot(self, ctx: commands.Context):
        """Otherbot configuration options."""
        # Following logic from Trusty's welcome cog:
        # https://github.com/TrustyJAID/Trusty-cogs/blob/master/welcome/welcome.py#L81
        guild = ctx.guild
        if not ctx.invoked_subcommand:
            guild_data = await self.config.guild(guild).all()
            settings_name = dict(
                ping="Ping role",
                reporting="Channel reporting",
                watching="Offline tracking",
                online_watching="Online tracking",
            )
            msg = ""
            if ctx.channel.permissions_for(ctx.me).embed_links:
                em = discord.Embed(
                    color=await ctx.embed_colour(), title=f"Otherbot settings for {guild.name}"
                )
                for attr, name in settings_name.items():
                    if attr == "ping":
                        role = guild.get_role(guild_data["ping"])
                        if role:
                            msg += f"**{name}**: {role.mention}\n"
                        else:
                            msg += f"**{name}**: Not set.\n"
                    elif attr == "reporting":
                        channel = guild.get_channel(guild_data["reporting"])
                        if channel:
                            msg += f"**{name}**: {channel.mention}\n"
                        else:
                            msg += f"**{name}**: Not set.\n"
                    elif attr == "watching":
                        if guild_data["watching"]:
                            msg += (
                                f"**{name}**: "
                                + " ".join(await self.get_watching(guild_data["watching"]))
                                + "\n"
                            )
                        else:
                            msg += f"**{name}**: Not set.\n"
                    elif attr == "online_watching":
                        if guild_data["online_watching"]:
                            msg += (
                                f"**{name}**: "
                                + " ".join(await self.get_watching(guild_data["online_watching"]))
                                + "\n"
                            )
                        else:
                            msg += f"**{name}**: Not set.\n"
                em.description = msg
                em.set_thumbnail(url=guild.icon_url)
                await ctx.send(embed=em)
            else:
                msg = "```\n"
                for attr, name in settings_name.items():
                    if attr == "ping":
                        role = guild.get_role(guild_data["ping"])
                        if role:
                            msg += f"{name}: {role.mention}\n"
                        else:
                            msg += f"{name}: Not set.\n"
                    elif attr == "reporting":
                        channel = guild.get_channel(guild_data["reporting"])
                        if channel:
                            msg += f"{name}: {channel.mention}\n"
                        else:
                            msg += f"{name}: Not set.\n"
                    elif attr == "watching":
                        if guild_data["watching"]:
                            msg += (
                                f"{name}: "
                                + ", ".join(await self.get_watching(guild_data["watching"]))
                                + "\n"
                            )
                        else:
                            msg += f"{name}: Not set."
                    elif attr == "online_watching":
                        if guild_data["online_watching"]:
                            msg += (
                                f"{name}: "
                                + " ".join(await self.get_watching(guild_data["online_watching"]))
                                + "\n"
                            )
                        else:
                            msg += f"{name}: Not set.\n"
                msg += "```"
                await ctx.send(msg)

    @otherbot.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Sets the channel to report in.
        
        Default to the current one.
        """
        if not channel:
            channel = ctx.channel
        await self.config.guild(ctx.guild).reporting.set(channel.id)
        await ctx.send(f"Reporting channel set to: {channel.mention}.")

    @otherbot.command()
    async def pingrole(self, ctx: commands.Context, role_name: discord.Role = None):
        """Sets the role to use for pinging. Leave blank to reset it."""
        if not role_name:
            await self.config.guild(ctx.guild).ping.set(None)
            return await ctx.send("Ping role cleared.")
        await self.config.guild(ctx.guild).ping.set(role_name.id)
        pingrole_id = await self.config.guild(ctx.guild).ping()
        pingrole_obj = discord.utils.get(ctx.guild.roles, id=pingrole_id)
        await ctx.send(f"Ping role set to: `{pingrole_obj.name}`.")

    @otherbot.group(name="watch", aliases=["watching"])
    async def otherbot_watch(self, ctx: commands.Context):
        """Watch settings."""
        pass

    @otherbot_watch.group(name="offline")
    async def otherbot_watch_offline(self, ctx: commands.Context):
        """Manage offline notifications."""
        pass

    @otherbot_watch_offline.command(name="add")
    async def otherbot_watch_offline_add(self, ctx: commands.Context, bot: discord.Member):
        """Add a bot that will be tracked when it goes offline."""
        if not bot.bot:
            return await ctx.send(
                "You can't track normal users. Please try again with a bot user."
            )

        async with self.config.guild(ctx.guild).watching() as watch_list:
            watch_list.append(bot.id)
        await ctx.send(f"I will now track {bot.mention} when it goes offline.")

    @otherbot_watch_offline.command(name="remove")
    async def otherbot_watch_offline_remove(self, ctx: commands.Context, bot: discord.Member):
        """Removes a bot currently tracked."""
        if not bot.bot:
            return await ctx.send(
                "You can't choose a normal user. Please try again with a bot user."
            )

        async with self.config.guild(ctx.guild).watching() as watch_list:
            try:
                watch_list.remove(bot.id)
                await ctx.send(
                    f"Successfully removed {bot.mention} from offline tracked bot list."
                )
            except ValueError:
                await ctx.send(f"{bot.mention} is not currently tracked.")

    @otherbot_watch_offline.command(name="list")
    async def otherbot_watch_offline_list(self, ctx: commands.Context):
        """Lists currently tracked bots."""
        watching = await self.config.guild(ctx.guild).watching()
        if not watching:
            return await ctx.send("There is currently no bots tracked for offline status.")

        watching_list = await self.get_watching(watching)
        await ctx.send(
            f"{len(watching):,} bot{'s' if len(watching) > 1 else ''} are currently tracked for offline status:\n"
            + ", ".join(watching_list)
        )

    @otherbot_watch.group(name="online")
    async def otherbot_watch_online(self, ctx: commands.Context):
        """Manage online notifications."""
        pass

    @otherbot_watch_online.command(name="add")
    async def otherbot_watch_online_add(self, ctx: commands.Context, bot: discord.Member):
        """Add a bot that will be tracked when it comes back online."""
        if not bot.bot:
            return await ctx.send(
                "You can't track normal users. Please try again with a bot user."
            )

        async with self.config.guild(ctx.guild).online_watching() as watch_list:
            watch_list.append(bot.id)
        await ctx.send(f"I will now track {bot.mention} when it goes back online.")

    @otherbot_watch_online.command(name="remove")
    async def otherbot_watch_online_remove(self, ctx: commands.Context, bot: discord.Member):
        """Removes a bot currently tracked."""
        if not bot.bot:
            return await ctx.send(
                "You can't choose a normal user. Please try again with a bot user."
            )

        async with self.config.guild(ctx.guild).online_watching() as watch_list:
            try:
                watch_list.remove(bot.id)
                await ctx.send(f"Successfully removed {bot.mention} from online tracked bot list.")
            except ValueError:
                await ctx.send(f"{bot.mention} is not currently tracked.")

    @otherbot_watch_online.command(name="list")
    async def otherbot_watch_online_list(self, ctx: commands.Context):
        """Lists currently tracked bots."""
        watching = await self.config.guild(ctx.guild).online_watching()
        if not watching:
            return await ctx.send("There is currently no bots tracked for online status.")

        watching_list = await self.get_watching(watching)
        await ctx.send(
            f"{len(watching):,} bot{'s' if len(watching) > 1 else ''} are currently tracked for online status:\n"
            + ", ".join(watching_list)
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild is None or not after.bot:
            return

        data = await self.config.guild(after.guild).all()
        channel = self.bot.get_channel(data["reporting"])
        if not channel:
            return
        if (
            before.status != discord.Status.offline
            and after.status == discord.Status.offline
            and (after.id in data["watching"])
        ):
            em = discord.Embed(
                color=0x8B0000,
                description=f"{after.mention} is offline. \N{LARGE RED CIRCLE}",
                timestamp=datetime.utcnow(),
            )
            try:
                if not data["ping"]:
                    await channel.send(embed=em)
                else:
                    await channel.send("<@&{}>".format(data["ping"]), embed=em)
            except discord.Forbidden:
                async with self.config.guild(after.guild).watching() as old_data:
                    old_data.remove(after.id)
                return
        elif (
            before.status == discord.Status.offline
            and after.status != discord.Status.offline
            and (after.id in data["online_watching"])
        ):
            em = discord.Embed(
                color=0x008800,
                description=f"{after.mention} is back online. \N{WHITE HEAVY CHECK MARK}",
                timestamp=datetime.utcnow(),
            )
            try:
                if not data["ping"]:
                    await channel.send(embed=em)
                else:
                    await channel.send("<@&{}>".format(data["ping"]), embed=em)
            except discord.Forbidden:
                async with self.config.guild(after.guild).online_watching() as old_data:
                    old_data.remove(after.id)
                return
        else:
            return

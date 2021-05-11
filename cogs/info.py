import discord
from discord.ext import commands

import sys

from utils.converters import MemberOrFetchedUser

class Info(commands.Cog):
    """Discord information related commands."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(aliases=['hi'])
    async def hello(self, ctx):
        """Greets you."""
        await ctx.send("Greetings.")

    @commands.command(aliases=['pfp'])
    async def avatar(self, ctx, *, user: MemberOrFetchedUser = None):
        """Shows user's avatar.
        
        Providing no argument shows own avatar. IDs can be provided for fetching
        users outside the guild.
        """
        user = user or ctx.author
        e = discord.Embed(colour=user.colour)
        e.set_author(name=str(user), url=user.avatar_url_as(static_format='png'))
        e.set_image(url=user.avatar_url_as(static_format='png'))
        await ctx.send(embed=e)

    @commands.command()
    async def about(self, ctx):
        """About the Bot."""

        bot_user = self.bot.user
        source = "[sneaky source code](https://github.com/euphonicazure/SneakyNinja)"
        owner = self.bot.get_user(self.bot.owner_id)
        py_ver = sys.version.split()[0]
        dpy_ver = discord.__version__
        dpy_logo = ('https://cdn.discordapp.com/attachments/336642776609456130/'
                    '581468512065683466/pydiscord-guild-new.png')
        # dpy logo source: discord.py guild -
        # https://discordapp.com/channels/336642139381301249/336642776609456130/581468466469404683

        member_count, unique_member_count = sum(g.member_count for g in self.bot.guilds), len(self.bot.users)

        e = discord.Embed(
            title=bot_user.name, description=self.bot.description,
            colour=self.bot.colour, timestamp=ctx.timenow()
        )
        e.set_author(name=str(owner), icon_url=owner.avatar_url)
        e.set_thumbnail(url=bot_user.avatar_url_as(static_format='png'))
        e.add_field(
            name="Statistics",
            value=f"members: {member_count}\nunique: {unique_member_count}\nguilds: {len(self.bot.guilds)}"
        )
        e.add_field(name="Created at", value=bot_user.created_at.strftime(ctx.tformat))
        e.add_field(name="Source", value=source)
        e.set_footer(text=f"Python {py_ver} | discord.py {dpy_ver}", icon_url=dpy_logo)

        await ctx.send(embed=e)

    @commands.command(aliases=['info','whois'])
    async def userinfo(self, ctx, *, user: MemberOrFetchedUser = None):
        """Show user's info.

        Providing no argument shows own info. IDs can be provided for fetching
        users outside the guild.
        """

        user = user or ctx.author
        created = user.created_at.strftime(ctx.tformat)
        shared = sum(g.get_member(user.id) is not None for g in self.bot.guilds)
        try:
            user_nick = user.nick
            joined = user.joined_at.strftime(ctx.tformat)
            roles = ", ".join([role.mention for role in reversed(user.roles)])
        except AttributeError:
            joined, roles, user_nick = None, None, None

        e = discord.Embed(colour=user.colour)
        e.set_author(name=str(user), url=user.avatar_url_as(static_format='png'))
        e.set_thumbnail(url=user.avatar_url_as(static_format='png'))
        e.add_field(name="ID", value=user.id)
        e.add_field(name="nickname", value=user_nick)
        e.add_field(name="shared", value=shared)
        e.add_field(name="Created on", value=created, inline=False)
        e.add_field(name="Joined on", value=joined, inline=False)
        e.add_field(name="Roles", value=roles, inline=False)
        await ctx.send(embed=e)
    
    @commands.command(aliases=['serverinfo'])
    async def guildinfo(self, ctx):
        """Shows information regarding the server."""

        guild = ctx.guild
        bot_count = len([m for m in ctx.guild.members if m.bot])
        tc, vc, cat = len(guild.text_channels), len(guild.voice_channels), len(guild.categories) 

        e = discord.Embed(colour=self.bot.colour, description=guild.description)
        e.set_author(name=guild.name, url=guild.icon_url_as(static_format='png'))
        e.set_thumbnail(url=guild.icon_url_as(static_format='png'))
        e.add_field(name="ID", value=guild.id, inline=True)
        e.add_field(name="Region", value=guild.region, inline=True)
        e.add_field(name="Verification", value=guild.verification_level, inline=True)
        e.add_field(name="Members", value=f"{guild.member_count} ({bot_count} bot)", inline=True)
        e.add_field(name="Created", value=guild.created_at.strftime(ctx.tformat), inline=True)
        e.add_field(name="Nitro", value=f"lvl: {guild.premium_tier} & user: {guild.premium_subscription_count}", inline=True)
        e.add_field(name="Channels", value=f"{tc} text channels, {vc} voice channels & {cat} categories")
        e.set_footer(text=f"Owned by {str(guild.owner)}", icon_url=guild.owner.avatar_url)
        await ctx.send(embed=e)

    @commands.group(aliases=['role'], invoke_without_command=True)
    async def roles(self, ctx):
        """Shows all server role and some info about them."""

        # TODO: Paginate this command maybe in case of too many roles.
        roles = reversed(ctx.guild.roles)  # highest role first
        name_count, colour, mentionable = [], [], []
        for role in roles:
            name_count.append(f'{role.mention} ({len(role.members)})')
            colour.append(str(role.colour))
            mentionable.append(str(role.mentionable))

        e = discord.Embed(title=f"Roles - {len(name_count)}", colour=self.bot.colour)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        e.add_field(name="name", value='\n'.join(name_count), inline=True)
        e.add_field(name="colour", value='\n'.join(colour), inline=True)
        e.add_field(name="mentionable", value='\n'.join(mentionable), inline=True)

        await ctx.send(embed=e)

    @roles.command(name='info')
    async def roles_info(self, ctx, *, role: discord.Role = None):
        """Shows detailed information about a specific role.

        Providing no argument shows own top role info.
        """

        role = role or ctx.author.top_role        
        e = discord.Embed(
            description=f"{role.mention} - {len(role.members)}",
            colour=role.colour, timestamp=role.created_at
        )
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        e.add_field(name="ID", value=role.id)
        e.add_field(name="Colour", value=str(role.colour), inline=True)
        e.add_field(name='\u200b', value='\u200b')
        e.add_field(name="Managed", value=role.managed, inline=True)
        e.add_field(name="Mentionable", value=role.mentionable, inline=True)
        e.add_field(name="Hoisted", value=role.hoist, inline=True)
        e.set_footer(text=f"Created")

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Info(bot))

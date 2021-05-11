import discord
from discord.ext import commands

import re
from typing import Union, Optional

from utils.converters import MemberOrFetchedUser, MessageFlagParser


class Mod(commands.Cog):
    """Moderation commands."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None
    
    @commands.command()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """kicks a member from the server.

        Both Bot and command user must have Kick Member permission.
        """
        reason = reason or f"By {ctx.author} (ID: {ctx.author.id})"
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f"See ya, {member}")

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, user: MemberOrFetchedUser, day: Optional[int] = 0, *, reason=None):
        """Bans a member or a user (by ID) from the server.

        Both the user and the bot must have Ban Member permission.
        """
        reason = reason or f"By {ctx.author} (ID: {ctx.author.id})"
        if day < 0 or day > 7:
            return await ctx.send("Minimum 0 days and Maximum 7 days of member message can be deleted")

        # discord.Object(id=x) for banning members outside the guild
        await ctx.guild.ban(discord.Object(id=user.id), delete_message_days=day, reason=reason)
        await ctx.send(f"Ba Bye, {user}")

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, user, *, reason = None):
        """Unbans a user from the server.

        Both the user and the bot must have ban permission.
        """
        # Not using user: int to handle the exception manually
        try:
            user = await ctx.guild.fetch_ban(discord.Object(id=int(user)))
        except ValueError:
            return await ctx.send("I need the user's ID to unban.")
        except discord.NotFound:
            return await ctx.send("Never banned this user before.")

        reason = reason or f"By {ctx.author} (ID: {ctx.author.id})"        
        await ctx.guild.unban(user.user, reason=reason)
        await ctx.send(f"Thought {user.user}'s gone forever.")

    @commands.command()
    @commands.has_guild_permissions(kick_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason=None):
        """Ban and unbans a member immediately to delete their messages upto 7 days.

        The user and the bot must have kick and ban permission respectively.
        """
        reason = reason or f"By {ctx.author} (ID: {ctx.author.id})"
        await ctx.guild.ban(member, delete_message_days=7, reason=reason)
        await ctx.guild.unban(member)
        await ctx.send(f"Forgotten and exiled, {member}.")

    async def _voice_patch(self, targets, **kwargs):
        """Voice patches provided target and returns the total member count of the target(s)"""
        member_count = 0
        for target in targets:
            if isinstance(target, discord.Member):
                await target.edit(**kwargs)
                member_count += 1
            elif isinstance(target, discord.VoiceChannel):
                member_count += len(target.members)
                for member in target.members:
                    await member.edit(**kwargs)
        return member_count    

    @commands.group(name='voice', aliases=['vc'], invoke_without_command=False)
    @commands.cooldown(1, 10.0, commands.BucketType.guild)
    async def _voice(self, ctx):
        """Voice moderation related commands."""
        pass

    @_voice.command(name='mute')
    @commands.has_guild_permissions(mute_members=True)
    async def _voice_mute(self, ctx, targets: commands.Greedy[Union[discord.Member, discord.VoiceChannel]]):
        """Voice mutes multiple members.
        
        Both the user and the bot must have Mute Members permission.
        """
        count = await self._voice_patch(targets, mute=True)
        await ctx.send(f"The less men think, the more they talk. Muted: {count}")
    
    @_voice.command(name='unmute')
    @commands.has_guild_permissions(mute_members=True)
    async def _voice_unmute(self, ctx, targets: commands.Greedy[Union[discord.Member, discord.VoiceChannel]]):
        """Voice unmutes multiple members.
        
        Both the user and the bot must have mute members permission.
        """
        count = await self._voice_patch(targets, mute=False)
        await ctx.send(f"Unmuted: {count}")
    
    @_voice.command(name='deaf')
    @commands.has_guild_permissions(deafen_members=True)
    async def _voice_deaf(self, ctx, targets: commands.Greedy[Union[discord.Member, discord.VoiceChannel]]):
        """Voice deafens multiple members.
        
        Both the user and the bot must have deafen_members permission.
        """
        count = await self._voice_patch(targets, deafen=True)
        await ctx.send(f"Deafened: {count}")

    @_voice.command(name='undeaf')
    @commands.has_guild_permissions(deafen_members=True)
    async def _voice_undeaf(self, ctx, targets: commands.Greedy[Union[discord.Member, discord.VoiceChannel]]):
        """Voice undeafens multiple members.
        
        Both the user and the bot must have deafen_members permission.
        """
        count = await self._voice_patch(targets, deafen=False)
        await ctx.send(f"undeafened: {count}")

    @commands.command(name='purge')
    @commands.has_guild_permissions(manage_messages=True)
    async def msg_purge(self, ctx, limit: int, *, flags: MessageFlagParser = None):
        """Purge messages with handy options.
        
        Both the user and the bot must have Manage Message permission. Additional Options:
        purges message if message -
        `-u`, `--user` - author is among user(s).
        `-c`, `--contains` - content contains provided words.
        `-b`, `--bot` - author is a bot.
        `-e`, `--everyone` - actually mentions everyone or here.
        `-em`, `--embed` - has embed(s).
        `-ro`, `--reaction-over` - has reactions over provided integer.
        `-mo`, `--mention-over` - has mentions over provided integer.
        `-r`, `--regex` - matches the regex pattern.
        `-ric`, `--regex-ignorecase` - can be used with `-r` to ignorecase.
        """

        if limit > 1000:
            return await ctx.send("1000 messages at most.")

        predicates = [lambda m: True]

        if flags:
            args = flags.args
            if args.user:
                user = [await MemberOrFetchedUser().convert(ctx, user) for user in args.user]
                predicates.append(lambda m: m.author in user)
            if args.contains:
                predicates.append(lambda m: any(contain in m.content for contain in args.contains))
            if args.bot:
                predicates.append(lambda m: m.author.bot)
            if args.everyone:
                predicates.append(lambda m: m.mention_everyone)
            if args.embed:
                predicates.append(lambda m: bool(m.embeds))
            if args.reaction_over:
                predicates.append(lambda m: len(m.reactions) > args.reaction_over)
            if args.mention_over:
                predicates.append(lambda m: len(m.raw_mentions) > args.mention_over)
            if args.regex:
                if args.regex_ignorecase:
                    pattern = re.compile(args.regex, re.IGNORECASE)
                else:
                    pattern = re.compile(args.regex)
                predicates.append(lambda m: bool(pattern.search(m.content)))

        def check(msg):
            return all(predicate(msg) for predicate in predicates)

        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(f"{len(deleted)} Messages? Wiped out their existence.", delete_after=3)


def setup(bot):
    bot.add_cog(Mod(bot))

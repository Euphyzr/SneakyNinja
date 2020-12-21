import discord
from discord.ext import commands

from .utils.converters import EmbedFlagParser


class Manage(commands.Cog):
    """Server management related commands."""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(aliases=['mkembed'])
    async def makembed(self, ctx, *, flags: EmbedFlagParser):
        """Create your own embed.
        
        Avialable Options:
        `-t`, `--title` - The title of the embed.
        `-d`, `--description` - The description of the embed.
        `-c`, `--colour` - The colour of the embed. Accepts both RGB and hex.
        `-si`, `--set-image` - Url of the embed's image.
        `-st`, --`set-thumbnail` - Url of the embed's thumbnail.
        `-sf`, `--set-footer` - Foote's text and icon's url. Provide empty quote for no icon.
        `-af`, `--add-field` - Field's name, value and inline state.

        You can also add multiple fields, also make sure to seperate the name and value with quotes.
        """

        args = flags.args
        e = discord.Embed(timestamp=ctx.timenow())
        e.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)

        if args.title:
            e.title = args.title

        if args.description:
            e.description = args.description

        if args.colour:
            colour = args.colour  # list
            if len(colour) == 1:
                colour = colour[0]
                if colour.startswith('#'):
                    colour = colour[1:] 
                try:
                    dcolour = discord.Colour(int(colour, base=16))
                except ValueError:
                    raise commands.BadArgument("Not a valid hex.")
            elif len(colour) == 3:
                try:
                    colour = tuple(map(int, colour))
                except ValueError:
                    raise commands.BadArgument("Only integers are allowed in RGB.")
                dcolour = discord.Colour.from_rgb(*colour)
            else:
                raise commands.BadArgument("Not a valid colour.")
            if dcolour.value < 0 or dcolour.value > 16777215:
                raise commands.BadArgument("Not a valid colour.")
            e.colour = dcolour

        if args.set_image:
            e.set_image(url=args.set_image)

        if args.set_thumbnail:
            e.set_thumbnail(url=args.set_thumbnail)

        if args.set_footer:
            text, icon_url = args.set_footer
            e.set_footer(text=text, icon_url=icon_url)

        if args.add_field:
            for field in args.add_field:
                name, value, inline = field
                inline = False if inline.lower() == 'false' else True
                e.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Manage(bot))

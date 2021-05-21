import discord
from discord.ext import commands

import textwrap

import wikipedia
import googletrans

class Utilities(commands.Cog):
    """Utility commands."""

    def __init__(self, bot):
        self.bot = bot
        self.translator = googletrans.Translator()

    @commands.command(name='wikipedia', aliases=['wiki'])
    async def wikisummary(self, ctx, *, topic):
        """Get summary of any wikipedia page."""
        wiki_icon = "https://upload.wikimedia.org/wikipedia/commons/6/6e/Wikipedia_logo_silver.png"
        em = discord.Embed(colour=0xF9F0F0)
        em.set_author(name="wikipedia", icon_url=wiki_icon)
        em.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

        try:
            page = await self.bot.loop.run_in_executor(None, wikipedia.page, topic)
        except wikipedia.DisambiguationError as e:
            em.title = "Disambiguation"
            em.description = "\n".join(e.options[:5])
            return await ctx.send(embed=em)
        except Exception as e:
            return await ctx.send(e)

        placeholder = f"... [Continue]({page.url})"
        summary = textwrap.shorten(page.summary, width=1024, placeholder=placeholder)
        images = list(filter(lambda i: i.endswith((".jpg", ".JPG", ".png", ".PNG")), page.images))
        em.title, em.url = page.title, page.url
        em.add_field(name="Summary", value=summary)
        if images:
            em.set_thumbnail(url=images[0])
        await ctx.send(embed=em)

    async def _generate_translated_embed(self, ctx, translated):
        e = discord.Embed(colour=discord.Colour.blue())
        icon_url = (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Google_Translate_logo.svg/"
            "1200px-Google_Translate_logo.svg.png"
        )
        e.set_author(name="Translator", icon_url=icon_url)
        e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

        src = googletrans.LANGUAGES.get(translated.src, 'Auto-Detected').title()
        dest = googletrans.LANGUAGES.get(translated.dest, 'English').title()
        e.add_field(name=f"From {src}", value=translated.origin)
        e.add_field(name=f"To {dest}", value=translated.text)

        return e

    @commands.command(aliases=['tl'])
    async def translate(self, ctx, *, text: commands.clean_content):
        """Auto-detects and translates the provided text to English."""
        try:
            translated = await self.bot.loop.run_in_executor(None, self.translator.translate, text)
        except Exception as e:
            return await ctx.send(e)

        e = await self._generate_translated_embed(ctx, translated)
        await ctx.send(embed=e)

    @commands.command(aliases=['tlto', 'tl2'])
    async def translateto(self, ctx, dest, *, text):
        """Auto-detects and translates the provided text to another Language."""
        try:
            translated = await self.bot.loop.run_in_executor(None, self.translator.translate, text, dest)
        except ValueError:
            return await ctx.send("Not a valid destination language.")
        except Exception as e:
            return await ctx.send(e)

        e = await self._generate_translated_embed(ctx, translated)
        await ctx.send(embed=e)

    @commands.group(name='math', invoke_without_command=True)
    async def _math(self, ctx):
        """Mathemetical operations that can be done."""
        pass

    async def _math_calculate(self, ctx, operation, expression):
        url = f"https://newton.now.sh/api/v2/{operation}/{expression}"
        async with ctx.session.get(url) as resp:
            if resp.status == 200:
                respjs = await resp.json()
                e = discord.Embed(
                    title=f'{operation.title()} `{expression}`',
                    description=f"```{respjs['result']}```",
                    colour=discord.Colour.blurple(),
                )
                e.set_footer(text=f"Requested by {ctx.author}")
                return await ctx.send(embed=e)
            return await ctx.send("Unable to perform calculation.")

    @_math.command(name='factor')
    async def _math_factor(self, ctx, *, expression):
        """Calculates the factor for an expression."""
        await self._math_calculate(ctx, 'factor', expression)

    @_math.command(name='derive')
    async def _math_derive(self, ctx, *, expression):
        """Calculates the derivative for an expression."""
        await self._math_calculate(ctx, 'derive', expression)

    @_math.command(name='integrate')
    async def _math_integrate(self, ctx, *, expression):
        """Calculates the integration for an expression."""
        await self._math_calculate(ctx, 'integrate', expression)

    @_math.command(name='zeroes')
    async def _math_zeroes(self, ctx, *, expression):
        """Calculates the values for which an expression yields zero."""
        await self._math_calculate(ctx, 'zeroes', expression)


def setup(bot):
    bot.add_cog(Utilities(bot))

import discord
from discord.ext import commands

import random
import textwrap

import wikipedia
import googletrans

class Fun(commands.Cog):
    """Fun and some utility related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.translator = googletrans.Translator() 
    
    @commands.command()
    async def choose(self, ctx, *choices: commands.clean_content):
        """Randomly chooses a result from the provided choices.
        
        In case of multiworded choices use quotes. E.g - choose "very good" bad.
        """
        if not choices:
            return await ctx.send("No choices provided.")
        await ctx.send(random.choice(choices))
    
    @commands.command(aliases=['randint'])
    async def randomnumber(self, ctx, start: int, end: int):
        """Picks a random number between the provided numbers"""
        start, end = (end, start) if start > end else (start, end)
        await ctx.send(random.randint(start, end))

    @commands.command(aliases=['cat', 'neko'])
    async def cats(self, ctx):
        """Get a random cat pic. =^-^="""
        async with ctx.session.get('https://api.thecatapi.com/v1/images/search') as resp:
            if resp.status == 200:
                respjs = await resp.json()
                e = discord.Embed(title='Look a lovely cat!', colour=ctx.author.colour or self.bot.colour)
                e.set_image(url=respjs[0]['url'])
                e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
                return await ctx.send(embed=e)
            return await ctx.send("The cat escaped.")

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

    @commands.command()
    async def reddit(self, ctx, subreddit):
        """Get 5 hot reddit posts from a subreddit."""
        
        url = f'https://www.reddit.com/r/{subreddit}/'
        params = {'limit': '5'}
        async with ctx.session.get(url + 'hot.json', params=params) as resp:
            if resp.status == 200:
                respjs = await resp.json()
                posts = respjs['data']['children']
                if not posts:
                    return await ctx.send("Not a valid subreddit or doesn't have any posts.")

                e = discord.Embed(colour=discord.Colour.red())
                e.set_author(name=subreddit, url=url, icon_url='https://i.redd.it/rq36kl1xjxr01.png')
                e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

                e = {
                    'color': 0xe74c3c,
                    'author': dict(name=subreddit, url=url, icon_url='https://i.redd.it/rq36kl1xjxr01.png'),
                    'footer': dict(text=f"Requested by {ctx.author}", icon_url=str(ctx.author.avatar_url)),
                    'fields': []
                }
            
                sticky = {'name': 'Sticky', 'value': '', 'inline': False}
                normal = {'name': 'Posts', 'value': '', 'inline': False}
                for post in posts:
                    data = post['data']
                    title, url, stickied = data['title'], data['url'], data['stickied']
                    # nsfw = 'nsfw' if data['over_18'] else '', # will implement this later
                    flair = data['link_flair_text'] 
                    flair = f'[{flair}]' if flair else ''

                    if stickied:
                        sticky['value'] += f"[{title}]({url}) {flair}" + "\n"
                    else:
                        normal['value'] += f"[{title}]({url}) {flair}" + "\n"
                
                if sticky:
                    e['fields'].append(sticky)
                if normal:
                    e['fields'].append(normal)

                return await ctx.send(embed=discord.Embed.from_dict(e))
            await ctx.send("Couldn't get the subreddit posts")     

 
def setup(bot):
    bot.add_cog(Fun(bot))

import discord
from discord.ext import commands

import random

class Fun(commands.Cog):
    """Fun commands."""

    def __init__(self, bot):
        self.bot = bot
    
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

    @commands.command()
    async def reddit(self, ctx, subreddit):
        """Get 5 hot reddit posts from a subreddit."""

        url = f"https://www.reddit.com/r/{subreddit.split('/')[-1]}/hot.json"
        params = {'limit': '5'}
        async with ctx.session.get(url, params=params) as resp:
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
                
                if sticky['value']:
                    e['fields'].append(sticky)
                if normal['value']:
                    e['fields'].append(normal)

                return await ctx.send(embed=discord.Embed.from_dict(e))
            await ctx.send("Sorry, couldn't get the subreddit posts.")

    @commands.command()
    async def coffee(self, ctx):
        async with ctx.session.get("https://coffee.alexflipnote.dev/random.json") as resp:
            if resp.status == 200:
                respjs = await resp.json()
                e = discord.Embed(title='A coffee for you!', colour=ctx.author.colour or self.bot.colour)
                e.set_image(url=respjs['file'])
                e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
                return await ctx.send(embed=e)
            return await ctx.send("No Coffee today.")

    @commands.command()
    async def facts(self, ctx):
        async with ctx.session.get("https://nekos.life/api/v2/fact") as resp:
            if resp.status == 200:
                respjs = await resp.json()
                e = discord.Embed(
                    title='Facts', description=respjs['fact'],
                    colour=ctx.author.colour or self.bot.colour
                )
                e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
                return await ctx.send(embed=e)
            return await ctx.send("No facts today.")

    @commands.command()
    async def asciify(self, ctx, *, text):
        url, params = "https://artii.herokuapp.com/make", {'text': text}
        async with ctx.session.get(url, params=params) as resp:
            if resp.status == 200:
                resp_txt = await resp.text()
                return await ctx.send(f"```{resp_txt}```")
            return await ctx.send("Sorry, couldn't get the ASCII.")

    @commands.command()
    async def quote(self, ctx):
        payload = {'method': 'getQuote', 'format': 'json', 'lang': 'en'}
        async with ctx.session.post("http://api.forismatic.com/api/1.0/", data=payload) as resp:
            if resp.status == 200:
                respjs = await resp.json()
                e = discord.Embed(
                    title='Random Quote',
                    url=respjs['quoteLink'],
                    description=respjs['quoteText'],
                    colour=ctx.author.colour or self.bot.colour,
                )
                e.set_footer(text=f"ー {respjs['quoteAuthor'] or 'unknown'} | Requested by {ctx.author}")
                return await ctx.send(embed=e)
            return await ctx.send("Sorry, couldn't get any quotes.")


def setup(bot):
    bot.add_cog(Fun(bot))

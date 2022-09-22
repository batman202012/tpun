from redbot.core import data_manager
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core import bank, data_manager
from datetime import datetime
from dateutil import tz, parser
from discord import app_commands
import discord
import requests
import logging
import random
import inflect
import asyncio
import time
import calendar


class occupations(commands.Cog):
    """
    Adds Occupations that server members can choose from a job board. Members earn money based on their job by spending time in vc
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.occupations')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_global = {
            "title": "",
            "salary": 0.0,
            "vcstarttime": "",
            "cooldown": ""
        }
        default_guild = {
            "maxsalary": 100000,
            "chancescalar": 1.0,
            "timediff": 3600.0,
            "salaryscalar": 1.0
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    async def create_embed(self, jobs: dict):
        description="A list of avalaible jobs below\nThe higher the salary the less chance of getting the job"
        embed = discord.Embed(title="Job Board", description=description, color=0xc72327)
        iteration = 1
        p = inflect.engine()
        for title, salary in jobs.items():
            message = "Title: " + title + " \nSalary: " + str(int(salary)) + "\nCurrency/Hr: " + str(((3600/(60*60*24*30)) * int(salary) * 100) * 0.27)
            embed.add_field(name=":{0}:".format(p.number_to_words(iteration)), value=message, inline=False)
            iteration = iteration + 1
        return embed

    def pred(self, emojis, mess, user: discord.Member):
        return ReactionPredicate.with_emojis(emojis, mess, user)

    async def jobChooser(self, ctx: commands.Context, emoji, mess: discord.Message, jobs: dict):
        jobDict = jobs.keys()
        jobList = list(jobDict)[:4]
        jobName = ""
        jobSalary = ""
        if emoji == "1️⃣":
            jobName = jobList[0]
            jobSalary = jobs[jobList[0]]
        elif emoji == "2️⃣":
            jobName = jobList[1]
            jobSalary = jobs[jobList[1]]
        elif emoji == "3️⃣":
            jobName = jobList[2]
            jobSalary = jobs[jobList[2]]
        elif emoji == "4️⃣":
            jobName = jobList[3]
            jobSalary = jobs[jobList[3]]
        #Add chance of failing to get job perentage based on salary
        maxsalary = await self.config.guild(ctx.guild).maxsalary()
        chanceScalar = await self.config.guild(ctx.guild).chancescalar()
        jobChance = 1 - ((jobSalary / maxsalary) * chanceScalar)
        roll = random.random()
        if roll <= jobChance: 
            #set that occupation to users job
            await self.config.member(ctx.author).title.set(jobName)
            await self.config.member(ctx.author).salary.set(jobSalary)
            await mess.reply(f"Congrats you got the job as `{jobName}`, your new salary is `{jobSalary}`")
        else:
            await mess.reply("I'm sorry but you didn't qualify for the job. Guess it's back to searching.")
        #start cooldown for job searching
        time_format = '%Y %m %d %H:%M:%S %z'
        utc_zone = tz.gettz('UTC')
        time = datetime.utcnow()
        await self.config.member(ctx.author).cooldown.set(time.strftime(time_format))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        salary = await self.config.member(member).salary()
        if salary is not None:
            time_format = '%Y %m %d %H:%M:%S %z'
            utc_zone = tz.gettz('UTC')
            salaryScalar = await self.config.guild(member.guild).salaryscalar()
            if before.channel is None and after.channel is not None:
                #start a timer for how long user is in vc
                time = datetime.utcnow()
                starttimestr = time.strftime(time_format)
                await self.config.member(member).vcstarttime.set(starttimestr)
            elif before.channel is not None and after.channel is None:
                #end the time for how long the user was in vc
                endtime = datetime.utcnow()
                starttimestr = await self.config.member(member).vcstarttime()
                starttime = parser.parse(starttimestr)
                secondsInVc = (endtime - starttime).total_seconds()
                #pay user based on how long they were in vc
                pay = int(((secondsInVc / (60*60*24*30)) * int(salary) * salaryScalar) * 0.27)
                self.log.info(f"{member.display_name} was paid {str(pay)} currency for being in vc for {(secondsInVc/60)} minutes")
                await bank.deposit_credits(member, pay)
            elif before.channel is not None and after.channel is not None:
                pass
            else:
                self.log.warning("Something went wrong in on_voice_update")

    @commands.hybrid_group(name="job", with_app_command=True)
    async def job(self, ctx: commands.Context):
        """
        Base command for occupation related commands
        """
        pass

    @job.command(name="board")
    async def jobboard(self, ctx: commands.Context) -> None:
        """
        Displays the job board with a list of jobs
        """
        #check cooldown for job searching
        cooldown = await self.config.member(ctx.author).cooldown()
        timediff = await self.config.guild(ctx.guild).timediff()
        max_salary = await self.config.guild(ctx.guild).maxsalary()
        if cooldown is None:
            cooldown = datetime.utcfromtimestamp(1302872043.0)
        else:
            cooldown = parser.parse(cooldown)
        if cooldown.timestamp() + timediff < datetime.utcnow().timestamp():
            adzuna_keys = await self.bot.get_shared_api_tokens("adzuna")
            if adzuna_keys.get("app_id") is None or adzuna_keys.get("api_key") is None:
                return await ctx.reply("The bot owner still needs to set the adzuna app id and secret using using `[p]set api adzuna app_id,<app id> api_key,<api key>`")
            else:
                pass
            #use api to get random jobs, if not possible use List
            response = requests.get("http://api.adzuna.com/v1/api/jobs/gb/search/1?app_id={0}&app_key={1}&results_per_page=50&full_time=1&salary_max={2}&content-type=application/json".format(adzuna_keys.get("app_id"), adzuna_keys.get("api_key"), max_salary))
            jobs = response.json()
            jobResults: list = jobs["results"]
            titleList: dict = {}
            for job in jobResults:
                titleList.update({job["title"]:job["salary_max"]})
            jobList = list(titleList)
            #choose 4 jobs from the list we get back at random
            job1 = jobList[await self.random_generator(jobList)]
            job2 = jobList[await self.random_generator(jobList)]
            job3 = jobList[await self.random_generator(jobList)]
            job4 = jobList[await self.random_generator(jobList)]
            titleList = {job1:titleList[job1], job2:titleList[job2], job3:titleList[job3], job4:titleList[job4]}
            #display 4 jobs in an embed
            embed = await self.create_embed(titleList)
            mess = await ctx.send(embed=embed)
            #wait for user to emoji react to choose one
            iteration = 1
            emojis = []
            p = inflect.engine()
            for job in titleList:
                if iteration == 1:
                    emojis.append("1️⃣")
                elif iteration == 2:
                    emojis.append("2️⃣")
                elif iteration == 3:
                    emojis.append("3️⃣")
                elif iteration == 4:
                    emojis.append("4️⃣")
                else:
                    pass
                iteration = iteration + 1
            start_adding_reactions(mess, emojis)
            try:
                result = await ctx.bot.wait_for("reaction_add", timeout=300.0, check=self.pred(emojis, mess, ctx.author))
                emoji = str(result[0])
                await self.jobChooser(ctx, emoji, mess, titleList)
            except asyncio.TimeoutError:
                await ctx.reply("You didn't go to any of your interviews. All your possible employers have found other workers. Back to applying.", ephemeral=True)
                time_format = '%Y %m %d %H:%M:%S %z'
                utc_zone = tz.gettz('UTC')
                timeNow = datetime.utcnow()
                await self.config.member(ctx.author).cooldown.set(timeNow.strftime(time_format))
            else:
                pass
        else:
            await ctx.reply(f"None of the jobs you've applied to have replied yet. Try again <t:{int(calendar.timegm(cooldown.timetuple()) + timediff)}:R>", ephemeral=True)

    async def random_generator(self, jobList):
        return random.randint(0, (len(jobList)-1))

    @job.command(name="current")
    async def currentjob(self, ctx: commands.Context) -> None:
        """
        Displays the user's current job
        """
        title = await self.config.member(ctx.author).title()
        salary = await self.config.member(ctx.author).salary()
        if title != None:
            await ctx.reply(f"Your current job is `{title}` and your salary is `{str(salary)}`")
        else:
            await ctx.reply("You do not have a job yet.")

    @job.command(name="quit")
    async def quitjob(self, ctx: commands.Context):
        """
        Quits your current job
        """
        await self.config.member(ctx.author).title.set(None)
        await self.config.member(ctx.author).salary.set(None)
        await ctx.reply("You quit your job. Better search for a new one soon...")


    @commands.guildowner_or_permissions()
    @job.command(name="settings")
    @app_commands.choices(subcommand=[
        app_commands.Choice(name="Max Salary", value="maxsalary"),
        app_commands.Choice(name="Chance Scalar", value="chancescalar"),
        app_commands.Choice(name="Cooldown", value="cooldown"),
        app_commands.Choice(name="Salary Scalar", value="salaryscalar"),
        app_commands.Choice(name="current", value="current")
    ])
    @app_commands.describe(subcommand="This is the setting you wish to change")
    async def settings(self, ctx: commands.Context, subcommand: app_commands.Choice[str], setting: float):

        async def maxsalary(self, ctx: commands.Context, setting: float = 10000) -> None:
            """
            Command for setting the max salary
            """
            await self.config.guild(ctx.guild).maxsalary.set(int(setting))
            wages = [20000, 40000, 75000, 100000, 125000, 150000]
            chanceScalar = await self.config.guild(ctx.guild).chancescalar()
            message = "The max salary was set to `{0}`".format(int(setting))
            for wage in wages:
                chance = 100 * (1 - ((wage / int(setting)) * chanceScalar))
                if chance < 0:
                    chance = 0
                message = message + f"\nThe current chance to get a `{wage}` salary job is `{chance}%`"
            await ctx.reply(message)

        async def chancescalar(self, ctx: commands.Context, setting: float = 1.0) -> None:
            """
            Command for setting the scalar for chances of getting a job

            The closer to 0 the more likely, the higher than 1 the less likely
            """
            await self.config.guild(ctx.guild).chancescalar.set(setting)
            wages = [20000, 40000, 75000, 100000, 125000, 150000]
            maxsalary = await self.config.guild(ctx.guild).maxsalary()
            message = "The chance scalar was set to `{0}`".format(setting)
            for wage in wages:
                chance = 100 * (1 - ((wage / maxsalary) * setting))
                if chance < 0:
                    chance = 0
                message = message + f"\nThe current chance to get a `{wage}` salary job is `{chance}%`"
            await ctx.reply(message)


        async def cooldown(self, ctx: commands.Context, setting: float = 1.0) -> None:
            """
            Command for setting the cooldown
            """
            await self.config.guild(ctx.guild).timediff.set(int(setting))
            await ctx.reply(f"The job search cooldown was set to `{int(setting)}` seconds.")

        async def salaryscalar(self, ctx: commands.Context, setting: float = 1.0) -> None:
            """
            Command for setting the salary scalar

            This multiplies the pay by a number
            """
            await self.config.guild(ctx.guild).salaryscalar.set(setting)
            wages = [20000, 40000, 75000, 100000, 125000, 150000]
            maxsalary = await self.config.guild(ctx.guild).maxsalary()
            message = "The salary scalar was set to `{0}`".format(setting)
            for wage in wages:
                salary = int(((3600 / (60*60*24*30)) * int(wage) * setting) * 0.27)
                message = message + f"\nThe hourly pay of a {wage} salary job is `{salary}`"
            await ctx.reply(message)

        async def current(self, ctx: commands.Context) -> None:
            """
            Displays current settings for occupations cog
            """
            maxsalary = await self.config.guild(ctx.guild).maxsalary()
            cooldown = await self.config.guild(ctx.guild).timediff()
            chanceScalar = await self.config.guild(ctx.guild).chancescalar()
            salaryScalar = await self.config.guild(ctx.guild).salaryscalar()
            embed = discord.Embed(title="Job Settings", description="The current settings in this guild are:", color=0xc72327)
            embed.add_field(name="Max salary:", value=maxsalary, inline=False)
            embed.add_field(name="Cooldown:", value=cooldown, inline=False)
            embed.add_field(name="Chance Scalar:", value=chanceScalar, inline=False)
            embed.add_field(name="Salary Scalar:", value=salaryScalar, inline=False)
            mess = await ctx.reply(embed=embed)

        if subcommand == "maxsalary":
            await maxsalary(ctx, setting)
        elif subcommand == "chancescalar":
            await chancescalar(ctx, setting)
        elif subcommand == "cooldown":
            await cooldown(ctx, setting)
        elif subcommand == "salaryscalar":
            await salaryscalar(ctx, setting)
        elif subcommand == "current":
            await current(ctx)
        else:
            await ctx.reply("This is not a valid subcommand options are: 'maxsalary', 'chancescalar','cooldown','salaryscalar', or 'current'")

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord
import re
import logging


class rep(commands.Cog):
    """
    Reputation cog
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.rep')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_global = {
            "reputation": {}
        }
        self.config.register_global(**default_global)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if bool(re.search("thank", message.content, flags=re.I | re.X)) and message.mentions is not None:
            users = message.mentions
            names = []
            found: bool = False
            for user in users:
                names.append(user.mention)
            x = await self.config.reputation()
            for user in users:
                id = user.id
                for userId, userRep in x.items():
                    if user.id != message.author.id and userId == str(id):
                        currentRep = userRep + 1
                        newWrite = {id: currentRep}
                        await message.channel.send("**+rep** {0} you now have: {1} Rep".format(user.name, str(currentRep)))
                        found = True
                        break
                if not found:
                    newWrite = {id: 1}
                x.pop(str(id), None)
                x.update(newWrite)
            await self.config.reputation.set(x)
                    await message.reply("**+rep** {0} you now have: {1} Rep".format(user.name, str(currentRep)))

    @commands.mod()
    @commands.hybrid_command(name="repremove", with_app_command=True)
    async def repremove(self, ctx: commands.Context, user: discord.Member, amount: int) -> None:
        """
        Removes a amount from a users reputation
        """
        newWrite = None
        x = await self.config.reputation()
        for userId, userRep in x.items():
            if userId == str(user.id):
                currentRep = userRep - amount
                newWrite = {user.id: currentRep}
        if newWrite is not None:
            x.pop(str(user.id), None)
            x.update(newWrite)
            await ctx.reply("**-rep** {0} took away {1} rep from {2}. They now have {3}"
                .format(ctx.author.name, amount, user.name, currentRep)
        else:
        await self.config.reputation.set(x)
            await ctx.reply("You can't take reputation away from someone who doesn't have one.", ephemeral=True)

    @commands.hybrid_command(name="checkrep", with_app_command=True)
    async def checkrep(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Displays a user's reputation
        """
        userFound = False
        x = await self.config.reputation()
        for userId, userRep in x.items():
            if userId == str(user.id):
                userFound = True
        if userFound is False:
            await ctx.reply("{0} has {1} reputation".format(user.name, currentRep))
            await ctx.reply("{0} doesn't have a reputation.".format(user.name))

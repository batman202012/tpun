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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if bool(re.search("thank", message.content, flags=re.I | re.X)) and message.mentions is not None:
            users = message.mentions
            names = []
            for user in users:
                id = user.id
                names.append(user.mention)
                if user.id != message.author.id:
                    currentRep = await self.config.member(user).reputation()
                    if currentRep is None:
                        currentRep = 0
                    newWrite = currentRep + 1
                    await message.reply("**+rep** {0} you now have: {1} Rep".format(user.name, str(currentRep)))
                    await self.config.member(user).reputation.set(newWrite)

    @commands.mod()
    @commands.hybrid_command(name="repremove", with_app_command=True)
    async def repremove(self, ctx: commands.Context, user: discord.Member, amount: int) -> None:
        """
        Removes a amount from a users reputation
        """
        newWrite = None
        currentRep = await self.config.member(user).reputation()
        if currentRep is not None and currentRep != 0:
            newWrite = currentRep - amount
            await ctx.reply("**-rep** {0} took away {1} rep from {2}. They now have {3}"
                .format(ctx.author.name, amount, user.name, currentRep)
            )
            if newWrite is not None:
                if newWrite >= 0:
                    await self.config.member(user).reputation.set(newWrite)
                else:
                    await self.config.member(user).reputation.set(0)
            else:
                self.log.warning(f"Failed to write reputation for {user.name}")
        else:
            await ctx.reply("You can't take reputation away from someone who doesn't have one.", ephemeral=True)

    @commands.hybrid_command(name="checkrep", with_app_command=True)
    async def checkrep(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Displays a user's reputation
        """
        currentRep = await self.config.member(user).reputation()
        if currentRep is not None and currentRep != 0:
            await ctx.reply("{0} has {1} reputation".format(user.name, currentRep))
        else:
            await ctx.reply("{0} doesn't have a reputation.".format(user.name))

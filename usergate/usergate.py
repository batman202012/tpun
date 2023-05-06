from dis import disco
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord
import datetime
import time
import logging
import asyncio


class usergate(commands.Cog):
    """
    User gate cog
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.usergate')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_guild = {
            "usergate": 0
        }
        self.config.register_guild(**default_guild)
        super().__init__()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        userGate = await self.config.guild(guild).usergate()
        if time.mktime(member.created_at.timetuple()) > (time.mktime(datetime.datetime.now().timetuple()) - (userGate * 24 * 60 * 60)):
            await member.kick(reason=f"Account is under {str(userGate)} days old")


    @commands.hybrid_command(name="usergate", with_app_command=True)
    async def usergate(self, ctx: commands.Context, days: int) -> None:
        """
        Usergate setup command

        Sets the number of days a user's account must exist before joining server, if user does not meet requirement they will get kicked.
        """
        guild = ctx.guild
        await self.config.guild(guild).usergate.set(days)
        await ctx.reply(f"Usergate was set to {days} days", ephemeral=True)

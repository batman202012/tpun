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
            await member.kick(reason="Account is under {0} days old".format(str(userGate)))

    @discord.app_commands.Command(name="usergate", description="Usergate setup command")
    async def usergate(self, interaction: discord.Interaction, days: int) -> None:
        """
        Usergate setup command

        Sets the number of days a user's account must exist before joining server, if user does not meet requirement they will get kicked.
        """
        guild = interaction.guild
        await self.config.guild(guild).usergate.set(days)
        await interaction.response.send_message("Usergate was set to {0} days".format(days), ephemeral=True)

    @commands.command(name="usergatesync")
    async def usergatesync(self, ctx: commands.Context):
        self.log.info("clearing commands...")
        self.bot.tree.remove_command("usergate", guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)

        self.log.info("waiting to avoid rate limit...")
        await asyncio.sleep(1)
        self.bot.tree.add_command(self.usergate, guild=ctx.guild)
        commands = [c.name for c in self.bot.tree.get_commands(guild=ctx.guild)]
        self.log.info("registered commands: %s", ", ".join(commands))
        self.log.info("syncing commands...")
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("VC Commands were synced")
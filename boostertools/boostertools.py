from typing import Literal
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import logging
import discord
import asyncio


class boostertools(commands.Cog):
    """
    Cog for managing boosters
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.boostertools')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_guild = {
            "boosterroles": []
        }

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        booster_colors = self.config.guild(before.guild).boosterroles()
        if before.guild.premium_subscriber_role in before.roles and after.guild.premium_subscriber_role not in after.roles:
            for role in after.roles:
                if role.id in booster_colors:
                    await after.remove_roles(role, reason="{0} is no longer boosting and this is a booster color")

    @commands.hybrid_command(name="btsetup", with_app_command=True)
    async def btsetup(self, ctx: commands.Context) -> None:
        mess1 = await ctx.reply("Send a message pinging any booster only roles.")

        def check(m):
            return m.channel == mess1.channel

        msg = await self.bot.wait_for('message', check=check, timeout=600)
        roles = []
        for i in msg.role_mentions:
            roles.append(i.id)
        await mess1.delete()
        await self.config.guild(ctx.guild).boosterroles.set(roles)
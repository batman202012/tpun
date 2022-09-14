import json
from pathlib import Path
import discord

from redbot.core.bot import Red
from redbot.core.config import Config

from .pvc import pvc

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    await bot.add_cog(pvc(bot))

    async def vcOwnerRead(guild, owner):
        i = await pvc(bot).config.guild(guild).owners()
        for vcOwner, vcId in i.items():
            if vcOwner == str(owner):
                return bot.get_channel(int(vcId))

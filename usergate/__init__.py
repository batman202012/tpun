import json
from pathlib import Path

from redbot.core.bot import Red

from .usergate import usergate

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    bot.tree.remove_command("usergate")
    await bot.add_cog(usergate(bot))
    bot.tree.add_command(usergate.usergate)
    await bot.tree.sync()
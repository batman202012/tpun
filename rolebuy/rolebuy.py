from typing import Literal
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core import bank
import discord
import asyncio
import logging
RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class rolebuy(commands.Cog):
    """
    Cog for buying roles
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.rolebuy')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_guild = {
            "buyableroles": {}
        }
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        # TODO: Replace this with the proper end user data removal handling.
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    @commands.hybrid_group(name="rb", with_app_command=True)
    async def rb(self, ctx):
        """
        Base command for all timed ping commands
        """
        pass

    @rb.command(name="buy", with_app_command=True)
    async def buy(self, ctx: commands.Context, role: discord.Role) -> None:
        """
        Buys a role for money
        """
        buyableRoles = await self.config.guild(ctx.guild).buyableroles()
        userAccount: bank.Account = await bank.get_account(ctx.author)
        if str(role.id) in buyableRoles.keys():
            if userAccount.balance >= buyableRoles[str(role.id)]:
                await ctx.author.add_roles(role)
                await bank.set_balance(ctx.author, userAccount.balance - buyableRoles[str(role.id)])
                await ctx.reply(f"You bought {role.name} for {buyableRoles[str(role.id)]} currency")
            else:
                await ctx.reply(f"I'm sorry but you don't have enough to buy {role.name} it costs {buyableRoles[str(role.id)]} currency", ephemeral=True)
        else:
            await ctx.reply("Sorry this role is not for sale, run rb list to find out with ones are.", ephemeral=True)

    @commands.guildowner_or_permissions()
    @rb.command(name="add", with_app_command=True)
    async def add(self, ctx: commands.Context, role: discord.Role, cost: int) -> None:
        """
        Adds a role to the buyable role list
        """
        buyableRoles = await self.config.guild(ctx.guild).buyableroles()
        nC = {str(role.id): cost}
        buyableRoles.update(nC)
        await self.config.guild(ctx.guild).buyableroles.set(buyableRoles)
        await ctx.reply(f"{role.mention} was added to the buyable roles list with cost {cost} currency", ephemeral=True)

    @commands.guildowner_or_permissions()
    @rb.command(name="remove", with_app_command=True)
    async def remove(self, ctx: commands.Context, role: discord.Role) -> None:
        """
        Removes a role from the buyable role list
        """
        buyableRoles = await self.config.guild(ctx.guild).buyableroles()
        if str(role.id) in buyableRoles.keys():
            buyableRoles.pop(str(role.id), None)
            await self.config.guild(ctx.guild).buyableroles.set(buyableRoles)
            await ctx.send(f"{role.mention} was removed from the buyable role List", ephemeral=True)
        else:
            await ctx.send("That role isn't a buyable role")

    @rb.command(name="list", with_app_command=True)
    async def list(self, ctx: commands.Context) -> None:
        """
        Lists all the timed ping roles for the server
        """
        roles = ""
        i = await self.config.guild(ctx.guild).buyableroles()
        for role, cost in i.items():
            roles = roles + f"<@&{role}> with cost of {cost} currency \n"
        if roles != "":
            mess1 = await ctx.reply(roles, ephemeral=True)
        else:
            mess1 = await ctx.reply("There are no buyable roles set up yet", ephemeral=True)
        await asyncio.sleep(120)
        await mess1.delete()

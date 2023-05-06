from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord
import asyncio
from redbot.core.utils.menus import start_adding_reactions
import datetime
from redbot.core.utils.predicates import ReactionPredicate
import logging


class verifier(commands.Cog):
    """
    Emoji Verification cog
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.verifier')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_guild = {
            "verifierroles": {}
        }
        self.config.register_guild(**default_guild)

    async def emojiVerifier(self, ctx: commands.Context, emoji, mess1, user: discord.Member):
        unverified: int = None
        male: int
        female: int
        nb: int
        i = await self.config.guild(ctx.guild).verifierroles()
        for key, role in i.items():
            if key == "unverified":
                unverified = ctx.guild.get_role(int(role))
            elif key == "male":
                male = ctx.guild.get_role(int(role))
            elif key == "female":
                female = ctx.guild.get_role(int(role))
            elif key == "nb":
                nb = ctx.guild.get_role(int(role))
        role: discord.Role = None
        if emoji == "♂":
            role = male
        elif emoji == "♀":
            role = female
        elif emoji == "💜":
            role = nb
        if unverified in user.roles:
            await user.add_roles(role)
            await user.remove_roles(unverified)
            await ctx.reply("User Verified as {0}".format(role.name))
            await mess1.delete()
        elif unverified is None:
            await ctx.reply("Server was not setup, please ask the owner to run [p]vsetup", ephemeral=True)
        else:
            await ctx.reply("User is already verified!", ephemeral=True)
            await mess1.delete()

    def pred(self, emojis, mess1, user: discord.Member):
        return ReactionPredicate.with_emojis(emojis, mess1, user)

    @commands.admin()
    @commands.hybrid_command(name="verify", with_app_command=True)
    async def verify(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Opens the verification gui
        """
        description0: str = 'From below please choose the emoji that best identifies your gender'
        embed = discord.Embed(color=0xe02522, title='Verified emoji selector', description=description0)
        embed.set_footer(text="♂ : Male | ♀ : Female|💜 : Non Binary")
        embed.timestamp = datetime.datetime.utcnow()
        mess1 = await ctx.channel.send(embed=embed)
        emojis = ["♂", "♀", "💜"]
        start_adding_reactions(mess1, emojis)
        try:
            result = await ctx.bot.wait_for("reaction_add", timeout=21600.0, check=self.pred(emojis, mess1, user))
            emoji = str(result[0])
            await self.emojiVerifier(ctx, emoji, mess1, user)
        except asyncio.TimeoutError:
            await ctx.channel.send('Verification gui timed out.')
            await mess1.delete()
        else:
            pass

    @commands.guildowner()
    @commands.hybrid_command(name="vsetup")
    async def setup(self, ctx: commands.Context) -> None:
        """
        Setup command for verify cog
        """
        newWrite: dict = {}
        guild = ctx.guild
        x = await self.config.guild(guild).verifierroles()

        def check(m):
            return m.channel == mess0.channel

        mess0 = await ctx.send("Please input the role for unverified members.", ephemeral=True)
        msg0 = await self.bot.wait_for('message', check=check, timeout=120)
        if msg0.content != "none":
            for i in msg0.role_mentions:
                newWrite.update({"unverified": i.id})
        mess1 = await ctx.send("Please input the role for verified males", ephemeral=True)
        msg1 = await self.bot.wait_for('message', check=check, timeout=120)
        if msg1.content != "none":
            for i in msg1.role_mentions:
                newWrite.update({"male": i.id})
        mess2 = await ctx.send("Please input the role for verified females", ephemeral=True)
        msg2 = await self.bot.wait_for('message', check=check, timeout=120)
        if msg2.content != "none":
            for i in msg2.role_mentions:
                newWrite.update({"female": i.id})
        mess3 = await ctx.send("Please input the role for verified non-binary", ephemeral=True)
        msg3 = await self.bot.wait_for('message', check=check, timeout=120)
        if msg3.content != "none":
            for i in msg3.role_mentions:
                newWrite.update({"nb": i.id})
        x.update(newWrite)
        await self.config.guild(guild).verifierroles.set(x)

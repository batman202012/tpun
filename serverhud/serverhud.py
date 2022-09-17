from typing import Literal
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord
import asyncio
import logging
from datetime import datetime, timedelta
RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class serverhud(commands.Cog):
    """
    Cog for creating info channels
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.serverhud')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_guild = {
            "totmem": {
                "channel": 0,
                "prefix": "",
                "name": "Total Members",
                "suffix": ""
            },
            "newmem": {
                "channel": 0,
                "prefix": "",
                "name": "New Members",
                "suffix": ""
            },
            "truemem": {
                "channel": 0,
                "prefix": "",
                "name": "Total Users",
                "suffix": ""
            },
            "totbot": {
                "channel": 0,
                "prefix": "",
                "name": "Total Bots",
                "suffix": ""
            },
            "booster": {
                "channel": 0,
                "prefix": "",
                "name": "Boosters",
                "suffix": ""
            },
            "boosterbar": {
                "channel": 0,
                "prefix": "",
                "stylefull": "*",
                "styleempty": "-"
            },
            "truememcount": 0,
            "newmemcount": 0,
        }
        self.config.register_guild(**default_guild)

    async def members(self, guild: discord.Guild):
        true_member_count = await self.config.guild(guild).truememcount()
        newmembers = await self.config.guild(guild).newmemcount()
        totmem = guild.member_count
        totmemDict = await self.config.guild(guild).totmem()
        totmemId = totmemDict["channel"]
        if totmemId != 0:
            channel: discord.ChannelType = guild.get_channel(totmemId)
            await channel.edit(name='{0} {1}: {2} {3}'.format(totmemDict["prefix"], totmemDict["name"], totmem, totmemDict["suffix"]))
            await asyncio.sleep(15)
            pass

        newmemObj = await self.config.guild(guild).newmem()
        newmemId = newmemObj["channel"]
        if newmemId != 0:
            channel: discord.ChannelType = guild.get_channel(newmemId)
            await channel.edit(name='{0} {1}: {2} {3}'.format(newmemObj["prefix"], newmemObj["name"], newmembers, newmemObj["suffix"]))
            await asyncio.sleep(15)
            pass

        truememObj = await self.config.guild(guild).truemem()
        truememId = truememObj["channel"]
        if truememId != 0:
            channel: discord.ChannelType = guild.get_channel(truememId)
            await channel.edit(name='{0} {1}: {2} {3}'.format(truememObj["prefix"], truememObj["name"], true_member_count, truememObj["suffix"]))
            await asyncio.sleep(15)
            pass

        totbotObj = await self.config.guild(guild).totbot()
        totbotId = totbotObj["channel"]
        if totbotId != 0:
            channel: discord.ChannelType = guild.get_channel(totbotId)
            bot_count: int = totmem - true_member_count
            await channel.edit(name='{0} {1}: {2} {3}'.format(totbotObj["prefix"], totbotObj["name"], bot_count, totbotObj["suffix"]))
            await asyncio.sleep(15)
            pass

    async def boosters(self, guild: discord.Guild):
        booster_count: int = guild.premium_subscription_count
        boosterObj = await self.config.guild(guild).booster()
        boosterId = boosterObj["channel"]
        if boosterId != 0:
            channel: discord.ChannelType = guild.get_channel(boosterId)
            await channel.edit(name='{0} {1}: {2} {3}'.format(boosterObj["prefix"], boosterObj["name"], booster_count, boosterObj["suffix"]))
            await asyncio.sleep(15)
            pass

        boosterBarObj = await self.config.guild(guild).boosterbar()
        boosterBarId = boosterBarObj["channel"]
        mess = ""
        stylefull = boosterBarObj["stylefull"]
        styleempty = boosterBarObj["styleempty"]
        if boosterBarId != 0:
            channel: discord.ChannelType = guild.get_channel(boosterBarId)
            if booster_count < 2:
                for i in range(booster_count):
                    mess = mess + stylefull
                for i in range(2 - booster_count):
                    mess = mess + styleempty
                await channel.edit(name='{0}Lvl 1{1}'.format(boosterBarObj["prefix"], mess))
                await asyncio.sleep(15)
            elif booster_count < 7:
                for i in range(booster_count):
                    mess = mess + stylefull
                for i in range(7 - booster_count):
                    mess = mess + styleempty
                await channel.edit(name='{0}Lvl 2{1}'.format(boosterBarObj["prefix"], mess))
                await asyncio.sleep(15)
            elif booster_count < 14:
                for i in range(booster_count - 7):
                    mess = mess + stylefull
                for i in range(14 - booster_count):
                    mess = mess + styleempty
                await channel.edit(name='{0}Lvl 3{1}'.format(boosterBarObj["prefix"], mess))
                await asyncio.sleep(15)
            elif booster_count > 14:
                for i in range(7):
                    mess = mess + stylefull
                await channel.edit(name='{0}Max{1}'.format(boosterBarObj["prefix"], mess))
                await asyncio.sleep(15)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if not member.bot:
            memberList = guild.members
            await self.config.guild(guild).truememcount.set(len([m for m in memberList if not m.bot]))
            await self.config.guild(guild).newmemcount.set(len([m for m in memberList if m.joined_at > datetime.today() - timedelta(days=1)]))
        await self.members(guild)
        await self.boosters(guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        if not member.bot:
            memberList = guild.members
            await self.config.guild(guild).truememcount.set(len([m for m in memberList if not m.bot]))
            await self.config.guild(guild).newmemcount.set(len([m for m in memberList if m.joined_at > datetime.today() - timedelta(days=1)]))
        await self.members(guild)
        await self.boosters(guild)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        await asyncio.sleep(30)
        if before.guild.premium_subscriber_role not in before.roles and after.guild.premium_subscriber_role in after.roles:
            await self.boosters(before.guild)
        elif before.guild.premium_subscriber_role in before.roles and after.guild.premium_subscriber_role not in after.roles:
            await self.boosters(before.guild)


    @commands.hybrid_group(name="serverhud", with_app_command=True)
    async def serverhud(self, ctx):
        """
        Base command for all server hud settings
        """
        pass

    @commands.guildowner_or_permissions()
    @serverhud.command(name="setchannel")
    async def setchannel(self, ctx: commands.Context, type: str, channel: discord.VoiceChannel) -> None:
        """
        Sets the channel info type and location

        The command syntax is [p]serverhud setchannel <type> <channel id>
        For a list of channel types use [p]serverhud types
        """
        channel = channel.id
        types = ["newmem", "totmem", "totbot", "truemem", "booster", "boosterbar"]
        for x in types:
            if x == type:
                if x == "newmem":
                    newmemDict: dict = await self.config.guild(ctx.guild).newmem()
                    newmemDict.update({"channel": channel})
                    await self.config.guild(ctx.guild).newmem.set(newmemDict)
                    await ctx.reply(f"The new member count channel has been set to <#{channel}>", ephemeral=True)
                elif x == "totmem":
                    totmemDict: dict = await self.config.guild(ctx.guild).totmem()
                    totmemDict.update({"channel": channel})
                    await self.config.guild(ctx.guild).totmem.set(totmemDict)
                    await ctx.reply(f"The total member count channel has been set to <#{channel}>", ephemeral=True)
                elif x == "totbot":
                    totbotDict: dict = await self.config.guild(ctx.guild).totbot()
                    totbotDict.update({"channel": channel})
                    await self.config.guild(ctx.guild).totbot.set(totbotDict)
                    await ctx.reply(f"The total bot count channel has been set to <#{channel}>", ephemeral=True)
                elif x == "truemem":
                    truememDict: dict = await self.config.guild(ctx.guild).truemem()
                    truememDict.update({"channel": channel})
                    await self.config.guild(ctx.guild).truemem.set(truememDict)
                    await ctx.reply(f"The True member count channel has been set to <#{channel}>", ephemeral=True)
                elif x == "booster":
                    boosterDict: dict = await self.config.guild(ctx.guild).booster()
                    boosterDict.update({"channel": channel})
                    await self.config.guild(ctx.guild).booster.set(boosterDict)
                    await ctx.reply(f"The Booster count channel has been set to <#{channel}>", ephemeral=True)
                elif x == "boosterbar":
                    boosterBarDict: dict = await self.config.guild(ctx.guild).boosterbar()
                    boosterBarDict.update({"channel": channel})
                    await self.config.guild(ctx.guild).boosterbar.set(boosterBarDict)
                    await ctx.reply(f"The Booster count channel has been set to <#{channel}>", ephemeral=True)
            else:
                pass
        pass

    @commands.guildowner_or_permissions()
    @serverhud.command(name="setprefix")
    async def setprefix(self, ctx: commands.Context, type: str, *, prefix: str) -> None:
        """
        Sets the prefix for this type of info channel

        For a list of channel types use [p]serverhud types
        """
        types = ["newmem", "totmem", "totbot", "truemem", "booster", "boosterbar"]
        for x in types:
            if x == type:
                if x == "newmem":
                    newmemDict: dict = await self.config.guild(ctx.guild).newmem()
                    newmemDict.update({"prefix": prefix})
                    await self.config.guild(ctx.guild).newmem.set(newmemDict)
                    await ctx.reply(f"The new member count prefix has been set to {prefix}", ephemeral=True)
                elif x == "totmem":
                    totmemDict: dict = await self.config.guild(ctx.guild).totmem()
                    totmemDict.update({"prefix": prefix})
                    await self.config.guild(ctx.guild).totmem.set(totmemDict)
                    await ctx.reply(f"The total member count prefix has been set to {prefix}", ephemeral=True)
                elif x == "totbot":
                    totbotDict: dict = await self.config.guild(ctx.guild).totbot()
                    totbotDict.update({"prefix": prefix})
                    await self.config.guild(ctx.guild).totbot.set(totbotDict)
                    await ctx.reply(f"The total bot count prefix has been set to {prefix}", ephemeral=True)
                elif x == "truemem":
                    truememDict: dict = await self.config.guild(ctx.guild).truemem()
                    truememDict.update({"prefix": prefix})
                    await self.config.guild(ctx.guild).truemem.set(truememDict)
                    await ctx.reply(f"The True member count prefix has been set to {prefix}", ephemeral=True)
                elif x == "booster":
                    boosterDict: dict = await self.config.guild(ctx.guild).booster()
                    boosterDict.update({"prefix": prefix})
                    await self.config.guild(ctx.guild).booster.set(boosterDict)
                    await ctx.reply(f"The Booster count prefix has been set to {prefix}", ephemeral=True)
                elif x == "boosterbar":
                    boosterBarDict: dict = await self.config.guild(ctx.guild).boosterbar()
                    boosterBarDict.update({"prefix": prefix})
                    await self.config.guild(ctx.guild).boosterbar.set(boosterBarDict)
                    await ctx.reply(f"The Booster Bar prefix has been set to {prefix}", ephemeral=True)
            else:
                pass
        pass

    @commands.guildowner_or_permissions()
    @serverhud.command(name="setsuffix")
    async def setsuffix(self, ctx: commands.Context, type: str, *, suffix: str) -> None:
        """
        Sets the suffix for this type of info channel

        For a list of channel types use [p]serverhud types
        """
        types = ["newmem", "totmem", "totbot", "truemem", "booster"]
        for x in types:
            if x == type:
                if x == "newmem":
                    newmemDict: dict = await self.config.guild(ctx.guild).newmem()
                    newmemDict.update({"suffix": suffix})
                    await self.config.guild(ctx.guild).newmem.set(newmemDict)
                    await ctx.reply(f"The new member count suffix has been set to {suffix}", ephemeral=True)
                elif x == "totmem":
                    totmemDict: dict = await self.config.guild(ctx.guild).totmem()
                    totmemDict.update({"suffix": suffix})
                    await self.config.guild(ctx.guild).totmem.set(totmemDict)
                    await ctx.reply(f"The total member count suffix has been set to {suffix}", ephemeral=True)
                elif x == "totbot":
                    totbotDict: dict = await self.config.guild(ctx.guild).totbot()
                    totbotDict.update({"suffix": suffix})
                    await self.config.guild(ctx.guild).totbot.set(totbotDict)
                    await ctx.reply(f"The total bot count suffix has been set to {suffix}", ephemeral=True)
                elif x == "truemem":
                    truememDict: dict = await self.config.guild(ctx.guild).truemem()
                    truememDict.update({"suffix": suffix})
                    await self.config.guild(ctx.guild).truemem.set(truememDict)
                    await ctx.reply(f"The True member count suffix has been set to {suffix}", ephemeral=True)
                elif x == "booster":
                    boosterDict: dict = await self.config.guild(ctx.guild).booster()
                    boosterDict.update({"suffix": suffix})
                    await self.config.guild(ctx.guild).booster.set(boosterDict)
                    await ctx.reply(f"The Booster count prefix has been set to {suffix}", ephemeral=True)
            else:
                pass
        pass

    @commands.guildowner_or_permissions()
    @serverhud.command(name="setname")
    async def setname(self, ctx: commands.Context, type: str, *, name: str) -> None:
        """
        Sets the name for this type of info channel

        For a list of channel types use [p]serverhud types
        """
        types = ["newmem", "totmem", "totbot", "truemem", "booster"]
        for x in types:
            if x == type:
                if x == "newmem":
                    newmemDict: dict = await self.config.guild(ctx.guild).newmem()
                    newmemDict.update({"name": name})
                    await self.config.guild(ctx.guild).newmem.set(newmemDict)
                    await ctx.reply(f"The new member count name has been set to {name}", ephemeral=True)
                elif x == "totmem":
                    totmemDict: dict = await self.config.guild(ctx.guild).totmem()
                    totmemDict.update({"name": name})
                    await self.config.guild(ctx.guild).totmem.set(totmemDict)
                    await ctx.reply(f"The total member count name has been set to {name}", ephemeral=True)
                elif x == "totbot":
                    totbotDict: dict = await self.config.guild(ctx.guild).totbot()
                    totbotDict.update({"name": name})
                    await self.config.guild(ctx.guild).totbot.set(totbotDict)
                    await ctx.reply(f"The total bot count name has been set to {name}", ephemeral=True)
                elif x == "truemem":
                    truememDict: dict = await self.config.guild(ctx.guild).truemem()
                    truememDict.update({"name": name})
                    await self.config.guild(ctx.guild).truemem.set(truememDict)
                    await ctx.reply(f"The True member count name has been set to {name}", ephemeral=True)
                elif x == "booster":
                    boosterDict: dict = await self.config.guild(ctx.guild).booster()
                    boosterDict.update({"name": name})
                    await self.config.guild(ctx.guild).booster.set(boosterDict)
                    await ctx.reply(f"The Booster count prefix has been set to {name}", ephemeral=True)
            else:
                pass
        pass

    @commands.guildowner_or_permissions()
    @serverhud.command(name="setstyle")
    async def setstyle(self, ctx: commands.Context, type: str, *, style: str) -> None:
        """
        Set's the style of the booster bar

        Valid types are full and empty
        """
        if type == "full":
            boosterBarDict: dict = await self.config.guild(ctx.guild).boosterbar()
            boosterBarDict.update({"stylefull": style})
            await self.config.guild(ctx.guild).boosterbar.set(boosterBarDict)
            await ctx.reply(f"The Booster Bar full style has been set to {style}", ephemeral=True)
        elif type == "empty":
            boosterBarDict: dict = await self.config.guild(ctx.guild).boosterbar()
            boosterBarDict.update({"styleempty": style})
            await self.config.guild(ctx.guild).boosterbar.set(boosterBarDict)
            await ctx.reply(f"The Booster Bar empty style has been set to {style}", ephemeral=True)
        else:
            await ctx.reply("That is not a valid booster bar type", ephemeral=True)

    @commands.guildowner_or_permissions()
    @serverhud.command(name="types")
    async def types(self, ctx: commands.Context) -> None:
        """
        Lists of the different types of channels you can set

        Use [p]serverhud setchannel <type> <channel mention>
        """
        mess = "The avaible types of channels are: new members from today (newmem), total members (totmem), total bots (totbot), True Members (truemem), Server Boosters Count (booster), Booster Bar (boosterbar)"
        await ctx.reply(mess, ephemeral=True)
        pass

    @commands.guildowner_or_permissions()
    @serverhud.command(name="test")
    async def test(self, ctx: commands.Context, event: str) -> None:
        """
        Test the cog to insure functionality

        You can test different events using this command:
        join, leave
        """
        if event == "join" or event == "leave":
            memberList = ctx.guild.members
            await self.config.guild(ctx.guild).truememcount.set(len([m for m in memberList if not m.bot]))
            await self.config.guild(ctx.guild).newmemcount.set(len([m for m in memberList if m.joined_at > datetime.today() - timedelta(days=1)]))
            await self.members(ctx.guild)
            await self.boosters(ctx.guild)
            await ctx.reply("Test of the member join/leave event.", ephemeral=True)
        else:
            await ctx.reply("That is not a valid event do [p]help serverhud test for a list of events", ephemeral=True)

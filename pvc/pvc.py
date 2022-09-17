from ast import Dict
from distutils.cmd import Command
from re import X
from typing import Literal
from typing_extensions import Self
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from discord import app_commands
import discord
import asyncio
import datetime
import logging
RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class pvc(commands.Cog):
    """
    Private voice channel cog
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.log = logging.getLogger('red.tpun.pvc')
        self.config = Config.get_conf(
            self,
            identifier=365398642334498816
        )
        default_guild = {
            "channel": 0,
            "channel_id": 0,
            "roles": []
        }
        self.config.register_guild(**default_guild)
        super().__init__()
        
    futureList: Dict = {}

    async def vcChannelRead(self, ctx: commands.Context):
        channel = await self.config.guild(ctx.guild).channel()
        return self.bot.get_channel(int(channel))

    async def vcRoleRead(self, ctx: commands.Context):
        return await self.config.guild(ctx.guild).roles()

    async def getVoiceChannel(self, ctx: commands.Context):
        vcId = await self.config.member(ctx.author).channel_id()
        if vcId is None or vcId == 0:
            voiceChannel = None
        else:
            voiceChannel = self.bot.get_channel(vcId)
        return voiceChannel

    async def checks(self, id, empty, ctx: commands.Context):
        channel = self.bot.get_channel(id)
        while empty.done() is not True:
            await asyncio.sleep(60)
            if len(channel.members) == 0:
                reason = "channel is empty"
                vcName = str(channel.name)
                x = await self.config.all_members(guild=ctx.guild)
                for vcOwner, ownDict in x.items():
                    for key, channelId in ownDict.items():
                        if channelId == id:
                            owner = ctx.guild.get_member(int(vcOwner))
                await self.config.member(owner).channel_id.set(0)
                await ctx.send("Succesfully deleted {2}'s voice channel: {0} because {1}".format(vcName, reason, owner.name))
                await channel.delete()
                pvc.futureList.pop(str(id), None)
                break
            else:
                pass

    def pred(self, emojis, mess1, user: discord.Member):
        return ReactionPredicate.with_emojis(emojis, mess1, user)

    async def emojiRequest(self, ctx: commands.Context, emoji, mess1, user: discord.Member):
        if emoji == "✅":
            vcId = await self.config.member(ctx.author).channel_id()
            voiceChannel = await self.bot.get_channel(vcId)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(ctx.author, read_messages=True, send_messages=True, read_message_history=True, view_channel=True, use_voice_activation=True, stream=True, connect=True, speak=True, reason="{0} accepted {1}'s request to join their vc: {2}".format(user.name, ctx.author.name, voiceChannel.name))
                if ctx.author.voice is not None:
                    if ctx.author.voice.channel.id != voiceChannel.id and ctx.author.voice.channel is not None:
                        await ctx.author.move_to(voiceChannel)
                        await ctx.reply("{0} accepted {1}'s vc request to join: {2}".format(user, ctx.author.name, voiceChannel.mention))
            else:
                await ctx.reply("{0} does not own a vc.".format(user.name), ephemeral=True)
            await mess1.delete()

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        # TODO: Replace this with the proper end user data removal handling.
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    @commands.hybrid_group(name='vc', with_app_command=True)
    async def vc(self, ctx: commands.Context):
        """
        Base command for all private voice channel commands
        """
        pass

    @vc.command(name='create', with_app_command=True)
    async def create(self, ctx: commands.Context, name: str="") -> None:
        """
        Creates a voice channel with <name>

        You can only have 1 vc. VC deletes after 1 minute of inactivity. You must join your vc within 1 minute or it will be deleted.
        """
        dsChannel = await self.vcChannelRead(ctx)
        roleList = await self.vcRoleRead(ctx)
        guild = ctx.guild
        vcChannel = await self.getVoiceChannel(ctx)
        if ctx.message.channel.id == dsChannel.id:
            category = ctx.channel.category
            run: bool = True
            if name == "":
                await ctx.reply("You need to type a voice channel name /vc create <Name>", ephemeral=True)
            else:
                pass
            if vcChannel is None:
                channel = await guild.create_voice_channel(name, category=category)
                await channel.set_permissions(ctx.author, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                for role in roleList:
                    await channel.set_permissions(guild.get_role(role), view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                if ctx.author.voice is not None and ctx.author.voice.channel.id != channel.id and ctx.author.voice.channel is not None:
                    await ctx.author.move_to(channel)
                vcId = channel.id
                await self.config.member(ctx.author).channel_id.set(vcId)
                await ctx.send("{0} was created by {1}".format(channel.mention, ctx.author.name))
                empty = asyncio.Future()
                pvc.futureList[str(vcId)] = empty
                asyncio.ensure_future(self.checks(vcId, empty, ctx))
            else:
                await ctx.reply("You already have a voice channel", ephemeral=True)
        else:
            await ctx.reply("This command only works in the custom vc {0} channel.".format(dsChannel.mention), ephemeral=True)

    @vc.command(name='delete', with_app_command=True)
    async def delete(self, ctx: commands.Context, reason: str="") -> None:
        """
        Deletes your personal channel

        The reason is optional
        """
        owner = ctx.author.id
        vcChannel = await self.getVoiceChannel(ctx)
        if vcChannel is not None:
            for id, futa in pvc.futureList.items():
                if futa.done() is not True:
                    futa.set_result(reason)
                    pvc.futureList.pop(str(vcChannel.id), None)
                    break
            if len(vcChannel.members) == 0 and reason is None:
                reason = "channel is empty"
            elif reason is None:
                reason = "user deleted their own channel"
            vcName = str(vcChannel.name)
            await vcChannel.delete()
            await self.config.member(ctx.author).channel_id.set(0)
            await ctx.reply("Succesfully deleted {2}'s voice channel: {0} because {1}".format(vcName, reason, ctx.author.name))
        else:
            await ctx.reply("{0} You can't delete a VC if you don't have one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name='name', with_app_command=True)
    async def name(self, ctx: commands.Context) -> None:
        """
        Returns the name of your vc
        """
        voiceChannel = await self.getVoiceChannel(ctx)
        if voiceChannel is not None:
            await ctx.reply("{0} Your personal vc is named {1}.".format(ctx.author.name, voiceChannel.mention), ephemeral=True)
        else:
            await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name='list', with_app_command=True)
    async def list(self, ctx: commands.Context) -> None:
        """
        Lists all the owners of vc's
        """
        guild: discord.Guild = ctx.guild
        embed = discord.Embed(title="VC Owners", description="All of the owners of private voice channels in the server are listed below", color=0xc72327)
        i = await self.config.all_members(guild=guild)
        for vcOwner, ownDict in i.items():
            for key, value in ownDict.items():
                if key == "channel_id":
                    if value == 0 or value is None:
                        pass
                    else:
                        name: discord.Member = await guild.fetch_member(vcOwner)
                        message = "<#" + str(value) + ">" + " ⌇ " + name.mention
                        embed.add_field(name="🔊", value=message, inline=True)
                else:
                    pass
        await ctx.reply(embed=embed)

    @vc.command(name="rename", with_app_command=True)
    async def rename(self, ctx: commands.Context, rename: str ="") -> None:
        """
        Renames your personal vc
        """
        if rename is None:
            await ctx.reply("{0} Please enter a new name for your vc.".format(ctx.author.name), ephemeral=True)
        else:
            voiceChannel = await self.getVoiceChannel(ctx)
            if voiceChannel is not None:
                await voiceChannel.edit(name=rename)
                await ctx.reply("{0} Your channel's name was changed to {1}".format(ctx.author.name, voiceChannel.mention))
            else:
                await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    def getRegion(self, int):
        conditions = {
            1: "us-west",
            2: "us-east",
            3: "us-south",
            4: "rotterdam",
            5: "singapore",
            6: "brazil",
            7: "hongkong",
            8: "india",
            9: "japan",
            10: "russia",
            11: "sydney",
            12: "southafrica",
            13: "south-korea"
        }
        if int in conditions.keys():
            return conditions[int]

    @vc.command(name="region", with_app_command=True)
    async def region(self, ctx: commands.Context, region: int) -> None:
        """
        Changes the region of your vc.

        The list of avaliable regions are as follows 0=Auto, 1=US West, 2=US East, 3=US South, 4=EU West,
         5=EU Central, 6=Brazil, 7=Hong Kong, 8=Brazil, 9=Japan, 10=Russia, 11=Sydney, 12=South Africa
        """
        region1 = self.getRegion(region)
        message = region1
        voiceChannel = await self.getVoiceChannel(ctx)
        if voiceChannel is not None:
            if region1 is None:
                region1 = None
                message = "auto"
            await voiceChannel.edit(rtc_region=region1)
            await ctx.reply("{0} Your vc: {1} was set to region {2}".format(ctx.author.name, voiceChannel.mention, message))
        else:
            await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="lock", with_app_command=True)
    async def lock(self, ctx: commands.Context) -> None:
        """
        Changes your vc to invite/request only.

        Members can join use `[p]vc invite <@user>` to invite someone or [p]vc request <@user to request to join
        """
        roleList = await self.vcRoleRead(ctx)
        voiceChannel = await self.getVoiceChannel(ctx)
        if voiceChannel is not None:
            for role in roleList:
                await voiceChannel.set_permissions(ctx.guild.get_role(role), view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, speak=True, connect=False, reason="{0} locked their vc: {1}".format(ctx.author.name, voiceChannel.name))
            await ctx.reply("{0} Your vc: {1} was locked".format(ctx.author.name, voiceChannel.mention))
        else:
            await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="unlock", with_app_command=True)
    async def unlock(self, ctx: commands.Context) -> None:
        """
        Unlocks your vc
        """
        owner = ctx.author.id
        roleList = await self.vcRoleRead(ctx)
        voiceChannel = await self.getVoiceChannel(ctx)
        if voiceChannel is not None:
            for role in roleList:
                await voiceChannel.set_permissions(ctx.guild.get_role(role), view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, speak=True, connect=True, reason="{0} unlocked their vc: {1}".format(owner, voiceChannel.name))
            await ctx.reply("{0} Your vc: {1} was unlocked".format(ctx.author.name, voiceChannel.mention))
        else:
            await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="invite", with_app_command=True)
    async def invite(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Invites a user to your vc

        Allow specified user to join your vc
        """
        if user is None:
            await ctx.reply("Please mention a user to invite.", ephemeral=True)
        else:
            voiceChannel = await self.getVoiceChannel(ctx)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, speak=True, connect=True, reason="{0} invited {1} to their vc: {2}".format(user.name, ctx.author.name, voiceChannel.name))
                await ctx.reply("{0} {1} invited you to their vc: {2}".format(user.mention, ctx.author.name, voiceChannel.mention))
            else:
                await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="limit", with_app_command=True)
    async def limit(self, ctx: commands.Context, limit: int = 0):
        """
        Sets the limit for how many spots are in vc, use 0 to remove limit
        """
        voiceChannel = await self.getVoiceChannel(ctx)
        if voiceChannel is not None:
            await voiceChannel.edit(user_limit=limit)
            await ctx.reply("{2} The user limit in your vc {0} was changed to {1}".format(voiceChannel.mention, limit, ctx.author.name))
        else:
            await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="request", with_app_command=True)
    async def request(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Sends a user a request to join their vc, request last 5 minutes
        """
        if user is None:
            await ctx.reply("{0} Please mention a user to request to join".format(ctx.author.name), ephemeral=True)
        else:
            if user.id == ctx.author.id:
                await ctx.reply("{0} you silly goose! You can't request to join your own vc.".format(ctx.author.name), ephemeral=True)
            else:
                dsChannel = await self.vcChannelRead(ctx)
                if ctx.message.channel.id == dsChannel.id:
                    embed = discord.Embed(color=0xe02522, title='Voice Channel Request', description='{0}: {1} is requesting to join your channel'.format(user.mention, ctx.author.name))
                    embed.set_footer(text='React with ✅ below to accept this request')
                    embed.timestamp = datetime.datetime.utcnow()
                    mess1 = await ctx.channel.send(embed=embed)
                    emojis = ["✅"]
                    start_adding_reactions(mess1, emojis)
                    try:
                        result = await ctx.bot.wait_for("reaction_add", timeout=300.0, check=self.pred(emojis, mess1, user))
                        emoji = str(result[0])
                        await self.emojiRequest(ctx, emoji, mess1, user)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('This request timed out.', ephemeral=True)
                        await mess1.delete()
                    except 404:
                        await ctx.channel.send("This request timed out", ephemeral=True)
                        await mess1.delete()
                    else:
                        pass

    @vc.command(name="kick", with_app_command=True)
    async def kick(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Kicks a user from your vc
        """
        if user is None:
            await ctx.reply("{0} Please mention a user to kick.".format(ctx.author.name), ephemeral=True)
        else:
            voiceChannel = await self.getVoiceChannel(ctx)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, stream=False, use_voice_activation=True, speak=False, connect=False, reason="{0} kicked {1} from their vc: {2}".format(ctx.author.name, user.name, voiceChannel.name))
                if user.voice is not None:
                    if user.voice.channel.id == voiceChannel.id:
                        await user.move_to(None)
                        await ctx.reply("{0} was kicked from your vc: {1}".format(user.name, voiceChannel.mention))
            else:
                await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="mute", with_app_command=True, type="user")
    async def mute(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Mutes a user inside your vc
        """
        if user is None:
            await ctx.reply("{0} Please mention a user to mute.".format(ctx.author.name), ephemeral=True)
        else:
            voiceChannel = await self.getVoiceChannel(ctx)
            if voiceChannel is not None and user.voice is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, stream=False, connect=True, speak=False, reason="{0} muted {1} in their vc: {2}".format(ctx.author.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await ctx.reply("{0} was muted in your vc: {1}".format(user.name, voiceChannel.mention))
            elif user.voice is None:
                await ctx.reply("You can't mute someone who isn't in a vc.", ephemeral=True)
            else:
                await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="unmute", with_app_command=True)
    async def unmute(self, ctx: commands.Context, user: discord.Member) -> None:
        """
        Unmutes a user inside your vc
        """
        if user is None:
            await ctx.reply("{0} Please mention a user to unmute.".format(ctx.author.name), ephemeral=True)
        else:
            voiceChannel = await self.getVoiceChannel(ctx)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, stream=True, use_voice_activation=True, connect=True, speak=True, reason="{0} unmuted {1} in their vc: {2}".format(ctx.author.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await ctx.reply("{0} was unmuted in your vc: {1}".format(user.name, voiceChannel.mention))
            else:
                await ctx.reply("{0} You have no vc created use /vc create <Name> to create one.".format(ctx.author.name), ephemeral=True)

    @vc.command(name="claim", with_app_command=True)
    async def claim(self, ctx: commands.Context) -> None:
        """
        Claims a voice channel from another user if they're not in it.
        """
        owner: int = 0
        newOwner = str(ctx.author.id)
        channelid = ctx.author.voice.channel.id
        guild = ctx.guild
        if channelid is not None:
            x = await self.config.all_members(guild=ctx.guild)
            for vcOwnList, ownDict in x.items():
                for key, vcId in ownDict.items():
                    if key == "channel_id":
                        if int(vcId) == int(channelid):
                            owner = int(vcOwnList)
                            ownerObj = await self.bot.get_or_fetch_member(guild, owner)
                            if ownerObj.voice is None or ownerObj.voice.channel.id != channelid:
                                await ctx.reply("{0} has claimed {1}".format(ctx.author.mention, self.bot.get_channel(vcId).mention))
                                await self.bot.get_channel(vcId).set_permissions(ctx.author, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                                await self.config.member(ownerObj).channel_id.set(0)
                                await self.config.member(ctx.author).channel_id.set(channelid)
                                break
                            else:
                                await ctx.reply("<@{0}> is still in their vc you can only run this when they have left".format(owner), ephemeral=True)

    @vc.command(name="transfer", with_app_command=True)
    async def transfer(self, ctx: commands.Context, newowner: discord.Member) -> None:
        """
        Transfers a voice channel to another user
        """
        owner = str(ctx.author.id)
        if ctx.author.voice is not None:
            channelid = ctx.author.voice.channel.id
            guild = ctx.guild
            alreadyOwns: bool = False
            if channelid is not None:
                x = await self.config.all_members(guild=guild)
                vcObj = await self.getVoiceChannel(ctx)
                ownerObj = await self.bot.get_or_fetch_member(guild, ctx.author.id)
                for vcOwner in x.items():
                    if vcOwner == newowner.id:
                        alreadyOwns = True
                else:
                    pass
                if vcObj is not None and vcObj.id == channelid:
                    if ownerObj.voice.channel.id == channelid and alreadyOwns == False:
                        await ctx.send("{0} has transfered vc ownership to {1}".format(ctx.author.mention, vcObj.mention))
                        await self.config.member(ctx.author).channel_id.set(0)
                        await self.config.member(newowner).channel_id.set(channelid)
                    elif alreadyOwns:
                        await ctx.reply("{0} already owns a vc".format(newowner.display_name), ephemeral=True)
                    else:
                        await ctx.reply("<@{0}> you must be in your vc to run this command".format(ctx.author.id), ephemeral=True)
                else:
                    await ctx.reply("You don't own this voice channel.", ephemeral=True)
        else:
            await ctx.reply("You can only run this command while you are in your voice channel.", ephemeral=True)

    @vc.command(name="setup", with_app_command=True)
    async def setup(self, ctx: commands.Context):
        """
        Set's up a channel for creating custom vc's in
        
        Please put this channel in the category you would like all custom vc's to be made in
        """
        guild = ctx.guild
        channel = await ctx.guild.create_text_channel("personal-vc-commands")
        mess0 = await ctx.channel.send("Make sure to put the personal-vc-commands channel in the category you wish channels to be made in. You may rename the channel to whatever you wish.")
        await self.config.guild(guild).channel.set(channel.id)
        mess1 = await ctx.channel.send("Please ping any roles you wish to have permissions to join channels on creation. These roles will also be used for unlock/lock commands. If you wish to allow anyone to join on creation type 'none'.")

        def check(m):
            return m.channel == mess1.channel

        msg = await self.bot.wait_for('message', check=check, timeout=600)
        roles = []
        if msg.content != "none":
            for i in msg.role_mentions:
                roles.append(i.id)
        else:
            roles.append(ctx.guild.id)
        await mess1.delete()
        await self.config.guild(guild).roles.set(roles)
        mess2 = await ctx.reply("Your settings are currently: {0} as the channel and {1} are the public roles that will be used.".format(channel.name, roles), ephemeral=True)
        await asyncio.sleep(30)
        await mess0.delete()

    @commands.is_owner()
    @vc.command(name="clearconfig")
    async def clearconfig(self, ctx: commands.Context):
        await self.config.clear_all_members(guild=ctx.guild)
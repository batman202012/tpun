from ast import Dict
from typing import Literal
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import discord
import asyncio
import datetime
import logging
RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


setattr(commands, "Literal", Literal)
from functools import partial
hybrid_command = partial(commands.hybrid_command, with_app_command=True)
hybrid_group = partial(commands.hybrid_group, with_app_command=True)

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
            "owners": {},
            "roles": []
        }
        self.config.register_guild(**default_guild)
    futureList: Dict = {}

    async def getVcList(self, guild):
        x = await self.config.guild(guild).owners()
        return x

    async def vcOwnerRead(self, guild, owner):
        i = await self.config.guild(guild).owners()
        for vcOwner, vcId in i.items():
            if vcOwner == str(owner):
                return self.bot.get_channel(int(vcId))

    async def vcChannelRead(self, ctx: commands.Context):
        channel = await self.config.guild(ctx.guild).channel()
        return self.bot.get_channel(int(channel))

    async def vcRoleRead(self, ctx: commands.Context):
        return await self.config.guild(ctx.guild).roles()

    async def checks(self, id, empty, ctx: commands.Context):
        channel = self.bot.get_channel(id)
        while empty.done() is not True:
            await asyncio.sleep(60)
            if len(channel.members) == 0:
                await pvc.delete(self, ctx)
                pvc.futureList.pop(str(id), None)
                break
            else:
                pass

    def pred(self, emojis, mess1, user: discord.Member):
        return ReactionPredicate.with_emojis(emojis, mess1, user)

    async def emojiRequest(self, ctx: commands.Context, emoji, mess1, user: discord.Member):
        if emoji == "✅":
            voiceChannel = await self.vcOwnerRead(ctx.guild, user.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(ctx.author, read_messages=True, send_messages=True, read_message_history=True, view_channel=True, use_voice_activation=True, stream=True, connect=True, speak=True, reason="{0} accepted {1}'s request to join their vc: {2}".format(user.name, ctx.author.name, voiceChannel.name))
                if ctx.author.voice is not None:
                    if ctx.author.voice.channel.id != voiceChannel.id and ctx.author.voice.channel is not None:
                        await ctx.author.move_to(voiceChannel)
                        await ctx.send("{0} accepted {1}'s vc request to join: {2}".format(user, ctx.author.name, voiceChannel.mention))
            else:
                await ctx.send("{0} does not own a vc.".format(user.name))
            await mess1.delete()

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        # TODO: Replace this with the proper end user data removal handling.
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    @hybrid_group()
    async def vc(self, ctx: commands.Context):
        """
        Base command for all private voice channel commands
        """
        pass

    @vc.command(name='create')
    async def create(self, ctx: commands.Context, vcName: str=""):
        """
        Creates a voice channel with <name>

        You can only have 1 vc. VC deletes after 1 minute of inactivity. You must join your vc within 1 minute or it will be deleted.
        """
        dsChannel = await self.vcChannelRead(ctx)
        roleList = await self.vcRoleRead(ctx)
        guild = ctx.guild
        owners = await self.config.guild(guild).owners()
        if ctx.message.channel.id == dsChannel.id:
            category = ctx.channel.category
            run: bool = True
            if vcName == "":
                await ctx.response.send_message("{0} You need to type a voice channel name {1}vc create <Name>".format(ctx.author.name, ctx.prefix), ephemeral=True)
            else:
                owner = ctx.author.id
                if vcName == "no activity":
                    await ctx.response.send_message("You can't create a game vc if you're not playing a game.", ephemeral=True)
                    run = False
            vc = await self.vcOwnerRead(guild, ctx.author.id)
            if vc:
                await ctx.response.send_message("{0} You already have a vc created named {1}".format(ctx.author.name, str(vc.name)), ephemeral=True)
                run = False
            if run:
                channel = await guild.create_voice_channel(vcName, category=category)
                await channel.set_permissions(ctx.author, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                for role in roleList:
                    await channel.set_permissions(guild.get_role(role), view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                if ctx.author.voice is not None and ctx.author.voice.channel.id != channel.id and ctx.author.voice.channel is not None:
                    await ctx.author.move_to(channel)
                vcId = channel.id
                nC = {owner: vcId}
                owners.update(nC)
                await self.config.guild(guild).owners.set(owners)
                await ctx.response.send_message("{0} was created by {1}".format(channel.mention, ctx.author.name))
                empty = asyncio.Future()
                pvc.futureList[str(vcId)] = empty
                asyncio.ensure_future(self.checks(vcId, empty, ctx))
        else:
            await ctx.send("This command only works in the custom vc {0} channel.".format(dsChannel.mention), ephemeral=True)

    @vc.command(name='delete')
    async def delete(self, ctx: commands.Context, *, reason: str=""):
        """
        Deletes your personal channel

        The reason is optional
        """
        owner = ctx.author.id
        x = await self.config.guild(ctx.guild).owners()
        vc = await self.vcOwnerRead(ctx.guild, ctx.author.id)
        if vc:
            vcId = vc.id
            for id, futa in pvc.futureList.items():
                if int(id) == vcId and futa.done() is not True:
                    futa.set_result(reason)
                    pvc.futureList.pop(str(vcId), None)
                    break
            channel = self.bot.get_channel(vcId)
            if len(channel.members) == 0 and reason == "":
                reason = "channel is empty"
            elif reason is None:
                reason = "user deleted their own channel"
            vcName = str(channel.name)
            await channel.delete()
            x.pop(str(owner), None)
            await self.config.guild(ctx.guild).owners.set(x)
            await ctx.send("Succesfully deleted {2}'s voice channel: {0} because {1}".format(vcName, reason, ctx.author.name))
        else:
            await ctx.send("{0} You can't delete a VC if you don't have one.".format(ctx.author.name))

    @vc.command(name='name')
    async def name(self, ctx: commands.Context):
        """
        Returns the name of your vc
        """
        voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
        if voiceChannel is not None:
            await ctx.send("{0} Your personal vc is named {1}.".format(ctx.author.name, voiceChannel.mention))
        else:
            await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.format))

    @vc.command(name='list')
    async def list(self, ctx: commands.Context):
        """
        Lists all the owners of vc's
        """
        guild: discord.Guild = ctx.guild
        embed = discord.Embed(title="VC Owners", description="All of the owners of private voice channels in the server are listed below", color=0xc72327)
        i = await self.getVcList(guild)
        for vcOwner, vcId in i.items():
            voiceChannel: discord.VoiceChannel = self.bot.get_channel(int(vcId))
            name: discord.Member = await guild.fetch_member(vcOwner)
            message = "<#" + str(voiceChannel.id) + ">" + " ⌇ " + name.mention
            embed.add_field(name="🔊", value=message, inline=True)
        await ctx.send(embed=embed)

    @vc.command(name="rename")
    async def rename(self, ctx: commands.Context, *, rename=None):
        """
        Renames your personal vc
        """
        if rename is None:
            await ctx.send("{0} Please enter a new name for your vc.".format(ctx.author.name))
        else:
            voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
            if voiceChannel is not None:
                await voiceChannel.edit(name=rename)
                await ctx.send("{0} Your channel's name was changed to {1}".format(ctx.author.name, voiceChannel.mention))
            else:
                await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

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

    @vc.command(name="region")
    async def region(self, ctx: commands.Context, region: int):
        """
        Changes the region of your vc.

        The list of avaliable regions are as follows 0=Auto, 1=US West, 2=US East, 3=US South, 4=EU West,
         5=EU Central, 6=Brazil, 7=Hong Kong, 8=Brazil, 9=Japan, 10=Russia, 11=Sydney, 12=South Africa
        """
        region1 = self.getRegion(region)
        message = region1
        voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
        if voiceChannel is not None:
            if region1 is None:
                region1 = None
                message = "auto"
            await voiceChannel.edit(rtc_region=region1)
            await ctx.send("{0} Your vc: {1} was set to region {2}".format(ctx.author.name, voiceChannel.mention, message))
        else:
            await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="lock")
    async def lock(self, ctx: commands.Context):
        """
        Changes your vc to invite/request only.

        Members can join use `[p]vc invite <@user>` to invite someone or [p]vc request <@user to request to join
        """
        roleList = await self.vcRoleRead(ctx)
        voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
        if voiceChannel is not None:
            for role in roleList:
                await voiceChannel.set_permissions(ctx.guild.get_role(role), view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, speak=True, connect=False, reason="{0} locked their vc: {1}".format(ctx.author.name, voiceChannel.name))
            await ctx.send("{0} Your vc: {1} was locked".format(ctx.author.name, voiceChannel.mention))
        else:
            await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="unlock")
    async def unlock(self, ctx: commands.Context):
        """
        Unlocks your vc
        """
        owner = ctx.author.id
        roleList = await self.vcRoleRead(ctx)
        voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
        if voiceChannel is not None:
            for role in roleList:
                await voiceChannel.set_permissions(ctx.guild.get_role(role), view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, speak=True, connect=True, reason="{0} unlocked their vc: {1}".format(owner, voiceChannel.name))
            await ctx.send("{0} Your vc: {1} was unlocked".format(ctx.author.name, voiceChannel.mention))
        else:
            await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="invite")
    async def invite(self, ctx: commands.Context, user: discord.Member):
        """
        Invites a user to your vc

        Allow specified user to join your vc
        """
        if user is None:
            await ctx.send("Please mention a user to invite.")
        else:
            voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, speak=True, connect=True, reason="{0} invited {1} to their vc: {2}".format(user.name, ctx.author.name, voiceChannel.name))
                await ctx.send("{0} {1} invited you to their vc: {2}".format(user.mention, ctx.author.name, voiceChannel.mention))
            else:
                await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="limit")
    async def limit(self, ctx: commands.Context, limit: int = 0):
        """
        Sets the limit for how many spots are in vc, use 0 to remove limit
        """
        voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
        if voiceChannel is not None:
            await voiceChannel.edit(user_limit=limit)
            await ctx.send("{2} The user limit in your vc {0} was changed to {1}".format(voiceChannel.mention, limit, ctx.author.name))
        else:
            await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="request")
    async def request(self, ctx: commands.Context, user: discord.Member):
        """
        Sends a user a request to join their vc, request last 5 minutes
        """
        if user is None:
            await ctx.send("{0} Please mention a user to request to join".format(ctx.author.name))
        else:
            if user.id == ctx.author.id:
                await ctx.send("{0} you silly goose! You can't request to join your own vc.".format(ctx.author.name))
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
                        await ctx.channel.send('This request timed out.')
                        await mess1.delete()
                    except 404:
                        await ctx.channel.send("This request timed out")
                        await mess1.delete()
                    else:
                        pass

    @vc.command(name="kick")
    async def kick(self, ctx: commands.Context, user: discord.Member):
        """
        Kicks a user from your vc
        """
        if user is None:
            await ctx.send("{0} Please mention a user to kick.".format(ctx.author.name))
        else:
            voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, stream=False, use_voice_activation=True, speak=False, connect=False, reason="{0} kicked {1} from their vc: {2}".format(ctx.author.name, user.name, voiceChannel.name))
                if user.voice is not None:
                    if user.voice.channel.id == voiceChannel.id:
                        await user.move_to(None)
                        await ctx.send("{0} was kicked from your vc: {1}".format(user.name, voiceChannel.mention))
            else:
                await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="mute")
    async def mute(self, ctx: commands.Context, user: discord.Member):
        """
        Mutes a user inside your vc
        """
        if user is None:
            await ctx.send("{0} Please mention a user to mute.".format(ctx.author.name))
        else:
            voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
            if voiceChannel is not None and user.voice is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, stream=False, connect=True, speak=False, reason="{0} muted {1} in their vc: {2}".format(ctx.author.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await ctx.send("{0} was muted in your vc: {1}".format(user.name, voiceChannel.mention))
            elif user.voice is None:
                await ctx.send("You can't mute someone who isn't in a vc.")
            else:
                await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="unmute")
    async def unmute(self, ctx: commands.Context, user: discord.Member):
        """
        Unmutes a user inside your vc
        """
        if user is None:
            await ctx.send("{0} Please mention a user to unmute.".format(ctx.author.name))
        else:
            voiceChannel = await self.vcOwnerRead(ctx.guild, ctx.author.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, stream=True, use_voice_activation=True, connect=True, speak=True, reason="{0} unmuted {1} in their vc: {2}".format(ctx.author.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await ctx.send("{0} was unmuted in your vc: {1}".format(user.name, voiceChannel.mention))
            else:
                await ctx.send("{0} You have no vc created use {1}vc create <Name> to create one.".format(ctx.author.name, ctx.prefix))

    @vc.command(name="claim")
    async def claim(self, ctx: commands.Context):
        """
        Claims a voice channel from another user if they're not in it.
        """
        owner: int = 0
        newOwner = str(ctx.author.id)
        channelid = ctx.author.voice.channel.id
        newWrite = {newOwner: channelid}
        guild = ctx.guild
        if channelid is not None:
            x = await self.config.guild(guild).owners()
            for vcOwnList, vcNameList in x.items():
                if int(vcNameList) == int(channelid):
                    owner = int(vcOwnList)
                    ownerObj = await self.bot.get_or_fetch_member(guild, owner)
                    if ownerObj.voice is None or ownerObj.voice.channel.id != channelid:
                        await ctx.send("{0} has claimed {1}".format(ctx.author.mention, self.bot.get_channel(vcNameList).mention))
                        await self.bot.get_channel(vcNameList).set_permissions(ctx.author, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                        x.pop(str(owner), None)
                        x.update(newWrite)
                        break
                    else:
                        await ctx.send("<@{0}> is still in their vc you can only run this when they have left".format(owner))
            await self.config.guild(guild).owners.set(x)

    @vc.command(name="transfer")
    async def transfer(self, ctx: commands.Context, newOwner: discord.Member):
        """
        Transfers a voice channel to another user
        """
        owner = str(ctx.author.id)
        if ctx.author.voice is not None:
            channelid = ctx.author.voice.channel.id
            newWrite = {str(newOwner.id): int(channelid)}
            guild = ctx.guild
            if channelid is not None:
                x = await self.config.guild(guild).owners()
                vcObj = await self.vcOwnerRead(guild, ctx.author.id)
                ownerObj = await self.bot.get_or_fetch_member(guild, ctx.author.id)
                if vcObj is not None and vcObj.id == channelid:
                    if ownerObj.voice.channel.id == channelid and str(newOwner.id) not in x.keys():
                        await ctx.send("{0} has transfered vc ownership to {1}".format(ctx.author.mention, vcObj.mention))
                        x.pop(str(owner), None)
                        x.update(newWrite)
                    elif str(newOwner.id) in x.keys():
                        await ctx.send("{0} already owns a vc".format(newOwner.display_name))
                    else:
                        await ctx.send("<@{0}> you must be in your vc to run this command".format(ctx.author.id))
                else:
                    await ctx.send("You don't own this voice channel.")
                await self.config.guild(guild).owners.set(x)
        else:
            await ctx.send("You can only run this command while you are in your voice channel.")

    @commands.guildowner_or_permissions()
    @vc.command(name="setup")
    async def setup(self, ctx: commands.Context):
        """
        Set's up a channel for creating custom vc's in, please put this channel in the category you would like all custom vc's to be made in
        """
        guild = ctx.guild
        channel = await ctx.guild.create_text_channel("personal-vc-commands")
        mess0 = await ctx.send("Make sure to put the personal-vc-commands channel in the category you wish channels to be made in. You may rename the channel to whatever you wish.")
        await self.config.guild(guild).channel.set(channel.id)
        mess1 = await ctx.send("Please ping any roles you wish to have permissions to join channels on creation. These roles will also be used for unlock/lock commands. If you wish to allow anyone to join on creation type 'none'.")

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
        mess2 = await ctx.send("Your settings are currently: {0} as the channel and {1} are the public roles that will be used.".format(channel.name, roles))
        await asyncio.sleep(30)
        await mess0.delete()
        await mess2.delete()

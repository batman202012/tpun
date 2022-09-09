from ast import Dict
from distutils.cmd import Command
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


class pvc(commands.Cog):
    """
    Private voice channel cog
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        log = logging.getLogger('red.tpun.pvc')
        self.log = log
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
        super().__init__()
        
    futureList: Dict = {}

    async def getVcList(self, guild):
        x = await self.config.guild(guild).owners()
        return x

    async def vcOwnerRead(self, guild, owner):
        i = await self.config.guild(guild).owners()
        for vcOwner, vcId in i.items():
            if vcOwner == str(owner):
                return self.bot.get_channel(int(vcId))

    async def vcChannelRead(self, interaction: discord.Interaction):
        channel = await self.config.guild(interaction.guild).channel()
        return self.bot.get_channel(int(channel))

    async def vcRoleRead(self, interaction: discord.Interaction):
        return await self.config.guild(interaction.guild).roles()

    async def checks(self, id, empty, interaction: discord.Interaction):
        channel = self.bot.get_channel(id)
        while empty.done() is not True:
            await asyncio.sleep(60)
            if len(channel.members) == 0:
                await pvc.delete(self, interaction)
                pvc.futureList.pop(str(id), None)
                break
            else:
                pass

    def pred(self, emojis, mess1, user: discord.Member):
        return ReactionPredicate.with_emojis(emojis, mess1, user)

    async def emojiRequest(self, interaction: discord.Interaction, emoji, mess1, user: discord.Member):
        if emoji == "✅":
            voiceChannel = await self.vcOwnerRead(interaction.guild, user.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(interaction.user, read_messages=True, send_messages=True, read_message_history=True, view_channel=True, use_voice_activation=True, stream=True, connect=True, speak=True, reason="{0} accepted {1}'s request to join their vc: {2}".format(user.name, interaction.user.name, voiceChannel.name))
                if interaction.user.voice is not None:
                    if interaction.user.voice.channel.id != voiceChannel.id and interaction.user.voice.channel is not None:
                        await interaction.user.move_to(voiceChannel)
                        await interaction.response.send_message("{0} accepted {1}'s vc request to join: {2}".format(user, interaction.user.name, voiceChannel.mention))
            else:
                await interaction.response.send_message("{0} does not own a vc.".format(user.name), ephemeral=True)
            await mess1.delete()

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        # TODO: Replace this with the proper end user data removal handling.
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    vc = discord.app_commands.Group(name="vc", description="Base command for all private voice channel commands")

    @vc.command(name='create')
    async def create(self, interaction: discord.Interaction, vcname: str="") -> None:
        """
        Creates a voice channel with <name>

        You can only have 1 vc. VC deletes after 1 minute of inactivity. You must join your vc within 1 minute or it will be deleted.
        """
        dsChannel = await self.vcChannelRead(interaction)
        roleList = await self.vcRoleRead(interaction)
        guild = interaction.guild
        owners = await self.config.guild(guild).owners()
        if interaction.channel.id == dsChannel.id:
            category = interaction.channel.category
            run: bool = True
            if vcname == "":
                await interaction.response.send_message("You need to type a voice channel name /vc create <Name>", ephemeral=True)
            else:
                owner = interaction.user.id
                if vcname == "no activity":
                    await interaction.response.send_message("You can't create a game vc if you're not playing a game.", ephemeral=True)
                    run = False
            vc = await self.vcOwnerRead(guild, interaction.user.id)
            if vc:
                await interaction.response.send_message("You already have a vc created named {1}".format(str(vc.name)), ephemeral=True)
                run = False
            if run:
                channel = await guild.create_voice_channel(vcname, category=category)
                await channel.set_permissions(interaction.user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                for role in roleList:
                    await channel.set_permissions(guild.get_role(role), view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                if interaction.user.voice is not None and interaction.user.voice.channel.id != channel.id and interaction.user.voice.channel is not None:
                    await interaction.user.move_to(channel)
                vcId = channel.id
                nC = {owner: vcId}
                owners.update(nC)
                await self.config.guild(guild).owners.set(owners)
                await interaction.response.send_message("{0} was created by {1}".format(channel.mention, interaction.user.name))
                empty = asyncio.Future()
                pvc.futureList[str(vcId)] = empty
                asyncio.ensure_future(self.checks(vcId, empty, interaction))
        else:
            await interaction.response.send_message("This command only works in the custom vc {0} channel.".format(dsChannel.mention), ephemeral=True)

    @vc.command(name='delete')
    async def delete(self, interaction: discord.Interaction, reason: str="") -> None:
        """
        Deletes your personal channel

        The reason is optional
        """
        owner = interaction.user.id
        x = await self.config.guild(interaction.guild).owners()
        vc = await self.vcOwnerRead(interaction.guild, interaction.user.id)
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
            await self.config.guild(interaction.guild).owners.set(x)
            await interaction.response.send_message("Succesfully deleted {2}'s voice channel: {0} because {1}".format(vcName, reason, interaction.user.name))
        else:
            await interaction.response.send_message("{0} You can't delete a VC if you don't have one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name='name')
    async def name(self, interaction: discord.Interaction) -> None:
        """
        Returns the name of your vc
        """
        voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
        if voiceChannel is not None:
            await interaction.response.send_message("{0} Your personal vc is named {1}.".format(interaction.user.name, voiceChannel.mention), ephemeral=True)
        else:
            await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name='list')
    async def list(self, interaction: discord.Interaction) -> None:
        """
        Lists all the owners of vc's
        """
        guild: discord.Guild = interaction.guild
        embed = discord.Embed(title="VC Owners", description="All of the owners of private voice channels in the server are listed below", color=0xc72327)
        i = await self.getVcList(guild)
        for vcOwner, vcId in i.items():
            voiceChannel: discord.VoiceChannel = self.bot.get_channel(int(vcId))
            name: discord.Member = await guild.fetch_member(vcOwner)
            message = "<#" + str(voiceChannel.id) + ">" + " ⌇ " + name.mention
            embed.add_field(name="🔊", value=message, inline=True)
        await interaction.response.send_message(embed=embed)

    @vc.command(name="rename")
    async def rename(self, interaction: discord.Interaction, rename: str ="") -> None:
        """
        Renames your personal vc
        """
        if rename is None:
            await interaction.response.send_message("{0} Please enter a new name for your vc.".format(interaction.user.name), ephemeral=True)
        else:
            voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
            if voiceChannel is not None:
                await voiceChannel.edit(name=rename)
                await interaction.response.send_message("{0} Your channel's name was changed to {1}".format(interaction.user.name, voiceChannel.mention))
            else:
                await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

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
    async def region(self, interaction: discord.Interaction, region: int) -> None:
        """
        Changes the region of your vc.

        The list of avaliable regions are as follows 0=Auto, 1=US West, 2=US East, 3=US South, 4=EU West,
         5=EU Central, 6=Brazil, 7=Hong Kong, 8=Brazil, 9=Japan, 10=Russia, 11=Sydney, 12=South Africa
        """
        region1 = self.getRegion(region)
        message = region1
        voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
        if voiceChannel is not None:
            if region1 is None:
                region1 = None
                message = "auto"
            await voiceChannel.edit(rtc_region=region1)
            await interaction.response.send_message("{0} Your vc: {1} was set to region {2}".format(interaction.user.name, voiceChannel.mention, message))
        else:
            await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="lock")
    async def lock(self, interaction: discord.Interaction) -> None:
        """
        Changes your vc to invite/request only.

        Members can join use `[p]vc invite <@user>` to invite someone or [p]vc request <@user to request to join
        """
        roleList = await self.vcRoleRead(interaction)
        voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
        if voiceChannel is not None:
            for role in roleList:
                await voiceChannel.set_permissions(interaction.guild.get_role(role), view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, speak=True, connect=False, reason="{0} locked their vc: {1}".format(interaction.user.name, voiceChannel.name))
            await interaction.response.send_message("{0} Your vc: {1} was locked".format(interaction.user.name, voiceChannel.mention))
        else:
            await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="unlock")
    async def unlock(self, interaction: discord.Interaction) -> None:
        """
        Unlocks your vc
        """
        owner = interaction.user.id
        roleList = await self.vcRoleRead(interaction)
        voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
        if voiceChannel is not None:
            for role in roleList:
                await voiceChannel.set_permissions(interaction.guild.get_role(role), view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, speak=True, connect=True, reason="{0} unlocked their vc: {1}".format(owner, voiceChannel.name))
            await interaction.response.send_message("{0} Your vc: {1} was unlocked".format(interaction.user.name, voiceChannel.mention))
        else:
            await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="invite")
    async def invite(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """
        Invites a user to your vc

        Allow specified user to join your vc
        """
        if user is None:
            await interaction.response.send_message("Please mention a user to invite.", ephemeral=True)
        else:
            voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, speak=True, connect=True, reason="{0} invited {1} to their vc: {2}".format(user.name, interaction.user.name, voiceChannel.name))
                await interaction.response.send_message("{0} {1} invited you to their vc: {2}".format(user.mention, interaction.user.name, voiceChannel.mention))
            else:
                await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="limit")
    async def limit(self, interaction: discord.Interaction, limit: int = 0):
        """
        Sets the limit for how many spots are in vc, use 0 to remove limit
        """
        voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
        if voiceChannel is not None:
            await voiceChannel.edit(user_limit=limit)
            await interaction.response.send_message("{2} The user limit in your vc {0} was changed to {1}".format(voiceChannel.mention, limit, interaction.user.name))
        else:
            await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="request")
    async def request(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """
        Sends a user a request to join their vc, request last 5 minutes
        """
        if user is None:
            await interaction.response.send_message("{0} Please mention a user to request to join".format(interaction.user.name), ephemeral=True)
        else:
            if user.id == interaction.user.id:
                await interaction.response.send_message("{0} you silly goose! You can't request to join your own vc.".format(interaction.user.name), ephemeral=True)
            else:
                dsChannel = await self.vcChannelRead(interaction)
                if interaction.message.channel.id == dsChannel.id:
                    embed = discord.Embed(color=0xe02522, title='Voice Channel Request', description='{0}: {1} is requesting to join your channel'.format(user.mention, interaction.user.name))
                    embed.set_footer(text='React with ✅ below to accept this request')
                    embed.timestamp = datetime.datetime.utcnow()
                    mess1 = await interaction.channel.send(embed=embed)
                    emojis = ["✅"]
                    start_adding_reactions(mess1, emojis)
                    try:
                        result = await interaction.bot.wait_for("reaction_add", timeout=300.0, check=self.pred(emojis, mess1, user))
                        emoji = str(result[0])
                        await self.emojiRequest(interaction, emoji, mess1, user)
                    except asyncio.TimeoutError:
                        await interaction.channel.send('This request timed out.', ephemeral=True)
                        await mess1.delete()
                    except 404:
                        await interaction.channel.send("This request timed out", ephemeral=True)
                        await mess1.delete()
                    else:
                        pass

    @vc.command(name="kick")
    async def kick(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """
        Kicks a user from your vc
        """
        if user is None:
            await interaction.response.send_message("{0} Please mention a user to kick.".format(interaction.user.name), ephemeral=True)
        else:
            voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, stream=False, use_voice_activation=True, speak=False, connect=False, reason="{0} kicked {1} from their vc: {2}".format(interaction.user.name, user.name, voiceChannel.name))
                if user.voice is not None:
                    if user.voice.channel.id == voiceChannel.id:
                        await user.move_to(None)
                        await interaction.response.send_message("{0} was kicked from your vc: {1}".format(user.name, voiceChannel.mention))
            else:
                await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="mute")
    async def mute(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """
        Mutes a user inside your vc
        """
        if user is None:
            await interaction.response.send_message("{0} Please mention a user to mute.".format(interaction.user.name), ephemeral=True)
        else:
            voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
            if voiceChannel is not None and user.voice is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, stream=False, connect=True, speak=False, reason="{0} muted {1} in their vc: {2}".format(interaction.user.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await interaction.response.send_message("{0} was muted in your vc: {1}".format(user.name, voiceChannel.mention))
            elif user.voice is None:
                await interaction.response.send_message("You can't mute someone who isn't in a vc.", ephemeral=True)
            else:
                await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="unmute")
    async def unmute(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """
        Unmutes a user inside your vc
        """
        if user is None:
            await interaction.response.send_message("{0} Please mention a user to unmute.".format(interaction.user.name), ephemeral=True)
        else:
            voiceChannel = await self.vcOwnerRead(interaction.guild, interaction.user.id)
            if voiceChannel is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, stream=True, use_voice_activation=True, connect=True, speak=True, reason="{0} unmuted {1} in their vc: {2}".format(interaction.user.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await interaction.response.send_message("{0} was unmuted in your vc: {1}".format(user.name, voiceChannel.mention))
            else:
                await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(interaction.user.name), ephemeral=True)

    @vc.command(name="claim")
    async def claim(self, interaction: discord.Interaction) -> None:
        """
        Claims a voice channel from another user if they're not in it.
        """
        owner: int = 0
        newOwner = str(interaction.user.id)
        isInVoice = interaction.user.voice
        guild = interaction.guild
        if isInVoice is not None:
            channelid = interaction.user.voice.channel.id
            newWrite = {newOwner: channelid}
            x = await self.config.guild(guild).owners()
            for vcOwnList, vcNameList in x.items():
                if int(vcNameList) == int(channelid):
                    owner = int(vcOwnList)
                    ownerObj = await self.bot.get_or_fetch_member(guild, owner)
                    if ownerObj.voice is None or ownerObj.voice.channel.id != channelid:
                        await interaction.response.send_message("{0} has claimed {1}".format(interaction.user.mention, self.bot.get_channel(vcNameList).mention))
                        await self.bot.get_channel(vcNameList).set_permissions(interaction.user, view_channel=True, read_messages=True, send_messages=True, read_message_history=True, use_voice_activation=True, stream=True, speak=True, connect=True)
                        x.pop(str(owner), None)
                        x.update(newWrite)
                        break
                    else:
                        await interaction.response.send_message("<@{0}> is still in their vc you can only run this when they have left".format(owner), ephemeral=True)
            await self.config.guild(guild).owners.set(x)
        else:
            await interaction.response.send_message("You can't claim a voice channel if you aren't in one", ephemeral=True)

    @vc.command(name="transfer")
    async def transfer(self, interaction: discord.Interaction, newowner: discord.Member) -> None:
        """
        Transfers a voice channel to another user
        """
        owner = str(interaction.user.id)
        if interaction.user.voice is not None:
            channelid = interaction.user.voice.channel.id
            newWrite = {str(newowner.id): int(channelid)}
            guild = interaction.guild
            if channelid is not None:
                x = await self.config.guild(guild).owners()
                vcObj = await self.vcOwnerRead(guild, interaction.user.id)
                ownerObj = await self.bot.get_or_fetch_member(guild, interaction.user.id)
                if vcObj is not None and vcObj.id == channelid:
                    if ownerObj.voice.channel.id == channelid and str(newowner.id) not in x.keys():
                        await interaction.response.send_message("{0} has transfered vc ownership to {1}".format(interaction.user.mention, vcObj.mention))
                        x.pop(str(owner), None)
                        x.update(newWrite)
                    elif str(newowner.id) in x.keys():
                        await interaction.response.send_message("{0} already owns a vc".format(newowner.display_name), ephemeral=True)
                    else:
                        await interaction.response.send_message("<@{0}> you must be in your vc to run this command".format(interaction.user.id), ephemeral=True)
                else:
                    await interaction.response.send_message("You don't own this voice channel.", ephemeral=True)
                await self.config.guild(guild).owners.set(x)
        else:
            await interaction.response.send_message("You can only run this command while you are in your voice channel.", ephemeral=True)

    @commands.command(name="vcsetup")
    async def vcsetup(self, ctx: commands.Context):
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

    @commands.command(name="vcsync")
    async def vcsync(self, ctx: commands.Context):
        self.log.info("clearing commands...")
        self.bot.tree.remove_command("vc", guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)

        self.log.info("waiting to avoid rate limit...")
        await asyncio.sleep(1)
        self.bot.tree.add_command(self.vc, guild=ctx.guild)
        commands = [c.name for c in self.bot.tree.get_commands(guild=ctx.guild)]
        self.log.info("registered commands: %s", ", ".join(commands))
        self.log.info("syncing commands...")
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("VC Commands were synced")
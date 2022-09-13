import json
from pathlib import Path
import discord

from redbot.core.bot import Red

from .pvc import pvc

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    await bot.add_cog(pvc(bot))

    @bot.tree.context_menu(name="PVC Mute")
    async def contextmute(interaction: discord.Interaction,  user: discord.User) -> None:
        config = pvc.Config.get_conf(
            pvc,
            identifier=365398642334498816
        )
        author = interaction.user
        if user is None:
            await interaction.response.send_message("{0} Please mention a user to mute.".format(author.name), ephemeral=True)
        else:
            i = await config.guild(interaction.guild).owners()
            for vcOwner, vcId in i.items():
                if vcOwner == str(interaction.user):
                    voiceChannel = bot.get_channel(int(vcId))
            if voiceChannel is not None and user.voice is not None:
                await voiceChannel.set_permissions(user, view_channel=True, read_messages=True, send_messages=False, read_message_history=True, use_voice_activation=True, stream=False, connect=True, speak=False, reason="{0} muted {1} in their vc: {2}".format(author.name, user.name, voiceChannel.name))
                if user.voice.channel.id == voiceChannel.id:
                    await user.move_to(voiceChannel)
                await interaction.response.send_message("{0} was muted in your vc: {1}".format(user.name, voiceChannel.mention))
            elif user.voice is None:
                await interaction.response.send_message("You can't mute someone who isn't in a vc.", ephemeral=True)
            else:
                await interaction.response.send_message("{0} You have no vc created use /vc create <Name> to create one.".format(author.name), ephemeral=True)
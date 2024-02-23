from redbot.core import data_manager
from redbot.core import commands, app_commands
from redbot.core import checks
from redbot.core.bot import Red
from redbot.core.config import Config
import discord
import logging
import asyncio
import openai
from openai import OpenAI
import os

class chatGPT(commands.Cog):
  def __init__(self, bot: Red) -> None:
    self.prompt = ""
    self.response = ""
    self.bot = bot
    self.log = logging.getLogger('red.tpun.chatGPT')
    self.config = Config.get_conf(
        self,
        identifier=365398642334498816
    )
    self.user_threads = {}
    defaultGlobalConfig = {
        "model": "gpt-3.5-turbo-0613",
        "tokenLimit": 1000
    }
    defaultGuildConfig = {
        "channels": [],
        "replyRespond": True
    }
    self.config.register_global(**defaultGlobalConfig)
    self.config.register_guild(**defaultGuildConfig)

  async def get_completion(self, user, model, tokenLimit, prompt):
    messages = [{"role": user, "content": prompt}]
    chatGPTKey = await self.bot.get_shared_api_tokens("openai")
    client = OpenAI(api_key=chatGPTKey.get("api_key"))
    response = client.chat.completions.create(
    model=model,
    messages=messages,
    max_tokens=tokenLimit,
    temperature=0.5
    )
    return response.choices[0].message.content

  async def send_message(self, user_id, message, model, tokenLimit) -> None:
    if user_id not in self.user_threads:
      self.user_threads[user_id] = ""
    self.prompt = self.user_threads[user_id]
    response = await self.get_completion(user_id, model, tokenLimit, message)
    self.user_threads[user_id] = response["choices"][0]["text"]
    return self.user_threads[user_id]

  

  async def send_chat(self, interaction: discord.Interaction, query: str):
    async with interaction.typing():
        try:
            model = await self.config.model()
            tokenLimit = await self.config.tokenLimit()
            self.log.debug("Sending query: `" + query + "` to chatGPT. With model: " + model)
            chatGPTKey = await self.bot.get_shared_api_tokens("openai")
            if chatGPTKey.get("api_key") is None:
                self.log.error("No api key set.")
                return await interaction.response.send_message("The bot owner still needs to set the openai api key using `[p]set api openai  api_key,<api key>`. It can be created at: https://beta.openai.com/account/api-keys")
            response: str = await self.send_message(interaction.author.id, query, model, tokenLimit)
            if len(response) > 0 and len(response) < 2000:
                self.log.debug("Response is under 2000 characters and is: `" + response + "`.")
                await interaction.response.send_message(response)
            elif len(response) > 2000:
                self.log.debug("Response is over 2000 characters sending as file attachment. Response is: `" + response + "`.")
                with open(str(interaction.author.id) + '.txt', 'w') as f:
                    f.write(response)
                with open(str(interaction.author.id) + '.txt', 'r') as f:
                    await interaction.response.send_message(file=discord.File(f))
                    os.remove(f)
            else:
                await interaction.response.send_message("I'm sorry, for some reason chatGPT's response contained nothing, please try sending your query again.", ephemeral=True)
        except openai.OpenAIError as err:
            await interaction.response.send_message(err)

  @commands.Cog.listener()
  async def on_message_without_command(self, message: discord.Message):
    whitelistedChannels: list = await self.config.guild(message.guild).channels()
    replyRespond: bool = await self.config.guild(message.guild).replyRespond()
    query = message.content
    validFile: bool = False
    validFileTypes = ['.py', '.js', '.txt', '.yaml', '.html', '.xml', '.c', '.java', '.cs', '.php', '.css']
    interaction = await self.bot.get_context(message)
    if whitelistedChannels is not None and message.channel.id in whitelistedChannels and message.author.id != self.bot.user.id:
        if message.attachments:
            # Get the file
            self.log.debug("Message has a file, is it valid?")
            file: discord.Attachment = message.attachments[0]
            for filetype in validFileTypes:
                if file.filename.endswith(filetype):
                    self.log.debug("It is valid.")
                    fileContents = await file.read()
                    query = query + "\n" + str(fileContents)
                    self.log.debug("Final query: " + query)
                    validFile = True
            if not validFile:
                await interaction.response.send_message("Sorry but that isn't a valid filetype.", ephemeral=True)
        await self.send_chat(interaction, query)
    if replyRespond and message.reference is not None and message.author.id != self.bot.user.id:
        # Fetching the message
        channel = self.bot.get_channel(message.reference.channel_id)
        msg = await channel.fetch_message(message.reference.message_id)
        context: commands.Context = await self.bot.get_context(msg)
        if context.author.id == self.bot.user.id:
            await self.send_chat(interaction, query)

  @app_commands.AppCommand(name="chatgpt")
  @app_commands.describe(chatgpt="Base command for chatGPT cog")
  async def chatgpt(self, interaction: discord.Interaction):
        """
        Base command for chatgpt related commands
        """
        pass

  @app_commands.AppCommandGroup(parent=chatgpt, name= "chat")
  @app_commands.describe(chatgpt="Send a message to chatGPT")
  async def chat(self, interaction: discord.Interaction, *, query: str):
    """
    Asks chatgpt a query
    """
    await self.send_chat(interaction, query)

  @checks.guildowner()
  @app_commands.AppCommandGroup(parent=chatgpt, name="channellist")
  @app_commands.describe(chatgpt="List of channels chatGPT will auto reply in.")
  async def channellist(self, interaction: discord.Interaction):
    """
    Lists the channels currently in the whitelist
    """
    currentChannels: list = await self.config.guild(interaction.guild).channels()
    if currentChannels is not None:
      message = "The current channels are:\n"
      for channelId in currentChannels:
        message = message + "<#" + str(channelId) + ">\n"
      await interaction.response.send_message(message)
    else:
      await interaction.response.send_message("There are currently no channels whitelisted for chatGPT.")


  @checks.guildowner()
  @app_commands.AppCommandGroup(parent=chatgpt, name= "set")
  @app_commands.describe(chatgpt="Commands to add/remove channel to/from chatGPT whitelist")
  @app_commands.choices(setting=[
        app_commands.Choice(name="channeladd", value="channeladd"),
        app_commands.Choice(name="channelremove", value="channelremove"),
        app_commands.Choice(name="replyRespond", value="replyRespond")
    ])
  async def set(self, interaction: discord.Interaction, setting: app_commands.Choice[str], value: str):
    """
    Changes settings for bot to use

    Use `[p]chatgpt set channeladd <channel_id>` or `[p]chatgpt set channelremove <channel_id>` to set up channel whitelist where the bot will respond.\n\n
    Use `[p]chatgpt set replyRespond <True or False>` to enable or disable the bot responding to replies regardless of channel
    """
    if setting == "channeladd":
      if value is discord.TextChannel:
        value: int = value.id
        pass
      channelId = int(value)
      channel = self.bot.get_channel(channelId)
      if channel == None:
          await interaction.response.send_message("That channel does not exist or the bot can not see it.", ephemeral=True)
          return
      elif channel.guild != interaction.guild:
          await interaction.response.send_message("That channel isn't in this server...", ephemeral=True)
          return
      currentChannels: list = await self.config.guild(interaction.guild).channels()
      self.log.info(currentChannels)
      if currentChannels is None:
          self.log.info("Current channel list is empty adding the new channel.", ephemeral=True)
          newChannels: list = [channelId]
          await interaction.response.send_message("<#" + str(channelId) + "> is now whitelisted.", ephemeral=True)
          await self.config.guild(interaction.guild).channels.set(newChannels)
          return
      if channelId not in currentChannels:
          self.log.info("Channel is not in list so we add it.")
          currentChannels.append(channelId)
          self.log.info(currentChannels)
          await interaction.response.send_message("<#" + str(channelId) + "> is now whitelisted.", ephemeral=True)
          await self.config.guild(interaction.guild).channels.set(currentChannels)
          return
      await interaction.response.send_message("<#" + str(channelId) + "> was already whitelisted.", ephemeral=True)

    elif setting == "channelremove":
      if value is discord.TextChannel:
        value: int = value.id
        pass
      currentChannels: list = await self.config.guild(interaction.guild).channels()
      try:
          currentChannels.remove(int(value))
          await self.config.guild(interaction.guild).channels.set(currentChannels)
          await interaction.response.send_message("<#" + str(value) + "> is no longer whitelisted.", ephemeral=True)
      except ValueError:
          await interaction.response.send_message("That channel was already not in channel list.", ephemeral=True)

    elif setting == "replyRespond":
        if value is str:
          value = value.lower()
        if value == "true" or value == "1":
            await self.config.guild(interaction.guild).replyRespond.set(True)
            await interaction.response.send_message("replyRespond is now set to True", ephemeral=True)
        elif value == "false" or value == "0":
            await self.config.guild(interaction.guild).replyRespond.set(False)
            await interaction.response.send_message("replyRespond is now set to False", ephemeral=True)
        else:
          await interaction.response.send_message("This command only accepts `true` or `false`.", ephemeral=True)

  @checks.is_owner()
  @app_commands.AppCommandGroup(parent=chatgpt, name="model")
  @app_commands.describe(chatgpt="Commands to select model for chatGPT to use.")
  @app_commands.choices(model=[
        app_commands.Choice(name="gpt-3.5-turbo-0613", value="0"),
        app_commands.Choice(name="gpt-3.5-turbo-16k-0613", value="1"),
        app_commands.Choice(name="gpt-4-0613", value="2"),
        app_commands.Choice(name="gpt-4-32k-0613", value="3"),
        app_commands.Choice(name="gpt-4-turbo-preview", value="4"),
        app_commands.Choice(name="gpt-4-0125-preview", value="5"),
    ])
  async def model(self, interaction: discord.Interaction, model: app_commands.Choice[str]):
    """
    Allows the changing of model chatbot is runnig. Options are: 0-`gpt-3.5-turbo-0613` 1-`gpt-3.5-turbo-16k-0613` 2-`gpt-4-0613` 3-`gpt-4-32k-0613` 4-`gpt-4-turbo-preview` 5-`gpt-4-0125-preview` current-`shows current model`\n\n

    For more information on what this means please check out: https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo
    """
    model_map = {
        "0": "gpt-3.5-turbo-0613",
        "1": "gpt-3.5-turbo-16k-0613",
        "2": "gpt-4-0613",
        "3": "gpt-4-32k-0613",
        "4": "gpt-4-turbo-preview",
        "5": "gpt-4-0125-preview",
        "gpt-3.5-turbo-0613": "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613": "gpt-3.5-turbo-16k-0613",
        "gpt-4-0613": "gpt-4-0613",
        "gpt-4-32k-0613": "gpt-4-32k-0613",
        "gpt-4-turbo-preview": "gpt-4-turbo-preview",
        "gpt-4-0125-preview": "gpt-4-0125-preview"
    }
    if model in model_map:
        await self.config.model.set(model_map[model])
        await interaction.response.send_message("The chatbot model is now set to: `" + model_map[model] + "`", ephemeral=True)
    elif model == "current":
        currentModel = await self.config.model()
        await interaction.response.send_message("The chatbot model is currently set to: " + currentModel, ephemeral=True)
    else:
        await interaction.response.send_message("That is not a valid model please use `[p]chatgpt model` to see valid models", ephemeral=True)

  @checks.is_owner()
  @app_commands.AppCommandGroup(parent=chatgpt, name="tokenlimit")
  @app_commands.describe(chatgpt="Commands to chose a token limit for each chatGPT interaction.")
  async def tokenlimit(self, interaction: discord.Interaction, tokenLimit: int):
    """
    Allows for changing the max amount of tokens used in one query, default is 1000. Token cost is counted as query + response. Check the Managing tokens article to see token limits on specific models.\n\n
    
    For more information on tokens check out: https://platform.openai.com/docs/guides/text-generation/managing-tokens
    For token prices also see: https://openai.com/api/pricing/
    """
    model = await self.config.model()
    model_limits = {
        "gpt-3.5-turbo-0613": (0, 4097),
        "gpt-3.5-turbo-16k-0613": (0, 16385),
        "gpt-4-0613": (0, 32768),
        "gpt-4-32k-0613": (0, 32768),
        "gpt-4-turbo-preview": (0, 128000),
        "gpt-4-0125-preview": (0, 128000)
    }

    if model in model_limits and model_limits[model][0] < tokenLimit <= model_limits[model][1]:
        await self.config.tokenlimit.set(tokenLimit)
        await interaction.response.send_message("Token limit is now set to " + str(tokenLimit), ephemeral=True)
    else:
        await interaction.response.send_message("That is not a valid token amount. Limits for this model are between " + str(model_limits[model][0]) + " and " + str(model_limits[model][1]) + ".", ephemeral=True)

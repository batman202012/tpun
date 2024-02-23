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
        "maxtokens": 1000
    }
    defaultGuildConfig = {
        "channels": [],
        "replyRespond": True
    }
    self.config.register_global(**defaultGlobalConfig)
    self.config.register_guild(**defaultGuildConfig)

  async def get_completion(self, user, model, maxtokens, prompt):
    messages = [{"role": user, "content": prompt}]
    chatGPTKey = await self.bot.get_shared_api_tokens("openai")
    client = OpenAI(api_key=chatGPTKey.get("api_key"))
    response = client.chat.completions.create(
    model=model,
    messages=messages,
    max_tokens=maxtokens,
    temperature=0.5
    )
    return response.choices[0].message.content

  async def send_message(self, user_id, message, model, maxtokens) -> None:
    if user_id not in self.user_threads:
      self.user_threads[user_id] = ""
    self.prompt = self.user_threads[user_id]
    response = await self.get_completion(user_id, model, maxtokens, message)
    self.user_threads[user_id] = response["choices"][0]["text"]
    return self.user_threads[user_id]

  

  async def send_chat(self, ctx: commands.Context, query: str):
    async with ctx.typing():
        try:
            model = await self.config.model()
            maxtokens = await self.config.maxtokens()
            self.log.debug("Sending query: `" + query + "` to chatGPT. With model: " + model)
            chatGPTKey = await self.bot.get_shared_api_tokens("openai")
            if chatGPTKey.get("api_key") is None:
                self.log.error("No api key set.")
                return await ctx.send("The bot owner still needs to set the openai api key using `[p]set api openai  api_key,<api key>`. It can be created at: https://beta.openai.com/account/api-keys")
            response: str = await self.send_message(ctx.author.id, query, model, maxtokens)
            if len(response) > 0 and len(response) < 2000:
                self.log.debug("Response is under 2000 characters and is: `" + response + "`.")
                await ctx.send(response)
            elif len(response) > 2000:
                self.log.debug("Response is over 2000 characters sending as file attachment. Response is: `" + response + "`.")
                with open(str(ctx.author.id) + '.txt', 'w') as f:
                    f.write(response)
                with open(str(ctx.author.id) + '.txt', 'r') as f:
                    await ctx.send(file=discord.File(f))
                    os.remove(f)
            else:
                await ctx.send("I'm sorry, for some reason chatGPT's response contained nothing, please try sending your query again.", ephemeral=True)
        except openai.OpenAIError as err:
            await ctx.send(err)

  @commands.Cog.listener()
  async def on_message_without_command(self, message: discord.Message):
    whitelistedChannels: list = await self.config.guild(message.guild).channels()
    replyRespond: bool = await self.config.guild(message.guild).replyRespond()
    query = message.content
    validFile: bool = False
    validFileTypes = ['.py', '.js', '.txt', '.yaml', '.html', '.xml', '.c', '.java', '.cs', '.php', '.css']
    ctx = await self.bot.get_context(message)
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
                await ctx.send("Sorry but that isn't a valid filetype.", ephemeral=True)
        await self.send_chat(ctx, query)
    if replyRespond and message.reference is not None and message.author.id != self.bot.user.id:
        # Fetching the message
        channel = self.bot.get_channel(message.reference.channel_id)
        msg = await channel.fetch_message(message.reference.message_id)
        context: commands.Context = await self.bot.get_context(msg)
        if context.author.id == self.bot.user.id:
            await self.send_chat(ctx, query)

  @commands.hybrid_group(name="chatgpt")
  async def chatgpt(self, ctx: commands.Context):
        """
        Base command for chatgpt related commands
        """
        pass

  @chatgpt.command(name="chat", description="Sends a message to chatGPT.")
  @app_commands.describe(query="Message to send chatGPT")
  async def chat(self, ctx: commands.Context, *, query: str):
    """
    Asks chatgpt a query
    """
    await self.send_chat(ctx, query)

  @checks.guildowner()
  @chatgpt.command(name="channellist", description="List of all the channels chatGPT is whitelisted in.")
  async def channellist(self, ctx: commands.Context):
    """
    Lists the channels currently in the whitelist
    """
    currentChannels: list = await self.config.guild(ctx.guild).channels()
    if currentChannels is not None:
      message = "The current channels are:\n"
      for channelId in currentChannels:
        message = message + "<#" + str(channelId) + ">\n"
      await ctx.send(message)
    else:
      await ctx.send("There are currently no channels whitelisted for chatGPT.")


  @checks.guildowner()
  @chatgpt.command(name="set", description="Change settings for chatGPT.")
  @app_commands.describe(value="Channel ID to add or remove. For replyRespond use True or False.")
  @app_commands.choices(setting=[
        app_commands.Choice(name="channeladd", value="channeladd"),
        app_commands.Choice(name="channelremove", value="channelremove"),
        app_commands.Choice(name="replyRespond", value="replyRespond")
    ])
  async def set(self, ctx: commands.Context, setting: app_commands.Choice[str], value: str):
    """
    Changes settings for bot to use

    Use `[p]chatgpt set channeladd <channel_id>` or `[p]chatgpt set channelremove <channel_id>` to set up channel whitelist where the bot will respond.\n\n
    Use `[p]chatgpt set replyRespond <True or False>` to enable or disable the bot responding to replies regardless of channel
    """
    if setting.value == "channeladd":
      if value is discord.TextChannel:
        value: int = value.id
        pass
      channelId = int(value)
      channel = self.bot.get_channel(channelId)
      if channel == None:
          await ctx.send("That channel does not exist or the bot can not see it.", ephemeral=True)
          return
      elif channel.guild != ctx.guild:
          await ctx.send("That channel isn't in this server...", ephemeral=True)
          return
      currentChannels: list = await self.config.guild(ctx.guild).channels()
      self.log.info(currentChannels)
      if currentChannels is None:
          self.log.info("Current channel list is empty adding the new channel.", ephemeral=True)
          newChannels: list = [channelId]
          await ctx.send("<#" + str(channelId) + "> is now whitelisted.", ephemeral=True)
          await self.config.guild(ctx.guild).channels.set(newChannels)
          return
      if channelId not in currentChannels:
          self.log.info("Channel is not in list so we add it.")
          currentChannels.append(channelId)
          self.log.info(currentChannels)
          await ctx.send("<#" + str(channelId) + "> is now whitelisted.", ephemeral=True)
          await self.config.guild(ctx.guild).channels.set(currentChannels)
          return
      await ctx.send("<#" + str(channelId) + "> was already whitelisted.", ephemeral=True)

    elif setting.value == "channelremove":
      if value is discord.TextChannel:
        value: int = value.id
        pass
      currentChannels: list = await self.config.guild(ctx.guild).channels()
      try:
          currentChannels.remove(int(value))
          await self.config.guild(ctx.guild).channels.set(currentChannels)
          await ctx.send("<#" + str(value) + "> is no longer whitelisted.", ephemeral=True)
      except ValueError:
          await ctx.send("That channel was already not in channel list.", ephemeral=True)

    elif setting.value == "replyRespond":
        if value is str:
          value = value.lower()
        if value == "true" or value == "1":
            await self.config.guild(ctx.guild).replyRespond.set(True)
            await ctx.send("replyRespond is now set to True", ephemeral=True)
        elif value == "false" or value == "0":
            await self.config.guild(ctx.guild).replyRespond.set(False)
            await ctx.send("replyRespond is now set to False", ephemeral=True)
        else:
          await ctx.send("This command only accepts `true` or `false`.", ephemeral=True)

  @checks.is_owner()
  @chatgpt.command(name="model", description="Select the model for chatGPT to use.")
  @app_commands.describe(model="Model for chatGPT to use.")
  @app_commands.choices(model=[
        app_commands.Choice(name="gpt-3.5-turbo-0613", value="0"),
        app_commands.Choice(name="gpt-3.5-turbo-16k-0613", value="1"),
        app_commands.Choice(name="gpt-4-0613", value="2"),
        app_commands.Choice(name="gpt-4-32k-0613", value="3"),
        app_commands.Choice(name="gpt-4-turbo-preview", value="4"),
        app_commands.Choice(name="gpt-4-0125-preview", value="5"),
        app_commands.Choice(name="current", value="current")
    ])
  async def model(self, ctx: commands.Context, model: app_commands.Choice[str]):
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
    self.log.error(model.value)
    if model.value in model_map:
        await self.config.model.set(model_map[model.value])
        await ctx.send("The chatbot model is now set to: `" + model_map[model.value] + "`", ephemeral=True)
    elif model.value == "current":
        currentModel = await self.config.model()
        await ctx.send("The chatbot model is currently set to: " + currentModel, ephemeral=True)
    else:
        await ctx.send("That is not a valid model please use `[p]chatgpt model` to see valid models", ephemeral=True)

  @checks.is_owner()
  @chatgpt.command(name="tokenlimit", description="Sets token limit for each chatGPT interaction.")
  @app_commands.describe(maxtokens="Token limit for each chatGPT interaction.")
  async def tokenlimit(self, ctx: commands.Context, maxtokens: int):
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

    if model in model_limits and model_limits[model][0] < maxtokens <= model_limits[model][1]:
        await self.config.maxtokens.set(maxtokens)
        await ctx.send("Token limit is now set to " + str(maxtokens), ephemeral=True)
    else:
        await ctx.send("That is not a valid token amount. Limits for this model are between " + str(model_limits[model][0]) + " and " + str(model_limits[model][1]) + ".", ephemeral=True)

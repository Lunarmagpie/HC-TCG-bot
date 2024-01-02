"""Run the bot."""
from importlib import import_module
from json import load
from os import listdir
from pickle import load as pklload
from time import time

from aiohttp.web import Application, AppRunner, TCPSite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from interactions import Client, listen

from util import DataGenerator, ServerManager

start = time()
with open("config.json") as f:
    CONFIG = load(f)


class Bot(Client):
    """Slightly modified discord client."""

    @listen()
    async def on_ready(self: "Bot") -> None:
        """Handle bot starting."""
        await bot.change_presence()
        await runner.setup()
        site = TCPSite(runner, "0.0.0.0", 8194)  # noqa: S104
        await site.start()
        scheduler.start()

    @listen()
    async def on_disconnect(self: "Bot") -> None:
        """Handle bot disconnection."""
        await runner.cleanup()
        scheduler.shutdown()


bot = Bot()

data_gen = DataGenerator(CONFIG["tokens"]["github"], branch="christmas")
scheduler = AsyncIOScheduler()

web_server = Application()
runner = AppRunner(web_server)

servers = []
for file in listdir("servers"):
    servers.append(import_module(f"servers.{file}").server)
server_manager = ServerManager(bot, servers, web_server, scheduler, data_gen.universe)

bot.load_extension("exts.admin", None, manager=server_manager)
bot.load_extension("exts.card", None, universe=data_gen.universe)
bot.load_extension("exts.dotd", None, manager=server_manager)
bot.load_extension("exts.forums", None, manager=server_manager)
bot.load_extension("exts.match", None, manager=server_manager)
bot.load_extension("exts.util", None)

print(f"Bot started in {round(time()-start, 2)}")

bot.start(CONFIG["tokens"]["discord"])

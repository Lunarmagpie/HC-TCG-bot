from interactions import Extension, Client, CommandContext, File, Embed, Choice, extension_command, option
from matplotlib import pyplot as plt
from datetime import datetime as dt
from collections import Counter
from io import BytesIO
from PIL import Image
from time import time

from deck import hashToStars, hashToDeck, universe
from probability import probability
from datagen import dataGetter

beige = (226, 202, 139)
typeColors = {
    "miner": (110, 105, 108),
    "terraform": (217, 119, 147),
    "speedrunner": (223, 226, 36),
    "pvp": (85, 202, 194),
    "builder": (184, 162, 154),
    "balanced": (101, 124, 50),
    "explorer": (103, 138, 190),
    "prankster": (116, 55, 168),
    "redstone": (185, 33, 42),
    "farm": (124, 204, 12)
}

def rgbToInt(rgb:tuple[int, int, int]):
    return (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]

class cardExt(Extension):
    def __init__(self, client:Client, dataGenerator:dataGetter) -> None:
        self.dataGenerator = dataGenerator
        self.lastReload = time()
        self.namedUniverse = [{"name": v["name"] if not "health" in v.keys(
        ) else f"{v['name']} {v['rarity'].replace('_', ' ')}", "value": k} for k, v in list(self.dataGenerator.universeData.items())]

    @extension_command()
    async def card(self, ctx:CommandContext):
        """Get information about cards and decks"""
    
    def count(self, s:str) -> str:
        final = []
        for k, v in Counter(s).most_common():
            final.append(f"{v}x {k}")
        return ", ".join(final)

    def longest(self, typeCounts:dict[str, dict]) -> list:
        return [key for key in typeCounts.keys() if typeCounts.get(key)==max([num for num in typeCounts.values()])]

    def getStats(self, deck:list) -> tuple[Image.Image, tuple[int,int,int], dict[str, int]]:
        typeCounts = {
            "miner": 0,
            "terraform": 0,
            "speedrunner": 0,
            "pvp": 0,
            "builder": 0,
            "balanced": 0,
            "explorer": 0,
            "prankster": 0,
            "redstone": 0,
            "farm": 0,
        }
        hermits, items, effects = [[] for _ in range(3)]
        for card in deck:
            if card.startswith("item"):
                items.append(card)
            elif card.endswith(("rare", "common")):
                hermits.append(card)
                if card in self.dataGenerator.universeData.keys():
                    typeCounts[self.dataGenerator.universeData[card]["hermitType"]] += 1
            else:
                effects.append(card)
        
        hermits.sort()
        items.sort()
        effects.sort()
        im = Image.new("RGBA", (6*200, 7*200))
        for i, card in enumerate(hermits + effects + items):
            toPaste = self.dataGenerator.universeImage[card].resize((200, 200)).convert("RGBA")
            im.paste(toPaste, ((i%6)*200,(i//6)*200), toPaste)
        return im, (len(hermits), len(effects), len(items)), typeCounts

    @card.subcommand()
    @option(
        description = "The exported hash of the deck",
    )
    @option(
        description = "The site to link the deck to",
        choices = [
            Choice(
                name = "Dev site",
                value = "https://hc-tcg.online/?deck=",
            ),
            Choice(
                name = "Xisumaverse",
                value = "https://tcg.xisumavoid.com/?deck=",
            ),
            Choice(
                name = "Beef",
                value = "https://tcg.omegaminecraft.com/?deck=",
            ),
            Choice(
                name = "Balanced",
                value = "https://tcg.prof.ninja/?deck=",
            ),
        ],
    )
    async def deck(self, ctx:CommandContext, deck:str, site:str="https://hc-tcg.online/?deck="):
        """Get information about a deck"""
        deckList = hashToDeck(deck, universe)
        im, hic, typeCounts = self.getStats(deckList)
        col = typeColors[self.longest(typeCounts)[0]]
        e = Embed(
            title = "Deck stats",
            description = f"Hash: {deck}",
            url = site + deck,
            timestamp = dt.now(),
            color = rgbToInt(col),
        )
        e.set_image("attachment://deck.png")
        e.add_field("Token cost", str(hashToStars(deck, self.dataGenerator.rarities)), True)
        e.add_field("HEI ratio", f"{hic[0]}:{hic[1]}:{hic[2]}", True)
        e.add_field("Types", len([typeList for typeList in typeCounts.values() if typeList != 0]), True)
        e.set_footer("Bot by Tyrannicodin16")
        with BytesIO() as im_binary:
            im.save(im_binary, 'PNG')
            im_binary.seek(0)
            await ctx.send(embeds=e, files=File(fp=im_binary, filename="deck.png"))

    @card.subcommand()
    @option(
        name = "card",
        description = "The card id to get",
        autocomplete = True,
    )
    async def info(self, ctx:CommandContext, card:str):
        """Get information about a card"""
        card = card.casefold() #Ensure all lowercase
        if card in self.dataGenerator.universeData.keys():
            if card in self.dataGenerator.universes["hermits"]: #Special for hermits
                dat = self.dataGenerator.universeData[card]
                col = typeColors[dat["hermitType"]]
                e = Embed(
                    title = dat["name"],
                    description = f"{dat['rarity'].capitalize().replace('_', ' ')} {dat['name']} - {self.dataGenerator.rarities[card]} tokens",
                    timestamp = dt.now(),
                    color = rgbToInt(col),
                )
                e.add_field("Rarity", "Ultra rare" if dat["rarity"] == "ultra_rare" else dat["rarity"].capitalize(), True)
                e.add_field("Primary attack", dat["primary"]["name"] if dat["primary"]["power"] == None else dat["primary"]["name"] + " - " + dat["primary"]["power"], False)
                e.add_field("Attack damage", dat["primary"]["damage"], True)
                e.add_field("Items required", self.count(dat["primary"]["cost"]), True)
                e.add_field("Secondary attack", dat["secondary"]["name"] if dat["secondary"]["power"] == None else dat["secondary"]["name"] + " - " + dat["secondary"]["power"].replace("\n\n", "\n"), False)
                e.add_field("Attack damage", dat["secondary"]["damage"], True)
                e.add_field("Items required", self.count(dat["secondary"]["cost"]), True)
            else:
                dat = self.dataGenerator.universeData[card]
                e = Embed(
                    title = dat["name"],
                    description = dat["description"] if "description" in dat.keys() else f"{dat['hermitType']} item card",
                    timestamp = dt.now(),
                    color = rgbToInt(typeColors[dat["hermitType"]]) if "hermitType" in dat.keys() else rgbToInt(beige),
                )
                e.add_field("Rarity", "Ultra rare" if dat["rarity"] == "ultra_rare" else dat["rarity"].capitalize(), True)
            e.set_thumbnail(f"attachment://{dat['id']}.png", height=200, width=200)
            e.set_footer("Bot by Tyrannicodin16")
            with BytesIO() as im_binary:
                self.dataGenerator.universeImage[card].save(im_binary, 'PNG')
                im_binary.seek(0)
                await ctx.send(embeds=e, files=File(f"{dat['id']}.png", im_binary))
        else:
            await ctx.send("Couldn't find that card!", ephemeral=True)
    
    @info.autocomplete("card")
    async def card_autocomplete(self, ctx: CommandContext, name: str = None):
        if not name:
            await ctx.populate(self.namedUniverse[0:25])
            return
        await ctx.populate([card for card in self.namedUniverse if name.lower() in card["name"].lower()][0:25])
    
    @card.subcommand()
    async def reload(self, ctx:CommandContext):
        """Reload the card data and images"""
        if self.lastReload + 60*30 < time(): #Limit reloading to every 30 minutes as it's quite slow
            await ctx.send("Reloading...", ephemeral=True)
            startTime = time()
            self.dataGenerator.reload()
            self.namedUniverse = [{"name": v["name"] if not "health" in v.keys() else f"{v['name']} {v['rarity'].replace('_', ' ')}", "value": k} for k, v in list(self.dataGenerator.universeData.items())]
            await ctx.send(f"Reloaded! Took {round(time()-startTime)}", ephemeral=True)
            self.lastReload = time()
            return
        await ctx.send("Reloaded within the last 10 minutes, please try again later.", ephemeral=True)

    @card.subcommand()
    @option("The number of hermits in your deck")
    @option("Looks for the number of turns to get this chance of having the desired number of cards")
    @option("The number of hermits you want")
    async def twohermits(self, ctx: CommandContext, hermits:int, desired_chance:int=50, desired_hermits:int=2):
        if hermits < 1 or hermits > 36:
            await ctx.send("Invalid hermit count (1-36)", ephemeral=True)
            return
        plt.figure()
        xs = [i for i in range(35)]
        ys = [probability(hermits, i, desired_hermits)*100 for i in xs]
        surpass = next((idx[0] for idx in enumerate(ys) if idx[1] >= desired_chance), None)
        plt.plot(xs, [round(y) for y in ys])
        plt.xlabel("Draws")
        plt.ylabel("Probability")
        plt.title(f"Chance of having {desired_hermits} hermits in your hand after x draws for {hermits} hermits")
        plt.grid(True)
        e = Embed(
            title=f"Chance of having {desired_hermits} hermits in your hand after x draws for {hermits} hermits",
            timestamp=dt.now(),
            color=rgbToInt((178, 178, 255)),
        )
        e.add_field("Initial draw chance", f"{ys[0]}%", inline=True)
        if surpass:
            e.add_field(f"Hits {desired_chance}%", f"{surpass} draw(s)", inline=True)
        else:
            e.add_field(f"Hits {desired_chance}%", "Never", inline=True)
        e.set_footer("Bot by Tyrannicodin | Probability calculations by Allophony")
        e.set_image("attachment://graph.png")
        with BytesIO() as figBytes:
            plt.savefig(figBytes, format="png")
            figBytes.seek(0)
            await ctx.send(embeds = e, files=File("graph.png", figBytes))
        plt.close()

def setup(client:Client, dataGenerator:dataGetter):
    cardExt(client, dataGenerator)

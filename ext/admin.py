import disnake
from disnake.ext import commands
from utils.bot import Bot
from utils.constants import GET_STARTED_CHANNEL_ID, JOIN_CLAN_CHANNEL_ID


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="dosetup")
    async def dosetup(self, ctx: commands.Context):
        gsv = disnake.ui.View()
        gsv.stop()
        gsv.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Verify"))
        gsv.add_item(disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Join"))
        m1 = await self.bot.server.get_channel(GET_STARTED_CHANNEL_ID).send(
            "Please select what you need to do\n\
`Verify` - you are **already in __our__ clan** and want to verify\n\
`Join` - you are not in the clan yet and want to join",
            view=gsv,
        )
        view = disnake.ui.View()
        view.stop()
        view.add_item(
            disnake.ui.Button(style=disnake.ButtonStyle.green, label="Join the Clan")
        )
        m2 = await self.bot.server.get_channel(JOIN_CLAN_CHANNEL_ID).send(
            "Press the button below to create new clan application!", view=view
        )
        await ctx.send(f"Setup completed\nGS ID: {m1.id}\nJC ID: {m2.id}\n")


def setup(bot: Bot):
    bot.add_cog(Admin(bot))

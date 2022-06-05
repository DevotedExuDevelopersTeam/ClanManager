from datetime import datetime

import disnake
from disnake.ext import commands, tasks

from utils.bot import Bot
from utils.constants import CLAN_ROLES
from utils.events import ON_SLASH_COMMAND_ERROR


class CoreLoops(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.unban_loop.start()

    @tasks.loop(minutes=10)
    async def unban_loop(self):
        threshold = datetime.now().timestamp()
        cur = await self.bot.execute(
            "SELECT id FROM bans WHERE banned_until < ?", threshold
        )
        results = await cur.fetchall()
        for r in results:
            try:
                await self.bot.server.unban(disnake.Object(r[0]))
            except:
                pass

    @unban_loop.before_loop
    async def loop_waiter(self):
        await self.bot.wait_until_ready()


class CoreListeners(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener(ON_SLASH_COMMAND_ERROR)
    async def error_handler(self, inter: disnake.ApplicationCommandInteraction, error):
        await inter.send(str(error), ephemeral=True)
        raise error

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        difference_roles = after_roles - before_roles
        difference_roles_ids = map(lambda r: r.id, difference_roles)
        for role_id in CLAN_ROLES:
            if role_id in difference_roles_ids:
                await after.add_roles(self.bot.clan_member, self.bot.verified)
                return


def setup(bot: Bot):
    bot.add_cog(CoreLoops(bot))
    bot.add_cog(CoreListeners(bot))

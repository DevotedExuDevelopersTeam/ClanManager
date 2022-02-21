from asyncio import sleep
from re import search
from typing import Callable

import disnake
from disnake.ext import commands
from utils.bot import Bot
from utils.constants import CLAN_ROLES
from utils.converters import TimeConverter
from utils.utils import to_discord_timestamp

clans = commands.Param(choices=list(CLAN_ROLES.keys()))


class Moderation(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def cog_slash_command_check(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> bool:
        return (
            inter.author.guild_permissions.administrator
            or self.bot.staff in inter.author.roles
        )

    @commands.slash_command(name="mute", description="Mutes (timeouts) a member.")
    async def mute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        time: TimeConverter,
        reason: str = "No reason provided",
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(
                "You cannot mute someone with higher top role than yours",
                ephemeral=True,
            )
            return

        await user.timeout(
            duration=time, reason=f"{reason} | Responsible moderator: {inter.author}"
        )
        await inter.send(
            f"Successfully muted {user.mention} until {to_discord_timestamp(time)}.\nReason: `{reason}`"
        )
        try:
            await user.send(
                f"You were muted in **{inter.guild.name}** until {to_discord_timestamp(time)}`.\nReason: `{reason}`"
            )
        except:
            pass

    @commands.slash_command(name="unmute", description="Unmutes a member.")
    async def unmute(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(
                "You cannot unmute someone with higher top role than yours",
                ephemeral=True,
            )
            return

        await user.timeout(
            duration=None,
            reason=f"Manual unmute | Responsible moderator: {inter.author}",
        )
        await inter.send("User Unmuted", f"Successfully unmuted {user.mention}")

    @commands.slash_command(name="ban", description="Bans a member.")
    async def ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        reason: str = "No reason provided",
        time: TimeConverter = None,
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(
                "You cannot ban someone with higher top role than yours", ephemeral=True
            )
            return

        await inter.response.defer()
        time_txt = f" until {to_discord_timestamp(time)}" if time is not None else ""
        try:
            await user.send(
                f"You were banned from **{inter.guild.name}**{time_txt}.\nReason: `{reason}`",
            )
        except:
            pass
        await user.ban(
            reason=f'{reason} | Responsible moderator: {inter.author} | Time: {time if time is not None else "permanent"}'
        )
        if time is not None:
            await self.bot.add_ban_record(user, time)
        await inter.send(
            f"Successfully banned **{user}**{time_txt}.\nReason: `{reason}`",
        )

    @commands.slash_command(name="kick", description="Kicks a member.")
    async def kick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        reason: str = "No reason provided",
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(
                "You cannot kick someone with higher top role than yours",
                ephemeral=True,
            )
            return

        await user.kick(reason=f"{reason} | Responsible moderator: {inter.author}")
        await inter.send(
            f"Successfully kicked **{user}**.\nReason: `{reason}`",
        )
        try:
            await user.send(
                f"You were kicked from **{inter.guild.name}**.\nReason: `{reason}`",
            )
        except:
            pass

    @commands.slash_command(name="purge", description="Purges messages in a channel")
    async def purge(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int,
        channel: disnake.TextChannel = None,
        user: disnake.Member = None,
    ):
        await inter.response.defer(ephemeral=True)
        channel = channel or inter.channel
        c: Callable[[disnake.Message], bool] = None
        if user is None:
            c = lambda m: not m.pinned
        else:
            c = lambda m: not m.pinned and m.author.id == user.id

        amount = len(await channel.purge(limit=amount, check=c))
        await inter.send(
            f"Successfully purged `{amount}` messages from {channel.mention}",
            delete_after=5,
        )

    @commands.message_command(name="Purge all below")
    async def purge_all_below(
        self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message
    ):
        await inter.response.defer(ephemeral=True)
        amount = len(await inter.channel.purge(after=message.created_at))
        await inter.send(
            f"Successfully purged `{amount}` messages from {inter.channel.mention}"
        )


class ClanManagement(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_slash_command_check(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        if any(
            [
                self.bot.officer in inter.author.roles,
                self.bot.staff in inter.author.roles,
                inter.author.guild_permissions.administrator,
            ]
        ):
            return True
        await inter.send(f"You cannot use this command.", ephemeral=True)
        return False

    @commands.slash_command(name="addclan", description="Adds a clan role to a member.")
    async def addclan(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        clan: str = clans,
    ):
        await user.add_roles(self.bot.get_role(CLAN_ROLES[clan]))
        await inter.send(f"Successfully added `{clan}` role to {user.mention}")

    @commands.slash_command(
        name="removeclan", description="Removed clan role from a member."
    )
    async def removeclan(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        clan: str = clans,
    ):
        await user.remove_roles(self.bot.get_role(CLAN_ROLES[clan]))
        await inter.send(f"Successfully removed `{clan}` role from {user.mention}")

    @commands.slash_command(name="spamping", description="Spam pings certain clan")
    async def spamping(
        self,
        inter: disnake.ApplicationCommandInteraction,
        clan: str = clans,
        times: int = commands.Param(ge=10, le=50),
        text: str = None,
    ):
        text = text or "GET ON"
        await inter.send(f"Started spamping!", ephemeral=True)
        c = inter.channel
        role = self.bot.get_role(CLAN_ROLES[clan])
        spam_messages = []
        for _ in range(times):
            spam_messages.append(await c.send(f"{role.mention} {text}"))
        await c.delete_messages(spam_messages)

    @commands.slash_command(name="setid", description="Sets ID for a member.")
    async def setid(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        new_id: int,
    ):
        current_id = search(r"\[\d*\]", user.display_name)
        if current_id is None:
            await user.edit(nick=f"[{new_id}] {user.display_name}")
        else:
            await user.edit(
                nick=user.display_name.replace(current_id.group(), f"[{new_id}]")
            )

        await inter.send(
            f"Successfully changed the ID for {user.mention}", ephemeral=True
        )


class Verification(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_slash_command_check(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> bool:
        if inter.channel_id == self.bot.verify.id:
            return True
        await inter.send(
            f"This command can only be used in {self.bot.verify.mention}",
            ephemeral=True,
        )
        return False

    @commands.slash_command(
        name="verify", description="Verifies your being in the clan."
    )
    async def verify_cmd(
        self,
        inter: disnake.ApplicationCommandInteraction,
        screenshot: disnake.Attachment = commands.Param(
            description="The screenshot of clan's page with your name in"
        ),
        clan: str = clans,
    ):
        if inter.author.id in self.bot.pending_verification_requests:
            await inter.send(
                f"You have already sent a verification request, please wait until it gets reviewed.",
                ephemeral=True,
            )
            return
        self.bot.pending_verification_requests.append(inter.author.id)
        await inter.response.defer(ephemeral=True)
        view = disnake.ui.View()
        view.stop()
        view.add_item(
            disnake.ui.Button(style=disnake.ButtonStyle.green, label="Accept")
        )
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.red, label="Deny"))
        await self.bot.pending_verification.send(
            f"{self.bot.officer.mention} new verification request from {inter.author.mention}\n\
```Regex data\n\
CLAN::{clan}\nBY::{inter.author.id}```",
            file=await screenshot.to_file(),
            view=view,
        )
        await inter.send(
            f"Your verification request was submitted, please wait until officers review it!",
            ephemeral=True,
        )


def setup(bot: Bot):
    bot.add_cog(Moderation(bot))
    bot.add_cog(ClanManagement(bot))
    bot.add_cog(Verification(bot))

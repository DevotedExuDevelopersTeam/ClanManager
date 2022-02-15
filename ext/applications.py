from re import search

import disnake
from disnake.ext import commands
from utils.bot import Bot
from utils.constants import CLAN_ROLES
from utils.events import ON_BUTTON_CLICK
from utils.forms import ClanApplicationForm, ReasonForm
from utils.views import ClansButtonsView


class ApplicationListeners(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def _process_get_started(self, inter: disnake.MessageInteraction):
        if inter.component.label == "Verify":
            await inter.response.defer(ephemeral=True)
            await inter.author.add_roles(self.bot.unverified)
            await inter.send(
                f"Please proceed to {self.bot.verify.mention} and use `/verify` command in there! Screenshot example",
                ephemeral=True,
                file=disnake.File("res/clan_example.png"),
            )

        elif inter.component.label == "Join":
            await inter.author.add_roles(self.bot.applicant)
            await inter.send(
                f"Please proceed to {self.bot.join_clan.mention}!", ephemeral=True
            )

    async def _process_join_clan(self, inter: disnake.MessageInteraction):
        if not inter.author.id in self.bot.pending_applicants:
            await inter.response.send_modal(ClanApplicationForm(self.bot))
        else:
            await inter.send(
                "You have already applied and your application has not been reviewed yet. Please wait for officers' decision.",
                ephemeral=True,
            )

    async def _process_application_review(self, inter: disnake.MessageInteraction):
        try:
            id = int(inter.message.embeds[0].description)
        except (IndexError, ValueError):
            return

        if not any(
            [
                self.bot.officer in inter.author.roles,
                self.bot.staff in inter.author.roles,
                inter.author.guild_permissions.administrator,
            ]
        ):
            await inter.send(
                f"You don't have right to review the applications.", ephemeral=True
            )
            return

        try:
            self.bot.pending_applicants.remove(id)
        except:
            pass

        if inter.component.label == "Deny":
            await inter.response.send_modal(ReasonForm(self.bot, inter, id))

        elif inter.component.label == "Accept":
            view = ClansButtonsView(inter.author.id, *CLAN_ROLES.keys())
            await inter.send(
                f"Please select a clan to accept this person to.", view=view
            )
            res = await view.get_result()
            await inter.delete_original_message()

            embed = inter.message.embeds[0].add_field(
                "APPROVED", f"By: {inter.author.mention}\nClan: {res}"
            )
            embed.color = 0x00FF00
            embed.title = "Accepted Application"
            await self.bot.accepted_applications.send(
                embed=inter.message.embeds[0],
                file=await inter.message.attachments[0].to_file(),
            )
            await inter.message.delete()

            member = self.bot.get_member(id)
            await member.remove_roles(self.bot.applicant)
            await member.add_roles(
                self.bot.get_role(CLAN_ROLES[res]), self.bot.verified
            )
            channel = await self.bot.server.create_text_channel(
                f"dc-{member}",
                category=self.bot.discussions,
                overwrites={
                    self.bot.server.default_role: disnake.PermissionOverwrite(
                        read_messages=False
                    ),
                    self.bot.officer: disnake.PermissionOverwrite(read_messages=True),
                    self.bot.staff: disnake.PermissionOverwrite(read_messages=True),
                    member: disnake.PermissionOverwrite(read_messages=True),
                },
            )

            await inter.send(
                f"The application was marked as approved. Discussion channel: {channel.mention}",
                ephemeral=True,
            )

            view = disnake.ui.View()
            view.stop()
            view.add_item(
                disnake.ui.Button(style=disnake.ButtonStyle.red, label="Close")
            )
            await channel.send(f"Created channel for discussion.", view=view)
            try:
                await member.send(
                    f"Congratulations, you were accepted into `{res}`! Please wait in {channel.mention} for further instructions."
                )
            except:
                pass

    async def _process_discussion_channel_close(
        self, inter: disnake.MessageInteraction
    ):
        if not any(
            [
                self.bot.officer in inter.author.roles,
                self.bot.staff in inter.author.roles,
                inter.author.guild_permissions.administrator,
            ]
        ):
            await inter.send(
                f"You don't have right to close this channel.", ephemeral=True
            )
            return

        await inter.response.send(f"Closing channel...")
        await inter.channel.delete()

    async def _process_verification_review(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        clan = search(r"CLAN::.*", inter.message.content).group().replace("CLAN::", "")
        member_id = int(
            search(r"BY::\d*", inter.message.content).group().replace("BY::", "")
        )
        member = self.bot.get_member(member_id)
        await member.remove_roles(self.bot.unverified)
        try:
            await self.bot.pending_verification_requests.remove(member_id)
        except:
            pass

        if inter.component.label == "Accept":
            role = self.bot.get_role(CLAN_ROLES[clan])
            await member.add_roles(role, self.bot.verified)
            await inter.message.delete()
            await inter.send(f"Verified {member.mention}", ephemeral=True)

        elif inter.component.label == "Deny":
            try:
                await member.send(
                    f"Your verification request was denied, please try again later."
                )
            except:
                pass
            await inter.message.delete()
            await inter.send(
                f"Denied application from {member.mention}", ephemeral=True
            )

    @commands.Cog.listener(ON_BUTTON_CLICK)
    async def applications_click_handler(self, inter: disnake.MessageInteraction):
        if inter.channel_id == self.bot.get_started.id:
            await self._process_get_started(inter)

        elif inter.channel_id == self.bot.join_clan.id:
            await self._process_join_clan(inter)

        elif inter.channel_id == self.bot.pending_applications.id:
            await self._process_application_review(inter)

        elif inter.channel.category_id == self.bot.discussions.id:
            await self._process_discussion_channel_close(inter)

        elif inter.channel_id == self.bot.pending_verification.id:
            await self._process_verification_review(inter)


def setup(bot: Bot):
    bot.add_cog(ApplicationListeners(bot))

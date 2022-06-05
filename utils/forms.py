from asyncio import TimeoutError, sleep
from os import remove

from disnake import (
    ButtonStyle,
    Embed,
    File,
    Message,
    MessageInteraction,
    ModalInteraction,
    PermissionOverwrite,
    TextInputStyle,
)
from disnake.ui import Button, Modal, TextInput, View

from utils.bot import Bot
from utils.constants import FAQ_CHANNEL_ID, OFFICER_ROLE_ID
from utils.image_processor import calculate_ssim
from utils.utils import extract_regex


class ClanApplicationForm(Modal):
    def __init__(self, bot: Bot):
        self.bot = bot
        components = [
            TextInput(
                label="Your ID", custom_id="ID", placeholder="12345678", max_length=15
            ),
            TextInput(
                label="Your clan rank",
                custom_id="Clan Rank",
                placeholder="Warrior",
                max_length=30,
            ),
            TextInput(
                label="Your average valor points",
                custom_id="Average Valor",
                placeholder="4000",
                max_length=15,
            ),
            TextInput(
                label="Your country or timezone",
                custom_id="Country | Timezone",
                placeholder="USA / EST",
                max_length=15,
            ),
            TextInput(
                label="Can you grind on war start?",
                custom_id="War Starter",
                placeholder="yes / no",
                max_length=10,
            ),
        ]
        super().__init__(title="Clan Application", components=components)

    async def callback(self, inter: ModalInteraction):
        data = inter.text_values
        try:
            await self.bot.set_pg_id(inter.id, int(data["ID"]))
        except Exception as e:
            print(e)

        channel = await inter.guild.create_text_channel(
            name=f"apl-{inter.author}",
            category=inter.channel.category,
            overwrites={
                inter.author: PermissionOverwrite(read_messages=True),
                inter.guild.default_role: PermissionOverwrite(read_messages=False),
            },
        )
        await inter.send(
            f"Thanks for submitting the form, now please go to {channel.mention} and attach the required profile screenshot!",
            ephemeral=True,
        )
        await channel.send(
            "Please attach your profile screenshot as shown in example. If you are not in any clan, head to friends page and search yourself.",
            file=File("res/profile_example.png"),
        )
        self.bot.pending_applicants.append(inter.author.id)
        while 1:
            try:
                m: Message = await self.bot.wait_for(
                    "message", check=lambda m: len(m.attachments) != 0, timeout=300
                )
                file_path = f".tmp/{inter.author.id}.png"
                await m.attachments[0].save(file_path)
                await m.delete()
                if calculate_ssim(file_path) < 0.4:
                    await channel.send(
                        f"Sorry, but this is the wrong screenshot. Please look at the example and try again. If you face the same issue, check out <#{FAQ_CHANNEL_ID}>."
                    )
                    continue

                embed = Embed(
                    color=0xFFFF00,
                    title="New Application",
                    description=f"```REGEX DATA\nID::{inter.author.id}```",
                )
                for k, v in data.items():
                    embed.add_field(k, v, inline=False)

                view = View()
                view.stop()
                view.add_item(Button(style=ButtonStyle.green, label="Accept"))
                view.add_item(Button(style=ButtonStyle.red, label="Deny"))
                await self.bot.pending_applications.send(
                    f"<@&{OFFICER_ROLE_ID}> new application by {inter.author.mention}",
                    embed=embed,
                    file=File(file_path),
                    view=view,
                )
                remove(file_path)

                await channel.send(
                    f"{inter.author.mention}, successfully sent your application! Now please wait for officers' decision."
                )
                await sleep(5)
                await channel.delete()

                return
            except TimeoutError:
                await channel.send(
                    f"{inter.author.mention}, your response has timed out. The channel is closing in 10 seconds. Please try again later."
                )
                await sleep(10)
                await channel.delete()
                self.bot.pending_applicants.remove(inter.author.id)
                return
            except Exception as e:
                self.bot.pending_applicants.remove(inter.author.id)
                await channel.send(
                    f"{inter.author.mention}, unknown error occured, we will be investigating it in the nearest time. Please be patient and attempt to try again."
                )
                await self.bot.admin.send(
                    f"{self.bot.owner.mention}, unknown error occured\n```{e}```"
                )
                raise e


class ReasonForm(Modal):
    def __init__(self, bot: Bot, inter: MessageInteraction, id: int):
        self.bot = bot
        self.inter = inter
        self.member = self.bot.get_member(id)
        components = [
            TextInput(
                label="Reason",
                placeholder="Provide the reason of denial",
                style=TextInputStyle.long,
                max_length=300,
                custom_id="reason",
            )
        ]
        super().__init__(title="Application Denial", components=components)

    async def callback(self, inter: ModalInteraction):
        await inter.response.defer(ephemeral=True)
        try:
            await self.member.send(
                f"Your clan application was denied: `{inter.text_values['reason']}`"
            )
        except:
            pass
        embed = self.inter.message.embeds[0].add_field(
            "DENIED", f"By: {inter.author}\nReason: {inter.text_values['reason']}"
        )
        embed.color = 0xFF0000
        embed.title = "Denied Application"
        await self.bot.denied_applications.send(
            f"Application by <@{extract_regex(embed.description, 'id')}> was denied.",
            embed=embed,
            file=await self.inter.message.attachments[0].to_file(),
        )
        await self.inter.message.delete()
        await self.inter.send(
            f"This application was marked as denied.\nReason: {inter.text_values['reason']}",
            ephemeral=True,
        )

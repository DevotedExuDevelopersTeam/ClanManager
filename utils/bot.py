import os
from datetime import datetime, timedelta

import disnake
from aiosqlite import connect
from disnake.ext import commands
from dotenv import load_dotenv
from exencolorlogs import Logger

from utils.constants import *


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            "cm!",
            intents=disnake.Intents.all(),
            strip_after_prefix=True,
            case_insensitive=True,
            test_guilds=[GUILD_ID],
        )
        self.log = Logger()
        self.add_check(self.global_check)
        self.add_app_command_check(self.slash_global_check, slash_commands=True)

        self.pending_applicants = []
        self.pending_verification_requests = []

    async def execute(self, query: str, *args):
        self.log.info(f'Executing query: "{query}" with args {args}...')
        cur = await self.db.execute(query, args)
        await self.db.commit()
        self.log.info("Query executed successfully.")
        return cur

    async def create_database(self):
        with open("config.sql", "r") as f:
            await self.execute(f.read())

    def run(self):
        if not os.path.exists(".tmp"):
            os.mkdir(".tmp")
        if not os.path.exists("data"):
            os.mkdir("data")

        load_dotenv()
        try:
            self.load_extensions("ext")
            super().run(os.getenv("TOKEN"))
        except disnake.LoginFailure:
            self.log.critical(
                "Improper token has been parsed. Please enter new token and restart the bot."
            )
            self.write_new_token()

    async def start(self, *args, **kwargs):
        self.log.info("Connecting to database...")
        self.db = await connect("data/database.db")
        self.log.info("Database connection established.")
        await self.create_database()

        await super().start(*args, **kwargs)

    async def close(self):
        self.log.info("Closing database connection...")
        await self.db.close()
        self.log.info("Database connection closed.")

        await super().close()

    async def on_ready(self):
        self.log.info("Bot is ready!")

        # server definition
        self.server = self.get_guild(GUILD_ID)

        # roles definition
        self.staff = self.get_role(STAFF_ROLE_ID)
        self.unverified = self.get_role(UNVERIFIED_ROLE_ID)
        self.applicant = self.get_role(APPLICANT_ROLE_ID)
        self.officer = self.get_role(OFFICER_ROLE_ID)
        self.verified = self.get_role(VERIFIED_ROLE_ID)
        self.clan_member = self.get_role(CLAN_MEMBER_ROLE_ID)

        # channels definition
        self.get_started = self.get_channel(GET_STARTED_CHANNEL_ID)
        self.join_clan = self.get_channel(JOIN_CLAN_CHANNEL_ID)
        self.verify = self.get_channel(VERIFY_CHANNEL_ID)
        self.discussions = self.get_channel(DISCUSSIONS_CATEGORY_ID)
        self.pending_verification = self.get_channel(PENDING_VERIFICATIONS_CHANNEL_ID)
        self.admin = self.get_channel(LOG_CHANNEL_ID)

        # application channels definition
        self.pending_applications = self.get_channel(PENDING_APPLICATIONS_CHANNEL_ID)
        self.accepted_applications = self.get_channel(ACCEPTED_APPLICATIONS_CHANNEL_ID)
        self.denied_applications = self.get_channel(DENIED_APPLICATIONS_CHANNEL_ID)

    @staticmethod
    def global_check(ctx: commands.Context):
        return ctx.channel.type != disnake.ChannelType.private

    @staticmethod
    def slash_global_check(inter: disnake.ApplicationCommandInteraction):
        return inter.channel.type != disnake.ChannelType.private

    async def add_ban_record(self, user: disnake.Member, time: timedelta):
        await self.execute(
            "INSERT OR REPLACE INTO bans VALUES (?, ?)",
            user.id,
            (datetime.now() + time).timestamp(),
        )

    def get_role(self, role_id: int):
        return self.server.get_role(role_id)

    def get_member(self, member_id: int):
        return self.server.get_member(member_id)

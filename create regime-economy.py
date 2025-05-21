import asyncio
import datetime
import logging
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button
from discord.utils import format_dt

from tortoise.exceptions import BaseORMException, DoesNotExist, IntegrityError
from tortoise.expressions import Q

from ballsdex.core.models import (
    Ball,
    BallInstance,
    BlacklistedGuild,
    BlacklistedID,
    BlacklistHistory,
    GuildConfig,
    Player,
    Special,
    Economy,
    Regime,
    Trade,
    TradeObject,
)
from ballsdex.core.utils.buttons import ConfirmChoiceView
from ballsdex.core.utils.enums import (
    DONATION_POLICY_MAP,
    FRIEND_POLICY_MAP,
    MENTION_POLICY_MAP,
    PRIVATE_POLICY_MAP,
)
from ballsdex.core.utils.logging import log_action
from ballsdex.core.utils.paginator import FieldPageSource, Pages, TextPageSource
from ballsdex.core.utils.transformers import (
    BallTransform,
    EconomyTransform,
    RegimeTransform,
    SpecialTransform,
)
from ballsdex.packages.admin.menu import BlacklistViewFormat
from ballsdex.packages.countryballs.countryball import CountryBall
from ballsdex.packages.trade.display import TradeViewFormat, fill_trade_embed_fields
from ballsdex.packages.trade.trade_user import TradingUser
from ballsdex.settings import settings

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot
    from ballsdex.packages.countryballs.cog import CountryBallsSpawner

log = logging.getLogger("ballsdex.packages.admin.cog")
FILENAME_RE = re.compile(r"^(.+)(\.\S+)$")

@app_commands.guilds(*settings.admin_guild_ids)
@app_commands.default_permissions(administrator=True)
class Admin(commands.GroupCog):
    """
    Bot admin commands.
    """

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_any_role(*settings.root_role_ids)
    async def create_regime(
        self,
        interaction: discord.Interaction,
        name: str,
        background: discord.Attachment,
    ):
        """
        Create a new regime.

        Parameters
        ----------
        name: str
            The name of the regime.
        background: discord.Attachment
            The background image for the regime.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            background_path = await save_file(background)  
        except Exception as e:
            await interaction.followup.send(
                f"Failed to save the background image: {str(e)}", ephemeral=True
            )
            return

        try:
            regime = await Regime.create(
                name=name,
                background=f"/{background_path}"  
            )
        except Exception as e:
            await interaction.followup.send(
                f"Failed to create the regime: {str(e)}", ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Regime `{regime.name}` created successfully!", ephemeral=True
        )
        await log_action(
            f"{interaction.user} created a new regime: {regime.name}.",
            self.bot,
        )

    @app_commands.command()
    @app_commands.checks.has_any_role(*settings.root_role_ids)
    async def create_economy(
        self,
        interaction: discord.Interaction,
        name: str,
        icon: discord.Attachment,  
    ):
        """
        Create a new economy.

        Parameters
        ----------
        name: str
            The name of the economy.
        icon: discord.Attachment
            The icon for the economy.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            icon_path = await save_file(icon)  
        except Exception as e:
            await interaction.followup.send(
                f"Failed to save the icon: {str(e)}", ephemeral=True
            )
            return

        try:
            economy = await Economy.create(
                name=name,
                icon=f"/{icon_path}"  
            )
        except Exception as e:
            await interaction.followup.send(
                f"Failed to create the economy: {str(e)}", ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Economy `{economy.name}` created successfully!", ephemeral=True
        )
        await log_action(
            f"{interaction.user} created a new economy: {economy.name}.",
            self.bot,
        )

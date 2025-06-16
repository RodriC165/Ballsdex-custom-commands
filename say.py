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

    @app_commands.command(name="say", description="Send a message through the bot")
    @app_commands.checks.has_any_role(*settings.root_role_ids, *settings.admin_role_ids)
    async def admin_say(self, interaction: discord.Interaction, message: str):
        """
        Send a message through the bot.

        Parameters
        ----------
        message: str
            The message the bot will send.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await interaction.channel.send(message)
            await interaction.followup.send(f"✅ Message sent: `{message}`", ephemeral=True)
            await log_action(
                f"{interaction.user} used /admin say to send: '{message}' in {interaction.channel}.",
                self.bot,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I do not have permission to send messages in this channel.", ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error sending message: {str(e)}", ephemeral=True
            )

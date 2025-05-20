import enum
import logging
import string
from collections import defaultdict
from typing import TYPE_CHECKING, cast
import random
import logging
import json
import os
import aiohttp
import io

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, button
from discord.utils import get
from discord.errors import NotFound
from tortoise.exceptions import DoesNotExist
from tortoise.functions import Count

from ballsdex.core.models import BallInstance, DonationPolicy, Player, Ball, Special, Trade, TradeObject, specials, balls
from ballsdex.core.utils.buttons import ConfirmChoiceView
from ballsdex.core.utils.paginator import FieldPageSource, Pages
from ballsdex.core.utils.transformers import (
    BallEnabledTransform,
    BallInstanceTransform,
    SpecialEnabledTransform,
    TradeCommandType,
)
from ballsdex.core.utils.utils import inventory_privacy, is_staff
from ballsdex.packages.balls.countryballs_paginator import CountryballsViewer, DuplicateViewMenu
from ballsdex.settings import settings

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("ballsdex.packages.countryballs")

class Balls(commands.GroupCog, group_name=settings.players_group_cog_name):
    """
    View and manage your countryballs collection.
    """

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    @app_commands.choices(art_type=[
        app_commands.Choice(name="Spawn Art", value="spawn"),
        app_commands.Choice(name="Card Art", value="card"),
        app_commands.Choice(name="Emoji", value="emoji"),
    ])
    async def art(
        self,
        interaction: discord.Interaction,
        countryball: BallEnabledTransform,
        art_type: str,
    ):
        """
        Showcase the art of a country ball.

        Parameters
        ----------
        countryball: BallEnabledTransform
            The country ball you want to see the art of.
        art_type: str
            The type of art to display.
        """
        await interaction.response.defer(thinking=True)

        if not countryball:
            await interaction.followup.send(
                "No se encontró la countryball especificada.", ephemeral=True
            )
            return

        def generate_random_name():
            source = string.ascii_uppercase + string.ascii_lowercase + string.ascii_letters
            return "".join(random.choices(source, k=15))

        ball_emoji = self.bot.get_emoji(countryball.emoji_id) or "🏐"

        try:
            if art_type == "spawn":
                extension = countryball.wild_card.split(".")[-1]
                file_location = "." + countryball.wild_card
                file_name = f"nt_{generate_random_name()}.{extension}"
                file = discord.File(file_location, filename=file_name)
                content = (
                    f"**{countryball.country}** - Spawn\n"
                    f" {countryball.country} Spawn."
                )
                await interaction.followup.send(content=content, file=file, ephemeral=True)
                file.close()

            if art_type == "card":
                extension = countryball.collection_card.split(".")[-1]
                file_location = "." + countryball.collection_card
                file_name = f"nt_{generate_random_name()}.{extension}"
                file = discord.File(file_location, filename=file_name)
                content = (
                    f"**{countryball.country}** - Card\n"
                    f" {countryball.country} Card."
                )
                await interaction.followup.send(content=content, file=file, ephemeral=True)
                file.close()

            elif art_type == "emoji":
                emoji_url = f"https://cdn.discordapp.com/emojis/{countryball.emoji_id}.png"
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as response:
                        if response.status != 200:
                            await interaction.followup.send(
                                "Could not get emoji image.", ephemeral=True
                            )
                            return
                        emoji_data = await response.read()
                file = discord.File(
                    io.BytesIO(emoji_data),
                    filename=f"{countryball.country}_emoji.png"
                )
                content = (
                    f"**{countryball.country}** - Emoji\n"
                    f"{countryball.country} Emoji."
                )
                await interaction.followup.send(content=content, file=file, ephemeral=True)
                file.close()

        except discord.Forbidden:
            log.error(f"Missing permission to send art in channel {interaction.channel}.")
            await interaction.followup.send(
                "I don't have permission to submit this art.", ephemeral=True
            )
        except discord.HTTPException as e:
            log.error(f"Failed to send art: {e}", exc_info=True)
            await interaction.followup.send(
                "An error occurred while displaying the art.", ephemeral=True
            )
        except Exception as e:
            log.error(f"Unexpected error in art command: {e}", exc_info=True)
            await interaction.followup.send(
                "An unexpected error occurred.", ephemeral=True
            )

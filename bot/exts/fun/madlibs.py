import json
from asyncio import TimeoutError
from pathlib import Path
from random import choice

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

# import json
# from typing import Literal
# from typing import List

TIMEOUT = 60.0


class Madlibs(commands.Cog):
    """
    Cog for the Madlibs game.

    Madlibs is a game where the player is asked to enter a word that
    fits a random part of speech (e.g. noun, adjective, verb, plural noun, etc.).
    The bot chooses a random number of user inputs (within the specified bounds
    of the command arguments) to use for the game and a random story.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.templates = self._load_templates()

    @staticmethod
    def _load_templates() -> list:
        madlibs_stories = Path("bot/resources/fun/madlibs_templates (1).json")

        with open(madlibs_stories) as file:
            return json.load(file)

    @staticmethod
    def madlibs_embed(part_of_speech: str, number_of_inputs: int) -> Embed:
        """Method to have the bot send an embed with the game information."""
        madlibs_embed = Embed(
            title="Madlibs",
            color=Colours.python_blue,
        )

        madlibs_embed.add_field(
            name="Enter a word that fits the given part of speech!",
            value=f"Part of speech: {part_of_speech}"
        )

        madlibs_embed.set_footer(text=f'Inputs remaining: {number_of_inputs}')

        return madlibs_embed

    @commands.command()
    async def madlibs(
        self,
        ctx: commands.Context,
    ) -> None:
        """Play Madlibs with the bot, where you have to enter a word that fits the part of speech that you are given!"""
        random_template = choice(self.templates["templates"])
        # random_template = self.templates["templates"][0]

        current_input = 0

        number_of_inputs = len(random_template["blanks"])

        part_of_speech = random_template["blanks"][current_input]

        madlibs_embed = self.madlibs_embed(part_of_speech, number_of_inputs)

        original_message = await ctx.send(embed=madlibs_embed)

        while True:
            part_of_speech = random_template["blanks"][current_input]

            try:
                message = await self.bot.wait_for(event='message', timeout=TIMEOUT)
            except TimeoutError:
                timeout_embed = Embed(title='Timeout!',
                                      description='Uh oh! Looks like the bot timed out! Please try again later.',
                                      color=Colours.soft_red)

                await ctx.send(embed=timeout_embed)
                return

            word = message.content
            submitted_words = []
            submitted_words += word

            # str_template = ' '.join(random_template["value"])
            # for word, blank in zip(submitted_words, random_template["value"]):
            #     word_in_story = blank.replace("", word)

            # random_template["value"] += submitted_words

            current_input += 1
            number_of_inputs -= 1

            madlibs_embed.clear_fields()

            madlibs_embed = self.madlibs_embed(part_of_speech, number_of_inputs)

            await original_message.edit(embed=madlibs_embed)

            if number_of_inputs == 0:
                break

        str_template = ' '.join(random_template["value"])
        str_template_with_words = str_template.join(submitted_words)

        story_embed = Embed(
            title=random_template["title"],
            description=str_template_with_words,
            color=Colours.bright_green,
        )

        await ctx.send(embed=story_embed)


def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    bot.add_cog(Madlibs(bot))

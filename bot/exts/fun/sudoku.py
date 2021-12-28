import datetime

import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

# import random

BACKGROUND = (242, 243, 244)
BLACK = 0
SUDOKU_TEMPLATE_PATH = "bot/resources/fun/sudoku_template.png"
NUM_FONT = ImageFont.truetype("bot/resources/fun/Roboto-Medium.ttf", 99)


class SudokuGame:
    """Class that contains information and regarding Sudoku game."""

    def __init__(self, ctx: commands.Context, difficulty: str):
        self.ctx = ctx
        self.image = Image.open(SUDOKU_TEMPLATE_PATH)
        self.solution = self.generate_board()
        self.puzzle = self.generate_puzzle()
        self.running: bool = True
        self.invoker: discord.Member = ctx.author
        self.started_at: datetime.datetime = datetime.datetime.now()
        self.difficulty: str = difficulty  # enum class?
        self.hints: list[datetime.datetime] = []

    def draw_num(self, digit: int, position: tuple[int, int]) -> Image:
        """Draw a number on the sudoku board."""
        digit = str(digit)
        if digit in "123456" and len(digit) == 1:
            draw = ImageDraw.Draw(self.image)
            draw.text(self.index_to_coord(position), str(digit), fill=BLACK, font=NUM_FONT)
            self.image.show()
            return self.image

    @staticmethod
    def index_to_coord(position: tuple[int, int]) -> tuple[int, int]:
        """Convert a 2d list index to a coordinate on the sudoku image."""
        return position[0] * 100 + 20, position[1] * 100 - 5

    @staticmethod
    def generate_board() -> list[list[int]]:
        """Generate a valid Sudoku with one solution."""
        pass

    def generate_puzzle(self) -> list[list[int]]:
        """Remove numbers from a valid Sudoku solution based on the difficulty. Returns a Sudoku puzzle."""
        pass

    @property
    def solved(self) -> bool:
        """Check if the puzzle has been solved."""
        return self.solution == self.puzzle


class Sudoku(commands.Cog):
    """Cog for the Sudoku game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: dict[int:SudokuGame] = {}

    @commands.group(aliases=["s"])
    async def sudoku(self, ctx: commands.Context) -> None:
        """
        Play Sudoku with the bot!

        Sudoku is a grid game where you start with a 9x9 grid, and you are given certain numbers on the
        grid. In this version of the game, however, the grid will be a 6x6 one instead of the traditional
        9x9. All numbers on the grid, traditionally, are 1-9, and no number can repeat itself in any row,
        column, or any of the smaller 3x3 grids. In this version of the game, it would be 2x3 smaller grids
        instead of 3x3 and numbers 1-6 will be used on the grid.
        """
        if not self.games.get(ctx.author.id):
            await self.start(ctx)

    @sudoku.command()
    async def start(self, ctx: commands.Context, difficulty: str = "Normal") -> None:
        """Start a sudoku game."""
        if self.games.get(ctx.author.id):
            await ctx.send("You are already playing a game!")
            return
        self.games[ctx.author.id] = SudokuGame(ctx, difficulty)
        await ctx.send("Started a Sudoku game.")

    @sudoku.command(aliases=["end", "stop"])
    async def finish(self, ctx: commands.Context) -> None:
        """End a Sudoku game."""
        game = self.games.get(ctx.author.id)
        if game:
            if ctx.author == game.invoker:
                del game
                await ctx.send("Ended the current game.")
            else:
                await ctx.send("Only the owner of the game can end it!")
        else:
            await ctx.send("You are not playing a sudoku game! Type `.sudoku start` to begin.")

    @sudoku.command(aliases=["who", "information", "score"])
    async def info(self, ctx: commands.Context) -> None:
        """Send info about a currently running Sudoku game."""
        game = self.games[ctx.author.id]
        if not game.running:
            await ctx.send("There are no currently running games!")
            return
        current_time = datetime.datetime.now()
        info_embed = discord.Embed(title="Sudoku Game Information", color=Colours.grass_green)
        info_embed.add_field(name="Player", value=game.invoker.name)
        info_embed.add_field(name="Current Time", value=(current_time - game.started_at))
        info_embed.add_field(name="Progress", value="N/A")  # add in this variable
        info_embed.add_field(name="Difficulty", value=game.difficulty)
        info_embed.set_author(name=game.invoker.name, icon_url=game.invoker.display_avatar.url)
        info_embed.add_field(name="Hints Used", value=len(game.hints))
        await ctx.send(embed=info_embed)


class SudokuView(discord.ui.View):
    """A set of buttons to control a sudoku game."""

    def __init__(self, ctx: commands.Context):
        super(SudokuView, self).__init__()
        self.ctx = ctx
        # self.children[0]

    @discord.ui.button(style=discord.ButtonStyle.red, label="End game")
    async def end_button(self, _: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Button that ends the current game."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku finish"))

    @discord.ui.button(style=discord.ButtonStyle.green, label="Hint")
    async def hint_button(self, _: discord.ui.Select, interaction: discord.Interaction) -> discord.Message:
        """Button that fills in one square on the sudoku board."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description="Sorry, but this interaction can only be used by the original author.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True


def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    bot.add_cog(Sudoku(bot))

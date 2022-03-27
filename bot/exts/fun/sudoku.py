# import copy
import os
import random
import time
from asyncio import TimeoutError
from typing import Optional

import PIL
import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

# from builtins import int

BACKGROUND = (242, 243, 244)
BLACK = 0
SUDOKU_TEMPLATE_PATH = "bot/resources/fun/sudoku_template.png"
NUM_FONT = PIL.ImageFont.truetype("bot/resources/fun/Roboto-Medium.ttf", 99)


class CoordinateConverter(commands.Converter):
    """Converter used in Sudoku game."""

    async def convert(self, argument: str) -> tuple[int, int]:
        """Convert alphanumeric grid coordinates to 2d list index. (e.g. 'C1'-> (2, 0))."""
        argument = sorted(argument.lower())
        if len(argument) != 2:
            raise commands.BadArgument("The coordinate must be two characters long.")
        if argument[0].isnumeric() and not argument[1].isnumeric():
            number, letter = argument[0], argument[1]
        else:
            raise commands.BadArgument("The coordinate must comprise of"
                                       "1 letter from A to F, and 1 number from 1 to 6.")
        if 0 > int(number) > 10 or letter not in "abcdef":
            raise commands.BadArgument("The coordinate must comprise of"
                                       "1 letter from A to F, and 1 number from 1 to 6.")
        return ord(letter)-97, int(number)-1


class GenerateSudokuPuzzle:
    """Class that contains functions for generating Sudoku puzzles."""

    def __init__(self, grid: list[list[int]]):
        self.counter = 0
        self.path = []
        # self.puzzle = self.generate_puzzle(grid)
        # self.difficulty: str = difficulty  # enum class?
        self.grid = grid
        # self.puzzle = self.GenerateSudokuPuzzle()
        # self.num_of_zeros = num_of_zeros
        # self.original = copy.deepcopy(self.grid)

    def test_sudoku(self, grid: list[list[int]]) -> bool:
        """Tests each square to make sure it is a valid puzzle."""
        for row in range(6):
            for col in range(6):
                num = grid[row][col]
                # Remove number from grid to test if it's valid
                grid[row][col] = 0
                if not self.valid_location(grid, row, col, num):
                    return False
                else:
                    # Put number back in grid
                    grid[row][col] = num
        return True

    @staticmethod
    def num_used_in_row(grid, row, number) -> bool:
        """Returns True if the number has been used in that row."""
        if number in grid[row]:
            return True
        return False

    @staticmethod
    def num_used_in_column(grid, col, number) -> bool:
        """Returns True if the number has been used in that column."""
        for i in range(6):
            if grid[i][col] == number:
                return True
        return False

    @staticmethod
    def num_used_in_subgrid(grid, row, col, number) -> bool:
        """Returns True if the number has been used in that subgrid/box."""
        sub_row = (row // 2) * 2
        sub_col = (col // 2) * 2
        for i in range(sub_row, (sub_row + 2)):
            for j in range(sub_col, (sub_col + 2)):
                if grid[i][j] == number:
                    return True
        return False

    def valid_location(self, grid, row, col, number) -> bool:
        """Return False if the number has been used in the row, column or subgrid."""
        if self.num_used_in_row(grid, row, number):
            return False
        elif self.num_used_in_column(grid, col, number):
            return False
        elif self.num_used_in_subgrid(grid, row, col, number):
            return False
        return True

    @staticmethod
    def find_empty_square(grid) -> (int, int):
        """Return the next empty square coordinates in the grid."""
        for i in range(6):
            for j in range(6):
                if grid[i][j] == 0:
                    return i, j
        return

    @staticmethod
    def get_non_empty_squares(grid) -> list:
        """Returns a shuffled list of non-empty squares in the puzzle."""
        non_empty_squares = []
        for i in range(len(grid)):
            for j in range(len(grid)):
                if grid[i][j] != 0:
                    non_empty_squares.append((i, j))
        random.shuffle(non_empty_squares)
        return non_empty_squares

    # def set_difficulty(self, difficulty) -> None:
    #     if difficulty == "easy": # Generate 12 clues, 24 0's.
    #         self.num_of_zeros = 24
    #     if difficulty == "medium": # Generate 11 clues, 23 0's.
    #         self.num_of_zeros = 23
    #     if difficulty == "hard": # Generate 10 clues, 22 0's.
    #         self.num_of_zeros = 22

    def generate_solution(self, grid) -> bool:
        """Generates a full solution with backtracking."""
        number_list = [1, 2, 3, 4, 5, 6]
        for i in range(0, 36):
            row = i // 6
            col = i % 6
            # Find next empty cell
            if grid[row][col] == 0:
                shuffle(number_list)
                for number in number_list:
                    if self.valid_location(grid, row, col, number):
                        self.path.append((number, row, col))
                        grid[row][col] = number
                        if not self.find_empty_square(grid):
                            return True
                        else:
                            if self.generate_solution(grid):
                                # If the grid is full
                                return True
                break

        grid[row][col] = 0
        return False

    def remove_numbers_from_grid(self) -> None:
        """Remove numbers from the grid to create the puzzle."""
        # Get all non-empty squares from the grid
        non_empty_squares = self.get_non_empty_squares(self.grid)
        non_empty_squares_count = len(non_empty_squares)
        rounds = 3
        while rounds > 0 and non_empty_squares_count >= 11:
            # There should be at least 11 clues for easy puzzles,
            # 10 clues for medium puzzles, and 9 clues for hard puzzles.
            row, col = non_empty_squares.pop()
            non_empty_squares_count -= 1
            # Might need to put the square value back if there is more than one solution
            removed_square = self.grid[row][col]
            self.grid[row][col] = 0
            # Initialize solutions counter to zero
            self.counter = 0
            # If there is more than one solution, put the last removed cell back into the grid
            if self.counter != 1:
                self.grid[row][col] = removed_square
                non_empty_squares_count += 1
                rounds -= 1

    def generate_puzzle(self) -> None:
        """Remove numbers from a valid Sudoku solution based on the difficulty. Returns a Sudoku puzzle."""
        self.grid = [[0 for _ in range(6)] for _ in range(6)]
        self.generate_solution(self.grid)
        return self.remove_numbers_from_grid(self.grid)


class SudokuGame:
    """Class that contains functions that are necessary for Sudoku to work properly, such as
    drawing numbers on the board and displaying game information."""

    def __init__(self, ctx: commands.Context):
        # self.grid = grid
        self.puzzle = self.GenerateSudokuPuzzle()
        self.ctx = ctx
        self.image = PIL.Image.open(SUDOKU_TEMPLATE_PATH)
        self.running: bool = True
        self.invoker: discord.Member = ctx.author
        self.started_at = time.time()
        self.hints: list[time.time] = []
        self.message = None
        # self.num_of_zeros = GenerateSudokuPuzzle.num_of_zeros
        # self.solution = GenerateSudokuPuzzle.generate_solution(grid)

    def draw_num(self, digit: int, position: tuple[int, int]) -> PIL.Image:
        """Draw a number on the Sudoku board."""
        digit = str(digit)
        if digit in "123456" and len(digit) == 1:
            draw = PIL.ImageDraw.Draw(self.image)
            draw.text(self.index_to_coord(position), str(digit), fill=BLACK, font=NUM_FONT)
            return self.image

    @staticmethod
    def index_to_coord(position: tuple[int, int]) -> tuple[int, int]:
        """Convert a 2D list index to an (x, y) coordinate on the Sudoku image."""
        return position[0] * 83 + 98, (position[1]) * 83 + 13

    def info_embed(self, ctx: commands.Context) -> discord.Embed:
        """Create an embed that displays game information."""
        current_time = time.time()
        info_embed = discord.Embed(title="Sudoku Game Information", color=Colours.grass_green)
        info_embed.set_author(name=ctx.author, icon_url=self.invoker.display_avatar.url)
        info_embed.add_field(name="Current Time", value=(current_time - self.started_at))
        info_embed.add_field(name="Progress", value="N/A")  # value will be (36 - # of 0's) / 36
        info_embed.add_field(name="Difficulty", value=self.difficulty)
        info_embed.add_field(name="Hints Used", value=len(self.hints))
        return info_embed

    # @property
    # def solved(self) -> bool:
    #     """Check if the puzzle has been solved."""
    #     return self.solution == self.puzzle

    async def update_board(self, digit: int = None, coord: (int, int) = None) -> None:
        """This function keeps the board up-to-date as new guesses are inputted by the player."""
        update_board = discord.Embed(title="Sudoku",
                                     description="Waiting for input...", color=Colours.soft_orange)
        if digit and coord:
            self.draw_num(digit, coord)
        self.image.save("sudoku.png")
        file = discord.File("sudoku.png")
        update_board.set_image(url="attachment://sudoku.png")
        if self.message:
            await self.message.delete()
        self.message = await self.ctx.send(file=file, embed=update_board, view=SudokuView(self.ctx))
        os.remove("sudoku.png")

        return self.puzzle


class SudokuCog(commands.Cog):
    """Cog for the Sudoku game."""

    def __init__(self, grid: list[list[int]], bot: Bot):
        self.bot = bot
        self.games: dict[int, SudokuGame] = {}
        # self.ctx = ctx
        self.grid = grid
        self.puzzle = GenerateSudokuPuzzle(GenerateSudokuPuzzle().grid)
        # self.difficulty = SudokuDifficulty.

    def author_check(self, ctx: commands.Context, message: discord.Message) -> bool:
        return message.channel.id == ctx.channel.id and message.author.id == ctx.author.id

    @commands.group(aliases=["s"], invoke_without_command=True)
    async def sudoku(self, ctx: commands.Context, coord: Optional[CoordinateConverter] = None,
                     digit: Optional[str] = None) -> None:
        """
        Play Sudoku with the bot!

        Sudoku is a grid game where you start with a 9x9 grid, and you are given certain numbers on the
        grid. In this version of the game, however, the grid will be a 6x6 one instead of the traditional
        9x9. All numbers on the grid, traditionally, are 1-9, and no number can repeat itself in any row,
        column, or any of the smaller 3x3 grids. In this version of the game, it would be 2x3 smaller grids
        instead of 3x3 and numbers 1-6 will be used on the grid.
        """
        game = self.games.get(ctx.author.id)
        if not game:
            # discord.ui.View(timeout=60.0)
            # await ctx.send("Please select your difficulty with the buttons below:", view=SudokuDifficulty(ctx))

                # await self.bot.wait_for(event=discord.ui.button, timeout=60.0, check=self.author_check)
            # except TimeoutError:
            #     timeout_embed = discord.Embed(
            #         title=random.choice(NEGATIVE_REPLIES),
            #         description="Uh oh! You took too long to respond!",
            #         color=Colours.soft_red
            #     )

                # await ctx.send(ctx.author.mention, embed=timeout_embed)

            await self.start(ctx)
        elif coord and digit.isnumeric() and -1 < int(digit) < 10 or digit.lower() == "x":
            print(f"{coord=}, {digit=}")
            await game.update_board(digit, coord)
        else:
            raise commands.BadArgument
            # await ctx.send("Welcome to Sudoku! Type your guesses like so: `A1 1`")
            # await self.start(ctx)
            # await self.bot.wait_for(event="message")
            # if coord and digit.isnumeric() and -1 < int(digit) < 10 or digit in "xX":
            #     # print(f"{coord=}, {digit=}")
            #     await game.update_board(digit, coord)
            # else:
            #     raise commands.BadArgument

    @sudoku.command()
    async def start(self, ctx: commands.Context) -> None:
        """Start a Sudoku game."""
        if self.games.get(ctx.author.id):
            await ctx.send("You are already playing a game!")
            return
        self.games[ctx.author.id] = SudokuGame(ctx, self.puzzle)
        await ctx.send("Started a Sudoku game.")

    @sudoku.command(aliases=["end", "stop"])
    async def finish(self, ctx: commands.Context) -> None:
        """End a Sudoku game."""
        game = self.games.get(ctx.author.id)
        if game:
            if ctx.author == game.invoker:
                del self.games[ctx.author.id]
                await ctx.send("Ended the current game.")
            else:
                await ctx.send("Only the owner of the game can end it!")
        else:
            await ctx.send("You are not playing a Sudoku game! Type `.sudoku start` to begin.")

    @sudoku.command(aliases=["who", "information", "score"])
    async def info(self, ctx: commands.Context) -> None:
        """Send info about a currently running Sudoku game."""
        game = self.games.get(ctx.author.id)
        if game:
            await ctx.send(embed=game.info_embed())
        else:
            await ctx.send("You are not playing a game!")

    @sudoku.command()
    async def hint(self, ctx: commands.Context) -> None:
        """Fill in one empty square on the Sudoku board."""
        game = self.games.get(ctx.author.id)
        if game:
            game.hints.append(time.time())
            while True:
                x, y = random.randint(0, 5), random.randint(0, 5)
                if game.puzzle[x][y] == 0:
                    await game.update_board(digit=random.randint(0, 5), coord=(x, y))
                    break


class SudokuView(discord.ui.View):
    """A set of buttons to control a Sudoku game."""

    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.disabled = None
        self.ctx = ctx
        # self.children[0]

    @discord.ui.button(style=discord.ButtonStyle.green, label="Hint")
    async def hint_button(self, *_) -> None:
        """Button that fills in one empty square on the Sudoku board."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku hint"))

    @discord.ui.button(style=discord.ButtonStyle.primary, label="Game Info")
    async def info_button(self, *_) -> None:
        """Button that displays information about the current game."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku information"))

    @discord.ui.button(style=discord.ButtonStyle.red, label="End Game")
    async def end_button(self, *_) -> None:
        """Button that ends the current game."""
        await self.ctx.invoke(self.ctx.bot.get_command("sudoku finish"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            error_embed = discord.Embed(
                description="Sorry, but this button can only be used by the original author.")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return False
        return True


def setup(bot: Bot) -> None:
    """Load the Sudoku cog."""
    bot.add_cog(SudokuCog(bot))

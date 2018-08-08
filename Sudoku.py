import argparse
import numpy as np
from tkinter import Tk, Canvas, Frame, Button, BOTH, TOP, BOTTOM, LEFT


BOARDS = ['debug', 'easy', 'hard']  # Available sudoku boards
MARGIN = 20  # Pixels around the board
SIDE = 50  # Width of every board cell.
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9  # Width and height of the whole board
BUTTON_HEIGHT = 40  # height of button below th board


class SudokuError(Exception):
    """
    An application specific error.
    """
    pass


class SudokuCSP(object):
    """
    A csp AI to solve the game of sudoku
    """
    def __init__(self, board):
        self.board = board
        self.constraints = list()

    def generate_all_binary_constraints(self):
        alldiff_constraints = self.generate_all_constraints()

        print("Alldiff constraints:", len(alldiff_constraints))
        binaries = []
        for constraint in alldiff_constraints:
            binaries = binaries + self.alldiff_as_binary(constraint)
        binaries = set(tuple(binaries))
        print("Binary constraints: (9 choose 2)*18 + ((9 choose 2)-(3 choose 2)*6)*9 = ", len(binaries))
        # binaries bound by lambda x, y: not (x == y)
        return binaries

    def generate_all_constraints(self):
        # a row is [(0, 0), (1, 0), ... (8, 0)]
        row_constraints = []
        column_constraints = []
        box_constraints = []
        for i in range(9):
            row_constraints.append([])
            column_constraints.append([])
            box_constraints.append([])
        for i in range(9):
            for j in range(9):
                column_constraints[i].append((i, j))
                row_constraints[i].append((j, i))

        index = 0
        for j in {0, 3, 6}:
            for k in {0, 3, 6}:
                for l in range(j, j+3):
                    for m in range(k, k+3):
                        box_constraints[index].append((l, m))
                index += 1

        return tuple(box_constraints + row_constraints + column_constraints)

    def alldiff_as_binary(self, elements):
        # generate a all combinations of indexes of elements
        combinations = self.combination(len(elements), 2).T

        # replace indexes with elements and return
        element_array = np.array(elements)
        output_list = element_array[combinations].tolist()
        return [tuple(tuple(x) for x in item) for item in output_list]

    def combination(self, n, k):
        a = np.ones((k, n-k+1), dtype=int)
        a[0] = np.arange(n-k+1)
        for j in range(1, k):
            reps = (n-k+j) - a[j-1]
            a = np.repeat(a, reps, axis=1)
            ind = np.add.accumulate(reps)
            a[j, ind[:-1]] = 1-reps[1:]
            a[j, 0] = j
            a[j] = np.add.accumulate(a[j])
        return a


def parse_arguments():
    """
    Parses arguments of the form:
        sudoku.py <board name>
    Where `board name` must be in the `BOARD` list
    """
    # initialize parser for input
    arg_parser = argparse.ArgumentParser()
    # require the --board argument
    arg_parser.add_argument("--board",
                            help="Desired board name",
                            type=str,
                            choices=BOARDS,
                            required=True)

    # Creates a dictionary of keys = argument flag, and value = argument
    args = vars(arg_parser.parse_args())
    return args


class SudokuUI(Frame):
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.

    parent: Tk()
    game: SudokuGame()
    """
    def __init__(self, parent, game):
        self.game = game
        Frame.__init__(self, parent)
        self.parent = parent

        # holds cord of selected box
        self.row, self.col = -1, -1

        self.__initUI()

    def __initUI(self):
        # label the title of program
        self.parent.title("Sudoku")
        self.pack(fill=BOTH)

        bottomframe = Frame(root)
        bottomframe.pack(side=BOTTOM)
        # the canvas for the game to be drawn on, width and height specified
        self.canvas = Canvas(self,
                             width=WIDTH,
                             height=HEIGHT)
        self.canvas.pack(fill=BOTH, side=TOP)

        # Clear board button, calls __clear_answers function
        clear_button = Button(bottomframe,
                              text="Clear answers",
                              height=BUTTON_HEIGHT,
                              command=self.__clear_answers)

        # Place the button on the bottom and have it fill the entire width/height assigned
        clear_button.pack(fill=BOTH, side=LEFT)

        # Clear board button, calls __clear_answers function
        solve_button = Button(bottomframe,
                              text="Solve With CSP",
                              height=BUTTON_HEIGHT,
                              command=self.game.run_ai)

        # Place the button on the bottom and have it fill the entire width/height assigned
        solve_button.pack(fill=BOTH, side=LEFT)

        # draw the grid (a bunch of lines)
        self.__draw_grid()

        # draw numbers based on array
        self.__draw_puzzle()

        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __draw_grid(self):
        """
        Draws grid divided with blue lines into 3x3 squares
        """
        for i in range(10):
            color = "blue" if i % 3 == 0 else "gray"

            # vertical line
            x0 = MARGIN + i * SIDE
            y0 = MARGIN
            x1 = MARGIN + i * SIDE
            y1 = HEIGHT - MARGIN
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            # horizontal line
            x0 = MARGIN
            y0 = MARGIN + i * SIDE
            x1 = WIDTH - MARGIN
            y1 = MARGIN + i * SIDE
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    # draw the numbers
    def __draw_puzzle(self):
        # delete the old numbers
        self.canvas.delete("numbers")

        # loop through number array and draw new numbers
        for i in range(9):
            for j in range(9):
                # the number to draw
                answer = self.game.puzzle[i][j]
                # if not 0 (our placeholder for no numbers), draw number as text
                if answer != 0:
                    # place in middel of the sqare ( add SIDE // 2)
                    x = MARGIN + j * SIDE + SIDE // 2
                    y = MARGIN + i * SIDE + SIDE // 2
                    original = self.game.start_puzzle[i][j]
                    # if number started in puzzle make it black otherwise make it green
                    color = "black" if answer == original else "sea green"
                    self.canvas.create_text(
                        x, y, text=answer, tags="numbers", fill=color
                    )

    # outlines box in red
    def __draw_cursor(self):
        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = MARGIN + self.col * SIDE + 1
            y0 = MARGIN + self.row * SIDE + 1
            x1 = MARGIN + (self.col + 1) * SIDE - 1
            y1 = MARGIN + (self.row + 1) * SIDE - 1
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="red", tags="cursor"
            )

    # draws a circle with YOU WIN over the screen
    def __draw_victory(self):
        # create a oval (which will be a circle)
        x0 = y0 = MARGIN + SIDE * 2
        x1 = y1 = MARGIN + SIDE * 7
        self.canvas.create_oval(
            x0, y0, x1, y1,
            tags="victory", fill="dark orange", outline="orange"
        )
        # create text
        x = y = MARGIN + 4 * SIDE + SIDE // 2
        self.canvas.create_text(
            x, y,
            text="You win!", tags="victory",
            fill="white", font=("Arial", 32)
        )

    # given a click event, records the cell clicked on and outlines box in red
    def __cell_clicked(self, event):
        if self.game.game_over:
            return
        x, y = event.x, event.y
        if (MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN):
            # allow canvas to recieve keyboard bindings
            self.canvas.focus_set()

            # get row and col numbers from x,y coordinates
            row, col = (y - MARGIN) // SIDE, (x - MARGIN) // SIDE

            # if cell was selected already - deselect it
            if (row, col) == (self.row, self.col):
                self.row, self.col = -1, -1
            elif self.game.puzzle[row][col] == 0:
                self.row, self.col = row, col
        else:
            self.row, self.col = -1, -1

        self.__draw_cursor()

    # if key is pressed add num to square currently focused on and check for victory
    def __key_pressed(self, event):
        if self.game.game_over:
            return
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            self.game.puzzle[self.row][self.col] = int(event.char)
            self.col, self.row = -1, -1
            self.__draw_puzzle()
            self.__draw_cursor()
            if self.game.check_win():
                self.__draw_victory()

    # reset the game
    def __clear_answers(self):
        self.game.start()
        self.canvas.delete("victory")
        self.__draw_puzzle()


class SudokuBoard(object):
    """
    Sudoku Board representation
    """
    def __init__(self, board_file):
        self.board = self.__create_board(board_file)

    def __create_board(self, board_file):
        board = []
        for line in board_file:
            line = line.strip()
            if len(line) != 9:
                raise SudokuError(
                    "Each line in the sudoku puzzle must be 9 chars long."
                )
            board.append([])

            for c in line:
                if not c.isdigit():
                    raise SudokuError(
                        "Valid characters for a sudoku puzzle must be in 0-9"
                    )
                board[-1].append(int(c))

        if len(board) != 9:
            raise SudokuError("Each sudoku puzzle must be 9 lines long")
        return board


class SudokuGame(object):
    """
    A Sudoku game, in charge of storing the state of the board and checking
    whether the puzzle is completed.
    """
    def __init__(self, board_file):
        self.board_file = board_file
        self.start_puzzle = SudokuBoard(board_file).board

    def start(self):
        self.game_over = False
        self.puzzle = []
        for i in range(9):
            self.puzzle.append([])
            for j in range(9):
                self.puzzle[i].append(self.start_puzzle[i][j])

    def check_win(self):
        for row in range(9):
            if not self.__check_row(row):
                return False
        for column in range(9):
            if not self.__check_column(column):
                return False
        for row in range(3):
            for column in range(3):
                if not self.__check_square(row, column):
                    return False
        self.game_over = True
        return True

    def __check_block(self, block):
        return set(block) == set(range(1, 10))

    def __check_row(self, row):
        return self.__check_block(self.puzzle[row])

    def __check_column(self, column):
        return self.__check_block(
            [self.puzzle[row][column] for row in range(9)]
        )

    def __check_square(self, row, column):
        return self.__check_block(
            [
                self.puzzle[r][c]
                for r in range(row * 3, (row + 1) * 3)
                for c in range(column * 3, (column + 1) * 3)
            ]
        )

    def run_ai(self):
        ai = SudokuCSP(self.puzzle)
        print(ai.generate_all_binary_constraints())


if __name__ == '__main__':
    args = parse_arguments()

    # open using 'with' to safely exit out of file when program ends
    with open('%s.sudoku' % args['board'], 'r') as boards_file:
        # initialize the game with the boards_file
        game = SudokuGame(boards_file)

        # start the game
        game.start()

        # start Tk the gui library
        root = Tk()

        # pass it into SudokuUI, that controls our GUI
        SudokuUI(root, game)

        # widthxheight string where width and height are measured in pixel
        # +40 for button
        root.geometry("%dx%d" % (WIDTH, HEIGHT + BUTTON_HEIGHT * 2))

        # start drawing the program
        root.mainloop()

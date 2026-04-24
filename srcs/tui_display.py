import time
from enum import Enum
from rich import print
from rich.text import Text
from rich.console import Console
from .zones import Zone
from .map_data import Map
from .drones import Drone


class SquareType(Enum):

    EMPTY = 0
    ZONE = 1
    CONNECTION = 2
    DRONE = 3
    TITLE = 4


class MapSquare:

    def __init__(
        self,
        square_type: SquareType,
        coor: tuple[int, int],
        char: Text
    ) -> None:

        self.type: SquareType = square_type
        self.row: int = coor[0]
        self.col: int = coor[1]
        self.char: Text = char


class MapZone:

    def __init__(
        self,
        zone: Zone,
        square_sz: int,
        characters: dict[str, str]
    ) -> None:

        self.zone: Zone = zone
        self.sz: int = TuiDisplay.get_zone_sz(self.zone)
        self.start_coor: tuple[int, int] = (
            (square_sz - self.sz) // 2,
            (square_sz * 2 - (self.sz * 2)) // 2
        )
        self.end_coor: tuple[int, int] = (
            self.start_coor[0] + self.sz,
            self.start_coor[1] + self.sz * 2
        )
        self.characters: dict[str, Text] = {
            char_type: Text(char, style=self.zone.color)
            for char_type, char in characters.items()
        }
        self.squares: list[list[MapSquare | None]] = [
            [None for _ in range(self.sz * 2)]
            for _ in range(self.sz)
        ]
        # print(f"created zone {self.zone.name} with size = {self.sz}\n")

    @property
    def start_row(self) -> int:

        return self.squares[0][0].row

    @property
    def end_row(self) -> int:

        return self.squares[-1][-1].row

    @property
    def start_col(self) -> int:

        return self.squares[0][0].col

    @property
    def end_col(self) -> int:

        return self.squares[-1][-1].col

    def is_in(self, row: int, col: int) -> bool:

        return (
            self.start_coor[0] <= row < self.end_coor[0]
            and self.start_coor[1] <= col < self.end_coor[1]
        )

    def get_zone_char(self, minirow: int, minicol: int) -> Text:

        if minirow != self.start_coor[0] and minirow != self.end_coor[0]:
            if minicol == self.start_coor[1] or minicol == self.end_coor[1]:
                return self.characters["vertical"]
            else:
                return self.characters["empty"]
        if minirow == self.start_coor[0]:
            corner: str = "up"
        else:
            corner = "down"
        if minicol != self.start_coor[1] and minicol != self.end_coor[1]:
            return self.characters["horizontal"]
        elif minicol == self.start_coor[1]:
            return self.characters[corner + "left_corner"]
        else:
            return self.characters[corner + "right_corner"]


class TuiDisplay:

    def __init__(self, drone_map: Map, drones: list[Drone]) -> None:

        self.map: Map = drone_map
        self.drones: list[Drone] = drones
        self.create_map()

    @staticmethod
    def get_zone_sz(zone: Zone) -> int:

        return 3 + (zone.max_drones - (
            1 if zone.max_drones > 2 else 0)
        ) // 2

    def calculate_map_size(self) -> None:

        min_x: int = min(self.map.hubs, key=lambda hub: hub.x).x
        max_x: int = max(self.map.hubs, key=lambda hub: hub.x).x
        min_y: int = min(self.map.hubs, key=lambda hub: hub.y).y
        max_y: int = max(self.map.hubs, key=lambda hub: hub.y).y

        self.width: int = abs(max_x - min_x) + 1
        self.height: int = abs(max_y - min_y) + 1
        self.bias_x: int = (- min_x if min_x < 0 else 0)
        self.bias_y: int = (- min_y if min_y < 0 else 0)

        self.square_sz: int = self.get_zone_sz(
            max(self.map.hubs, key=lambda hub: self.get_zone_sz(hub))
        )

        # print(f"map width: {self.width}, map height: {self.height}, square size: {self.square_sz}\n")

    def find_map_zone(self, seek_x: int, seek_y: int) -> MapZone | None:

        for hub in self.map.hubs:

            if hub.x + self.bias_x == seek_x and hub.y + self.bias_y == seek_y:
                return self.zones[hub.name]

        return None

    def create_map(self) -> None:

        self.calculate_map_size()

        self.board: list[list[MapSquare | None]] = []
        self.zones: dict[str, MapZone] = {}
        self.console: Console = Console(color_system="256")
        self.characters: dict[str, str] = {
            "horizontal": "═",
            "vertical": "║",
            "upleft_corner": "╔",
            "upright_corner": "╗",
            "downleft_corner": "╚",
            "downright_corner": "╝",
            "empty": " "
        }
        for hub in self.map.hubs:
            self.zones[hub.name] = MapZone(
                hub,
                self.square_sz,
                self.characters
            )

        for row_nb in range(self.height):

            for _ in range(self.square_sz):
                self.board.append([
                    None for _ in range(self.square_sz * 2 * self.width)
                ])

            for col_nb in range(self.width):

                self.create_line(row_nb, col_nb)

        for zone_name, zone in self.zones.items():
            self.add_title(zone, zone_name)

        # print(f"any None remaining:{any(square is None for row in self.board for square in row)}\n")

    def create_line(self, row_nb: int, col_nb: int) -> None:

        zone: MapZone | None = self.find_map_zone(col_nb, row_nb)

        for minirow in range(self.square_sz):

            for minicol in range(self.square_sz * 2):

                sq_row: int = row_nb * self.square_sz + minirow
                sq_col: int = col_nb * (self.square_sz * 2) + minicol
                if zone and zone.is_in(minirow, minicol):
                    # print(f"square row={minirow} col={minicol} is part of zone {zone.zone.name} with start coor = {zone.start_coor} and end coor = {zone.end_coor}\n")
                    cur_square: MapSquare = MapSquare(
                        SquareType.ZONE,
                        (sq_row, sq_col),
                        zone.get_zone_char(minirow, minicol)
                    )
                    zone.squares[
                        minirow - zone.start_coor[0]
                    ][
                        minicol - zone.start_coor[1]
                    ] = cur_square
#                elif self.is_connection(minirow, minicol):
#                    cur_square = MapSquare(
#                        SquareType.CONNECTION,
#                        (minirow, minicol),
#                        connection_char,
#                        self.console
#                    )
                else:
                    cur_square = MapSquare(
                        SquareType.EMPTY,
                        (sq_row, sq_col),
                        Text(self.characters["empty"])
                    )
                self.board[sq_row][sq_col] = cur_square

    def add_title(self, zone: MapZone, name: str) -> None:

        letters_to_fit: int = len(name) - zone.sz * 2

        self.add_row_after(zone, 1)

        if letters_to_fit <= 0:
            start_point: int = zone.start_col
        else:
            self.add_col_before(zone, letters_to_fit // 2)
            self.add_col_after(zone, letters_to_fit // 2 + letters_to_fit % 2)
            start_point = zone.start_col - letters_to_fit // 2

        for char_nb in range(len(name)):

            self.board[zone.end_row + 1][
                start_point + char_nb
            ].char = Text(name[char_nb], style=zone.zone.color)
            self.board[zone.end_row + 1][
                start_point + char_nb
            ].type = SquareType.TITLE

    def add_row_after(self, zone: MapZone, nb_rows: int) -> None:

        for _ in range(nb_rows):

            new_row: list[None | MapSquare] = [
                MapSquare(
                    SquareType.EMPTY,
                    (zone.end_row + 1, col),
                    Text(self.characters["empty"])
                )
                for col in range(self.square_sz * self.width * 2)
            ]
            if zone.end_row != len(self.board) - 1:
                self.board.insert(zone.end_row + 1, new_row)
            else:
                self.board.append(new_row)
            change_row: int = zone.end_row + 2
            while change_row < len(self.board):
                for square in self.board[change_row]:
                    square.row += 1
                change_row += 1

    def add_col_before(self, zone: MapZone, nb_cols: int) -> None:

        for _ in range(nb_cols):

            for row in range(len(self.board)):

                self.board[row].insert(zone.start_col, MapSquare(
                    SquareType.EMPTY,
                    (row, zone.start_col),
                    Text(self.characters["empty"])
                ))
                change_col: int = zone.start_col + 1
                while change_col < len(self.board[row]):
                    self.board[row][change_col].col = change_col
                    change_col += 1

    def add_col_after(self, zone: MapZone, nb_cols: int) -> None:

        for _ in range(nb_cols):

            for row in range(len(self.board)):

                new_col: MapSquare = MapSquare(
                    SquareType.EMPTY,
                    (row, zone.end_col + 1),
                    Text(self.characters["empty"])
                )
                if zone.end_col == len(self.board[row]) - 1:
                    self.board[row].append(new_col)
                else:
                    self.board[row].insert(zone.end_col + 1, new_col)
                change_col: int = zone.end_col + 1
                while change_col < len(self.board[row]):
                    self.board[row][change_col].col = change_col
                    change_col += 1

#    def create_connections(self) -> None:
#
#        self.zones: dict[Zone, tuple[tuple[int, int], tuple[int, int]]] = {}
#        self.total_height: int = 0
#        self.total_width: int = 0
#        for row in self.board:
#            width: int = 0
#            for square in row:
#                width += square.width
#                square.add_board_coordinates()
#                self.total_width += square.width
#            self.total_height += max(
#                row, key=lambda square: square.height
#            ).height
#
#        for row in range(len(self.board)):
#            for square_nb in range(len(self.board[row])):
#                if self.board[row][square_nb].zone:
#                    self.zones[self.board[row][square_nb].zone] = (
#                        (square_nb, row)
#                            )

    def display_map(self) -> None:

        for row in self.board:
            for square in row:
                self.console.print(square.char, end="")
            print()
        print()
        time.sleep(0.1)

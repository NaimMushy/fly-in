import random
import time
from rich import print
from rich.text import Text
from rich.console import Console
from .zones import Zone
from .map_data import Map
from .drones import Drone


class MapSquare:

    def __init__(
        self,
        zone: Zone | None,
        console: Console,
        borders: dict[str, str]
    ) -> None:

        self.sz: int = 3 + (
            0 if not zone
            else (zone.max_drones - 1) // 2
        ) + 1
        self.zone: Zone | None = zone
        self.cur_line_nb: int = 0
        self.display_over: bool = False
        self.drone_squares: dict[Drone, tuple[int, int]] = {}
        self.console: Console = console
        if zone:
            self.borders: dict[str, Text] = {
                char_type: Text(char, style=zone.color)
                for char_type, char in borders.items()
            }
        self.fill_square()

    def fill_square(self) -> None:

        self.blank_space: Text = Text(" ")
        self.px: list[list[Text]] = [
            [
                self.blank_space for _ in range(self.sz * 2)
            ] for _ in range(self.sz)
        ]

        if not self.zone:
            return

        # print(f"found zone : {self.zone.name}\n")
        for line_nb in range(self.sz):

            if line_nb != 0 and line_nb != self.sz - 1:
                self.px[line_nb][0] = self.borders["vertical"]
                self.px[line_nb][-1] = self.borders["vertical"]

            elif line_nb == 0:
                self.px[line_nb] = [
                     self.borders["horizontal"]
                     for _ in range(self.sz * 2)
                ]
                self.px[line_nb][0] = self.borders["upleft_corner"]
                self.px[line_nb][-1] = self.borders["upright_corner"]

            else:
                self.px[line_nb] = [
                     self.borders["horizontal"]
                     for _ in range(self.sz * 2)
                ]
                self.px[line_nb][0] = self.borders["downleft_corner"]
                self.px[line_nb][-1] = self.borders["downright_corner"]

    def fill_drones(self) -> None:

        if not self.zone:
            return

        drone_text: Text
        if self.drone_squares:

            drones_to_discard: dict[Drone, tuple[int, int]] = {
                drone: drone_coor
                for drone, drone_coor in self.drone_squares.items()
                if drone not in self.zone.occupied
            }

            for drone, drone_coor in drones_to_discard.items():

                self.px[drone_coor[1]][drone_coor[0]] = self.blank_space
                self.drone_squares.pop(drone)

        for drone in self.zone.occupied:

            if drone in self.drone_squares:
                continue

            drone_x: int = random.randint(1, self.sz - 2)
            drone_y: int = random.randint(1, self.sz - 2)

            while (drone_x, drone_y) in self.drone_squares.values():

                drone_x = random.randint(1, self.sz - 2)
                drone_y = random.randint(1, self.sz - 2)

            self.drone_squares[drone] = (drone_x, drone_y)
            # print(f"drone x chosen: {drone_x}, drone y chosen : {drone_y}")
            drone_text = Text(f"{drone.id}", style="white blink")
            self.px[drone_y][drone_x] = drone_text

    def display_square_line(self) -> None:

        self.fill_drones()
        for char in self.px[self.cur_line_nb]:
            self.console.print(char, end="")
        self.cur_line_nb += 1
        if self.cur_line_nb >= self.sz:
            self.display_over = True


class TuiDisplay:

    def __init__(self, drone_map: Map, drones: list[Drone]) -> None:

        self.map: Map = drone_map
        self.hubs: list[Zone] = drone_map.hubs
        self.drones: list[Drone] = drones
        self.create_map()

    def calculate_map_size(self) -> None:

        min_x: int = min(self.hubs, key=lambda hub: hub.x).x
        max_x: int = max(self.hubs, key=lambda hub: hub.x).x
        min_y: int = min(self.hubs, key=lambda hub: hub.y).y
        max_y: int = max(self.hubs, key=lambda hub: hub.y).y

        self.width: int = abs(max_x - min_x) + 1
        self.height: int = abs(max_y - min_y) + 1
        self.bias_x: int = (- min_x if min_x < 0 else 0)
        self.bias_y: int = (- min_y if min_y < 0 else 0)

    def find_zone(self, seek_x: int, seek_y: int) -> Zone | None:

        for hub in self.hubs:

            if hub.x + self.bias_x == seek_x and hub.y + self.bias_y == seek_y:
                return hub

        return None

    def create_map(self) -> None:

        self.calculate_map_size()
        self.board: list[list[MapSquare]] = [
            [] for _ in range(self.height)
        ]
        console: Console = Console(color_system="256")
        self.borders: dict[str, str] = {
            "horizontal": "═",
            "vertical": "║",
            "upleft_corner": "╔",
            "upright_corner": "╗",
            "downleft_corner": "╚",
            "downright_corner": "╝"
        }

        for board_y in range(self.height):

            for board_x in range(self.width):

                zone: Zone | None = self.find_zone(board_x, board_y)
                if zone:
                    self.board[zone.y + self.bias_y].append(MapSquare(
                        zone,
                        console,
                        self.borders
                    ))
                else:
                    self.board[board_y].append(MapSquare(
                        None,
                        console,
                        self.borders
                    ))

    def reset_squares(self) -> None:

        for row in self.board:
            for square in row:
                square.display_over = False
                square.cur_line_nb = 0

    def display_map(self) -> None:

        for row in self.board:
            while not all([
                square.display_over
                for square in row
            ]):
                for square in row:
                    if not square.display_over:
                        square.display_square_line()
                    else:
                        print(f"{' ' * (square.sz * 2)}", end="")
                print()
        print()
        self.reset_squares()
        time.sleep(0.1)

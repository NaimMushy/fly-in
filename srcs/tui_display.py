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
        height: int,
        width: int,
        zone: Zone | None,
        console: Console,
        borders: dict[str, str],
        zone_text: str,
        text_pos: str
    ) -> None:

        self.height: int = height
        self.width: int = width
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
        self.zone_title: list[Text] = []
        if zone_text:
            self.zone_title = [
                Text(char, style="white")
                for char in zone_text
            ]
        self.text_pos: str = text_pos
        self.fill_square()

    def fill_square(self) -> None:

        self.blank_space: Text = Text(" ")
        self.px: list[list[Text]] = [
            [
                self.blank_space for _ in range(self.width)
            ] for _ in range(
                self.height if not self.zone_title else self.height + 1
            )
        ]

        if self.zone_title:
            if self.text_pos == "first":
                start_index: int = self.width - len(self.zone_title)
            elif self.text_pos == "second":
                start_index = 0
            else:
                start_index = (self.width - len(self.zone_title)) // 2
            i = 0
            while i < len(self.zone_title):
                self.px[-1][start_index + i] = self.zone_title[i]
                i += 1

        if not self.zone:
            return

        for line_nb in range(self.height):

            if line_nb != 0 and line_nb != self.height - 1:
                self.px[line_nb][0] = self.borders["vertical"]
                self.px[line_nb][-1] = self.borders["vertical"]

            elif line_nb == 0:
                self.px[line_nb] = [
                     self.borders["horizontal"]
                     for _ in range(self.width)
                ]
                self.px[line_nb][0] = self.borders["upleft_corner"]
                self.px[line_nb][-1] = self.borders["upright_corner"]

            else:
                self.px[line_nb] = [
                     self.borders["horizontal"]
                     for _ in range(self.width)
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

            drone_x: int = random.randint(1, self.width - 2)
            drone_y = random.randint(1, self.height - 1 - (
                1 if self.zone_title else 0
            ))

            while (drone_x, drone_y) in self.drone_squares.values():

                drone_x = random.randint(1, self.width - 2)
                drone_y = random.randint(1, self.height - 1 - (
                    1 if self.zone_title else 0
                ))

            self.drone_squares[drone] = (drone_x, drone_y)
            drone_text = Text(f"{drone.id}", style="white blink")
            self.px[drone_y][drone_x] = drone_text

    def display_square_line(self) -> None:

        self.fill_drones()
        for char in self.px[self.cur_line_nb]:
            self.console.print(char, end="")
        self.cur_line_nb += 1
        if self.cur_line_nb >= len(self.px):
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
        self.console: Console = Console(color_system="256")
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
                    if board_x != 0 and self.board[board_y][-1].zone:
                        self.board[board_y].append(MapSquare(
                            3,
                            3,
                            None,
                            self.console,
                            self.borders,
                            "",
                            ""
                        ))
                    self.create_zone_square(zone, board_x, board_y)
                else:
                    self.board[board_y].append(MapSquare(
                        3,
                        3,
                        None,
                        self.console,
                        self.borders,
                        "",
                        ""
                    ))

    def create_zone_square(self, zone: Zone, x: int, y: int) -> None:

        zone_sz: int = 3 + (zone.max_drones - (
            1 if zone.max_drones > 2 else 0)
        ) // 2
        letters_to_fit: int = len(zone.name) - zone_sz * 2
#        print(
#            f"zone {zone.name}, zone size: {zone_sz}, "
#            f"max drones: {zone.max_drones}, letters to fit: {letters_to_fit}"
#        )

        if letters_to_fit <= 0:
            self.board[zone.y + self.bias_y].append(MapSquare(
                zone_sz,
                zone_sz * 2,
                zone,
                self.console,
                self.borders,
                zone.name,
                ""
            ))
            return

        if x == 0:
            self.board[zone.y + self.bias_y].append(MapSquare(
                zone_sz,
                zone_sz * 2,
                zone,
                self.console,
                self.borders,
                zone.name[:zone_sz * 2 + 1],
                ""
            ))
            self.board[zone.y + self.bias_y].append(MapSquare(
                zone_sz,
                letters_to_fit,
                None,
                self.console,
                self.borders,
                zone.name[zone_sz * 2:],
                "second"
            ))
            return

        if x == self.width - 1:
            self.board[zone.y + self.bias_y].append(MapSquare(
                zone_sz,
                letters_to_fit,
                None,
                self.console,
                self.borders,
                zone.name[:letters_to_fit],
                "first"
            ))
            self.board[zone.y + self.bias_y].append(MapSquare(
                zone_sz,
                zone_sz * 2,
                zone,
                self.console,
                self.borders,
                zone.name[letters_to_fit:],
                ""
            ))
            return

        self.board[zone.y + self.bias_y].append(MapSquare(
            zone_sz,
            (letters_to_fit // 2 if letters_to_fit > 1 else 1) + 1,
            None,
            self.console,
            self.borders,
            zone.name[:letters_to_fit // 2],
            "first"
        ))
        self.board[zone.y + self.bias_y].append(MapSquare(
            zone_sz,
            zone_sz * 2,
            zone,
            self.console,
            self.borders,
            zone.name[letters_to_fit // 2:zone_sz * 2 + (
                1 if letters_to_fit > 1 else 0
            )],
            ""
        ))
        self.board[zone.y + self.bias_y].append(MapSquare(
            zone_sz,
            letters_to_fit // 2 + (letters_to_fit % 2),
            None,
            self.console,
            self.borders,
            zone.name[zone_sz * 2 + (1 if letters_to_fit > 1 else 0):],
            "second"
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
                        print(f"{' ' * (square.width)}", end="")
                print()
        print()
        self.reset_squares()
        time.sleep(0.1)

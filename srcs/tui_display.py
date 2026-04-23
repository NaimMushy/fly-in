import random
import time
from .zones import Zone
from .map_data import Map
from .drones import Drone


class MapSquare:

    def __init__(self, size: int, zone: Zone | None) -> None:

        self.sz: int = 3 * size
        self.zone: Zone | None = zone
        self.cur_line_nb: int = 0
        self.display_over: bool = False

    def fill_square(self) -> None:

        self.px: list[list[str]] = [
            [
                " " for _ in range(self.sz)
            ] for _ in range(self.sz)
        ]

        if self.zone:
            drone_squares: list[tuple[int, int]] = []
            for _ in range(len(self.zone.occupied)):
                drone_x: int = 1
                drone_y: int = 1
                while (drone_x, drone_y) in drone_squares:
                    drone_x = random.randint(1, self.sz - 1)
                    drone_y = random.randint(1, self.sz - 1)
                drone_squares.append((drone_x, drone_y))
                self.px[drone_y][drone_x] = "\x1B[37m \x1B[0m"
            hor_line: list[str] = [
                (f"{self.zone.color}-\x1B[0m") for _ in range(self.sz)
            ]
            for line in self.px:
                if line != self.px[0] and line != self.px[-1]:
                    line[0] = f"{self.zone.color}|\x1B[0m"
                    line[-1] = f"{self.zone.color}|\x1B[0m"
                else:
                    line = hor_line

    def display_square_line(self) -> None:

        print(self.px[self.cur_line_nb], end="")
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

    def find_zone(self, seek_x: int, seek_y: int) -> Zone | None:

        for hub in self.hubs:

            if hub.x == seek_x and hub.y == seek_y:
                return hub

        return None

    def create_map(self) -> None:

        self.calculate_map_size()
        self.board: list[list[MapSquare]] = [
            [] for _ in range(self.height)
        ]

        for board_y in range(self.height):

            for board_x in range(self.width):

                zone: Zone | None = self.find_zone(board_x, board_y)
                if zone:
                    self.board[zone.y][zone.x] = MapSquare(
                        zone.max_drones,
                        zone
                    )
                else:
                    self.board[board_y][board_x] = MapSquare(
                        1,
                        None
                    )

    def reset_squares(self) -> None:

        for row in self.board:
            for square in row:
                square.display_over = False
                square.cur_line_nb = 0

    def display_map(self) -> None:

        for row in self.board:
            for square in row:
                if not square.display_over:
                    square.display_square_line()
                else:
                    print(" " * square.sz, end="")
            print()
        self.reset_squares()
        time.sleep(0.1)

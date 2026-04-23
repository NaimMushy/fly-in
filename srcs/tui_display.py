import random
import time
from .zones import Zone
from .map_data import Map
from .drones import Drone


class MapSquare:

    def __init__(self, size: int, zone: Zone | None) -> None:

        self.height: int = 3 + 1 * (
            0 if not zone
            else (zone.max_drones - 1) // 2
        )
        self.width: int = self.height * 2
#        if zone:
#            print(f"x for square zone {zone.name} = {self.width}")
#            print(f"y for square zone {zone.name} = {self.height}")
        self.zone: Zone | None = zone
        self.cur_line_nb: int = 0
        self.display_over: bool = False
        self.drone_squares: dict[Drone, tuple[int, int]] = {}
        self.fill_square()

    def fill_square(self) -> None:

        self.px: list[list[str]] = [
            [
                " " for _ in range(self.width)
            ] for _ in range(self.height)
        ]

        if self.zone:
            # print(f"found zone : {self.zone.name}\n")
            hor_line: list[str] = [
                f"{self.zone.color}--\x1B[0m" for _ in range(self.height)
            ]
            for line_nb in range(len(self.px)):
                if line_nb != 0 and line_nb != len(self.px) - 1:
                    self.px[line_nb][0] = f"{self.zone.color}|\x1B[0m"
                    self.px[line_nb][-1] = f"{self.zone.color}|\x1B[0m"
                    # print(f"changing vertical line: {line}\n")
                else:
                    self.px[line_nb] = hor_line
                    # print(f"changing horizontal line: {line}\n")

    def fill_drones(self) -> None:

        if not self.zone:
            return

        if self.drone_squares:

            drones_to_discard: dict[Drone, tuple[int, int]] = {
                drone: drone_coor
                for drone, drone_coor in self.drone_squares.items()
                if drone not in self.zone.occupied
            }

            for drone, drone_coor in drones_to_discard.items():

                self.px[drone_coor[1]][drone_coor[0]] = " "
                self.drone_squares.pop(drone)

        for drone in self.zone.occupied:

            if drone in self.drone_squares:
                continue

            drone_x: int = random.randint(1, self.width - 2)
            drone_y: int = random.randint(1, self.height - 2)

            while (drone_x, drone_y) in self.drone_squares.values():

                drone_x = random.randint(1, self.width - 2)
                drone_y = random.randint(1, self.height - 2)

            self.drone_squares[drone] = (drone_x, drone_y)
            # print(f"drone x chosen: {drone_x}, drone y chosen : {drone_y}")
            self.px[drone_y][drone_x] = f"\x1B[37m{drone.id}\x1B[0m"

    def display_square_line(self) -> None:

        self.fill_drones()
        for char in self.px[self.cur_line_nb]:
            print(char, end="")
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
                    self.board[zone.y].append(MapSquare(
                        zone.max_drones,
                        zone
                    ))
                else:
                    self.board[board_y].append(MapSquare(
                        1,
                        None
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

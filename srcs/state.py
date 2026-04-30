import time
from rich import print
from rich.text import Text
from rich.console import Console


class Char:

    def __init__(self, char: str, style: str, zone_name: str, is_border: bool) -> None:

        self.char: str = char
        self.style: str = style
        self.relation: str = zone_name
        self.is_zone: bool = False
        if self.relation:
            self.is_zone = True
        self.is_border: bool = is_border
        self.connection_char: str = ""
        self.connection_relation: str = ""
        self.parent: "Char"
        self.dist_from_start: int = 0
        self.dist_from_arrival: int = 0
        self.dir_from_parent: tuple[int, int] | None = None
        self.row: int = 0
        self.col: int = 0

    @property
    def total_dist(self) -> int:

        return self.dist_from_start + self.dist_from_arrival

    def update_dist(self, parent: "Char", in_to_explore: bool, goal: "Char") -> None:

        new_dir: tuple[int, int] = (self.row - parent.row, self.col - parent.col)
        goal_dir: tuple[int, int] = (
            0 if self.row == goal.row else (1 if goal.row > self.row else -1),
            0 if self.col == goal.col else (1 if goal.col > self.col else -1)
        )

        turn_penalty: int = 0
        if parent.dir_from_parent and parent.dir_from_parent != new_dir:
            turn_penalty = 5

        alignment_penalty: int = 0
        if new_dir != goal_dir:
            alignment_penalty = 1

        new_dist: int = parent.dist_from_start + 1 + turn_penalty + alignment_penalty

        if not in_to_explore or new_dist < self.dist_from_start:
            self.dist_from_start = new_dist
            self.parent = parent
            self.dir_from_parent = new_dir


class State:

    def __init__(self, info_mode: int, console: Console) -> None:

        self.dis: list[str | Text] = []
        self.drone_moves: str = ""
        self.nb_drone_moved: int = 0
        self.zones_occupied: dict[str, list[int]] = {}
        self.drones_delivered: list[int] = []
        self.info_mode: int = info_mode
        self.console: Console = console
        self.display_map: list[list[Char]] = []

    def display_info(self) -> None:

        print("\n\n")
        for line in self.display_map:
            for char in line:
                char_to_print: str = char.char
                if char.connection_char:
                    char_to_print = char.connection_char
                if char.style:
                    self.console.print(Text(char_to_print, style=char.style), end="")
                else:
                    print(char_to_print, end="")
        time.sleep(0.1)
        if not self.drone_moves:
            return
        print("\n==== DRONE MOVEMENTS ====\n")
        print(f" ➤ {self.drone_moves}")
        if self.info_mode != 0:
            print("\n==== ADDITIONAL INFORMATION ====\n")
            print(f" ➤ number of drones that moved: {self.nb_drone_moved}\n")
            print(" ➤ zones currently occupied:\n")
            if len(self.zones_occupied) == 0:
                print(" 0")
            for zone, occupying in self.zones_occupied.items():
                print(f" {zone}:", end="")
                for drone_id in occupying:
                    print(f" D{drone_id}", end="")
                print("\n")
            print(" ➤ drones already delivered:", end="")
            if len(self.drones_delivered) == 0:
                print(" 0", end="")
            for drone_id in self.drones_delivered:
                print(f" D{drone_id}", end="")
            print("\n")
        time.sleep(0.1)

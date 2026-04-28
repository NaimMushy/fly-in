import time
from rich import print
from rich.text import Text
from rich.console import Console


class State:

    def __init__(self, info_mode: int, console: Console) -> None:

        self.dis: list[str | Text] = []
        self.drone_moves: str = ""
        self.nb_drone_moved: int = 0
        self.zones_occupied: dict[str, list[int]] = {}
        self.drones_delivered: list[int] = []
        self.info_mode: int = info_mode
        self.console: Console = console

    def display_info(self) -> None:

        print("\n\n")
        for line_piece in self.dis:
            self.console.print(line_piece, end="")
        time.sleep(0.1)
        if not self.drone_moves:
            return
        print("\n==== DRONE MOVEMENTS ====\n")
        print(self.drone_moves)
        if self.info_mode != 0:
            print("\n==== ADDITIONAL INFORMATION ====\n")
            print(f"number of drones that moved: {self.nb_drone_moved}\n")
            print("zones currently occupied:\n")
            if len(self.zones_occupied) == 0:
                print(" 0")
            for zone, occupying in self.zones_occupied.items():
                print(f" -> {zone}:", end="")
                for drone_id in occupying:
                    print(f" D{drone_id}", end="")
                print("\n")
            print("drones already delivered:", end="")
            if len(self.drones_delivered) == 0:
                print(" 0", end="")
            for drone_id in self.drones_delivered:
                print(f" D{drone_id}", end="")
            print("\n")
        time.sleep(0.1)

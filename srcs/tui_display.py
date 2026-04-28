import time
import pyfiglet
from rich import print
from rich.text import Text
from rich.console import Console
from .zones import Zone  # Connection
from .map_data import Map
from .drones import DroneMonitor, Drone
from .state import State


class DisplayZone:

    def __init__(
        self, z: Zone,
        characters: dict[str, str],
        console: Console,
        info_mode: int = 0
    ) -> None:

        self.zone: Zone = z
        self.name: str = z.name
        self.size: int = 3 + ((self.zone.max_drones - 1) // 2)
        self.width: int = self.size * 2
        self.height: int = self.size
        self.info_mode: int = info_mode
        self.nltf: int = self.width - len(self.name)
        if self.nltf < 0:
            self.width = len(self.name)
        if info_mode:
            self.tltf: int = self.width - len(self.zone.zone_type)
            if self.tltf < 0:
                self.width = len(self.zone.zone_type)
                self.nltf = self.width - len(self.name)
        self.row_id: int = 0
        self.characters: dict[str, str] = characters
        self.console: Console = console
        self.parents: list["DisplayZone"] = []

    def update_drones(self) -> None:

        self.drones: dict[int, list[Drone]] = {
            line_nb: [] for line_nb in range(1 + self.info_mode, self.size + self.info_mode)
        }
        space_left: int = self.size * 2 - 2
        line: int = 1 + self.info_mode
        for drone in self.zone.occupied:
            if space_left >= 1 + len(str(drone.id)):
                self.drones[line].append(drone)
                space_left -= 1 + len(str(drone.id))
            else:
                if line + self.info_mode == self.size - 1 + self.info_mode:
                    break
                line += 1
                space_left = self.size * 2 - 2

    def print_space(self, length: int) -> str:

        return f"{self.characters['space'] * length}"

    def print_style(self, char: str, length: int) -> Text:

        return Text(
            f"{self.characters[char] * length}",
            style=self.zone.color
        )

    def print_line(self, line: int, state: State) -> None:

        if line > self.height + self.info_mode:
            state.dis.append(self.print_space(self.width))
            return
        if line == self.height + self.info_mode:
            if self.nltf > 0:
                state.dis.append(self.print_space(self.nltf // 2))
            state.dis.append(Text(self.name, style=self.zone.color))
            if self.nltf > 0:
                state.dis.append(self.print_space(self.nltf // 2 + self.nltf % 2))
            return
        if self.info_mode and line == 0:
            if self.tltf > 0:
                state.dis.append(self.print_space(self.tltf // 2))
            state.dis.append(Text(self.zone.zone_type.upper(), style=self.zone.color))
            if self.tltf > 0:
                state.dis.append(self.print_space(self.tltf // 2 + self.tltf % 2))
            return
        self.update_drones()
        if self.info_mode and self.tltf < 0:
            state.dis.append(self.print_space((-self.tltf) // 2))
        elif self.nltf < 0:
            state.dis.append(self.print_space((-self.nltf) // 2))
        if line == self.info_mode or line == self.height - 1 + self.info_mode:
            if line == self.info_mode:
                cor: str = "u"
            else:
                cor = "l"
            state.dis.append(self.print_style((cor + "lcor"), 1))
            state.dis.append(self.print_style("hor", self.size * 2 - 2))
            state.dis.append(self.print_style((cor + "rcor"), 1))
        else:
            state.dis.append(self.print_style("ver", 1))
            space_left = self.size * 2 - 2
            for drone in self.drones[line]:
                state.dis.append(Text(
                    f"{self.characters['drone']}{drone.id}",
                    style=self.zone.color
                ))
                space_left -= 1 + len(str(drone.id))
            state.dis.append(self.print_space(space_left))
            state.dis.append(self.print_style("ver", 1))
        if self.info_mode and self.tltf < 0:
            state.dis.append(self.print_space((-self.tltf) // 2 + (-self.tltf) % 2))
        elif self.nltf < 0:
            state.dis.append(self.print_space((-self.nltf) // 2 + (-self.nltf) % 2))


class Row:

    def __init__(self, row_id: int, pad: int) -> None:

        self.id: int = row_id
        self.zones: list[DisplayZone] = []
        self.height: int = 0
        self.width: int = -pad
        self.padding: int = pad

    def add_new_zone(self, z: DisplayZone) -> None:

        self.zones.append(z)
        self.width += z.width + self.padding
        if z.height > self.height:
            self.height = z.height
        z.row_id = self.id


class TuiDisplay:

    def __init__(self, drone_map: Map, info_mode: int) -> None:

        self.map: Map = drone_map
        self.console: Console = Console()
        self.characters: dict[str, str] = {
            "hor": "═",
            "ver": "║",
            "ulcor": "╔",
            "urcor": "╗",
            "llcor": "╚",
            "lrcor": "╝",
            "space": " ",
            "drone": "■",
            "empty": ""
        }
        self.zones: dict[str, DisplayZone] = {
            zone.name: DisplayZone(zone, self.characters, self.console, info_mode)
            for zone in self.map.hubs
        }
        self.padding: int = 10
        self.info_mode: int = info_mode
        self.create_rows()

    def display_map(self, state: State) -> None:

        for row in self.rows:
            self.print_row(row, state)

    @staticmethod
    def display_menu() -> None:

        print(pyfiglet.figlet_format("Welcome to Fly-In !", font="bigchief"), end="")
        print(r"""
                              *     .--.
                                   / /  `
                  +               | |
                         '         \ \__,
                     *          +   '--'  *
                         +   /\
            +              .'  '.   *
                   *      /======\      +
                         ;:.  _   ;
                         |:. (_)  |
                         |:.  _   |
               +         |:. (_)  |          *
                         ;:.      ;
                       .' \:.    / `.
                      / .-'':._.'`-. \
                      |/    /||\    \|
                    _..--'""````""'--.._
              _.-'``                    ``'-._
            -'                                '-
        """)

    @staticmethod
    def display_options(info_mode: int, map_file: str) -> None:
        print("\n✦ MENU OPTIONS ✦\n")
        print(f"     ➤ s: SELECT NEW MAP (current map: {map_file})")
        print("     ➤ l: LAUNCH THE DRONES")
        print(f"     ➤ i: TOGGLE INFO MODE ({'off' if info_mode == 0 else 'on'})")
        print("     ➤ q: QUIT PROGRAM")
        time.sleep(0.1)

    @staticmethod
    def display_state(state: State) -> None:

        state.display_info()
        print("\n✦ SIMULATION OPTIONS ✦\n")
        print("     ➤ n: NEXT STEP")
        print("     ➤ p: PREVIOUS STEP")
        print("     ➤ m: RETURN TO MENU")
        time.sleep(0.1)

    @staticmethod
    def display_end(drone_monitor: DroneMonitor, info_mode: int) -> None:

        print("\n✦ ✦ ✦ ✦ END OF THE SIMULATION ✦ ✦ ✦ ✦\n")
        print(f"     ➤ number of turns: {drone_monitor.turns}")
        if info_mode != 0:
            print(f"     ➤ average number of turns per drone: {drone_monitor.avg}")
        time.sleep(0.1)

    def print_row(self, row: Row, state: State) -> None:

        row_pad: int = self.max_row_len - row.width
        for line in range(row.height + 5 + self.info_mode):
            state.dis.append(f"{' ' * (row_pad // 2)}")
            for zone in row.zones:
                zone.print_line(line, state)
                if zone != row.zones[-1]:
                    state.dis.append(f"{' ' * 10}")
            state.dis.append(f"{' ' * (row_pad // 2 + row_pad % 2)}")
            state.dis.append("\n")

    def in_a_row(self, z: DisplayZone) -> bool:

        for row in self.rows:

            if z in row.zones:
                return True

        return False

    def create_rows(self) -> None:

        self.rows: list[Row] = [Row(0, self.padding)]
        cur_row: int = 0
        new_zone: DisplayZone = self.zones[self.map.start_hub.name]
        self.rows[cur_row].add_new_zone(new_zone)
        goal: DisplayZone = self.zones[self.map.end_hub.name]
        while goal not in self.rows[cur_row].zones:
            self.rows.append(Row(cur_row + 1, self.padding))
            for z in self.rows[cur_row].zones:
                for connection in z.zone.connections.values():
                    new_zone = self.zones[connection.zone2.name]
                    if z == new_zone:
                        continue
                    if self.in_a_row(new_zone):
                        continue
                    self.rows[cur_row + 1].add_new_zone(new_zone)
                    new_zone.parents.append(z)
            cur_row += 1
        for zone_id in range(len(self.map.hubs)):
            if not self.in_a_row(self.zones[self.map.hubs[zone_id].name]):
                row_id: int = 0
                if zone_id > 0:
                    row_id = self.zones[self.map.hubs[zone_id - 1].name].row_id
                self.rows[row_id].add_new_zone(
                    self.zones[self.map.hubs[zone_id].name]
                )
        self.max_row_len = max(self.rows, key=lambda row: row.width).width

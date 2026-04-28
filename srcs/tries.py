import time
import pyfiglet
from rich import print
from rich.text import Text
from rich.console import Console
from .zones import Zone  # Connection
from .map_data import Map
from .drones import DroneMonitor, Drone
from .state import State


class DisplayCon:

    def __init__(self, length: int = 1) -> None:

        self.length: int = length
        self.line: int = 0


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
        self.parents: list[DisplayZone] = []
        self.children: list["DisplayZone"] = []
        self.space_after: int = 0
        self.space_before: int = 0

    def add_receiving(self) -> None:

        self.receiving: dict[str, list[DisplayCon]] = {
            "left": [],
            "right": [],
            "ver": []
        }

        if len(self.parents) == 1:
            self.receiving["ver"].append(DisplayCon())
            return

        direction: str = "left"
        ver: bool = True
        if len(self.parents) > 2:
            ver = False
        for parent in self.parents:
            new_con: DisplayCon = DisplayCon()
            if direction == "left":
                new_con.length = parent.con_width // 2
            elif direction == "right":
                new_con.length = parent.con_width // 2
            if direction in ["left", "right"]:
                if len(self.receiving[direction]) == 0:
                    new_con.line = (self.height) // 2
                else:
                    new_con.line = self.receiving[direction][-1].line - 1
                    for con in self.receiving[direction]:
                        con.length += parent.con_width
            self.receiving[direction].append(new_con)
            if direction == "left":
                if ver:
                    direction = "right"
                else:
                    direction = "ver"
                    ver = True
            elif direction == "ver":
                direction = "right"
            elif direction == "right":
                direction = "left"

    def add_giving(self) -> None:

        self.giving: dict[str, list[DisplayCon]] = {
            "left": [],
            "right": [],
            "ver": []
        }

        if len(self.children) == 1:
            self.giving["ver"].append(DisplayCon())
            self.children[0].space_after = self.space_after
            return

        direction: str = "left"
        ver: bool = True
        if len(self.children) > 2:
            ver = False
        for child in self.children:
            new_con: DisplayCon = DisplayCon()
            if direction == "left":
                new_con.length = child.con_width // 2
                child.space_after = self.con_width - child.width - (child.width // 2)
            elif direction == "right":
                new_con.length = child.con_width // 2
            if direction in ["left", "right"]:
                if len(self.giving[direction]) == 0:
                    new_con.line = (self.height) // 2 + 1
                else:
                    new_con.line = self.receiving[direction][-1].line + 1
                    for con in self.receiving[direction]:
                        con.length += child.con_width
            self.giving[direction].append(new_con)
            if direction == "left":
                if ver:
                    direction = "right"
                else:
                    direction = "ver"
                    ver = True
            elif direction == "ver":
                direction = "right"
            elif direction == "right":
                direction = "left"

    def print_left_cons(self, state: State, line: int) -> None:

        if len(self.receiving["left"]) == 0 and len(self.giving["left"]) == 0:
            state.dis.append(" ")
            return

        space: int = 0
        if len(self.receiving["left"]) > 0:
            space = self.receiving["left"][0].length
        if len(self.giving["left"]) > 0 and self.giving["left"][0].length > space:
            space = self.giving["left"][0].length
        space_left: int = space
        for con in self.receiving["left"]:

            if line < con.line:
                state.dis.append(f"{self.characters['ver']}")
                space_left -= 1

            elif line == con.line:
                state.dis.append(f"{self.characters['llcor']}{self.characters['hor'] * (con.length - 1)}")
                space_left = 0
                break

        state.dis.append(f"{' ' * space_left}")
        space_left = space
        for con in self.giving["left"]:

            if line > con.line:
                state.dis.append(f"{self.characters['ver']}")
                space_left -= 1

            elif line == con.line:
                state.dis.append(f"{self.characters['ulcor']}{self.characters['hor'] * (con.length - 1)}")
                space_left = 0
                break

        state.dis.append(f"{' ' * space_left}")

    def print_right_cons(self, state: State, line: int) -> None:

        if len(self.receiving["right"]) == 0 and len(self.giving["right"]) == 0:
            state.dis.append(f"{' ' * self.space_after}")
            return

        space: int = max(self.receiving["right"] + self.giving["right"], key=lambda con: con.length).length

        for con in self.receiving["right"]:

            if line == con.line:
                state.dis.append(f"{self.characters['hor'] * (con.length - 1)}{self.characters['lrcor']}")

            elif line < con.line:
                state.dis.append(f"{' ' * (con.length - 2)}{self.characters['ver']}")

        if self.space_after - space > 0:
            state.dis.append(f"{' ' * (self.space_after - space)}")

        for con in self.giving["right"]:

            if line == con.line:
                state.dis.append(f"{self.characters['hor'] * (con.length - 1)}{self.characters['urcor']}")

            elif con.line < line:
                state.dis.append(f"{' ' * (con.length - 1)}{self.characters['ver']}")

        if self.space_after - space > 0:
            state.dis.append(f"{' ' * (self.space_after - space)}")

    @property
    def con_width(self) -> int:

        if len(self.children) <= 1:
            return self.width

        con_width: int = self.width
        for child in self.children:

            if child.name == self.name:
                continue

            if child.row_id < self.row_id:
                continue

            con_width += child.con_width // 2

        return con_width

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

    def print_vertical(self, line: int, state: State, cons: dict[str, list[DisplayCon]]) -> None:

        self.print_left_cons(state, line)
        padding: int = (self.size * 2) - len(cons["ver"])
        state.dis.append(f"{' ' * (padding // 2)}")
        for con in cons["ver"]:
            state.dis.append(self.characters["ver"])
        state.dis.append(f"{' ' * (padding // 2 + padding % 2)}")
        self.print_right_cons(state, line)

    def print_line(self, line: int, state: State) -> None:

        if line > self.height + self.info_mode:
            self.print_vertical(line, state, self.giving)
            return
        if line < 0:
            self.print_vertical(line, state, self.receiving)
            return
        if line == self.height + self.info_mode:
            self.print_left_cons(state, line)
            if self.nltf > 0:
                state.dis.append(f"{' ' * (self.nltf // 2)}")
            state.dis.append(Text(self.name, style=self.zone.color))
            if self.nltf > 0:
                state.dis.append(f"{' ' * (self.nltf // 2 + self.nltf % 2)}")
            self.print_right_cons(state, line)
            return
        if self.info_mode and line == 0:
            self.print_left_cons(state, line)
            if self.tltf > 0:
                state.dis.append(f"{' ' * (self.tltf // 2)}")
            state.dis.append(Text(self.zone.zone_type.upper(), style=self.zone.color))
            if self.tltf > 0:
                state.dis.append(f"{' ' * (self.tltf // 2 + self.tltf % 2)}")
            self.print_right_cons(state, line)
            return
        self.print_left_cons(state, line)
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
        self.print_right_cons(state, line)


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
        time.sleep(0.2)

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
        time.sleep(0.3)

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

        # row_pad: int = self.max_row_len - row.width
        for line in range(-3, row.height + 5 + self.info_mode):
            # state.dis.append(f"{' ' * (row_pad // 2)}")
            for zone in row.zones:
                zone.print_line(line, state)
                # if zone != row.zones[-1]:
                    # state.dis.append(f"{' ' * 10}")
            # state.dis.append(f"{' ' * (row_pad // 2 + row_pad % 2)}")
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
                    if new_zone not in z.children:
                        z.children.append(new_zone)
                    if not self.in_a_row(new_zone):
                        self.rows[cur_row + 1].add_new_zone(new_zone)
                    if new_zone.row_id > z.row_id:
                        new_zone.parents.append(z)
            cur_row += 1
        self.max_row_len = max(self.rows, key=lambda row: row.width).width
        for zone_id in range(len(self.map.hubs)):
            if not self.in_a_row(self.zones[self.map.hubs[zone_id].name]):
                row_id: int = 0
                if zone_id > 0:
                    row_id = self.zones[self.map.hubs[zone_id - 1].name].row_id
                self.rows[row_id].add_new_zone(
                    self.zones[self.map.hubs[zone_id].name]
                )
        for zone_name, zone in self.zones.items():
            zone.add_receiving()
            zone.add_giving()

        for zone_name, zone in self.zones.items():
            print(f"zone {zone_name} has space after {zone.space_after}\n")

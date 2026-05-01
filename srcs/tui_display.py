import time
import pyfiglet
from rich import print
from rich.console import Console
from typing import Callable
from .zones import Zone  # Connection
from .map_data import Map
from .drones import DroneMonitor, Drone
from .path import PathFinder
from .state import State, Char


DIRECTIONS: dict[str, dict[str, Callable]] = {
    "up": {
        "preferred": lambda self: (
            self.bounds[0] - 1,
            (self.bounds[2] + self.bounds[3]) // 2
        ),
        "edge_iter": lambda self: (
            (self.bounds[0] - 1, c)
            for c in range(self.bounds[2], self.bounds[3] + 1)
        ),
        "valid": lambda self, lines: self.bounds[0] - 1 >= 0
    },
    "down": {
        "preferred": lambda self: (
            self.bounds[1] + 1, (self.bounds[2] + self.bounds[3]) // 2
        ),
        "edge_iter": lambda self: (
            (self.bounds[1] + 1, c)
            for c in range(self.bounds[2], self.bounds[3] + 1)
        ),
        "valid": lambda self, lines: self.bounds[1] + 1 < len(lines)
    },
    "left": {
        "preferred": lambda self: (
            (self.bounds[0] + self.bounds[1]) // 2,
            self.bounds[2] - 1
        ),
        "edge_iter": lambda self: (
            (r, self.bounds[2] - 1)
            for r in range(self.bounds[0], self.bounds[1] + 1)
        ),
        "valid": lambda self, lines: self.bounds[2] - 1 >= 0
    },
    "right": {
        "preferred": lambda self: (
            (self.bounds[0] + self.bounds[1]) // 2,
            self.bounds[3] + 1
        ),
        "edge_iter": lambda self: (
            (r, self.bounds[3] + 1)
            for r in range(self.bounds[0], self.bounds[1] + 1)
        ),
        "valid": lambda self, lines: self.bounds[3] + 1 < len(lines[0])
    }
}

CHARACTERS: dict[str, str] = {
    "hor": "═",
    "ver": "║",
    "ulcor": "╔",
    "urcor": "╗",
    "llcor": "╚",
    "lrcor": "╝",
    "space": " ",
    "drone": "■",
    "connection": "◇",
    "empty": "",
    "title": "Welcome to Fly-In !!"
}


class DisplayZone:

    def __init__(
        self,
        z: Zone,
        info_mode: int = 0
    ) -> None:

        self.zone: Zone = z
        self.row_id: int = 0
        self.size: int = 3 + ((self.zone.max_drones - 1) // 2)
        self.width: int = self.size * 2
        self.height: int = self.size
        self.info_mode: int = info_mode
        self.nltf: int = self.width - len(self.zone.name)
        if self.nltf < 0:
            self.width = len(self.zone.name)
        if info_mode:
            self.tltf: int = self.width - len(self.zone.zone_type)
            if self.tltf < 0:
                self.width = len(self.zone.zone_type)
                self.nltf = self.width - len(self.zone.name)
        self.parents: list["DisplayZone"] = []

    def add_row(self, row: int, lines: list[list[Char]]) -> None:

        self.row: int = row

    def add_col(self, col: int, lines: list[list[Char]]) -> None:

        self.col: int = col
        if self.info_mode and hasattr(self, "row"):
            r: int = self.row + 1
            c: int = self.col
            if lines[r][c].is_border:
                while lines[r][c - 1].is_border:
                    c -= 1
            else:
                while not lines[r][c].is_border:
                    c += 1
            self.col = c

    @property
    def bounds(self) -> tuple[int, int, int, int]:

        if not hasattr(self, "row") or not hasattr(self, "col"):
            return 0, 0, 0, 0

        top = self.row
        bottom = self.row + self.height + self.info_mode
        left = self.col
        right = self.col + self.size * 2 - 1

        return top, bottom, left, right

    def choose_point(
        self,
        facade: str,
        lines: list[list[Char]]
    ) -> Char | None:

        options = DIRECTIONS[facade]

        if not options["valid"](self, lines):
            return None

        pref = options["preferred"](self)
        if lines[pref[0]][pref[1]].relation == "":
            return lines[pref[0]][pref[1]]

        for r, c in options["edge_iter"](self):
            if lines[r][c].relation == "":
                return lines[r][c]

        return None

    def relative_position(self, parent: "DisplayZone") -> str:
        t1, b1, l1, r1 = self.bounds
        t2, b2, l2, r2 = parent.bounds

        if b2 < t1:
            return "up"
        if t2 > b1:
            return "down"
        if r2 < l1:
            return "left"
        if l2 > r1:
            return "right"
        if t2 < t1:
            return "up"
        return "down"

    def choose_arrival(self, parent: "DisplayZone", side: str) -> str:
        t1, b1, l1, r1 = self.bounds
        t2, b2, l2, r2 = parent.bounds

        if side == "left":
            return (
                "right" if not (b2 < t1 or t2 > b1)
                else ("up" if t2 > b1 else "down")
            )

        if side == "right":
            return (
                "left" if not (b2 < t1 or t2 > b1)
                else ("up" if t2 > b1 else "down")
            )

        if side == "up":
            return (
                "down" if not (r2 < l1 or l2 > r1)
                else ("left" if l2 > r1 else "right")
            )

        return (
            "up" if not (r2 < l1 or l2 > r1)
            else ("left" if l2 > r1 else "right")
        )

    @staticmethod
    def set_arrival_dist(lines: list[list[Char]], arrival: Char) -> None:

        for line in range(len(lines)):

            for char in range(len(lines[line])):

                lines[line][char].dist_from_start = 0

                lines[line][char].dist_from_arrival = (
                    abs(line - arrival.row)
                    + abs(char - arrival.col)
                )

                lines[line][char].dir_from_parent = None

    def trace_connections(
        self,
        lines: list[list[Char]],
        zones: dict[str, "DisplayZone"]
    ) -> None:

        self.paths: dict[str, list[tuple[int, int]]] = {}

        for parent in [
            zones[con.zone1.name]
            for con in self.zone.connections.values()
            if con.zone1.name != self.zone.name
        ]:

            side: str = self.relative_position(parent)

            start_point: Char | None = self.choose_point(side, lines)
            if not start_point:
                continue

            arrival: Char | None = parent.choose_point(
                self.choose_arrival(parent, side), lines
            )
            if not arrival:
                continue

            path_found: list[tuple[int, int]] = []
            explored: list[Char] = [start_point]
            to_explore: list[Char] = PathFinder.find_valid_neighbors(
                lines, start_point, [], explored, parent.zone.name, arrival
            )

            self.set_arrival_dist(lines, arrival)

            while (
                not path_found
                and len(explored) < len(lines) * len(lines[0])
            ):

                next_point: Char | None = PathFinder.find_next_point(
                    to_explore
                )

                if not next_point:
                    break

                to_explore.remove(next_point)
                explored.append(next_point)

                if (
                    next_point == arrival
                    or (
                        next_point.relation == parent.zone.name
                        and not next_point.is_border
                    )
                ):

                    path_found = PathFinder.retrace_steps(
                        next_point, start_point
                    )
                    break

                to_explore = PathFinder.find_valid_neighbors(
                    lines,
                    next_point,
                    to_explore,
                    explored,
                    parent.zone.name,
                    arrival
                )

            if not path_found:
                continue

            self.paths[parent.zone.name] = path_found

            for r, c in path_found:

                lines[r][c].connection_char = CHARACTERS["connection"]
                lines[r][c].style = self.zone.color

    def update_drones(self, lines: list[list[Char]]) -> None:

        if not hasattr(self, "drones"):
            self.drones: list[tuple[Drone, int, int]] = []

        for drone, row, col in self.drones:
            if drone not in self.zone.occupied:
                self.drones.remove((drone, row, col))
                lines[row][col].char = " "
                lines[row][col].style = ""
                for c in str(drone.id):
                    col += 1
                    lines[row][col].char = " "
                    lines[row][col].style = ""

        if len(self.drones) > 0:
            drone_r: int = self.drones[-1][1]
            drone_c: int = (
                self.drones[-1][2] + 1 + len(str(self.drones[-1][0].id))
            )
        else:
            drone_r = self.row + self.info_mode + 1
            drone_c = self.col + 1

        for drone in self.zone.occupied:

            if drone in [d[0] for d in self.drones]:
                continue

            if drone_c >= self.col + self.size * 2 - 2:
                drone_r += 1
                drone_c = self.col + 1

            self.drones.append((drone, drone_r, drone_c))
            drone_c += 1 + len(str(drone.id))

        self.update_con_drones(lines)
        self.add_drones(lines)

    def update_con_drones(self, lines: list[list[Char]]) -> None:

        if not hasattr(self, "con_drones"):
            self.con_drones: list[tuple[Drone, int, int, str]] = []

        for con_drone, con_r, con_c, p_name in self.con_drones:

            if (
                con_drone in self.zone.occupied
                or con_drone not in self.zone.connections[p_name].occupied
            ):

                self.con_drones.remove((con_drone, con_r, con_c, p_name))

                lines[con_r][con_c].connection_char = "c"
                lines[con_r][con_c].style = self.zone.color

                for c in str(con_drone.id):

                    con_c += 1

                    if lines[con_r][con_c].connection_char:
                        lines[con_r][con_c].connection_char = "c"
                        lines[con_r][con_c].style = self.zone.color
                    else:
                        lines[con_r][con_c].char = " "
                        lines[con_r][con_c].style = ""

        for parent_name, path in self.paths.items():

            for drone in self.zone.connections[parent_name].occupied:

                if drone in [cd[0] for cd in self.con_drones]:
                    continue

                if (
                    self.zone.zone_type == "restricted"
                    and drone not in self.zone.occupied
                ):
                    self.con_drones.append((
                        drone, path[len(path) // 2 + len(self.con_drones)][0],
                        path[len(path) // 2 + len(self.con_drones)][1],
                        parent_name
                    ))

    def add_drones(self, lines: list[list[Char]]) -> None:

        for drone, row, col in self.drones:

            lines[row][col].char = CHARACTERS["drone"]
            lines[row][col].style = self.zone.color + " blink"

            for c in str(drone.id):

                col += 1
                lines[row][col].char = c
                lines[row][col].style = self.zone.color + " blink"

        for con_drone, con_row, con_col, p_name in self.con_drones:

            lines[con_row][con_col].connection_char = CHARACTERS["drone"]
            lines[con_row][con_col].style = self.zone.color + " blink"

            for con_c in str(con_drone.id):

                con_col += 1
                lines[con_row][con_col].char = con_c
                lines[con_row][con_col].style = self.zone.color + " blink"

    @staticmethod
    def add_space(length: int) -> list[Char]:

        return [
            Char(" ", "", "", False)
            for _ in range(length)
        ]

    def add_styled(self, char: str, length: int) -> list[Char]:

        return [
            Char(char, self.zone.color, self.zone.name, True)
            for _ in range(length)
        ]

    def add_title(
        self,
        cur_line: list[Char],
        title: str,
        padding: int
    ) -> None:

        if padding > 0:
            cur_line += self.add_space(padding // 2)
        for c in title:
            cur_line.append(Char(c, self.zone.color, self.zone.name, False))
        if padding > 0:
            cur_line += self.add_space(padding // 2 + padding % 2)

    def add_to_line(self, line: int, cur_line: list[Char]) -> None:

        if line > self.height + self.info_mode:
            cur_line += self.add_space(self.width)
            return

        if line == self.height + self.info_mode:

            self.add_title(cur_line, self.zone.name, self.nltf)
            return

        if self.info_mode and line == 0:

            self.add_title(cur_line, self.zone.zone_type, self.tltf)
            return

        if self.info_mode and self.tltf < 0:
            cur_line += self.add_space((-self.tltf) // 2)

        elif self.nltf < 0:
            cur_line += self.add_space((-self.nltf) // 2)

        if line == self.info_mode or line == self.height - 1 + self.info_mode:

            if line == self.info_mode:
                cor: str = "u"
            else:
                cor = "l"

            fst: str = CHARACTERS[cor + "lcor"]
            mid: str = CHARACTERS["hor"]
            last: str = CHARACTERS[cor + "rcor"]

        else:

            fst = CHARACTERS["ver"]
            mid = CHARACTERS["space"]
            last = CHARACTERS["ver"]

        cur_line.append(Char(
            fst,
            self.zone.color,
            self.zone.name,
            True
        ))
        cur_line += self.add_styled(mid, self.size * 2 - 2)
        cur_line.append(Char(
            last,
            self.zone.color,
            self.zone.name,
            True
        ))

        if self.info_mode and self.tltf < 0:
            cur_line += self.add_space((-self.tltf) // 2 + (-self.tltf) % 2)

        elif self.nltf < 0:
            cur_line += self.add_space((-self.nltf) // 2 + (-self.nltf) % 2)


class Row:

    def __init__(self, row_id: int, pad: int) -> None:

        self.id: int = row_id
        self.zones: list[DisplayZone] = []
        self.lines: list[list[Char]] = []
        self.height: int = 0
        self.width: int = -pad
        self.padding: int = pad

    def add_new_zone(self, z: DisplayZone) -> None:

        self.zones.append(z)
        self.width += z.width + self.padding
        if z.height > self.height:
            self.height = z.height
        z.row_id = self.id

    def fill_lines(self) -> None:

        for line in range(self.height + 5):

            cur_line: list[Char] = []

            for zone in self.zones:

                zone.add_to_line(line, cur_line)

                if zone != self.zones[-1]:
                    cur_line += DisplayZone.add_space(self.padding)

            self.lines.append(cur_line)


class TuiDisplay:

    def __init__(self, drone_map: Map, info_mode: int) -> None:

        self.map: Map = drone_map
        self.console: Console = Console()
        self.zones: dict[str, DisplayZone] = {
            zone.name: DisplayZone(zone, info_mode)
            for zone in self.map.hubs
        }
        self.padding: int = 10
        self.info_mode: int = info_mode
        self.create_rows()

    def map_updated(self) -> list[list[Char]]:

        for row in self.rows:
            for zone in row.zones:
                zone.update_drones(self.lines)

        copycat: list[list[Char]] = []

        for line in self.lines:

            new_line: list[Char] = []

            for c in line:

                new_char: Char = Char(c.char, c.style, c.relation, c.is_border)

                if c.connection_char:
                    new_char.connection_char = c.connection_char

                new_line.append(new_char)

            copycat.append(new_line)

        return copycat

    @staticmethod
    def display_menu() -> None:

        print(pyfiglet.figlet_format(
            CHARACTERS["menu_title"],
            font="bigchief"
        ), end="")

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
        print(
            "     ➤ i: TOGGLE INFO MODE "
            f"({'off' if info_mode == 0 else 'on'})"
        )
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
    def display_end(info_mode: int, turns: int, avg: int) -> None:

        print("\n✦ ✦ ✦ ✦ END OF THE SIMULATION ✦ ✦ ✦ ✦\n")
        print(f"     ➤ number of turns: {turns}")
        if info_mode != 0:
            print(
                "     ➤ average number of turns per drone: {avg}"
            )
        time.sleep(0.1)

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

                    new_zone.parents.append(z)

                    if self.in_a_row(new_zone):
                        continue

                    self.rows[cur_row + 1].add_new_zone(new_zone)

            cur_row += 1

        self.add_missing_zones()
        self.create_lines()

    def add_missing_zones(self) -> None:

        for zone_id in range(len(self.map.hubs)):

            if not self.in_a_row(self.zones[self.map.hubs[zone_id].name]):

                row_id: int = 0

                if zone_id > 0:
                    row_id = self.zones[self.map.hubs[zone_id - 1].name].row_id

                self.rows[row_id].add_new_zone(
                    self.zones[self.map.hubs[zone_id].name]
                )

    def create_lines(self) -> None:

        self.lines: list[list[Char]] = []

        for row in self.rows:
            row.fill_lines()

        self.max_row_len: int = max(len(row.lines[0]) for row in self.rows)

        for row in self.rows:

            for line in row.lines:

                new_line: list[Char] = []
                row_pad: int = self.max_row_len - len(line)

                if row_pad > 0:
                    new_line += DisplayZone.add_space(row_pad // 2)

                new_line += line

                if row_pad > 0:
                    new_line += DisplayZone.add_space(
                        row_pad // 2 + row_pad % 2
                    )

                new_line.append(Char("\n", "", "", False))
                self.lines.append(new_line)

        for r in range(len(self.lines)):

            for c in range(len(self.lines[r])):

                if not hasattr(self.zones[self.lines[r][c].relation], "row"):
                    self.zones[
                        self.lines[r][c].relation
                    ].add_row(r, self.lines)

                if not hasattr(self.zones[self.lines[r][c].relation], "col"):
                    self.zones[
                        self.lines[r][c].relation
                    ].add_col(c, self.lines)

                self.lines[r][c].row = r
                self.lines[r][c].col = c

        for row_id in range(len(self.rows) - 1, -1, -1):

            for zone in range(len(self.rows[row_id].zones) - 1, -1, -1):

                self.rows[row_id].zones[zone].trace_connections(
                    self.lines,
                    self.zones
                )

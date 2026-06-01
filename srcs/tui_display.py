import time
import pyfiglet
from rich import print
from rich.console import Console
from typing import Callable, Generator
from .zones import Zone, Connection
from .map_data import Map
from .path import PathFinder
from .state import State, Char


PREFERRED_DIR: dict[str, Callable[["DisplayZone"], tuple[int, int]]] = {
    "up": lambda self: (
        self.bounds[0] - 1,
        (self.bounds[2] + self.bounds[3]) // 2
    ),
    "down": lambda self: (
        self.bounds[1] + 1, (self.bounds[2] + self.bounds[3]) // 2
    ),
    "left": lambda self: (
        (self.bounds[0] + self.bounds[1]) // 2,
        self.bounds[2] - 1
    ),
    "right": lambda self: (
        (self.bounds[0] + self.bounds[1]) // 2,
        self.bounds[3] + 1
    )
}


EDGE_DIR: dict[
    str,
    Callable[["DisplayZone"], Generator[tuple[int, int], None, None]]
] = {
    "up": lambda self: (
        (self.bounds[0] - 1, c)
        for c in range(self.bounds[2], self.bounds[3] + 1)
    ),
    "down": lambda self: (
        (self.bounds[1] + 1, c)
        for c in range(self.bounds[2], self.bounds[3] + 1)
    ),
    "left": lambda self: (
        (r, self.bounds[2] - 1)
        for r in range(self.bounds[0], self.bounds[1] + 1)
    ),
    "right": lambda self: (
        (r, self.bounds[3] + 1)
        for r in range(self.bounds[0], self.bounds[1] + 1)
    )
}


VALID_DIR: dict[str, Callable[["DisplayZone", list[list[Char]]], bool]] = {
    "up": lambda self, lines: self.bounds[0] - 1 >= 0,
    "down": lambda self, lines: self.bounds[1] + 1 < len(lines),
    "left": lambda self, lines: self.bounds[2] - 1 >= 0,
    "right": lambda self, lines: self.bounds[3] + 1 < len(lines[0])
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
    "menu_title": "Welcome to Fly-In !"
}


RAINBOW: list[str] = [
    "red",
    "dark_orange",
    "gold1",
    "spring_green1",
    "dark_green",
    "turquoise2",
    "dark_blue",
    "dark_purple"
]


RAINBOW_EXT: list[str] = [
    "dark_red",
    "red",
    "red3",
    "dark_orange3"
    "orange3",
    "gold3",
    "yellow1",
    "pale_green1",
    "dark_sea_green4",
    "dark_green",
    "pale_turquoise1",
    "sky_blue2"
    "navy_blue",
    "dark_magenta",
    "purple4",
    "hot_pink3"
]


class DisplayZone:

    """

    A class that represents the display of a zone in the simulation.

    """

    def __init__(
        self,
        z: Zone,
        info_mode: int = 0
    ) -> None:

        """

        Initializes the attributes of a DisplayZone object.

        Parameters
        ----------
        z : Zone
            The zone associated with the display zone.
        info_mode : int
            Indicates whether or not the information mode is activated.

        """

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
        if self.zone.color == "rainbow":
            self.rainbow_index: int = -1
            if self.size * 2 > 8:
                self.rainbow: list[str] = RAINBOW_EXT
            else:
                self.rainbow = RAINBOW

    def add_row(self, row: int) -> None:

        """

        Adds the attribute row
        that associates the top border of the DisplayZone
        to a line of the grid.

        Parameters
        ----------
        row : int
            The row representing the top border of the zone.

        """

        self.row: int = row

    def add_col(self, col: int, lines: list[list[Char]]) -> None:

        """

        Adds the attribute col
        that associates the left border of the DisplayZone
        to a column of the grid,
        changing it depending on the information mode.

        Parameters
        ----------
        col : int
            The column representing the left border of the zone.
        lines : list[list[Char]]
            The screen's grid containing all the points.

        """

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
    def color(self) -> str:

        """

        A property of the DisplayZone class
        used to get the proper color for the display characters.

        Returns
        -------
        str
            The color for the character's style.

        """
        if self.zone.color == "rainbow":
            self.rainbow_index += 1
            return self.rainbow[self.rainbow_index % len(self.rainbow)]

        return self.zone.color

    @property
    def bounds(self) -> tuple[int, int, int, int]:

        """

        A property of the DisplayZone class
        used to determine the bounds of the display zone.

        Returns
        -------
        tuple[int, int, int, int]
            Respectively the top, bottom, left and right bounds of the zone.

        """

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

        """

        Chooses an entry point for the start of the connection
        path between itself and another parent zone
        based on the facade given.

        Parameters
        ----------
        facade : str
            The facade from which to choose an entry point
            (either left, right, up or down).

        Returns
        -------
        Char | None
            The point of the grid selected to be the entry point
            if one is available, otherwise None.

        """

        if not VALID_DIR[facade](self, lines):
            return None

        pref = PREFERRED_DIR[facade](self)
        if lines[pref[0]][pref[1]].relation == "":
            return lines[pref[0]][pref[1]]

        for r, c in EDGE_DIR[facade](self):
            if lines[r][c].relation == "":
                return lines[r][c]

        return None

    def relative_position(self, parent: "DisplayZone") -> str:

        """

        Determines the relative position from itself to the parent zone.

        Parameters
        ----------
        parent : DisplayZone
            The parent zone to reach.

        Returns
        -------
        str
            Where the parent zone is located
            looking from the child zone's point of view.

        """

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

        """

        Determines the best side for the connection path
        between the child zone and the parent zone
        to arrive at.

        Parameters
        ----------
        parent : DisplayZone
            The parent zone to reach.
        side : str
            The side of the child zone from which
            the connection path starts from.

        Returns
        -------
        str
            The best side for the connection path to end up at.

        """

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

        """

        Resets the distance attributes of all the points in the grid.

        Parameters
        ----------
        lines : list[list[Char]]
            The screen's grid containing all the points.
        arrival : Char
            The point of arrival for the connection path.

        """

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

        """

        Traces a connection path between the zone
        and each of its parents.

        Parameters
        ----------
        lines : list[list[Char]]
            The screen's grid containing all the points.
        zones : dict[str, DisplayZone]
            All of the display zones in the simulation.

        """

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
                lines[r][c].style = self.color

    def update_drones(
        self,
        lines: list[list[Char]],
        drones_delivered: list[int],
        goal: str
    ) -> None:

        """

        Updates the drones that need to be displayed
        based on the current occupancy of the Zone associated.

        Parameters
        ----------
        lines : list[list[Char]]
            The screen's grid containing all the points.

        """

        if not hasattr(self, "drones"):
            self.drones: list[tuple[int, int, int]] = []

        occupying: list[int] = [drone.id for drone in self.zone.occupied]

        if self.zone.name == goal:
            occupying = drones_delivered

        for drone, row, col in self.drones:

            lines[row][col].char = " "
            lines[row][col].style = ""

            for c in str(drone):

                col += 1
                lines[row][col].char = " "
                lines[row][col].style = ""

        self.drones = []

        drone_r = self.row + self.info_mode + 1
        drone_c = self.col + 1

        for drone in occupying:

            if drone_c + 1 + len(str(drone)) > self.col + self.size * 2 - 1:
                drone_r += 1
                drone_c = self.col + 1

            self.drones.append((drone, drone_r, drone_c))
            drone_c += 1 + len(str(drone))

        self.update_con_drones(lines)
        self.add_drones(lines)

    def update_con_drones(self, lines: list[list[Char]]) -> None:

        """

        Updates the drones in the connections between the zone
        and other zones based on the connections' occupancy.

        Parameters
        ----------
        lines : list[list[Char]]
            The screen's grid containing all the points.

        """

        if not hasattr(self, "con_drones"):
            self.con_drones: list[tuple[int, int, int, str]] = []

        for con_drone, con_r, con_c, p_name in self.con_drones:

            lines[con_r][con_c].connection_char = CHARACTERS["connection"]
            lines[con_r][con_c].style = self.color

            for _ in str(con_drone):

                con_c += 1

                if lines[con_r][con_c].connection_char:
                    lines[con_r][con_c].connection_char = CHARACTERS[
                        "connection"
                    ]
                    lines[con_r][con_c].style = self.color
                else:
                    lines[con_r][con_c].char = " "
                    lines[con_r][con_c].style = ""

        self.con_drones = []

        for parent_name, path in self.paths.items():

            for drone in [
                dr.id for dr in self.zone.connections[parent_name].occupied
            ]:

                if (
                    self.zone.zone_type == "restricted"
                    and drone not in [d.id for d in self.zone.occupied]
                ):
                    self.con_drones.append((
                        drone, path[
                            (len(path) // 2) + len(self.con_drones)
                        ][0],
                        path[(len(path) // 2) + len(self.con_drones)][1],
                        parent_name
                    ))

    def add_drones(self, lines: list[list[Char]]) -> None:

        """

        Changes the points in the grid to display the drones
        that occupy both the zone and the possible connections.

        Parameters
        ----------
        lines : list[list[Char]]
            The screen's grid containing all the points.

        """

        for drone, row, col in self.drones:

            lines[row][col].char = CHARACTERS["drone"]
            lines[row][col].style = self.color + " blink"

            for c in str(drone):

                col += 1
                lines[row][col].char = c
                lines[row][col].style = self.color + " blink"

        for con_drone, con_row, con_col, _ in self.con_drones:

            lines[con_row][con_col].connection_char = CHARACTERS["drone"]
            lines[con_row][con_col].style = self.color + " blink"

            for c in str(con_drone):

                con_col += 1
                lines[con_row][con_col].connection_char = c
                lines[con_row][con_col].style = self.color + " blink"

    @staticmethod
    def add_space(length: int) -> list[Char]:

        """

        Creates a set of Char objects
        that just display empty space.

        Parameters
        ----------
        length : int
            The number of spaces required.

        Returns
        -------
        list[Char]
            The correct amount of spaces created.

        """

        return [
            Char(" ", "", "", False)
            for _ in range(length)
        ]

    def add_styled(self, char: str, length: int) -> list[Char]:

        """

        Creates a set of Char objects
        that display certain characters with style added.

        Parameters
        ----------
        length : int
            The number of styled characters required.

        Returns
        -------
        list[Char]
            The correct amount of styled characters created.

        """

        return [
            Char(char, self.color, self.zone.name, True)
            for _ in range(length)
        ]

    def add_title(
        self,
        cur_line: list[Char],
        title: str,
        padding: int
    ) -> None:

        """

        Adds a zone title to the current line being constructed
        with the correct padding before and after if required.

        Parameters
        ----------
        cur_line : list[Char]
            The current line of the grid being formed.
        title : str
            The title to add to the line.
        padding : str
            The type of the padding
            (either nltf = name_letters_to_fit or tltf = title_letters_to_fit)

        """

        if padding > 0:
            cur_line += self.add_space(padding // 2)

        for c in range(len(title)):

            cur_line.append(Char(
                title[c],
                self.color,
                self.zone.name,
                False
            ))

        if padding > 0:
            cur_line += self.add_space(padding // 2 + padding % 2)

    def add_to_line(self, line: int, cur_line: list[Char]) -> None:

        """

        Adds the characters to the current line
        needed to display the zone (titles, borders, spacing...).

        Parameters
        ----------
        line : int
            The index of the line in the grid.
        cur_line: list[Char]
            The line of the grid being formed
            to which the characters are being added.

        """

        if line > self.height + self.info_mode:
            cur_line += self.add_space(self.width)
            return

        if line == self.height + self.info_mode:

            self.add_title(cur_line, self.zone.name, self.nltf)
            return

        if self.info_mode and line == 0:

            self.add_title(cur_line, self.zone.zone_type.upper(), self.tltf)
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
            self.color,
            self.zone.name,
            True
        ))

        cur_line += self.add_styled(mid, self.size * 2 - 2)

        cur_line.append(Char(
            last,
            self.color,
            self.zone.name,
            True
        ))

        if self.info_mode and self.tltf < 0:
            cur_line += self.add_space((-self.tltf) // 2 + (-self.tltf) % 2)

        elif self.nltf < 0:
            cur_line += self.add_space((-self.nltf) // 2 + (-self.nltf) % 2)


class Row:

    """

    A class representing a row in the screen's grid.

    """

    def __init__(self, row_id: int) -> None:

        """

        Initializes the attributes of a Row object.

        Parameters
        ----------
        row_id : int
            The identifiant of the row indicating its position in the grid.
        pad : int
            The amount of padding to add between zones.

        """

        self.id: int = row_id
        self.zones: list[DisplayZone] = []
        self.lines: list[list[Char]] = []
        self.height: int = 0
        self.width: int = 0
        self.padding: int = 0

    def set_padding(self) -> None:

        self.ver_pad: int = 10
        self.hor_pad: int = 10
        self.width += self.hor_pad

        if len(self.zones) == 0:
            return

        max_pad: int = max([
            con.max_link_capacity for z in self.zones
            for con in z.zone.connections.values()
        ])
        self.hor_pad += max_pad
        self.ver_pad += (max_pad // 2)
        self.width += self.hor_pad * (len(self.zones) - 1)

    def add_new_zone(self, z: DisplayZone) -> None:

        """

        Adds a new zone to the list of display zone,
        updating the width and height of the row.

        Parameters
        ----------
        z : DisplayZone
            The new zone to add.

        """

        self.zones.append(z)
        self.width += z.width
        if z.height > self.height:
            self.height = z.height
        z.row_id = self.id

    def fill_lines(self) -> None:

        """

        Fills the lines forming the row,
        adding to each one the characters
        of the zones that need to appear on the specific line.

        """

        self.set_padding()

        for line in range(self.height + self.ver_pad):

            cur_line: list[Char] = []

            for zone in self.zones:

                zone.add_to_line(line, cur_line)

                if zone != self.zones[-1]:
                    cur_line += DisplayZone.add_space(self.hor_pad)

            self.lines.append(cur_line)


class TuiDisplay:

    """

    A class used to display a drone simulation
    with zones and connections in the terminal.

    """

    def __init__(self, drone_map: Map, info_mode: int) -> None:

        """

        Initializes the attributes of the TuiDisplay object.

        Parameters
        ----------
        drone_map : map
            The simulation map containing the hubs and connections.
        info_mode : int
            Indicates whether or not the information mode is activated.

        """

        self.map: Map = drone_map
        self.console: Console = Console()
        self.zones: dict[str, DisplayZone] = {
            zone.name: DisplayZone(zone, info_mode)
            for zone in self.map.hubs
        }
        self.padding: int = 10
        self.info_mode: int = info_mode
        self.create_rows()

    def map_updated(self, drones_delivered: list[int]) -> list[list[Char]]:

        """

        Updates the map display to reflect the drones' positions.

        Returns
        -------
        list[list[Char]]
            A copy of the updated display map.

        """

        for row in self.rows:

            for zone in row.zones:

                zone.update_drones(
                    self.lines,
                    drones_delivered,
                    self.map.end_hub.name
                )

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
    def display_menu(info_mode: int, map_file: str) -> None:

        """

        Displays the menu banner and options for the user.

        Parameters
        ----------
        info_mode : int
            Indicates whether or not the information mode is activated.
        map_file : str
            The path to the file currently being selected for the map data.

        """

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

        print("\n✦ MENU OPTIONS ✦\n")
        print(f"     ➤ s: SELECT NEW MAP (current map: {map_file})")
        print("     ➤ l: LAUNCH THE DRONES")
        print(
            "     ➤ i: TOGGLE INFO MODE "
            f"({'off' if info_mode == 0 else 'on'})"
        )
        print("     ➤ m: DISPLAY AVAILABLE MAP PATHS")
        print("     ➤ q: QUIT PROGRAM")

    @staticmethod
    def display_maps(maps: dict[str, list[str]], map_dir: str) -> None:

        """

        Displays the map paths for the user to copy paste.

        Parameters
        ----------
        maps: dict[str, list[str]]
            The dictionary containing map categories and their respective maps.
        map_dir: str
            The base directory in which the map paths are.

        """
        print("\n✦ MAPS AVAILABLE ✦\n")

        for map_type, map_path in maps.items():

            print(f" ➤ {map_type.upper()}:\n")

            for m in map_path:

                print(f" - {map_dir + '/' + map_type + '/' + m + '.txt'}")

            print()

        time.sleep(1)
        input("Press any key to continue...\n")

    @staticmethod
    def display_state(state: State, nb_turns: int) -> None:

        """

        Displays a given state of the simulation
        and the options for the user.

        Parameters
        ----------
        state : State
            The current state of the simulation to display.

        """

        state.display_info()

        print(f"\n✦ SIMULATION OPTIONS (turn {state.turn}/{nb_turns}) ✦\n")
        print("     ➤ n: NEXT STEP")
        print("     ➤ p: PREVIOUS STEP")
        print("     ➤ m: RETURN TO MENU")

    @staticmethod
    def display_end(info_mode: int, turns: int, avg: int) -> None:

        """

        Displays an end message for the simulation
        and some summary information.

        Parameters
        ----------
        info_mode : int
            Indicates whether or not the information mode is activated.
        turns : int
            The number of turns made during the simulation.
        avg : int
            The average number of turns per drone.

        """

        print("\n✦ ✦ ✦ ✦ END OF THE SIMULATION ✦ ✦ ✦ ✦\n")
        print(f"     ➤ number of turns: {turns}")
        if info_mode != 0:
            print(
                f"     ➤ average number of turns per drone: {avg}"
            )
        print()
        time.sleep(0.5)

    def in_a_row(self, z: DisplayZone) -> bool:

        """

        Determines whether or not the display zone given
        is already in a row.

        Parameters
        ----------
        z : DisplayZone
            The display zone to look for.

        Returns
        -------
        bool
            A boolean indicating whether or not the zone was found in a row.

        """

        for row in self.rows:

            if z in row.zones:
                return True

        return False

    def create_rows(self) -> None:

        """

        Creates all the rows needed for the simulation display
        and assigns display zones to them based on hierarchy.

        """

        self.rows: list[Row] = [Row(0)]
        cur_row: int = 0

        new_zone: DisplayZone = self.zones[self.map.start_hub.name]
        self.rows[cur_row].add_new_zone(new_zone)

        goal: DisplayZone = self.zones[self.map.end_hub.name]

        connections_explored: list[Connection] = []

        while goal not in self.rows[cur_row].zones:

            self.rows.append(Row(cur_row + 1))

            for z in self.rows[cur_row].zones:

                for connection in z.zone.connections.values():

                    if connection in connections_explored:
                        continue

                    new_zone = (
                        self.zones[connection.zone2.name]
                        if z.zone == connection.zone1
                        else self.zones[connection.zone1.name]
                    )

                    new_zone.parents.append(z)
                    connections_explored.append(connection)

                    if self.in_a_row(new_zone):
                        continue

                    self.rows[cur_row + 1].add_new_zone(new_zone)

            cur_row += 1

        self.add_missing_zones()
        self.create_lines()

    def add_missing_zones(self) -> None:

        """

        Adds the zones that are not part of a row
        into an existing row, based on the hub closest to them
        in the drone map.

        """

        for zone_id in range(len(self.map.hubs)):

            if not self.in_a_row(self.zones[self.map.hubs[zone_id].name]):

                row_id: int = 0

                if zone_id > 0:
                    row_id = self.zones[self.map.hubs[zone_id - 1].name].row_id

                self.rows[row_id].add_new_zone(
                    self.zones[self.map.hubs[zone_id].name]
                )

    def create_lines(self) -> None:

        """

        Creates the screen's grid by combining all of the rows' lines,
        adding padding before and after to make the rows' lengths equal.

        """

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

                if self.lines[r][c].is_zone:

                    if not hasattr(
                        self.zones[self.lines[r][c].relation], "row"
                    ):
                        self.zones[
                            self.lines[r][c].relation
                        ].add_row(r)

                    if not hasattr(
                        self.zones[self.lines[r][c].relation], "col"
                    ):
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

from rich import print
from rich.text import Text
from rich.console import Console
from .zones import Zone  # Connection
from .map_data import Map
from .drones import Drone


class DisplayZone:

    def __init__(
        self, z: Zone,
        characters: dict[str, str],
        console: Console
    ) -> None:

        self.zone: Zone = z
        self.name: str = z.name
        self.size: int = 3 + ((self.zone.max_drones - 1) // 2)
        self.width: int = self.size * 2
        self.height: int = self.size
        self.ltf: int = self.width - len(self.name)
        if self.ltf < 0:
            self.width = len(self.name)
        self.row_id: int = 0
        self.characters: dict[str, str] = characters
        self.console: Console = console
        self.parents: list["DisplayZone"] = []

    def update_drones(self) -> None:

        self.drones: dict[int, list[Drone]] = {
            line_nb: [] for line_nb in range(1, self.size)
        }
        space_left: int = self.size * 2 - 2
        line: int = 1
        for drone in self.zone.occupied:
            if space_left >= 1 + len(str(drone.id)):
                self.drones[line].append(drone)
                space_left -= 1 + len(str(drone.id))
            else:
                if line == self.size - 1:
                    break
                line += 1
                space_left = self.size * 2 - 2

    def print_space(self, length: int) -> None:

        print(f"{self.characters['space'] * length}", end="")

    def print_style(self, char: str, length: int) -> None:

        self.console.print(Text(
            f"{self.characters[char] * length}",
            style=self.zone.color
        ), end="")

    def print_line(self, line: int) -> None:

        if line > self.height:
            self.print_space(self.width)
            return
        if line == self.height:
            if self.ltf > 0:
                self.print_space(self.ltf // 2)
            self.console.print(Text(self.name, style=self.zone.color), end="")
            if self.ltf > 0:
                self.print_space(self.ltf // 2 + self.ltf % 2)
            return
        self.update_drones()
        if self.ltf < 0:
            self.print_space((-self.ltf) // 2)
        if line == 0 or line == self.height - 1:
            if line == 0:
                cor: str = "u"
            else:
                cor = "l"
            self.print_style((cor + "lcor"), 1)
            self.print_style("hor", self.size * 2 - 2)
            self.print_style((cor + "rcor"), 1)
        else:
            self.print_style("ver", 1)
            space_left = self.size * 2 - 2
            for drone in self.drones[line]:
                self.console.print(Text(
                    f"{self.characters['drone']}{drone.id}",
                    style=self.zone.color
                ), end="")
                space_left -= 1 + len(str(drone.id))
            self.print_space(space_left)
            self.print_style("ver", 1)
        if self.ltf < 0:
            self.print_space((-self.ltf) // 2 + (-self.ltf) % 2)


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

    def __init__(self, drone_map: Map) -> None:

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
            zone.name: DisplayZone(zone, self.characters, self.console)
            for zone in self.map.hubs
        }
        self.padding: int = 10
        self.create_rows()

    def display_map(self) -> None:

        for row in self.rows:
            self.print_row(row)

    def print_row(self, row: Row) -> None:

        row_pad: int = self.max_row_len - row.width
        for line in range(row.height + 5):
            print(f"{' ' * (row_pad // 2)}", end="")
            for zone in row.zones:
                zone.print_line(line)
                if zone != row.zones[-1]:
                    print(f"{' ' * 10}", end="")
            print(f"{' ' * (row_pad // 2 + row_pad % 2)}")

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

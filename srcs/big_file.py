import re
from typing import Callable
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing_extensions import Self as self
import time
import sys


sys.setrecursionlimit(8000)


class Connection:

    def __init__(
        self,
        name: str,
        zone1: "Zone",
        zone2: "Zone",
        max_link_capacity: int
    ) -> None:

        if zone1 is None or zone2 is None:

            raise ValueError(
                "A zone for a connection cannot be None\n"
            )

        if zone1 == zone2:

            raise ValueError(
                "Zones cannot be the same for a connection\n"
            )

        if not isinstance(max_link_capacity, int) or max_link_capacity < 1:

            raise ValueError(
                f"Invalid max link capacity '{max_link_capacity}'\n"
                "Max link capacity for a connection "
                "must be a positive integer"
            )

        self.name: str = name
        self.zone1: "Zone" = zone1
        self.zone2: "Zone" = zone2
        self.max_link_capacity: int = max_link_capacity
        self.wish_to_occupy: list = []
        self.occupied: list = []

    def free_spaces(self) -> int:

        if not self.occupied:
            return 0
        return len([
            drone for drone in self.occupied
            if drone.is_next_step_accessible(drone.path_to_follow)
        ])

    def calculate_wait_cost(self, drone: "Drone") -> int:

        cost: int = 1
        for drone_wish in self.wish_to_occupy:
            if drone_wish == drone:
                break
            cost += 1
        return abs(
            cost - (self.max_link_capacity - len(self.occupied))
        ) - self.free_spaces()

    def is_accessible(self, drone: "Drone") -> bool:

        space_remaining: int = self.max_link_capacity - len(self.occupied)

        if (
            space_remaining == 0 or (
                len(self.wish_to_occupy) >= space_remaining
                and drone not in self.wish_to_occupy[:space_remaining]
            )
        ):
            return False

        return True


class Zone(BaseModel):

    name: str
    x: int
    y: int
    zone_type: str = Field(default="normal")
    color: str | None = Field(default=None)
    max_drones: int = Field(default=1, gt=0)
    connections: dict = Field(default={})
    wish_to_occupy: list = Field(default=[])
    occupied: list = Field(default=[])

    @model_validator(mode="after")
    def validate_name(self) -> self:

        if " " in self.name or "-" in self.name:

            raise ValueError(
                f"Invalid name for the zone '{self.name}'\n"
                "There must not be spaces or dashes in a zone's name"
            )

        return self

    @model_validator(mode="after")
    def validate_zone_type(self) -> self:

        if self.zone_type not in [
            "normal",
            "priority",
            "restricted",
            "blocked"
        ]:

            raise ValueError(
                f"Invalid zone type for zone '{self.name}'\n"
                "Type must be one of "
                "'normal', 'priority', 'restricted', 'blocked'"
            )

        return self

    @model_validator(mode="after")
    def validate_color(self) -> self:

        if self.color and len(self.color.split(" ")) != 1:

            raise ValueError(
                f"Invalid color for zone '{self.name}'\n"
                "Color must be a single word"
            )

        return self

    def add_connection(
        self, new_connection: Connection,
        neighbor: "Zone"
    ) -> None:

        if neighbor.name in self.connections.keys():

            raise ValueError(
                f"Connection between '{self.name}' "
                f"and '{neighbor.name}' "
                "already exists!"
            )

        self.connections[neighbor.name] = new_connection

    def display_zone_info(self) -> None:

        print(
            f"zone {self.name}: "
            f"zone type {self.zone_type}, "
            f"max drones {self.max_drones}, "
            "connections", end=""
        )
        for con_name, con in self.connections.items():
            print(f" {con_name}: first zone={self == con.zone1}", end="")

        print("\n")

    def free_spaces(self) -> int:

        if not self.occupied:
            return 0
        return len([
            drone for drone in self.occupied
            if drone.is_next_step_accessible(drone.path_to_follow)
        ])

    def calculate_wait_cost(self, drone: "Drone") -> int:

        cost: int = 1
        for drone_wish in self.wish_to_occupy:
            if drone_wish == drone:
                break
            cost += 1
        return abs(
            cost - (self.max_drones - len(self.occupied))
        ) - self.free_spaces()

    def is_accessible(self, drone: "Drone") -> bool:

        space_remaining: int = self.max_drones - len(self.occupied)

        if (
            space_remaining == 0 or (
                len(self.wish_to_occupy) >= space_remaining
                and drone not in self.wish_to_occupy[:space_remaining]
            )
        ):
            return False

        return True


class Map:

    def validate_nb_drones(self, nb_drones: str) -> None:

        if hasattr(self, "nb_drones"):

            raise ValueError(
                "Number of drones already defined!"
            )

        self.nb_drones = int(nb_drones)

        if self.nb_drones < 1:

            raise ValueError(
                f"Invalid value '{nb_drones}' for number of drones\n"
                "Must be a positive integer"
            )

    def validate_start_hub(self, start_hub: str) -> None:

        if hasattr(self, "start_hub"):

            raise ValueError(
                "Start hub is already defined"
            )

        self.start_hub = self.add_hub(start_hub)

        if "max_drones" not in start_hub:
            self.start_hub.max_drones = self.nb_drones

        if self.start_hub.max_drones < self.nb_drones:
            raise ValueError(
                "The drone capacity of the starting hub "
                "should not be inferior to the number of drones"
            )

        if self.start_hub.zone_type == "blocked":
            raise ValueError(
                "The starting hub should not be a blocked zone"
            )

    def validate_end_hub(self, end_hub: str) -> None:

        if hasattr(self, "end_hub"):

            raise ValueError(
                "End hub is already defined"
            )

        self.end_hub = self.add_hub(end_hub)

        if "max_drones" not in end_hub:
            self.end_hub.max_drones = self.nb_drones

        if self.end_hub.max_drones < self.nb_drones:
            raise ValueError(
                "The drone capacity of the ending hub "
                "should not be inferior to the number of drones"
            )

        if self.end_hub.zone_type == "blocked":
            raise ValueError(
                "The end hub should not be a blocked zone"
            )

    def validate_connection(self, new_connection: str) -> None:

        if not hasattr(self, "hubs") or not self.hubs:

            raise ValueError(
                "No hubs have been defined, "
                f"impossible to create connection '{new_connection}'"
            )

        connection_params: list[str] = new_connection.split(" ")

        if not connection_params:

            raise ValueError(
                "No definition provided for a connection"
            )

        con_zones: list[str] = connection_params[0].split("-")
        con_metadata: int = MapParser.parse_con_metadata(connection_params)

        if len(con_zones) != 2:

            raise ValueError(
                f"Invalid connection format '{connection_params[0]}'\n"
                "Format must be '<zone1>-<zone2> [metadata](optional)'"
            )

        fst_zone: Zone | None = self.find_hub(con_zones[0])
        scd_zone: Zone | None = self.find_hub(con_zones[1])

        if not fst_zone or not scd_zone:

            raise ValueError(
                f"Invalid hub(s) given for connection '{connection_params[0]}'"
            )

        connection: Connection = Connection(
            connection_params[0],
            fst_zone,
            scd_zone,
            con_metadata
        )
        fst_zone.add_connection(connection, scd_zone)
        scd_zone.add_connection(connection, fst_zone)

    def find_hub(self, hub_name: str) -> Zone | None:

        if hasattr(self, "hubs"):

            for hub in self.hubs:

                if hub.name == hub_name:

                    return hub

        print(f"No hub {hub_name} found\n")

        return None

    def add_hub(self, new_hub: str) -> Zone:

        hub_params: list[str] = new_hub.split(" ")

        if len(hub_params) < 3:

            raise ValueError(
                f"Invalid zone definition '{new_hub}' for hub\n"
                "Zone definition must contain at least a name and coordinates"
            )

        if len(hub_params) > 6:

            raise ValueError(
                f"Invalid zone definition '{new_hub}' for hub\n"
                "Zone definition must not contain "
                "more than a name, coordinates, "
                "and optional metadata 'zone', 'color' and 'max_drones'"
            )

        if not hasattr(self, "hubs"):

            self.hubs: list[Zone] = []

        for hub in self.hubs:

            if hub.name == hub_params[0]:

                raise ValueError(
                    f"Hub '{hub.name}' already exists\n"
                    "You must choose unique names for each zone"
                )

            if (int(hub_params[1]), int(hub_params[2])) == (hub.x, hub.y):

                raise ValueError(
                    f"Coordinates for hub '{hub_params[0]}' "
                    f"are the same as hub '{hub.name}'\n"
                    "Each zone must have unique coordinates"
                )

        metadata: tuple[
            str, str | None, int
        ] = MapParser.parse_hub_metadata(hub_params)

        hub_created: Zone = Zone(
            name=hub_params[0],
            x=int(hub_params[1]),
            y=int(hub_params[2]),
            zone_type=metadata[0],
            color=metadata[1],
            max_drones=metadata[2]
        )
        print(f"successfully created hub {hub_created.name}")

        self.hubs.append(hub_created)

        return hub_created


class MapParser:

    def parse_map(self, filename: str) -> Map | None:

        self.map: Map = Map()
        self.lines: dict[str, tuple[list[str], Callable]] = {
            "nb_drones": ([], self.map.validate_nb_drones),
            "start_hub": ([], self.map.validate_start_hub),
            "end_hub": ([], self.map.validate_end_hub),
            "hub": ([], self.map.add_hub),
            "connection": ([], self.map.validate_connection)
        }

        try:

            with open(filename) as map_file:

                fst: bool = True

                for line in map_file:

                    if not line.startswith("#") and line.strip():

                        if fst:
                            if "nb_drones" not in line:
                                raise ValueError(
                                    "The first line should be "
                                    "the number of drones"
                                )
                            fst = False
                        self.parse_line(line.strip())

                for parameter in self.lines.values():

                    for definition in parameter[0]:
                        parameter[1](definition)

            if not hasattr(self.map, "start_hub"):

                raise ValueError(
                    "Missing start hub!"
                )

            if not hasattr(self.map, "end_hub"):

                raise ValueError(
                    "Missing end hub!"
                )

            if not hasattr(self.map, "nb_drones"):

                raise ValueError(
                    "Missing number of drones!"
                )

        except Exception as err:

            print(
                "Caught Parsing Error :"
            )

            if isinstance(err, ValidationError):

                for error in err.errors():
                    print(error["msg"])

            else:

                print(err)

            return None

        else:

            return self.map

    def parse_line(self, line: str) -> None:

        if not (match := re.match("([a-z_]+): (.+)", line, re.I)):

            raise ValueError(
                f"Invalid format for line '{line}'\n"
                "Format must be '<parameter>: <definition>'"
            )

        parameter: str = match.group(1)

        if parameter not in self.lines.keys():

            raise ValueError(
                f"Invalid parameter type '{parameter}' for line '{line}'\n"
                "Parameter must be one of 'nb_drones', 'start_hub', "
                "'end_hub', 'hub', or 'connection'"
            )

        self.lines[parameter][0].append(match.group(2))

    @staticmethod
    def parse_hub_metadata(params: list[str]) -> tuple[str, str | None, int]:

        if len(params) < 3:
            raise ValueError(
                "Missing definition parameters for the hub\n"
                "Parameters required are the hub's name and coordinates"
            )

        zone: str = "normal"
        color: str | None = None
        max_drones: int = 1

        zone_defined: bool = False
        color_defined: bool = False
        max_drones_defined: bool = False

        if len(params) == 3:
            return (zone, color, max_drones)

        if not (params[3].startswith("[") and params[-1].endswith("]")):

            raise ValueError(
                f"Invalid metadata format in zone definition '{params}'\n"
                "Metadata must be incased in brackets '[]'"
            )

        params[3] = params[3].replace("[", "")
        params[-1] = params[-1].replace("]", "")

        for p in range(3, len(params)):

            if not (match := re.match("([a-z_]+)=(.+)", params[p], re.I)):

                raise ValueError(
                    f"Invalid format for metadata '{params[p]}'\n"
                    "Metadata must be of '<parameter>=<value>' format"
                )

            if match.group(1) == "zone":

                if zone_defined:

                    raise ValueError(
                        f"Invalid metadata '{params[p]}'\n"
                        "Zone type is already defined"
                    )

                zone = match.group(2)
                zone_defined = True

            elif match.group(1) == "color":

                if color_defined:

                    raise ValueError(
                        f"Invalid metadata '{params[p]}'\n"
                        "Color for the zone is already defined"
                    )

                color = match.group(2)
                color_defined = True

            elif match.group(1) == "max_drones":

                if max_drones_defined:

                    raise ValueError(
                        f"Invalid metadata '{params[p]}'\n"
                        "Maximum drones for the zone is already defined"
                    )

                max_drones = int(match.group(2))
                max_drones_defined = True

            else:

                raise ValueError(
                    f"Invalid parameter '{match.group(1)}' for metadata\n"
                    "Valid parameters are 'zone', 'color' and 'max_drones'"
                )

        return (zone, color, max_drones)

    @staticmethod
    def parse_con_metadata(con_params: list[str]) -> int:

        max_cap: int = 1

        if len(con_params) > 2:

            raise ValueError(
                "Too many values given "
                f"for connection definition '{con_params}'\n"
                "Definition must contain the two connection zones "
                "and optional metadata must contain only 'max_link_capacity'"
            )

        if len(con_params) > 1:

            if not (
                con_params[1].startswith("[")
                and con_params[1].endswith("]")
            ):

                raise ValueError(
                    f"Invalid metadata format for '{con_params[1]}'\n"
                    "Metadata must always be incased in brackets '[]'"
                )

            con_params[1] = con_params[1].replace("[", "")
            con_params[1] = con_params[1].replace("]", "")

            if not (match := re.match(
                "max_link_capacity=([0-9]+)",
                con_params[1]
            )):

                raise ValueError(
                    f"Invalid parameter or format '{con_params[1]}' "
                    "given as connection metadata\n"
                    "Only parameter accepted is 'max_link_capacity' "
                    "and the corresponding value must be a positive integer"
                )

            max_cap = int(match.group(1))

        return max_cap


class Path:

    def __init__(self, path: list[Zone], cost: int) -> None:

        self.path: list[Zone] = path
        self.cost: int = cost
        self.priority: bool = False

    def display_path(self) -> None:

        print("path: ", end="")
        for zone in self.path:

            print(f"{zone.name} - ", end="")

        print(f"cost={self.cost}")


class Pathfinder:

    def __init__(self, drone_map: Map) -> None:

        self.map: Map = drone_map

    def calculate_paths(
        self,
        current_hub: Zone,
        current_path: list[Zone],
        cost: int,
        dest: Zone,
        possible_paths: list[Path]
    ) -> list[Path]:

        if current_hub.zone_type == "blocked":

            return

        if current_hub == dest:

            possible_paths.append(Path(current_path + [dest], cost))

        else:

            for branch in current_hub.connections.values():

                cost_to_add: int = 1

                if current_hub == branch.zone1:

                    if branch.zone2 in current_path:
                        return

                    if branch.zone2.zone_type == "restricted":
                        cost_to_add += 1

                    for path in possible_paths:
                        if current_path + [current_hub] == path.path:
                            return

                    self.calculate_paths(
                        branch.zone2,
                        current_path + [current_hub],
                        cost + cost_to_add,
                        dest,
                        possible_paths
                    )

        return possible_paths


class Drone:

    def __init__(
        self, drone_id: int,
        start_pos: Zone
    ) -> None:

        self.id: int = drone_id
        self.current_zone: Zone | Connection = start_pos
        self.occupying: list[Zone | Connection] = [self.current_zone]
        self.waiting: bool = False

    def update_intent(self) -> None:

        if self not in self.next_zone.wish_to_occupy:
            self.next_zone.wish_to_occupy.append(self)

        if (
            not isinstance(self.current_zone, Connection)
            and self not in self.next_zone.connections[
                self.current_zone.name
            ].wish_to_occupy
        ):
            self.next_zone.connections[
                self.current_zone.name
            ].wish_to_occupy.append(self)

    def turn_action(self) -> None:

        if self.is_next_step_accessible(self.path_to_follow):

            self.waiting = False

            for occup in self.occupying:
                occup.occupied.remove(self)
            self.occupying = []

            if self.next_zone.zone_type == "restricted":

                if isinstance(self.current_zone, Connection):

                    self.current_zone = self.next_zone
                    self.path_to_follow.path.remove(self.current_zone)
                    self.path_to_follow.cost -= 1

                else:

                    self.current_zone = self.next_zone.connections[
                        self.current_zone.name
                    ]

            else:

                self.next_zone.connections[
                    self.current_zone.name
                ].wish_to_occupy.remove(self)
                self.next_zone.connections[
                    self.current_zone.name
                ].occupied.append(self)
                self.occupying.append(self.next_zone.connections[
                    self.current_zone.name
                ])
                self.current_zone = self.next_zone

            self.current_zone.wish_to_occupy.remove(self)
            self.current_zone.occupied.append(self)
            self.occupying.append(self.current_zone)

        else:

            self.waiting = True

    def is_next_step_accessible(self, path: Path) -> bool:

        if (
            isinstance(self.current_zone, Connection)
            or (
                hasattr(self, "next_zone")
                and self.current_zone == self.next_zone
            )
        ):
            return True

        next_step: Zone = path.path[0]
        # print(f"\ndrone D{self.id} is trying to determine if zone {next_step.name} is accessible, current position {self.current_zone.name}\n")
        connection: Connection = next_step.connections[self.current_zone.name]
        ns_sp_rem: int = next_step.max_drones - len(
            next_step.occupied
        )
        con_sp_rem: int = connection.max_link_capacity - len(
            connection.occupied
        )

        if con_sp_rem == 0:
            return False

        if ns_sp_rem == 0:

            if next_step.zone_type == "restricted":

                if (
                    len(next_step.wish_to_occupy) < next_step.free_spaces()
                    or self in next_step.wish_to_occupy[
                        :next_step.free_spaces()
                    ]
                ):
                    return True

            return False

        return (
            connection.is_accessible(self)
            and next_step.is_accessible(self)
        )

    def free_connections(self) -> None:

        connections_occupied: list[Connection] = [
            zone for zone in self.occupying
            if isinstance(zone, Connection)
        ]
        for con in connections_occupied:
            con.occupied.remove(self)
            self.occupying.remove(con)

    def reevaluate_drone_path(self, pathfinder: Pathfinder) -> None:

        if isinstance(self.current_zone, Connection):
            return

        self.free_connections()

        possible_paths: list[Path] = pathfinder.calculate_paths(
            self.current_zone,
            [],
            0,
            pathfinder.map.end_hub,
            []
        )

        for path in possible_paths:

            if len(path.path) > 1:
                path.path = path.path[1:]

            if not self.is_next_step_accessible(path):

                if not path.path[0].connections[
                    self.current_zone.name
                ].is_accessible(self):

                    path.cost += path.path[0].connections[
                        self.current_zone.name
                    ].calculate_wait_cost(self)

                elif not path.path[0].is_accessible(self):

                    path.cost += path.path[0].calculate_wait_cost(self)

            if path.path[0].zone_type == "priority":
                path.priority = True

        self.path_to_follow = possible_paths[0]

        for path in possible_paths:

            if path.cost < self.path_to_follow.cost:
                self.path_to_follow = path

            elif (
                path.cost == self.path_to_follow.cost
                and path.priority and not self.path_to_follow.priority
            ):
                self.path_to_follow = path

        self.next_zone: Zone = self.path_to_follow.path[0]
        self.update_intent()
#        if self.id == 6:
#            print("\n\nall possible paths:\n")
#            for path in possible_paths:
#                path.display_path()
#                print()
#            print("\npath chosen by D6:")
#            self.path_to_follow.display_path()
#            print()


class DroneMonitor:

    def __init__(self, drone_map: Map, pathfinder: Pathfinder) -> None:

        self.drone_map: Map = drone_map
        self.pathfinder: Pathfinder = pathfinder
        self.drones: list[Drone] = []
        self.turns: int = 0

        for drone_id in range(1, self.drone_map.nb_drones + 1):

            new_drone: Drone = Drone(
                drone_id,
                self.drone_map.start_hub
            )
            self.drones.append(new_drone)
            self.drone_map.start_hub.occupied.append(new_drone)

#        print("\n==== DRONES ====\n\n")
#        for drone in self.drones:
#            print(f"-> drone D{drone.id}")

    def update_drones(self) -> None:

        # print("\n==== REEVALUATING DRONE PATHS ====\n\n")
        for drone in self.drones:

            drone.reevaluate_drone_path(self.pathfinder)

#        print("\n==== PATHS CHOSEN ====\n\n")
#        for drone in self.drones:
#            print(f"-> drone D{drone.id}:\n")
#            drone.path_to_follow.display_path()
#            print()

        # print("\n==== DRONES TURN ACTION ====\n\n")
        for drone in self.drones:

            drone.turn_action()

        moving_drones: list[Drone] = [
            drone for drone in self.drones
            if not drone.waiting
        ]

        # print("\n==== DISPLAYING DRONE MOVEMENTS ====\n\n")
        for drone in moving_drones:
            if drone != moving_drones[0]:
                print(" ", end="")
            print(f"D{drone.id}-{drone.current_zone.name}", end="")
            if drone.current_zone == self.drone_map.end_hub:
                for occupying in drone.occupying:
                    occupying.occupied.remove(drone)
                self.drones.remove(drone)

        print()
        time.sleep(0.1)
        self.turns += 1

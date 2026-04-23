import re
from typing import Callable
from pydantic import ValidationError
from .zones import Zone, Connection


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
            name=connection_params[0],
            zone1=fst_zone,
            zone2=scd_zone,
            max_link_capacity=con_metadata
        )
        fst_zone.add_connection(connection, scd_zone.name)
        scd_zone.add_connection(connection, fst_zone.name)

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
            str, str, int
        ] = MapParser.parse_hub_metadata(hub_params)

        hub_created: Zone = Zone(
            name=hub_params[0],
            x=int(hub_params[1]),
            y=int(hub_params[2]),
            zone_type=metadata[0],
            color=metadata[1],
            max_drones=metadata[2]
        )
        # print(f"successfully created hub {hub_created.name}")

        self.hubs.append(hub_created)

        return hub_created


class MapParser:

    def parse_map(self, filename: str) -> Map | None:

        self.map: Map = Map()
        self.lines: dict[
            str, tuple[list[str], Callable[[str], None | Zone]]
        ] = {
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

        except Exception as err:

            print(
                f"Caught Parsing Error for line:\n'{line}'"
            )

            if isinstance(err, ValidationError):

                for error in err.errors():
                    print(f" => {error['msg']}")

            else:

                print(f" => {err}")

            return None

        else:

            for parameter in self.lines.values():

                for definition in parameter[0]:
                    parameter[1](definition)

            try:

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

            except ValueError as ve:

                print(f"Caught Parsing Error: {ve}")
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
    def parse_hub_metadata(params: list[str]) -> tuple[str, str, int]:

        if len(params) < 3:
            raise ValueError(
                "Missing definition parameters for the hub\n"
                "Parameters required are the hub's name and coordinates"
            )

        zone: str = "normal"
        color: str = "\x1B[37m"
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

                # color = match.group(2)
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

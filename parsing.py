import re
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self as self


class Connection:

    def __init__(
        self,
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

        self.zone1: "Zone" = zone1
        self.zone2: "Zone" = zone2
        self.max_link_capacity: int = max_link_capacity


class Zone(BaseModel):

    name: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    zone_type: str = Field(default="normal")
    color: str | None = Field(default=None)
    max_drones: int = Field(default=1, gt=0)
    connections: list = []

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

    def add_connection(self, new_connection: "Zone", max_cap: int) -> None:

        for connection in self.connections:

            if connection.zone2.name == new_connection.name:

                raise ValueError(
                    f"Connection between '{self.name}' "
                    f"and '{new_connection.name}' "
                    "already exists!"
                )

        self.connections.append(Connection(
            self,
            new_connection,
            max_cap
        ))


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

    def validate_end_hub(self, end_hub: str) -> None:

        if hasattr(self, "end_hub"):

            raise ValueError(
                "End hub is already defined"
            )

        self.end_hub = self.add_hub(end_hub)

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

        fst_zone.add_connection(scd_zone, con_metadata)
        scd_zone.add_connection(fst_zone, con_metadata)

    def find_hub(self, hub_name: str) -> Zone:

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

            if not hub_params[1].isdigit() or not hub_params[2].isdigit():

                raise ValueError(
                    f"Invalid coordinates '({hub_params[1]}, {hub_params[2]})' "
                    f"for hub '{hub_params[0]}'\n"
                    "Coordinates must be positive integers"
                )

            if (int(hub_params[1]), int(hub_params[2])) == (hub.x, hub.y):

                raise ValueError(
                    f"Coordinates for hub '{hub_params[0]}' "
                    f"are the same as hub '{hub.name}'\n"
                    "Each zone must have unique coordinates"
                )

        metadata: tuple[str, str | None, int] = MapParser.parse_hub_metadata(hub_params)

        hub_created: Zone = Zone(
            name=hub_params[0],
            x=int(hub_params[1]),
            y=int(hub_params[2]),
            zone_type=metadata[0],
            color=metadata[1],
            max_drones=metadata[2],
            connections=[]
        )
        print(f"successfully created hub {hub_created.name}")

        self.hubs.append(hub_created)

        return hub_created


class MapParser:

    def parse_map(self, filename: str) -> Map:

        self.map: Map = Map()

        try:

            with open(filename) as map_file:

                for line in map_file:

                    if not line.startswith("#") and line.strip():

                        self.parse_line(line.strip())

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
                "Caught Parsing Error "
                f"for line '{line.strip()}':"
            )

            if err.__class__.__name__ == "ValidationError":

                for error in err.errors():
                    print(error["msg"])

            else:

                print(err)

        else:

            return self.map

    def parse_line(self, line: str) -> None:

        if not (match := re.match("([a-z_]+): (.+)", line, re.I)):

            raise ValueError(
                f"Invalid format for line '{line}'\n"
                "Format must be '<parameter>: <definition>'"
            )

        parameter: str = match.group(1)

        if parameter == "nb_drones":

            self.map.validate_nb_drones(match.group(2))

        elif parameter == "start_hub":

            self.map.validate_start_hub(match.group(2))

        elif parameter == "end_hub":

            self.map.validate_end_hub(match.group(2))

        elif parameter == "hub":

            self.map.add_hub(match.group(2))

        elif parameter == "connection":

            self.map.validate_connection(match.group(2))

        else:

            raise ValueError(
                f"Invalid parameter type '{parameter}'\n"
                "Parameter must be one of 'nb_drones', 'start_hub', "
                "'end_hub', 'hub', or 'connection'"
            )

    @staticmethod
    def parse_hub_metadata(params: list[str]) -> tuple[str, str | None, int]:

        zone: str = "normal"
        color: str | None = None
        max_drones: int = 1

        zone_defined: bool = False
        color_defined: bool = False
        max_drones_defined: bool = False

        if len(params) > 3:

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


if __name__ == "__main__":

    import sys

    if len(sys.argv) == 2:

        map_parser: MapParser = MapParser()
        drone_map: Map = map_parser.parse_map(sys.argv[1])

    else:

        print("Invalid number of arguments provided, no map given to parse")

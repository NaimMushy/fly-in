import re
import time
from rich.color import Color, ColorParseError
from typing import Callable
from pydantic import ValidationError
from .zones import Zone, Connection


class FormatError(Exception):

    def __init__(self, msg: str) -> None:

        self.msg: str = msg


class MissingValueError(Exception):

    def __init__(self, msg: str) -> None:

        self.msg: str = msg


class UndefinedError(Exception):

    def __init__(self, msg: str) -> None:

        self.msg: str = msg


class RedefinedError(Exception):

    def __init__(self, msg: str) -> None:

        self.msg: str = msg


class Map:

    """

    A class representing a drone Map with zones and connections.

    """

    def validate_nb_drones(self, nb_drones: str) -> None:

        """

        Verifies and validates the number of drones given.

        Parameters
        ----------
        nb_drones : str
            A string giving the number of drones.

        Raises
        ------
        RedefinedError
            If the attribute nb_drones has already been defined.
        ValueError
            If the value for nb_drones is inferior to 1.

        """

        if hasattr(self, "nb_drones"):

            raise RedefinedError(
                "Number of drones already defined!"
            )

        self.nb_drones: int = int(nb_drones)

        if self.nb_drones < 1:

            raise ValueError(
                f"Invalid value '{nb_drones}' for number of drones\n"
                "Must be a positive integer"
            )

    def validate_start_hub(self, start_hub: str) -> None:

        """

        Verifies and validates the start hub given.

        Parameters
        ----------
        start_hub : str
            The name of the starting hub of the simulation.

        Raises
        ------
        RedefinedError
            If the attribute start_hub has already been defined.
        ValueError
            If the value for the drone capacity
            is inferior to the total number of drones.
        ValueError
            If the type of the starting hub is blocked.

        """

        if hasattr(self, "start_hub"):

            raise RedefinedError(
                "Start hub is already defined"
            )

        self.start_hub: Zone = self.add_hub(start_hub)

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

        """

        Verifies and validates the end hub given.

        Parameters
        ----------
        end_hub : str
            The name of the arrival hub of the simulation.

        Raises
        ------
        RedefinedError
            If the attribute end_hub has already been defined.
        ValueError
            If the type of the ending hub is blocked.

        """

        if hasattr(self, "end_hub"):

            raise RedefinedError(
                "End hub is already defined"
            )

        self.end_hub: Zone = self.add_hub(end_hub)

        if self.end_hub.zone_type == "blocked":
            raise ValueError(
                "The end hub should not be a blocked zone"
            )

    def validate_connection(self, new_connection: str) -> None:

        """

        Verifies and validates the new connection
        between two hubs given as parameter.

        Parameters
        ----------
        new_connection : str
            The name of the connection between two hubs of the map.

        Raises
        ------
        UndefinedError
            If no hubs have been defined yet.
        MissingValueError
            If the connection does not have parameters to define it.
        FormatError
            If the parameters' format does not correspond to the expected.
        UndefinedError
            If the hubs given are invalid (i.e. if one was not created).

        """

        if not hasattr(self, "hubs") or not self.hubs:

            raise UndefinedError(
                "No hubs have been defined, "
                f"impossible to create connection '{new_connection}'"
            )

        connection_params: list[str] = new_connection.strip().split()

        if not connection_params:

            raise MissingValueError(
                "No definition provided for a connection"
            )

        con_zones: list[str] = connection_params[0].strip().split("-")
        con_metadata: int = MapParser.parse_con_metadata(connection_params)

        if len(con_zones) != 2:

            raise FormatError(
                f"Invalid connection format '{connection_params[0]}'\n"
                "Format must be '<zone1>-<zone2> [metadata](optional)'"
            )

        fst_zone: Zone | None = self.find_hub(con_zones[0])
        scd_zone: Zone | None = self.find_hub(con_zones[1])

        if not fst_zone:

            raise UndefinedError(
                f"Invalid hub {con_zones[0]} given "
                f"for connection '{connection_params[0]}'\n"
                "This hub has not yet been defined"
            )

        if not scd_zone:

            raise UndefinedError(
                f"Invalid hub {con_zones[1]} given "
                f"for connection '{connection_params[0]}'\n"
                "This hub has not yet been defined"
            )

        if not hasattr(self, "connections"):
            self.connections: list[Connection] = []

        connection: Connection = Connection(
            name=connection_params[0],
            zone1=fst_zone,
            zone2=scd_zone,
            max_link_capacity=con_metadata
        )
        self.connections.append(connection)
        fst_zone.add_connection(connection, scd_zone.name)
        scd_zone.add_connection(connection, fst_zone.name)

    def find_hub(self, hub_name: str) -> Zone | None:

        """

        Finds a certain hub in the map given its name.

        Parameters
        ----------
        hub_name : str
            The name of the hub to find.

        Returns
        -------
        Zone | None
            The hub found if it exists, otherwise None.

        """

        if hasattr(self, "hubs"):

            for hub in self.hubs:

                if hub.name == hub_name:

                    return hub

        print(f"No hub {hub_name} found\n")

        return None

    def add_hub(self, new_hub: str) -> Zone:

        """

        Verifies and adds a new hub to the map if it passes the checks.

        Parameters
        ----------
        new_hub : str
            The name of the new hub to add to the map.

        Returns
        -------
        Zone
            The hub created.

        Raises
        ------
        MissingValueError
            If the zone does not have parameters to define it.
        FormatError
            If the parameters' format does not correspond to the expected.
        ValueError
            If a parameter given is the same as another hub's.

        """

        hub_params: list[str] = new_hub.strip().split()

        if len(hub_params) < 3:

            raise MissingValueError(
                f"Invalid zone definition '{new_hub}' for hub\n"
                "Zone definition must contain at least a name and coordinates"
            )

        if len(hub_params) > 6:

            raise FormatError(
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

        self.hubs.append(hub_created)

        return hub_created


class MapParser:

    """

    A class used to parse the map data given and create a new map.

    """

    def __init__(self) -> None:

        """

        Initializes the attribute of a MapParser object.

        """

        self.already_parsed: dict[str, Map] = {}

    def parse_map(self, filename: str) -> Map | None:

        """

        Parses the map data of the file provided
        and creates a new map if it is valid.

        Parameters
        ----------
        filename : str
            The path to the file that contains the map data.

        Returns
        -------
        Map | None
            The new map created if the data is valid, otherwise None.

        Raises
        ------
        ValueError
            If the first line of the map file
            is not defining the number of drones.
        MissingValueError
            If there are missing key attributes not provided in the map file.

        """

        if filename in self.already_parsed.keys():
            return self.already_parsed[filename]

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

        print(end=f"\nParsing '{filename}' ")
        for _ in range(3):

            for _ in range(3):

                print(end='.', flush=True)
                time.sleep(0.5)

            print(end='\b\b\b', flush=True)
            print(end='   ', flush=True)
            print(end='\b\b\b', flush=True)

        print("\n")

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

            if isinstance(err, OSError):
                print(f" => {err}")
                return None

            print(
                f"Caught {err.__class__.__name__} for line:\n"
            )

            if isinstance(err, ValidationError):

                for error in err.errors():
                    print(f" => {error['msg']}")

            else:

                print(f" => {err}")

            return None

        else:

            try:

                for parameter in self.lines.values():

                    for definition in parameter[0]:
                        parameter[1](definition)

                if not hasattr(self.map, "start_hub"):

                    raise MissingValueError(
                        "Missing start hub!"
                    )

                if not hasattr(self.map, "end_hub"):

                    raise MissingValueError(
                        "Missing end hub!"
                    )

                if not hasattr(self.map, "nb_drones"):

                    raise MissingValueError(
                        "Missing number of drones!"
                    )

            except Exception as err:

                print(f"Caught {err.__class__.__name__}: {err}")
                return None

            else:

                self.already_parsed[filename] = self.map

                return self.map

    def parse_line(self, line: str) -> None:

        """

        Parses one line of the file opened and verifies its format and content.

        Parameters
        ----------
        line : str
            The line to parse and validate.

        Raises
        ------
        FormatError
            If the line's format does not correspond to the expected.
        ValueError
            If the type of the parameter for the line is invalid.

        """

        if not (match := re.match("([a-z_]+): (.+)", line, re.I)):

            raise FormatError(
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

        self.lines[parameter][0].append(match.group(2).strip())

    @staticmethod
    def parse_hub_metadata(params: list[str]) -> tuple[str, str, int]:

        """

        Parses the metadata contained in the data given as parameters
        and extracts it if it is valid.

        Parameters
        ----------
        params : list[str]
            The list of parameters of the hub after parsing the line.

        Returns
        -------
        tuple[str, str, int]
            The zone type, the color, and maximum number of drones of the hub.

        Raises
        ------
        MissingValueError
            If the key parameters defining the zone are not present.
        FormatError
            If the metadata's format does not correspond to the expected.
        RedefinedError
            If the parameter being defined has already been set.
        ValueError
            If the type of the parameter given as metadata is invalid.

        """

        if len(params) < 3:
            raise MissingValueError(
                "Missing definition parameters for the hub\n"
                "Parameters required are the hub's name and coordinates"
            )

        zone: str = "normal"
        color: str = "white"
        max_drones: int = 1

        zone_defined: bool = False
        color_defined: bool = False
        max_drones_defined: bool = False

        if len(params) == 3:
            return (zone, color, max_drones)

        if not (params[3].startswith("[") and params[-1].endswith("]")):

            raise FormatError(
                f"Invalid metadata format in zone definition '{params}'\n"
                "Metadata must be incased in brackets '[]'"
            )

        params[3] = params[3].replace("[", "", 1)
        params[-1] = params[-1].replace("]", "", 1)

        for p in range(3, len(params)):

            if not (match := re.match("([a-z_]+)=(.+)", params[p], re.I)):

                raise FormatError(
                    f"Invalid format for metadata '{params[p]}'\n"
                    "Metadata must be of '<parameter>=<value>' format"
                )

            if match.group(1) == "zone":

                if zone_defined:

                    raise RedefinedError(
                        f"Invalid metadata '{params[p]}'\n"
                        "Zone type is already defined"
                    )

                zone = match.group(2)
                zone_defined = True

            elif match.group(1) == "color":

                if color_defined:

                    raise RedefinedError(
                        f"Invalid metadata '{params[p]}'\n"
                        "Color for the zone is already defined"
                    )

                try:
                    color_parsed: Color = Color.parse(match.group(2))

                except ColorParseError:

                    try:
                        color_parsed = Color.parse(match.group(2) + "1")

                    except ColorParseError:

                        if match.group(2) == "rainbow":
                            color = match.group(2)

                        color_defined = True
                        continue

                color = color_parsed.name
                color_defined = True

            elif match.group(1) == "max_drones":

                if max_drones_defined:

                    raise RedefinedError(
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

        """

        Parses the connection metadata contained in the data given
        and extracts it.

        Parameters
        ----------
        con_params : list[str]
            The connection parameters after the line was parsed.

        Returns
        -------
            The maximum number of drones (drone capacity)
            that can go through the connection at the same time.

        Raises
        ------
        FormatError
            If the metadata's format does not correspond to the expected.
        ValueError
            If the type of the parameter given as metadata is invalid.

        """

        max_cap: int = 1

        if len(con_params) > 2:

            raise FormatError(
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

                raise FormatError(
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

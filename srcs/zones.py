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
        self.wish_to_occupy: list = []
        self.occupied: list = []


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

    def add_connection(self, new_connection: "Zone", max_cap: int) -> None:

        if new_connection.name in self.connections.keys():

            raise ValueError(
                f"Connection between '{self.name}' "
                f"and '{new_connection.name}' "
                "already exists!"
            )

        self.connections[new_connection.name] = Connection(
            self,
            new_connection,
            max_cap
        )

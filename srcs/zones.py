from pydantic import BaseModel, Field, model_validator
from typing import Any as any
from typing_extensions import Self as self


class Connection(BaseModel):

    name: str
    zone1: "Zone"
    zone2: "Zone"
    max_link_capacity: int = Field(ge=1)
    wish_to_occupy: list[any] = Field(default=[])
    occupied: list[any] = Field(default=[])

    @model_validator(mode="after")
    def validate_zones(self) -> self:

        if self.zone1 is None or self.zone2 is None:

            raise ValueError(
                "A zone for a connection cannot be None\n"
            )

        if self.zone1 == self.zone2:

            raise ValueError(
                "Zones cannot be the same for a connection\n"
            )

        return self

    def free_spaces(self) -> int:

        if not self.occupied:
            return 0
        return len([
            drone for drone in self.occupied
            if drone.is_next_step_accessible(drone.path_to_follow)
        ])

    def calculate_wait_cost(self, drone_id: int) -> int:

        cost: int = 1
        for drone_wish in self.wish_to_occupy:
            if drone_wish.id == drone_id:
                break
            cost += 1
        return abs(
            cost - (self.max_link_capacity - len(self.occupied))
        ) - self.free_spaces()

    def is_accessible(self, drone_id: int) -> bool:

        space_remaining: int = self.max_link_capacity - len(self.occupied)

        return (space_remaining > 0 and (
            len(self.wish_to_occupy) < space_remaining
            or drone_id in [
                drone.id
                for drone in self.wish_to_occupy[:space_remaining]
            ]
        ))


class Zone(BaseModel):

    name: str
    x: int
    y: int
    zone_type: str = Field(default="normal")
    color: str = Field(default="\x1B[37m")
    max_drones: int = Field(default=1, gt=0)
    connections: dict[str, Connection] = Field(default={})
    wish_to_occupy: list[any] = Field(default=[])
    occupied: list[any] = Field(default=[])

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
        self,
        new_connection: Connection,
        neighbor: str
    ) -> None:

        if neighbor in self.connections.keys():

            raise ValueError(
                f"Connection between '{self.name}' "
                f"and '{neighbor}' "
                "already exists!"
            )

        self.connections[neighbor] = new_connection

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

    def calculate_wait_cost(self, drone_id: int) -> int:

        cost: int = 1
        for drone_wish in self.wish_to_occupy:
            if drone_wish.id == drone_id:
                break
            cost += 1
        return abs(
            cost - (self.max_drones - len(self.occupied))
        ) - self.free_spaces()

    def is_accessible(self, drone_id: int) -> bool:

        space_remaining: int = self.max_drones - len(self.occupied)

        return (space_remaining > 0 and (
            len(self.wish_to_occupy) < space_remaining
            or drone_id in [
                drone.id
                for drone in self.wish_to_occupy[:space_remaining]
            ]
        ))

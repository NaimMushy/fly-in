from pydantic import BaseModel, Field, model_validator
from typing import Any as any
from typing_extensions import Self as self


class Connection(BaseModel):

    """

    A class representing a connection between two zones.

    """

    name: str
    zone1: "Zone"
    zone2: "Zone"
    max_link_capacity: int = Field(default=1, ge=0)
    wish_to_occupy: list[any] = Field(default=[])
    occupied: list[any] = Field(default=[])

    @model_validator(mode="after")
    def validate_zones(self) -> self:

        """

        A validator used to verify the two zones given for the connection.

        """

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

        """

        Calculates how many drones will be able to go through the connection
        at the following turn.

        Returns
        -------
        int
            The number of drones able to pass through
            the connection at the next turn.

        """

        if not self.occupied:
            return 0

        return len([
            drone for drone in self.occupied
            if drone.current_zone != self
        ])

    def calculate_wait_cost(self, drone_id: int) -> int:

        """

        Calculates the added cost of waiting for the drone given
        that wishes to go through this connection.

        Parameters
        ----------
        drone_id : int
            The identifiant of the drone wishing to pass through.

        Returns
        -------
        int
            The waiting cost for the drone.

        """

        cost: int = 1

        for drone_wish in self.wish_to_occupy:

            if drone_wish.id == drone_id:
                break
            cost += 1

        return max(
            0,
            abs(
                cost - (self.max_link_capacity - len(self.occupied))
            ) - self.free_spaces()
        )

    def is_accessible(self, drone_id: int) -> bool:

        """

        Determines whether or not the connection is accessible
        for the drone given.

        Parameters
        ----------
        drone_id : int
            The identifiant of the drone wishing to go through.

        Returns
        -------
        bool
            True if the connection is accessible, False otherwise.

        """

        space_remaining: int = self.max_link_capacity - len(self.occupied)

        return (space_remaining > 0 and (
            len(self.wish_to_occupy) < space_remaining
            or drone_id in [
                drone.id
                for drone in self.wish_to_occupy[:space_remaining]
            ]
        ))


class Zone(BaseModel):

    """

    A class representing a zone of the simulation.

    """

    name: str
    x: int
    y: int
    zone_type: str = Field(default="normal")
    color: str = Field(default="white")
    max_drones: int = Field(default=1, ge=0)
    connections: dict[str, Connection] = Field(default={})
    wish_to_occupy: list[any] = Field(default=[])
    occupied: list[any] = Field(default=[])

    @model_validator(mode="after")
    def validate_name(self) -> self:

        """

        A validator that verifies if the name given for the zone is valid.

        """

        if " " in self.name or "-" in self.name:

            raise ValueError(
                f"Invalid name for the zone '{self.name}'\n"
                "There must not be spaces or dashes in a zone's name"
            )

        return self

    @model_validator(mode="after")
    def validate_zone_type(self) -> self:

        """

        A validator that verifies if the type given for the zone is valid.

        """

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

        """

        A validator that verifies if the color given for the zone is valid.
        """
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

        """

        Verifies if the new connection is valid
        and adds it to the zone's connections.

        Parameters
        ----------
        new_connection : Connection
            The connection to add.
        neighbor : str
            The name of the neighbor zone sharing the connection.

        """

        if neighbor in self.connections.keys():

            raise ValueError(
                f"Connection between '{self.name}' "
                f"and '{neighbor}' "
                "already exists!"
            )

        self.connections[neighbor] = new_connection

    def free_spaces(self) -> int:

        """

        Calculates how many drones will be able to occupy the zone
        at the following turn.

        Returns
        -------
        int
            The number of drones able to occupy the zone at the next turn.

        """

        if not self.occupied:
            return 0

        return len([
            drone for drone in self.occupied
            if drone.is_next_step_accessible(drone.path_to_follow)
        ])

    def calculate_wait_cost(self, drone_id: int) -> int:

        """

        Calculates the added cost of waiting for the drone given
        that wishes to occupy this zone.

        Parameters
        ----------
        drone_id : int
            The identifiant of the drone wishing to occupy the zone.

        Returns
        -------
        int
            The waiting cost for the drone.

        """

        cost: int = 1

        for drone_wish in self.wish_to_occupy:

            if drone_wish.id == drone_id:
                break

            cost += 1

        return max(
            0,
            abs(
                cost - (self.max_drones - len(self.occupied))
            ) - self.free_spaces()
        )

    def is_accessible(self, drone_id: int) -> bool:

        """

        Determines whether or not the zone is accesssible
        for the drone given.

        Parameters
        ----------
        drone_id : int
            The identifiant of the drone wishing to occupy the zone.

        Returns
        -------
        bool
            True if the zone is accessible, False otherwise.

        """

        space_remaining: int = self.max_drones - len(self.occupied)

        return (space_remaining > 0 and (
            len(self.wish_to_occupy) < space_remaining
            or drone_id in [
                drone.id
                for drone in self.wish_to_occupy[:space_remaining]
            ]
        ))

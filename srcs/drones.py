from .zones import Zone, Connection
from .map_data import Map
from .path import Path, PathFinder
from .state import State
import time


class Drone:

    """

    A class representing a drone in the simulation.

    """

    def __init__(
        self,
        drone_id: int,
        start_zone: Zone,
        end_hub: Zone
    ) -> None:

        """

        Initializes the attributes of a Drone object.

        Parameters
        ----------
        drone_id : int
            The identifiant of the drone.
        start_zone : Zone
            The zone in which the drone is at the beginning.
        end_hub : Zone
            The arrival zone of the simulation.

        """

        self.id: int = drone_id
        self.current_zone: Zone | Connection = start_zone
        self.goal: Zone = end_hub
        self.occupying: list[Zone | Connection] = [self.current_zone]
        self.waiting: bool = False
        self.turns: int = 0

    def update_intent(self) -> None:

        """

        Updates the intent of the drone regarding the following turn,
        where it wishes to go next.

        """

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

        """

        The action taken by the drone during the current turn.
        If the next zone of the drone's path is accessible, it moves,
        otherwise it stays put waiting.

        """

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

        """

        Determines whether or not the next step in the drone's path
        is accessible.

        Parameters
        ----------
        path : Path
            The path followed by the drone.

        Returns
        -------
        bool
            True if the next step is accessible, False otherwise.

        """

        if (
            isinstance(self.current_zone, Connection)
            or (
                hasattr(self, "next_zone")
                and (
                    self.current_zone == self.next_zone
                    or self.next_zone == self.goal
                )
            )
        ):
            return True

        next_step: Zone = path.path[0]
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
            connection.is_accessible(self.id)
            and next_step.is_accessible(self.id)
        )

    def free_connections(self) -> None:

        """

        Removes the drone from the connections it occupied
        while it was moving between zones.

        """

        connections_occupied: list[Connection] = [
            zone for zone in self.occupying
            if isinstance(zone, Connection)
        ]
        for con in connections_occupied:
            con.occupied.remove(self)
            self.occupying.remove(con)

    def reevaluate_drone_path(self) -> None:

        """

        Reevaluates the best path for the drone to follow.

        """

        if isinstance(self.current_zone, Connection):
            return

        self.free_connections()

        possible_paths: list[Path] = PathFinder.calculate_paths(
            self.current_zone,
            [],
            0,
            self.goal,
            []
        )

        for path in possible_paths:

            if len(path.path) > 1:
                path.path = path.path[1:]

            if not self.is_next_step_accessible(path):

                if not path.path[0].connections[
                    self.current_zone.name
                ].is_accessible(self.id):

                    path.cost += path.path[0].connections[
                        self.current_zone.name
                    ].calculate_wait_cost(self.id)

                elif not path.path[0].is_accessible(self.id):

                    path.cost += path.path[0].calculate_wait_cost(self.id)

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


class DroneMonitor:

    """

    A class used to monitor all the drones in the simulation.

    """

    def __init__(self, drone_map: Map) -> None:

        """

        Initializes the attributes of a DroneMonitor object.

        Parameters
        ----------
        drone_map : Map
            The map that contains all the hubs and connections.

        """

        self.drone_map: Map = drone_map
        self.drones: list[Drone] = []
        self.drones_delivered: list[Drone] = []
        self.turns: int = 0

        for drone_id in range(1, self.drone_map.nb_drones + 1):

            new_drone: Drone = Drone(
                drone_id,
                self.drone_map.start_hub,
                self.drone_map.end_hub
            )
            self.drones.append(new_drone)
            self.drone_map.start_hub.occupied.append(new_drone)

    @property
    def avg(self) -> int:

        """

        A property of the drone monitor
        to calculate the average number of turns per drone.

        Returns
        -------
        int
            The average number of turns per drone calculated.

        """

        return (
            sum(drone.turns for drone in self.drones_delivered)
            // self.drone_map.nb_drones
        )

    def update_drones(self, state: State) -> None:

        """

        Updates all the drones remaining in the simulation,
        first reevaluating their paths, then making them act,
        and then checking whether or not they arrived at destination.

        Parameters
        ----------
        state : State
            The current state of the simulation
            that needs to be updated with the current simulation data.

        """

        for drone in self.drones:

            drone.reevaluate_drone_path()
            drone.turns += 1

        moving_drones: list[Drone] = []

        for drone in self.drones:

            if drone not in moving_drones:
                drone.turn_action()

                if drone.current_zone == drone.goal:

                    for occupying in drone.occupying:
                        occupying.occupied.remove(drone)
                    moving_drones.append(drone)

        moving_drones += [
            drone for drone in self.drones
            if drone not in moving_drones
            and not drone.waiting
        ]

        state.nb_drone_moved = len(moving_drones)

        for drone in self.drones:

            for occupied in drone.occupying:

                if (
                    isinstance(occupied, Connection)
                    and drone.next_zone.zone_type != "restricted"
                    or occupied == drone.goal
                ):
                    continue

                if occupied.name not in state.zones_occupied.keys():
                    state.zones_occupied[occupied.name] = []

                state.zones_occupied[occupied.name].append(drone.id)

        for drone in moving_drones:

            if drone != moving_drones[0]:
                state.drone_moves += " "

            state.drone_moves += f"D{drone.id}-{drone.current_zone.name}"

            if drone.current_zone == drone.goal:

                self.drones_delivered.append(drone)
                self.drones.remove(drone)

        state.drones_delivered = [drone.id for drone in self.drones_delivered]
        self.turns += 1

        time.sleep(0.1)

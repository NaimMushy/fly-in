from .zones import Zone, Connection
from .map_data import Map
from .path import Path, PathFinder
from .state import State


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

            # print(f"drone {self.id} can move to next zone\n")
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

            # print(f"drone {self.id} has to wait a turn\n")
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
            or self.current_zone == self.goal
            or (
                hasattr(self, "next_zone")
                and (
                    self.current_zone == self.next_zone or
                    self.current_zone == path.path[0]
                    or (
                        self.next_zone == self.goal
                        and self.current_zone.connections[
                            self.goal.name
                        ].is_accessible(self.id)
                    )
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

            # print(f"no spaces remaining in connection {connection.name} for drone {self.id}\n")
            if next_step.zone_type == "restricted":

                if (
                    len(connection.wish_to_occupy) < connection.free_spaces()
                    or self in connection.wish_to_occupy[
                        :connection.free_spaces()
                    ]
                ):
                    return True

            return connection.is_accessible(self.id)

        if ns_sp_rem == 0:

            # print(f"no spaces remaining in zone {next_step.name} for drone {self.id}\n")
            if next_step.zone_type == "restricted":

                if (
                    len(next_step.wish_to_occupy) < next_step.free_spaces()
                    or self in next_step.wish_to_occupy[
                        :next_step.free_spaces()
                    ]
                ):
                    return True

            return next_step.is_accessible(self.id)

        # print(f"connection accessible: {connection.is_accessible(self.id)}, zone accessible: {next_step.is_accessible(self.id)} for drone {self.id}\n")
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

    def reevaluate_drone_path(self, cache: dict[str, list[Path]]) -> None:

        """

        Reevaluates the best path for the drone to follow.

        """

        if isinstance(self.current_zone, Connection):
            return

        self.free_connections()

        cache_path: str = self.current_zone.name
        possible_paths: list[Path] = []
        if cache_path in cache.keys():
            possible_paths = [
                Path(list(p.path), p.cost) for p in cache[cache_path]
            ]
        else:
            possible_paths = PathFinder.calculate_paths(
                self.current_zone,
                self.goal
            )
            cache[cache_path] = [
                Path(list(p.path), p.cost) for p in possible_paths
            ]

        for path in possible_paths:

            if path.path[0] == self.current_zone:
                path.path = path.path[1:]

            if not self.is_next_step_accessible(path):

                if not path.path[0].connections[
                    self.current_zone.name
                ].is_accessible(self.id):

                    # print(f"connection {path.path[0].connections[self.current_zone.name].name} is not accessible for drone {self.id}! added cost: {path.path[0].connections[self.current_zone.name].calculate_wait_cost(self.id)}\n")
                    # print(f"connection occupied : {len(path.path[0].connections[self.current_zone.name].occupied)}")
                    # print("connection wish to occupy:", end="")
                    # for wto in path.path[0].connections[self.current_zone.name].wish_to_occupy:
                    #     print(f" {wto.id}", end="")
                    # print("\n")
                    path.cost += path.path[0].connections[
                        self.current_zone.name
                    ].calculate_wait_cost(self.id)

                elif not path.path[0].is_accessible(self.id):

                    # print(f"zone {path.path[0].name} is not accessible for drone {self.id}! added cost: {path.path[0].calculate_wait_cost(self.id)}\n")
                    path.cost += path.path[0].calculate_wait_cost(self.id)

            if path.path[0].zone_type == "priority":
                path.priority = True

        self.path_to_follow: Path = possible_paths[0]

        for path in possible_paths:

            if path.cost < self.path_to_follow.cost:
                self.path_to_follow = path

            elif (
                path.cost == self.path_to_follow.cost
                and path.priority and not self.path_to_follow.priority
            ):
                self.path_to_follow = path

        self.next_zone: Zone = self.path_to_follow.path[0]


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

    def update_order(self) -> list[Drone]:

        """

        Calculates the order in which the drones
        should be updated to avoid circular dependency
        for zone occupation or inefficient waiting.

        Returns
        -------
        list[Drone]
            The ordered drones for the monitor's updating.

        """

        visited_drones: set[Drone] = set()
        stack_occupancy: set[Drone] = set()
        order: list[Drone] = []

        for start_drone in self.drones:

            if start_drone in visited_drones:
                continue

            drone_stack: list[Drone] = [start_drone]

            while drone_stack:

                cur_drone: Drone = drone_stack[-1]

                if cur_drone in visited_drones:
                    drone_stack.pop()
                    continue

                if cur_drone not in stack_occupancy:

                    stack_occupancy.add(cur_drone)

                    to_explore: None | Zone | Connection = (
                        self.get_dependency(cur_drone)
                    )

                    if to_explore:

                        for neighbor in to_explore.occupied:

                            if (
                                neighbor == cur_drone
                                or neighbor in visited_drones
                            ):
                                continue

                            drone_stack.append(neighbor)

                else:

                    drone_stack.pop()
                    stack_occupancy.discard(cur_drone)
                    order.append(cur_drone)
                    visited_drones.add(cur_drone)

        return order

    def path_update(self) -> None:

        """

        Reevaluate paths for each drone,
        making sure the drones are updated in order of zone occupancy
        so that a drone can evaluate path cost correctly.

        """

        for d in self.drones:
            d.reevaluate_drone_path(self.path_cache)
            d.update_intent()

        ordered_drones: list[Drone] = self.update_order()
        updated: set[Drone] = set()

        for drone in ordered_drones:

            if drone in updated:
                continue

            drone.reevaluate_drone_path(self.path_cache)
            drone.update_intent()
            updated.add(drone)
            # print(f"updated path for drone {drone.id}\n")

        for check_drone in self.drones:

            if check_drone not in updated:

                check_drone.reevaluate_drone_path(self.path_cache)
                check_drone.update_intent()
                # print(f"updated path for drone {check_drone.id}\n")

    def action_update(self) -> None:

        """

        Make each drone execute their turn,
        making sure the drones are updated in order of zone occupancy
        so that a drone can evaluate zone accessibility correctly.

        """
        ordered_drones: list[Drone] = self.update_order()
        updated: set[Drone] = set()

        for drone in ordered_drones:

            if drone in updated:
                continue

            drone.turn_action()
            updated.add(drone)
            # print(f"updated action for drone {drone.id}\n")

        for check_drone in self.drones:

            if check_drone not in updated:

                check_drone.turn_action()
                # print(f"updated action for drone {check_drone.id}\n")

    @staticmethod
    def get_dependency(drone: Drone) -> None | Zone | Connection:

        """

        Search for a possible zone or connection
        dependency for the drone given,
        looking if the next step for the drone
        is already occupied by other drones
        that should be updated before it.

        Parameters
        ----------
        drone: Drone
            The drone for which to look for a dependency.

        Returns
        -------
        None | Zone | Connection
            The dependency zone in which other drones should be updated first
            if found, otherwise None.

        """

        if not hasattr(drone, "next_zone"):

            return None

        if (
            drone.next_zone.zone_type == "restricted"
            and not isinstance(drone.current_zone, Connection)
        ):
            connection: Connection = drone.next_zone.connections[
                drone.current_zone.name
            ]
            if (
                len(connection.occupied) > 0 or
                len(connection.wish_to_occupy) >= connection.max_link_capacity
            ):
                return connection

        elif (
            len(drone.next_zone.occupied) > 0
            and drone.next_zone != drone.goal
        ):
            return drone.next_zone

        return None

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

        for free_z in self.drone_map.hubs:

            free_z.wish_to_occupy = []

        for free_c in self.drone_map.connections:

            free_c.wish_to_occupy = []

        self.path_cache: dict[str, list[Path]] = {}

        self.path_update()
        # print("\n\n==== PATHS CHOSEN ====\n")
        # for drone in self.drones:
        #     print(f"DRONE {drone.id} :", end="")
        #     for z in drone.path_to_follow.path:
        #         print(f" {z.name}", end="")
        #     print(f" -> cost: {drone.path_to_follow.cost}\n")
        self.action_update()

        moving_drones: list[Drone] = []

        for drone in self.drones:

            if drone not in moving_drones and drone.current_zone == drone.goal:

                for occupying in drone.occupying:
                    occupying.occupied.remove(drone)
                moving_drones.append(drone)

            drone.turns += 1

        moving_drones += [
            drone for drone in self.drones
            if drone not in moving_drones
            and not drone.waiting
        ]

        state.nb_drone_moved = len(moving_drones)

        for drone in self.drones:

            for occupied in drone.occupying:

                if (
                    (
                        isinstance(occupied, Connection)
                        and drone.next_zone.zone_type != "restricted"
                    )
                    or occupied == drone.goal
                ):
                    continue

                if occupied.name not in state.zones_occupied.keys():
                    state.zones_occupied[occupied.name] = []

                state.zones_occupied[occupied.name].append(drone.id)

        state.drones_delivered = []
        goal_occupancy: list[int] = []

        for drone in moving_drones:

            if drone != moving_drones[0]:
                state.drone_moves += " "

            state.drone_moves += f"D{drone.id}-{drone.current_zone.name}"

            if drone.current_zone == drone.goal:

                goal_occupancy.append(drone.id)
                self.drones_delivered.append(drone)
                self.drones.remove(drone)

        if len(goal_occupancy) > 0:
            state.zones_occupied[self.drone_map.end_hub.name] = goal_occupancy

        state.drones_delivered = [d.id for d in self.drones_delivered]

        self.turns += 1
        state.turn = self.turns

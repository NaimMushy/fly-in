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

            # print(f"drone {self.id} can move to next zone {self.next_zone.name}")
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

            # print(f"drone {self.id} has to wait a turn")
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
        # print(f"drone {self.id} : next step = {next_step.name}")
        connection: Connection = next_step.connections[self.current_zone.name]
        ns_sp_rem: int = next_step.max_drones - len(
            next_step.occupied
        )
        con_sp_rem: int = connection.max_link_capacity - len(
            connection.occupied
        )

        if con_sp_rem == 0:

#             print(f"drone {self.id}, no space remaining in connection {connection.name}, next step: {next_step.name}")
#             if next_step.zone_type == "restricted":
# 
#                 print(f"connection occupied : {[do.id for do in connection.occupied]}\n")
#                 print(f"connection wish to occupy : {[d.id for d in connection.wish_to_occupy]}\n")
#                 print(f"connection free spaces : {connection.free_spaces()}\n")
#                 print(f"connection drones allowed : {[dr.id for dr in connection.wish_to_occupy[:connection.free_spaces()]]}\n")
#                 if (
#                     len(connection.wish_to_occupy) < connection.free_spaces()
#                     or self in connection.wish_to_occupy[
#                         :connection.free_spaces()
#                     ]
#                 ):
#                     print(f"drone {self.id} can go through the connection")
#                     return True
# 
#             return connection.is_accessible(self.id)
            return False

        if ns_sp_rem == 0:

            # print(f"drone {self.id}, no space remaining in zone {next_step.name}")
            if next_step.zone_type == "restricted":

                if (
                    len(next_step.wish_to_occupy) < next_step.free_spaces()
                    or self in next_step.wish_to_occupy[
                        :next_step.free_spaces()
                    ]
                ):
                    # print(f"drone {self.id} can go through the connection")
                    return True

            # return next_step.is_accessible(self.id)
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

    def reevaluate_drone_path(self, cache: dict[str, list[Path]]) -> None:

        """

        Reevaluates the best path for the drone to follow.

        """

        if isinstance(self.current_zone, Connection):
            # print(f"first step: {self.path_to_follow.path[0].name}")
            return

        self.free_connections()

        cache_path: str = self.current_zone.name
        possible_paths: list[Path] = []
        if cache_path in cache.keys():
            possible_paths = [Path(list(p.path), p.cost) for p in cache[cache_path]]
        else:
            possible_paths = PathFinder.calculate_paths(
                self.current_zone,
                self.goal
            )
            cache[cache_path] = [Path(list(p.path), p.cost) for p in possible_paths]

#         time.sleep(1)
#         if hasattr(self, "path_to_follow"):
#             print(f"old path to follow for drone {self.id}:", end="")
#             for p in self.path_to_follow.path:
#                 print(f" {p.name}", end="")
#             print()
#         time.sleep(1)
        for path in possible_paths:

            if len(path.path) > 1:
                path.path = path.path[1:]

            if not self.is_next_step_accessible(path):

                # print(f"next step is not accessible for drone {self.id}\n")
                if not path.path[0].connections[
                    self.current_zone.name
                ].is_accessible(self.id):

                    path.cost += path.path[0].connections[
                        self.current_zone.name
                    ].calculate_wait_cost(self.id)

                elif not path.path[0].is_accessible(self.id):

                    path.cost += path.path[0].calculate_wait_cost(self.id)

                # print(f"new cost of path : {path.cost}\n")

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

#         time.sleep(1)
#         print(f"new path to follow for drone {self.id}:", end="")
#         for p in self.path_to_follow.path:
#             print(f" {p.name}", end="")
#         print()
#         time.sleep(1)
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

    def recursive_path_update(
        self,
        current_drone: Drone,
        updated_drones: set[Drone]
    ) -> None:

        if current_drone in updated_drones:
            # print(f"drone {current_drone.id} has already been updated!")
            return

        # print(f"reevaluating path for drone {current_drone.id}...\n")
        current_drone.reevaluate_drone_path(self.path_cache)
        # print("finished reevaluating path!")

        if hasattr(current_drone, "next_zone"):

            to_explore: Zone | Connection | None = None

            if (
                current_drone.next_zone.zone_type == "restricted"
                and not isinstance(current_drone.current_zone, Connection)
                and (
                    len(current_drone.next_zone.connections[
                        current_drone.current_zone.name
                    ].occupied) > 0 or
                    len(current_drone.next_zone.connections[
                        current_drone.current_zone.name
                    ].wish_to_occupy) >= current_drone.next_zone.connections[
                        current_drone.current_zone.name
                    ].max_link_capacity
                )
            ):
                to_explore = current_drone.next_zone.connections[
                    current_drone.current_zone.name
                ]

            elif (
                len(current_drone.next_zone.occupied) > 0
                and current_drone.next_zone != current_drone.goal
            ):
                to_explore = current_drone.next_zone

            if to_explore:

                for neighbor_drone in to_explore.occupied:

                    if neighbor_drone == current_drone:
                        continue
                    # print(f"drone {current_drone.id} is trying to update neighbor {neighbor_drone.id}")
                    self.recursive_path_update(neighbor_drone, updated_drones)

        current_drone.reevaluate_drone_path(self.path_cache)
        current_drone.update_intent()
        updated_drones.add(current_drone)
        # print(f"adding drone {current_drone.id} to the updated drones after intent\n")

    def recursive_action_update(
        self,
        current_drone: Drone,
        updated_drones: set[Drone]
    ) -> None:

        if current_drone in updated_drones:
            # print(f"drone {current_drone.id} has already been updated!")
            return

        if hasattr(current_drone, "next_zone"):

            to_explore: Zone | Connection | None = None

            if (
                current_drone.next_zone.zone_type == "restricted"
                and not isinstance(current_drone.current_zone, Connection)
                and (
                    len(current_drone.next_zone.connections[
                        current_drone.current_zone.name
                    ].occupied) > 0 or
                    len(current_drone.next_zone.connections[
                        current_drone.current_zone.name
                    ].wish_to_occupy) >= current_drone.next_zone.connections[
                        current_drone.current_zone.name
                    ].max_link_capacity
                )
            ):
                to_explore = current_drone.next_zone.connections[
                    current_drone.current_zone.name
                ]
                # print(f"drone {current_drone.id} is trying to explore connection {to_explore.name}")

            elif (
                len(current_drone.next_zone.occupied) > 0
                and current_drone.next_zone != current_drone.goal
            ):
                to_explore = current_drone.next_zone

            if to_explore:

                for neighbor_drone in to_explore.occupied:

                    if neighbor_drone == current_drone:
                        continue
                    # print(f"drone {current_drone.id} is trying to update neighbor {neighbor_drone.id}")
                    self.recursive_action_update(neighbor_drone, updated_drones)

        current_drone.turn_action()
        updated_drones.add(current_drone)

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

        self.path_cache: dict[str, list[Path]] = {}
        # print("\n==== PATH UPDATE ====\n")
        updated_drones: set[Drone] = set()
        for drone in self.drones:
            self.recursive_path_update(drone, updated_drones)

        # print("\n==== ACTION UPDATE ====\n")
        updated_drones = set()
        for drone in self.drones:
            self.recursive_action_update(drone, updated_drones)

        moving_drones: list[Drone] = []

        for drone in self.drones:

            if drone not in moving_drones and drone.current_zone == drone.goal:

                for occupying in drone.occupying:
                    occupying.occupied.remove(drone)
                moving_drones.append(drone)

            drone.turns += 1

        # print(f"moving drones: {[d_m.id for d_m in moving_drones]}")
        moving_drones += [
            drone for drone in self.drones
            if drone not in moving_drones
            and not drone.waiting
        ]
        # print(f"updated drones: {[d.id for d in updated_drones]}")
        # print(f"moving drones: {[d_m.id for d_m in moving_drones]}")

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

        time.sleep(0.1)

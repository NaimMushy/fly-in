from .zones import Zone, Connection
from .path import Path, Pathfinder
from .parsing import Map
import time


class Drone:

    def __init__(
        self, drone_id: int,
        start_pos: Zone
    ) -> None:

        self.id: int = drone_id
        self.current_zone: Zone | Connection = start_pos
        self.waiting: bool = False

    def turn_action(self) -> None:

        if self not in self.next_zone.wish_to_occupy:
            self.next_zone.wish_to_occupy.append(self)
        if (
            self.next_zone.zone_type == "restricted"
            and not isinstance(self.current_zone, Connection)
            and self not in self.next_zone.connections[
                self.current_zone.name
            ].wish_to_occupy
        ):
            self.next_zone.connections[
                self.current_zone.name
            ].wish_to_occupy.append(self)
        if self.is_next_step_accessible(self.path_to_follow):
            self.waiting = False
            self.current_zone.occupied.remove(self)
            self.next_zone.wish_to_occupy.remove(self)
            if (
                self.next_zone.zone_type == "restricted"
                and not isinstance(self.current_zone, Connection)
            ):
                self.current_zone = self.next_zone.connections[
                    self.current_zone.name
                ]
            else:
                self.current_zone = self.next_zone
            self.current_zone.occupied.append(self)
        else:
            self.waiting = True

    def is_next_step_accessible(self, path: Path) -> bool:

        next_step: Zone = path.path[0]
        connection: Connection = next_step.connections[self.current_zone.name]

        if self.current_zone == connection:
            return True

        if connection.space_remaining == 0:
            return False

        if next_step.space_remaining == 0:

            if next_step.zone_type == "restricted":
                free_spaces: int = len([
                    drone.is_next_step_accessible(drone.path_to_follow)
                    for drone in next_step.occupied
                ])
                if self in next_step.wish_to_occupy[free_spaces:]:
                    return True

            return False

        if self in connection.wish_to_occupy[connection.space_remaining:]:
            return True

        else:
            return False

        if self in next_step.wish_to_occupy[next_step.space_remaining:]:
            return True

        return False

    def reevaluate_drone_path(self, pathfinder: Pathfinder) -> None:

        if isinstance(self.current_zone, Connection) or self.waiting:
            return

        possible_paths: list[Path] = pathfinder.calculate_paths(
            self.current_zone,
            Path(),
            pathfinder.map.end_hub,
            []
        )

        for path in possible_paths:

            if len(path.path) > 1:
                path.path = path.path[1:]
            if not self.is_next_step_accessible(path):
                path.cost += 1
            if path.path[1].zone_type == "priority":
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


class DroneMonitor:

    def __init__(self, drone_map: Map, pathfinder: Pathfinder) -> None:

        self.drone_map: Map = drone_map
        self.pathfinder: Pathfinder = pathfinder
        self.drones: list[Drone] = []

        for drone_id in range(1, self.drone_map.nb_drones + 1):

            self.drones.append(Drone(
                drone_id,
                self.drone_map.start_hub
            ))

    def update_drones(self) -> None:

        for drone in self.drones:

            drone.reevaluate_drone_path(self.pathfinder)
            drone.turn_action()
            if not drone.waiting:
                print(f"D{drone.id}-{drone.current_zone.name}", end="")
            if drone != self.drones[0]:
                print(" ", end="")
            if drone.current_zone == self.drone_map.end_hub:
                drone.current_zone.occupied.remove(drone)
                self.drones.remove(drone)

        print()
        time.sleep(2)

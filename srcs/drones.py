from .parsing import Zone, Connection, Map


class Path:

    def __init__(self) -> None:

        self.path: list[Zone] = []
        self.cost: int = 0
        self.priority: bool = False


class Pathfinder:

    def __init__(self, drone_map: Map) -> None:

        self.map: Map = drone_map
        if not self.calculate_paths(
            self.map.start_hub,
            Path(),
            self.map.end_hub,
            []
        ):
            raise ValueError(
                "No paths found! Map considered invalid"
            )

    def calculate_paths(
        self,
        current_hub: Zone,
        current_path: Path,
        dest: Zone,
        possible_paths: list[Path]
    ) -> list[Path]:

        if current_hub.zone_type == "blocked":

            return possible_paths

        current_path.cost += 1

        if current_hub.zone_type == "restricted":
            current_path.cost += 1

        current_path.path.append(current_hub)

        if current_hub == dest:

            return possible_paths + [current_path]

        for branch in current_hub.connections:

            return self.calculate_paths(
                branch,
                current_path,
                dest,
                possible_paths
            )

        return possible_paths


class Drone:

    def __init__(
        self, drone_id: int,
        start_pos: Zone,
        path_to_follow: Path
    ) -> None:

        self.id: int = drone_id
        self.current_zone: Zone | Connection = start_pos
        self.path_to_follow: Path = path_to_follow
        self.waiting: bool = False

    def turn_action(self, pathfinder: Pathfinder) -> None:

        # this should be put in the main loop
        self.reevaluate_drone_path(pathfinder)
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

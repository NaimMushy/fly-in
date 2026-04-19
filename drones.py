class Drone:

    def __init__(self, drone_id: int, start_pos: tuple[int, int], path_to_follow: Path) -> None:

        self.id: int = drone_id
        self.pos: tuple[int, int] = start_pos
        self.waiting: bool = False
        self.next_dest: tuple[int, int] = start_pos
        self.path_to_follow: Path = path_to_follow


"""
ce que j'ai besoin de savoir pour mes drones:

    - leur position
    - s'ils attendent ou pas
    - leur hub actuel?
    - leur prochaine destination?
"""


class Path:

    def __init__(self) -> None:

        self.path: list[Zone] = []
        self.cost: int = 0


class Pathfinder:

    def __init__(self, drone_map: Map) -> None:

        self.map: Map = drone_map
        self.paths: list[Path] = self.calculate_paths(
            self.map.start_hub,
            Path(),
            self.map.end_hub,
            []
        )

    def calculate_paths(self, current_hub: Zone, current_path: Path, dest: Zone, possible_paths: list[Path]) -> list[Path]:

        if current_hub.zone_type == "blocked":

            return possible_paths

        current_path.cost += 1

        if current_hub.zone_type == "restricted":

            current_path.cost += 1

        if current_hub == dest:

            return possible_paths + current_path

        for branch in current_path.connections:

            return self.calculate_paths(branch, current_path, dest, possible_paths)

    def reevaluate_drone_path(self, drone: Drone) -> None:

        possible_paths: list[Path] = self.calculate_paths(
            drone.current_zone,
            Path(),
            self.map.end_hub,
            []
        )

        for path in possible_paths:

            if len(path.path) >= 2 and path.path[1].occupied == path.path[1].max_drones:
                path.cost += 1

        if len(drone.path_to_follow.path) >= 2 and drone.path_to_follow.path[1].occupied == drone.path_to_follow.path[1].max_drones:
            drone.path_to_follow.cost += 1

        for path in possible_paths:

            if path.priority > drone.path_to_follow.priority:
                drone.path_to_follow = path

            elif path.cost < drone.path_to_follow.cost:
                drone.path_to_follow = path

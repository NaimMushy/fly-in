class Drone:

    def __init__(self, drone_id: int, start_pos: tuple[int, int]) -> None:

        self.id: int = drone_id
        self.pos: tuple[int, int] = start_pos
        self.waiting: bool = False
        self.next_dest: tuple[int, int] = start_pos


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
            self.map.end_hub
        )

    def calculate_paths(self, current_hub: Zone, current_path: Path, dest: Zone) -> list[Path]:

        if current_hub.zone_type == "blocked":

            return self.paths

        current_path.cost += 1

        if current_hub.zone_type == "restricted":

            current_path.cost += 1

        if current_hub == dest:

            return self.paths + current_path

        for branch in current_path.connections:

            return self.calculate_paths(branch, current_path, dest)

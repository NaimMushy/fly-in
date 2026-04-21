from .parsing import Zone, Map


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

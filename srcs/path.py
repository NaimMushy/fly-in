from .zones import Zone


class Path:

    def __init__(self, path: list[Zone], cost: int) -> None:

        self.path: list[Zone] = path
        self.cost: int = cost
        self.priority: bool = False

    def display_path(self) -> None:

        print("path: ", end="")
        for zone in self.path:

            print(f"{zone.name} - ", end="")

        print(f"cost={self.cost}")


class PathFinder:

    @staticmethod
    def calculate_paths(
        current_hub: Zone,
        current_path: list[Zone],
        cost: int,
        dest: Zone,
        possible_paths: list[Path]
    ) -> list[Path]:

        if current_hub.zone_type == "blocked":

            return []

        if current_hub == dest:

            possible_paths.append(Path(current_path + [dest], cost))

        else:

            for branch in current_hub.connections.values():

                cost_to_add: int = 1

                if current_hub == branch.zone1:

                    if branch.zone2 in current_path:
                        return []

                    if branch.zone2.zone_type == "restricted":
                        cost_to_add += 1

                    for path in possible_paths:
                        if current_path + [current_hub] == path.path:
                            return []

                    PathFinder.calculate_paths(
                        branch.zone2,
                        current_path + [current_hub],
                        cost + cost_to_add,
                        dest,
                        possible_paths
                    )

        return possible_paths

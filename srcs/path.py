from .zones import Zone
from .state import Char


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

    @staticmethod
    def find_valid_neighbors(
        lines: list[list[Char]],
        point: Char,
        to_explore: list[Char],
        explored: list[Char],
        parent_name: str,
        arrival: Char
    ) -> list[Char]:

        neighbors: list[Char] = []

        directions: list[tuple[int, int]] = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        if point.dir_from_parent:

            directions.sort(key=lambda d: d != point.dir_from_parent)

        for direction in directions:

            if (
                point.row + direction[0] < 0
                or point.row + direction[0] >= len(lines)
            ):
                continue

            if (
                point.col + direction[1] < 0
                or point.col + direction[1] >= len(lines[0])
            ):
                continue

            neighbor: Char = lines[
                point.row + direction[0]
            ][point.col + direction[1]]

            if neighbor.is_zone and (
                neighbor.relation != parent_name
                or not neighbor.is_border
            ):
                continue

            neighbors.append(neighbor)

        for n in neighbors:

            if n in explored:
                continue

            n.update_dist(point, n in to_explore, arrival)

            if n not in to_explore:
                to_explore.append(n)

        return to_explore

    @staticmethod
    def find_next_point(to_explore: list[Char]) -> Char | None:

        if not to_explore:
            return None

        sorted_list: list[Char] = sorted(
            to_explore,
            key=lambda char: (
                char.total_dist,
                char.dist_from_arrival,
                -char.dist_from_start
            )
        )

        return sorted_list[0]

    @staticmethod
    def retrace_steps(arrival: Char, start: Char) -> list[tuple[int, int]]:

        point: Char = arrival

        path: list[tuple[int, int]] = []

        while (point.row, point.col) != (start.row, start.col):

            path.append((point.row, point.col))
            point = point.parent

        path.append((start.row, start.col))
        path.reverse()

        return path

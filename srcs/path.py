from .zones import Zone
from .state import Char


class Path:

    """

    A class to store the path between two points.

    """

    def __init__(self, path: list[Zone], cost: int) -> None:

        """

        Initializes the attributes of a Path object.

        Parameters
        ----------
        path : list[Zone]
            The path between two zones.
        cost : int
            The cost of the path in terms of movement.

        """

        self.path: list[Zone] = path
        self.cost: int = cost
        self.priority: bool = False


class PathFinder:

    """

    A class with a set of methods used to find paths between two points.

    """

    @staticmethod
    def calculate_paths(
        current_hub: Zone,
        current_path: list[Zone],
        cost: int,
        dest: Zone,
        possible_paths: list[Path]
    ) -> list[Path]:

        """

        Calculates all the available paths
        between a starting zone and a goal zone
        using recursion and backtracking.

        Parameters
        ----------
        current_hub : Zone
            The zone the path is currently at.
        current_path : list[Zone]
            The current path being constructed.
        cost : int
            The accumulated cost of the current path.
        dest : Zone
            The goal point of the path.
        possible_paths : list[Path]
            The total list of paths found until now.

        Returns
        -------
        list[Path]
            All the paths found between the start point and the destination.

        """

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

        """

        Finds all the neighbors available and not yet visited
        of the current point in the screen's grid.

        Parameters
        ----------
        lines : list[list[Char]]
            The entire screen's grid.
        to_explore : list[Char]
            The list of Char (points) to explore.
        explored : list[Char]
            The list of Char that have already been explored.
        parent_name : str
            The name of the parent Zone that needs to be reached.
        arrival : Char
            The arrival point calculated.

        Returns
        -------
        list[Char]
            The list of points to explore
            to which the neighbors of the current point have been added.

        """

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

        """

        Finds the next point that needs to be explored
        using the Manhattan distance as a criterion.

        Parameters
        to_explore : list[Char]
            The list of Char (points) yet to be explored.

        Returns
        -------
        Char | None:
            The next point to explore if found, otherwise None.

        """

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

        """

        Retrace the steps taken to form a path of grid points.

        Parameters
        ----------
        arrival : Char
            The goal and last point of the path.
        start : Char
            The starting point to be reached as the path retraces the steps.

        Returns
        -------
        list[tuple[int, int]]
            A list of grid coordinates that form the path.

        """

        point: Char = arrival

        path: list[tuple[int, int]] = []

        while (point.row, point.col) != (start.row, start.col):

            path.append((point.row, point.col))
            point = point.parent

        path.append((start.row, start.col))
        path.reverse()

        return path

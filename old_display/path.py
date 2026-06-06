import heapq
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
    def custom_dijkstra(
        start: Zone,
        dest: Zone,
        blocked_zones: set[str],
        root_path: list[Zone]
    ) -> Path | None:

        """

        A pathfinding algorithm that uses best-first-search
        with a priority queue in order to find the best cost path.

        Parameters
        ----------
        start : Zone
            The starting zone of the pathfinding.
        dest : Zone
            The goal point of the path.
        blocked_zones: int
            The zones that the path should not explore.
        root_path: list[Zone]
            The root path from which the current path found stems.

        Returns
        -------
        Path | None
            The best path found between the start and the destination
            if there is one, otherwise None.

        """
        unique: int = 0
        stack: list[tuple[int, int, bool, Zone, list[Zone]]] = [
            (0, unique, False, start, [start])
        ]
        best_cost: dict[str, int] = {}

        while stack:

            cost, _, is_priority, zone, path = heapq.heappop(stack)

            if zone.name in best_cost.keys() and best_cost[zone.name] < cost:
                continue

            best_cost[zone.name] = cost

            if zone == dest:
                return Path(root_path[:-1] + path, cost)

            for branch in zone.connections.values():

                neighbor: Zone = (
                    branch.zone2 if zone == branch.zone1
                    else branch.zone1
                )

                if (
                    neighbor in path
                    or neighbor.name in blocked_zones
                    or neighbor.zone_type == "blocked"
                    or neighbor.max_drones == 0
                    or branch.max_link_capacity == 0
                ):
                    continue

                cost_to_add: int = (
                    2 if neighbor.zone_type == "restricted"
                    else 1
                )
                new_priority: bool = (
                    is_priority or neighbor.zone_type == "priority"
                )
                unique += 1
                heapq.heappush(stack, (
                    cost + cost_to_add,
                    unique,
                    new_priority,
                    neighbor,
                    path + [neighbor]
                ))

        return None

    @staticmethod
    def calculate_paths(
        start: Zone,
        dest: Zone,
        nb_paths: int = 5
    ) -> list[Path]:

        """

        Calculates the number of paths required
        between a starting zone and a goal zone
        ensuring they have the best cost.

        Parameters
        ----------
        start : Zone
            The starting zone of the pathfinding.
        dest : Zone
            The goal point of the path.
        nb_paths: int
            The number of best paths asked.

        Returns
        -------
        list[Path]
            The best paths found between the start point and the destination.

        """

        if start == dest:
            return [Path([start], 0)]

        first_path: Path | None = PathFinder.custom_dijkstra(
            start,
            dest,
            set(),
            []
        )
        if not first_path:
            return []

        best_paths: list[Path] = [first_path]
        unique: int = 0

        for path_n in range(1, nb_paths):

            potential_paths: list[tuple[int, int, Path]] = []
            previous_path: Path = best_paths[path_n - 1]

            for node_id in range(len(previous_path.path) - 1):

                cur_node: Zone = previous_path.path[node_id]
                root_path: list[Zone] = previous_path.path[:node_id + 1]

                blocked_zones: set[str] = {
                    node.name for node in root_path[:-1]
                }
                for previous in best_paths:

                    if (
                        len(previous.path) > node_id + 1
                        and previous.path[:node_id + 1] == root_path
                    ):
                        blocked_zones.add(previous.path[node_id + 1].name)

                root_cost: int = 0

                for cost_id in range(1, len(root_path)):

                    root_cost += (
                        2 if root_path[cost_id].zone_type == "restricted"
                        else 1
                    )

                cur_path: Path | None = PathFinder.custom_dijkstra(
                    cur_node,
                    dest,
                    blocked_zones,
                    root_path
                )

                if cur_path:

                    cur_path.cost += root_cost

                    if not any(
                        potential_path.path == cur_path.path
                        for _, _, potential_path in potential_paths
                    ):
                        unique += 1
                        heapq.heappush(potential_paths, (
                            cur_path.cost,
                            unique,
                            cur_path
                        ))

            if not potential_paths:
                break

            _, _, next_best = heapq.heappop(potential_paths)
            best_paths.append(next_best)

        return best_paths

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
            The screen's grid containing all the points.
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

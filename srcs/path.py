from .zones import Zone, Connection
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
    def calculate_paths(start: Zone, dest: Zone) -> list[Path]:

        """

        Calculates all the available paths
        between a starting zone and a goal zone.

        Parameters
        ----------
        start : Zone
            The starting zone of the pathfinding.
        dest : Zone
            The goal point of the path.

        Returns
        -------
        list[Path]
            All the paths found between the start point and the destination.

        """

        current_hub: Zone = start
        current_con: Connection | None = None
        possible_paths: list[Path] = []
        current_path: list[tuple[Zone, Connection | None]] = []
        paths_refused: list[list[tuple[Zone, Connection | None]]] = []
        cost: int = 0
        found: bool = False

        while True:

            if (
                current_hub.zone_type == "blocked"
                or current_hub.max_drones == 0
                or (current_con and current_con.max_link_capacity == 0)
            ):
                if not current_path:
                    break
                if current_path + [(current_hub, current_con)] not in paths_refused:
                    paths_refused.append([z_c for z_c in current_path] + [(current_hub, current_con)])
                current_hub, current_con = current_path.pop()

            else:
                current_path.append((current_hub, current_con))
                print(f"adding hub {current_hub.name} to current path\n")

                if current_hub == dest:
                    print("found destination!\n")
                    possible_paths.append(Path([
                        z for z, c in current_path
                    ], cost))
                    current_path.pop()
                    if not current_path:
                        break
                    current_hub, current_con = current_path.pop()

                else:
                    found = False
                    print(f"exploring all connections of hub {current_hub.name}\n")
                    for branch in current_hub.connections.values():

                        cost_to_add: int = 1

                        neighbor: Zone = (
                            branch.zone2 if current_hub == branch.zone1
                            else branch.zone1
                        )
                        print(f"found neighbor {neighbor.name}\n")

                        print("paths refused until now:\n")
                        for p_r in paths_refused:
                            print(f"- {[zone.name for zone, con in p_r]}\n")
                        if neighbor in [zone for zone, con in current_path]:
                            print("neighbor already in current path\n")
                            continue

                        if neighbor.zone_type == "restricted":
                            cost_to_add += 1

                        if current_path + [(neighbor, branch)] in paths_refused:
                            print("neighbor is in a refused path\n")
                            continue

                        if not possible_paths:
                            already_exists: bool = False
                        else:
                            already_exists = True
                        for path in possible_paths:

                            already_exists = True
                            if len(path.path) < len(current_path) + 1:
                                continue
                            for z in range(len(current_path) + 1):

                                if path.path[z] != ([
                                    zone for zone, con in current_path
                                ] + [neighbor])[z]:
                                    already_exists = False
                                    break

                            if already_exists:
                                break

                        if not already_exists:
                            current_hub = neighbor
                            current_con = branch
                            cost += cost_to_add
                            found = True
                            break

                    if not found:
                        print("found no neighbor, adding current path to refused paths\n")
                        if current_path not in paths_refused:
                            paths_refused.append([z_c for z_c in current_path])
                        if not current_path:
                            break

                        current_path.pop()
                        if not current_path:
                            break
                        current_hub, current_con = current_path.pop()

        print(f"number of paths found: {len(possible_paths)}")
        return possible_paths

    @staticmethod
    def equal_paths(path: list[Zone], path_to_compare: list[Zone]) -> bool:

        for z in range(len(path_to_compare)):

            if path[z] != path_to_compare[z]:
                return False

        return True

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

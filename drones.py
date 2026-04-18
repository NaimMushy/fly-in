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

class Pathfinder:

    def __init__(self, drone_map: Map) -> None:

        self.map: Map = drone_map
        self.paths: list[list[Zone | Connection]] = []
    
    def calculate_paths(self) -> None:

        paths_explored: int = 0
        current_hub: Zone = self.map.end_hub
        visited_hubs: list[Zone] = []

        while pas tous trouvés:

            visited_hubs.append(current_hub)

from .parsing import MapParser, Map
from .path import Pathfinder
from .drones import DroneMonitor


if __name__ == "__main__":

    import sys

    if len(sys.argv) == 2:

        map_parser: MapParser = MapParser()
        drone_map: Map | None = map_parser.parse_map(sys.argv[1])
        if not drone_map:
            print("\n==== An error has been caught while parsing the map ====")
        try:
            pathfinder: Pathfinder = Pathfinder(drone_map)
        except ValueError as ve:
            print(f"{ve}\n")
        else:
            drone_monitor: DroneMonitor = DroneMonitor(
                drone_map,
                pathfinder
            )
            while drone_monitor.drones:
                drone_monitor.update_drones()

            print("==== All drones have been successfully delivered! ====")

    else:

        print("Invalid number of arguments provided, no map given to parse")

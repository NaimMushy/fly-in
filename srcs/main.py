from .big_file import MapParser, Map, Path, Pathfinder, DroneMonitor


if __name__ == "__main__":

    import sys

    if len(sys.argv) == 2:

        map_parser: MapParser = MapParser()
        drone_map: Map | None = map_parser.parse_map(sys.argv[1])
        if not drone_map:
            print("\n==== An error has been caught while parsing the map ====")
        else:
            pathfinder: Pathfinder = Pathfinder(drone_map)
            paths: list[Path] = pathfinder.calculate_paths(
                drone_map.start_hub,
                [],
                0,
                drone_map.end_hub,
                []
            )
            if not paths:
                print("No paths found, map considered invalid!\n")

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

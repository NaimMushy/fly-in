from srcs import MapParser, Map, Pathfinder, Path, DroneMonitor, TuiDisplay


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
                tui_display: TuiDisplay = TuiDisplay(
                    drone_map,
                    drone_monitor.drones
                )
                while drone_monitor.drones:
                    drone_monitor.update_drones()
                    tui_display.display_map()

                print(
                    "==== All drones have been successfully delivered! "
                    f"TURNS={drone_monitor.turns} ===="
                )

    else:

        print("Invalid number of arguments provided, no map given to parse")

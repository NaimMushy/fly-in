from srcs import MapParser, Map, Pathfinder, Path, DroneMonitor, TuiDisplay, State


if __name__ == "__main__":

    import sys

    map_parser: MapParser = MapParser()
    drone_map: Map | None = None
    TuiDisplay.display_menu()
    map_file: str = ""
    if len(sys.argv) == 2:
        map_file = sys.argv[1]
    menu_quit: bool = False
    info_mode: int = 0
    while menu_quit is False:

        if not map_file:
            TuiDisplay.display_options(info_mode)
            user_input: str = input()
            while user_input not in ["s", "i", "q"]:
                user_input = input()
            if user_input == "s":
                map_file = input("\nEnter the path to the map file: ")
            elif user_input == "i":
                info_mode = (1 if info_mode == 0 else 0)
            elif user_input == "q":
                menu_quit = True
        else:
            drone_map = map_parser.parse_map(map_file)
            if drone_map:
                menu_on: bool = False
                pathfinder: Pathfinder = Pathfinder(drone_map)
                paths: list[Path] = pathfinder.calculate_paths(
                    drone_map.start_hub,
                    [],
                    0,
                    drone_map.end_hub,
                    []
                )
                if paths:
                    drone_monitor: DroneMonitor = DroneMonitor(
                        drone_map,
                        pathfinder
                    )
                    tui_display: TuiDisplay = TuiDisplay(drone_map, info_mode)
                    new_state: State = State(info_mode, tui_display.console)
                    tui_display.display_map(new_state)
                    states: list[State] = [new_state]
                    while drone_monitor.drones:
                        new_state = State(info_mode, tui_display.console)
                        drone_monitor.update_drones(new_state)
                        tui_display.display_map(new_state)
                        states.append(new_state)
                    cur_state: int = 0
                    tui_display.display_state(states[cur_state])
                    while not menu_on:
                        user_input = input()
                        while user_input not in ["n", "p", "r"]:
                            user_input = input()
                        if user_input == "n":
                            if cur_state == len(states) - 1:
                                tui_display.display_end(drone_monitor, info_mode)
                                menu_on = True
                            else:
                                cur_state += 1
                                tui_display.display_state(states[cur_state])
                        elif user_input == "p" and cur_state != 0:
                            cur_state -= 1
                            tui_display.display_state(states[cur_state])
                        elif user_input == "r":
                            menu_on = True
                    map_file = ""
                else:
                    print("No paths found, map considered invalid!\n")
                    map_file = ""
            else:
                print("==== An error occured while parsing the map ====")
                map_file = ""

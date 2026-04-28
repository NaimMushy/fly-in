from srcs import MapParser, Map, PathFinder, DroneMonitor, TuiDisplay, State


if __name__ == "__main__":

    import sys

    map_parser: MapParser = MapParser()
    drone_map: Map | None = None
    default_map: str = "tests/sub_testmap.txt"
    TuiDisplay.display_menu()
    if len(sys.argv) == 2:
        map_file = sys.argv[1]
    else:
        map_file = default_map
    menu_quit: bool = False
    info_mode: int = 0
    while menu_quit is False:

        TuiDisplay.display_options(info_mode, map_file)
        user_input: str = input()
        while user_input not in ["s", "i", "q", "l"]:
            user_input = input()
        if user_input == "s":
            map_file = input("\nEnter the path to the map file: ")
        elif user_input == "i":
            info_mode = (1 if info_mode == 0 else 0)
        elif user_input == "q":
            menu_quit = True
        elif user_input == "l":
            drone_map = map_parser.parse_map(map_file)
            if drone_map:
                if PathFinder.calculate_paths(
                    drone_map.start_hub,
                    [],
                    0,
                    drone_map.end_hub,
                    []
                ):
                    print(f" ✔ Map {map_file} validated!\n")
                    drone_monitor: DroneMonitor = DroneMonitor(
                        drone_map,
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
                    menu_on: bool = False
                    while not menu_on:
                        user_input = input()
                        while user_input not in ["n", "p", "m"]:
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
                        elif user_input == "m":
                            menu_on = True
                else:
                    print(f" ✘ Map {map_file} refused : No paths found")
            else:
                print(f" ✘ Map {map_file} refused : Invalid data")

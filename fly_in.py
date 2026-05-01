import sys
from srcs import MapParser, Map, PathFinder, DroneMonitor, TuiDisplay, State


DEFAULT_MAP: str = "tests/sub_testmap.txt"


def main() -> None:

    map_parser: MapParser = MapParser()
    drone_map: Map | None = None
    states: dict[str, tuple[list[State], int, int]] = {}

    TuiDisplay.display_menu()

    if len(sys.argv) == 2:
        map_file = sys.argv[1]
    else:
        map_file = DEFAULT_MAP

    info_mode: int = 0
    user_input: str = ""

    while user_input != "q":

        TuiDisplay.display_options(info_mode, map_file)

        user_input = input()

        while user_input not in ["s", "i", "q", "l"]:
            user_input = input()

        if user_input == "s":
            map_file = input("\nEnter the path to the map file: ")

        elif user_input == "i":
            info_mode = (1 if info_mode == 0 else 0)

        elif user_input == "l":
            launch_drones(map_parser, drone_map, map_file, states, info_mode)


def launch_drones(
    map_parser: MapParser,
    drone_map: Map | None,
    map_file: str,
    states: dict[str, tuple[list[State], int, int]],
    info_mode: int
) -> None:

    drone_map = map_parser.parse_map(map_file)

    if not drone_map:
        print(f" ✘ Map {map_file} refused : Invalid data")
        return

    elif map_file not in states.keys() and not PathFinder.calculate_paths(
        drone_map.start_hub,
        [],
        0,
        drone_map.end_hub,
        []
    ):
        print(f" ✘ Map {map_file} refused : No paths found")
        return

    tui_display: TuiDisplay = TuiDisplay(drone_map, info_mode)

    if map_file not in states.keys():

        print(f" ✔ Map {map_file} validated!\n")

        drone_monitor: DroneMonitor = DroneMonitor(
            drone_map,
        )

        new_state: State = State(info_mode, tui_display.console)
        new_state.display_map = tui_display.map_updated()
        cur_states: list[State] = [new_state]

        while drone_monitor.drones:

            new_state = State(info_mode, tui_display.console)
            drone_monitor.update_drones(new_state)
            new_state.display_map = tui_display.map_updated()
            cur_states.append(new_state)

        states[map_file] = (cur_states, drone_monitor.turns, drone_monitor.avg)

    show_states(tui_display, states[map_file], info_mode)


def show_states(
    tui_display: TuiDisplay,
    states: tuple[list[State], int, int],
    info_mode: int
) -> None:

    cur_state: int = 0

    tui_display.display_state(states[0][cur_state])

    user_input = input()

    while user_input != "m":

        while user_input not in ["n", "p", "m"]:
            user_input = input()

        if user_input == "n":

            if cur_state == len(states[0]) - 1:
                tui_display.display_end(info_mode, states[1], states[2])

            else:
                cur_state += 1
                tui_display.display_state(states[0][cur_state])

        elif user_input == "p" and cur_state != 0:

            cur_state -= 1
            tui_display.display_state(states[0][cur_state])

    return


if __name__ == "__main__":

    main()

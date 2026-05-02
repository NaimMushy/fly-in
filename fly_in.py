import sys
from srcs import MapParser, Map, PathFinder, DroneMonitor, TuiDisplay, State


DEFAULT_MAP: str = "tests/sub_testmap.txt"


def main() -> None:

    """

    Launches a simulation of drone routing
    using pathfinding algorithm and a tui display.

    """

    map_parser: MapParser = MapParser()
    states: dict[str, list[tuple[list[State], int, int, int]]] = {}

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
            launch_drones(map_parser, map_file, states, info_mode)


def launch_drones(
    map_parser: MapParser,
    map_file: str,
    states: dict[str, list[tuple[list[State], int, int, int]]],
    info_mode: int
) -> None:

    """

    Goes through every step of the simulation
    and saves it in a specific state.

    Parameters
    ----------
    map_parser : MapParser
        The parser used to verify and validate map data.
    map_file : str
        The name of the file containing all of the map data.
    states : dict[str, list[tuple[list[State], int, int, int]]]
        A dictionary that saves all the simulations already done
        by associating a file name
        with a list of states and additional information.
    info_mode : int
        Indicates whether or not the information mode is activated.

    """

    drone_map: Map | None = map_parser.parse_map(map_file)

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

    if map_file not in states.keys() or (
        not any(lst_state[3] for lst_state in states.values())
    ):
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

        states[map_file].append((
            cur_states,
            drone_monitor.turns,
            drone_monitor.avg,
            info_mode
        ))

    for state_list in states[map_file]:

        if state_list[3] and info_mode:
            show_states(tui_display, state_list)
            return

        elif not info_mode and not state_list[3]:
            show_states(tui_display, state_list)
            return


def show_states(
    tui_display: TuiDisplay,
    states: tuple[list[State], int, int, int]
) -> None:

    """

    Displays the simulation steps
    based on the user's commands.

    Parameters
    ----------
    tui_display : TuiDisplay
        The display object used to display the user options and steps.
    states : tuple[list[State], int, int, int]
        All of the states pertaining to the current simulation
        being run.

    """

    cur_state: int = 0

    tui_display.display_state(states[0][cur_state])

    user_input = input()

    while user_input != "m":

        while user_input not in ["n", "p", "m"]:
            user_input = input()

        if user_input == "n":

            if cur_state == len(states[0]) - 1:
                tui_display.display_end(states[3], states[1], states[2])

            else:
                cur_state += 1
                tui_display.display_state(states[0][cur_state])

        elif user_input == "p" and cur_state != 0:

            cur_state -= 1
            tui_display.display_state(states[0][cur_state])

    return


if __name__ == "__main__":

    main()

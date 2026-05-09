import sys
import os
import time
from srcs import MapParser, Map, Path, PathFinder, DroneMonitor, TuiDisplay, State


DEFAULT_MAP: str = "maps/easy/01_linear_path.txt"


def main() -> None:

    """

    Launches a simulation of drone routing
    using pathfinding algorithm and a tui display.

    """

    map_parser: MapParser = MapParser()
    states: dict[str, list[tuple[list[State], int, int, int]]] = {}

    if len(sys.argv) > 2:
        print("Too many arguments for the program!")
        return

    map_file: str = DEFAULT_MAP

    if len(sys.argv) == 2:
        map_file = sys.argv[1]

    info_mode: int = 0
    user_input: str = ""
    ret: int = 0

    while user_input != "q" and ret != -1:

        try:

            os.system('clear')

            TuiDisplay.display_menu(info_mode, map_file)

            user_input = input()

            while user_input not in ["s", "i", "q", "l"] and user_input:
                print("Invalid command!")
                time.sleep(0.4)
                os.system('clear')
                TuiDisplay.display_menu(info_mode, map_file)
                user_input = input()

            if user_input == "s":
                map_file = input("\nEnter the path to the map file: ")

            elif user_input == "i":
                info_mode = (1 if info_mode == 0 else 0)
                os.system('clear')
                print(
                    f"{'Deactivated' if info_mode == 0 else 'Activated'} "
                    "information mode!"
                )
                time.sleep(1)

            elif user_input == "l":
                os.system('clear')
                ret = launch_drones(
                    map_parser,
                    map_file,
                    states,
                    info_mode
                )

        except KeyboardInterrupt:

            return


def launch_drones(
    map_parser: MapParser,
    map_file: str,
    states: dict[str, list[tuple[list[State], int, int, int]]],
    info_mode: int
) -> int:

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

    os.system('clear')
    drone_map: Map | None = map_parser.parse_map(map_file)

    if not drone_map:
        print(f" ✘ Map '{map_file}' refused : Invalid data\n")
        input("Press any key to continue...")
        return 0

    elif map_file not in states.keys() and not PathFinder.calculate_paths(
        drone_map.start_hub, drone_map.end_hub
    ):
        print(f" ✘ Map '{map_file}' refused : No paths found\n")
        input("Press any key to continue...")
        return 0

    tui_display: TuiDisplay = TuiDisplay(drone_map, info_mode)

    if map_file not in states.keys():

        map_parser.already_parsed[map_file] = drone_map
        print(f" ✔ Map '{map_file}' validated!\n")
        time.sleep(0.5)

    if map_file not in states.keys() or (
        info_mode and not any(lst_state[3] for lst_state in states[map_file])
    ):
        drone_monitor: DroneMonitor = DroneMonitor(
            drone_map,
        )

        new_state: State = State(info_mode, tui_display.console)
        new_state.turn = 0
        new_state.display_map = tui_display.map_updated([])
        new_state.zones_occupied[drone_map.start_hub.name] = [
            d.id for d in drone_map.start_hub.occupied
        ]
        cur_states: list[State] = [new_state]
        # turn_count: int = 1

        while drone_monitor.drones:

            # print(f"\n==== TURN {turn_count} ====\n\n")
            new_state = State(info_mode, tui_display.console)
            drone_monitor.update_drones(new_state)
            # print("updated drones!")
            new_state.display_map = tui_display.map_updated((
                []
                if drone_map.end_hub.name
                not in new_state.zones_occupied.keys()
                else new_state.zones_occupied[drone_map.end_hub.name]
            ))
            cur_states.append(new_state)
            # turn_count += 1

        if map_file not in states.keys():
            states[map_file] = []

        states[map_file].append((
            cur_states,
            drone_monitor.turns,
            drone_monitor.avg,
            info_mode
        ))

    time.sleep(1)
    for state_list in states[map_file]:

        if state_list[3] and info_mode:
            return show_states(tui_display, state_list)

        elif not info_mode and not state_list[3]:
            return show_states(tui_display, state_list)

    return 0


def show_states(
    tui_display: TuiDisplay,
    states: tuple[list[State], int, int, int]
) -> int:

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

    os.system('clear')
    tui_display.display_state(states[0][cur_state], states[1])

    user_input: str = ""

    while user_input != "m":

        try:

            user_input = input()

            while user_input not in ["n", "p", "m"] and user_input:
                print("Invalid command!")
                time.sleep(0.4)
                os.system('clear')
                tui_display.display_state(states[0][cur_state], states[1])
                user_input = input()

            if user_input == "n":

                os.system('clear')
                if cur_state == len(states[0]) - 1:
                    tui_display.display_end(states[3], states[1], states[2])
                    input("Press any key to continue...")
                    user_input = "m"

                else:
                    cur_state += 1
                    os.system('clear')
                    tui_display.display_state(states[0][cur_state], states[1])

            elif user_input == "p":

                if cur_state == 0:

                    print("Invalid command!")
                    time.sleep(0.4)
                    os.system('clear')
                    tui_display.display_state(states[0][cur_state], states[1])

                else:
                    cur_state -= 1
                    os.system('clear')
                    tui_display.display_state(states[0][cur_state], states[1])

        except KeyboardInterrupt:

            return -1

    return 0


if __name__ == "__main__":

    main()

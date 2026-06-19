import sys
import os
import time
from srcs import (
    MapParser,
    Map,
    PathFinder,
    DroneMonitor,
    TuiDisplay,
    ArcadeDisplay
)


DEFAULT_MAP: str = "maps/easy/01_linear_path.txt"


MAP_DIR: str = "maps"


MAPS: dict[str, dict[int, str]] = {
    "easy": {
        1: "01_linear_path",
        2: "02_simple_fork",
        3: "03_basic_capacity"
    },
    "medium": {
        4: "01_dead_end_trap",
        5: "02_circular_loop",
        6: "03_priority_puzzle"
    },
    "hard": {
        7: "01_maze_nightmare",
        8: "02_capacity_hell",
        9: "03_ultimate_challenge"
    },
    "challenger": {10: "01_the_impossible_dream"}
}


class App:

    """

    A class representing an application that handles every step
    of the drone simulation, including the terminal menu
    and user actions.

    """

    def __init__(self, initial_map: str = DEFAULT_MAP) -> None:

        """

        Initializes the attributes of an App object.

        Parameters
        ----------
        initial_map: str
            The map file path with which the application starts with.

        """

        self.map_parser: MapParser = MapParser()
        self.map_file: str = initial_map
        self.arcade_mode: bool = True

    def main_loop(self) -> None:

        """

        Handles menu interaction via the terminal
        and collects user input to go to the next step
        until the program stops.

        """

        user_input: str = ""

        while user_input != "q":

            try:

                os.system('clear')

                TuiDisplay.display_menu(self.arcade_mode, self.map_file)

                user_input = input()

                while (
                    user_input not in ["s", "q", "l", "m", "g"]
                    and user_input
                ):

                    print("Invalid command!")
                    time.sleep(0.4)
                    os.system('clear')
                    TuiDisplay.display_menu(self.arcade_mode, self.map_file)
                    user_input = input()

                if user_input == "s":

                    self.map_file = input("\nEnter the path to the map file: ")

                elif user_input == "g":

                    self.arcade_mode = not (self.arcade_mode)
                    os.system('clear')
                    toggling: str = (
                        "Deactivated" if not self.arcade_mode
                        else "Activated"
                    )
                    print(f"{toggling} graphic representation mode!")
                    time.sleep(1)

                elif user_input == "m":

                    os.system('clear')
                    map_file_index: str = ""
                    TuiDisplay.display_maps(MAPS, MAP_DIR)
                    map_file_index = input("Choose a map: ")

                    while (
                        not map_file_index.isdigit()
                        or not self.find_map(int(map_file_index))
                    ) and map_file_index != "q":

                        print("\nInvalid choice!")
                        os.system('clear')
                        TuiDisplay.display_maps(MAPS, MAP_DIR)
                        map_file_index = input("Choose a map: ")

                    if map_file_index != "q":

                        self.map_file = self.find_map(int(map_file_index))
                        os.system('clear')
                        self.launch_drones()

                elif user_input == "l":
                    os.system('clear')
                    self.launch_drones()

            except KeyboardInterrupt:

                return

    @staticmethod
    def find_map(input_map: int) -> str:

        """

        Helper method to find the corresponding map
        in the MAPS dict using its integer id.
        Returns the valid path to the map file.

        Parameters
        ----------
        input_map: int
            The map id in the MAP dictionary.

        Returns
        -------
        str
            The valid path to the map file
            (using the MAP_DIR and the map category).

        """

        for map_category, map_dict in MAPS.items():

            if input_map in map_dict.keys():

                return (
                    "/".join([
                        MAP_DIR,
                        map_category,
                        map_dict[input_map] + ".txt"
                    ])
                )

        return ""

    def launch_drones(self) -> None:

        """

        Launches a simulation of drone routing
        using pathfinding algorithm.
        Goes through every step of the simulation
        and shows it either through terminal output
        or a visual representation using the arcade library.

        Parameters
        ----------
        map_parser : MapParser
            The parser used to verify and validate map data.
        map_file : str
            The name of the file containing all of the map data.
        arcade_mode : int
            Indicates whether or not
            the graphic representation mode is activated.

        """

        os.system('clear')
        drone_map: Map | None = self.map_parser.parse_map(self.map_file)

        if not drone_map:
            print(f" ✘ Map '{self.map_file}' refused : Invalid data\n")
            input("Press any key to continue...")
            return

        elif not PathFinder.calculate_paths(
            drone_map.start_hub, drone_map.end_hub
        ):
            print(f" ✘ Map '{self.map_file}' refused : No paths found\n")
            input("Press any key to continue...")
            return

        print(f" ✓ Map '{self.map_file}' validated!\n")
        time.sleep(0.5)
        drone_monitor: DroneMonitor = DroneMonitor(
            drone_map,
        )

        if self.arcade_mode:

            display: ArcadeDisplay = ArcadeDisplay(drone_map.hubs)
            display.add_state(drone_map.hubs, drone_map.connections, [], "")

        while drone_monitor.drones:

            drone_monitor.update_drones()

            if self.arcade_mode:
                display.add_state(
                    drone_map.hubs,
                    drone_map.connections,
                    drone_monitor.drones_delivered,
                    drone_monitor.current_turn_log
                )

        if self.arcade_mode:
            display.start_visu()

        TuiDisplay.display_end(drone_monitor.turns, drone_monitor.avg)

        return


def main() -> None:

    if len(sys.argv) > 2:
        print(
            "Too many arguments for the program!\n"
            "Usage: poetry run python3 fly_in.py <map_file_path> (optional)"
        )

    if len(sys.argv) == 2:
        app: App = App(sys.argv[1])

    else:
        app = App()

    app.main_loop()


if __name__ == "__main__":

    main()

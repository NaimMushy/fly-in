import time
import pyfiglet


class TuiDisplay:

    """

    A class used to display a drone simulation
    with zones and connections in the terminal.

    """

    @staticmethod
    def display_menu(arcade_mode: bool, map_file: str) -> None:

        """

        Displays the menu banner and options for the user.

        Parameters
        ----------
        info_mode : int
            Indicates whether or not the information mode is activated.
        map_file : str
            The path to the file currently being selected for the map data.

        """

        print(pyfiglet.figlet_format(
            "Welcome to Fly-In !!",
            font="bigchief"
        ), end="")

        print(r"""
                              *     .--.
                                   / /  `
                  +               | |
                         '         \ \__,
                     *          +   '--'  *
                         +   /\
            +              .'  '.   *
                   *      /======\      +
                         ;:.  _   ;
                         |:. (_)  |
                         |:.  _   |
               +         |:. (_)  |          *
                         ;:.      ;
                       .' \:.    / `.
                      / .-'':._.'`-. \
                      |/    /||\    \|
                    _..--'""````""'--.._
              _.-'``                    ``'-._
            -'                                '-
        """)

        print("\n✦ MENU OPTIONS ✦\n")
        print(f"     ➤ s: SELECT NEW MAP (current map: {map_file})")
        print("     ➤ l: LAUNCH THE DRONES")
        print(
            "     ➤ g: TOGGLE GRAPHIC MODE "
            f"({'off' if not arcade_mode else 'on'})"
        )
        print("     ➤ m: DISPLAY AVAILABLE MAP PATHS")
        print("     ➤ q: QUIT PROGRAM")

    @staticmethod
    def display_maps(maps: dict[str, list[str]], map_dir: str) -> None:

        """

        Displays the map paths for the user to copy paste.

        Parameters
        ----------
        maps: dict[str, list[str]]
            The dictionary containing map categories and their respective maps.
        map_dir: str
            The base directory in which the map paths are.

        """
        print("\n✦ MAPS AVAILABLE ✦\n")

        for map_type, map_path in maps.items():

            print(f" ➤ {map_type.upper()}:\n")

            for m in map_path:

                print(f" - {map_dir + '/' + map_type + '/' + m + '.txt'}")

            print()

        time.sleep(1)
        input("Press any key to continue...\n")

    @staticmethod
    def display_end(turns: int, avg: int) -> None:

        """

        Displays an end message for the simulation
        and some summary information.

        Parameters
        ----------
        info_mode : int
            Indicates whether or not the information mode is activated.
        turns : int
            The number of turns made during the simulation.
        avg : int
            The average number of turns per drone.

        """

        print("\n✦ ✦ ✦ ✦ END OF THE SIMULATION ✦ ✦ ✦ ✦\n")
        print(f"     ➤ number of turns: {turns}")
        print(
            f"     ➤ average number of turns per drone: {avg}"
        )
        print()
        input("Press any key to continue...")

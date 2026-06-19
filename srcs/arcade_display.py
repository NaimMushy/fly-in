import arcade
import warnings
import tkinter as tk
from .zones import Zone, Connection
from .drones import Drone
from .color_palette import ColorPalette
from typing import Any as any


root: tk.Tk = tk.Tk()
root.withdraw()
WIDTH: int = root.winfo_screenwidth()
HEIGHT: int = root.winfo_screenheight()
root.quit()

NB_COMMANDS: int = 6
MAX_WIDGET_HEIGHT: int = HEIGHT // 4 + 40
WIN_HEIGHT: int = HEIGHT - MAX_WIDGET_HEIGHT
TARGET_FPS: float = 60
arcade.load_font("srcs/assets/ByteBounce.ttf")
CUSTOM_FONT: str = "ByteBounce"
DRONE_IMAGE: str = "srcs/assets/drone_pixel_art.avif"

warnings.filterwarnings("ignore")


class DisplayView(arcade.View):

    """

    A class inheriting from the arcade.View parent class
    that serves as a custom view for the drone display.

    """

    def __init__(self, display: "ArcadeDisplay") -> None:

        """

        Initializes the attributes of a DisplayView object.

        Parameters
        ----------
        display: ArcadeDisplay
            The ArcadeDisplay instance associated with this view.

        """

        super().__init__()

        self.display: "ArcadeDisplay" = display
        self.background_color: any = (
            ColorPalette.get_color("white")
        )
        self.target_fps: float = 60
        self.frame_count: int = 0
        self.on_pause: bool = False
        self.step_by_step: bool = False

    def on_update(self, delta_time: float = 1 / 60) -> None:

        """

        The implementation of the on_update method
        found in the parent class arcade.View
        which updates all the needed variables of the display.

        Parameters
        ----------
        delta_time: float
            The frequency of the view update.

        """

        if self.on_pause or self.step_by_step:
            return

        self.frame_count += 1

        if self.frame_count < self.target_fps:
            return

        self.frame_count = 0
        self.display.cur_state_id += 1

        if self.display.cur_state_id == len(self.display.states):
            self.display.cur_state_id = 0

    def on_draw(self) -> None:

        """

        The implementation of the on_draw method
        found in the parent class arcade.View
        which displays the view on the screen.

        """

        if self.on_pause and not self.step_by_step:
            return

        self.clear()
        self.display.draw_state()

    def on_key_press(self, key: int, modifiers: int) -> None:

        """

        The implementation of the on_key_press method
        found in the parent class arcade.View
        which handles the key events from the user.

        Parameters
        ----------
        key: int
            The keycode corresponding to the key pressed by the user.
        modifiers: int
            A variable used by the parent class in the original method
            to handle key events.

        """

        if key == arcade.key.SPACE:

            self.on_pause = not (self.on_pause)
            self.step_by_step = False

        if key == arcade.key.UP:

            if self.target_fps / 1.5 >= 2:
                self.target_fps = int(self.target_fps / 1.5)

        if key == arcade.key.DOWN:

            if self.target_fps * 1.5 <= 180:
                self.target_fps = int(self.target_fps * 1.5)

        if key == arcade.key.LEFT:

            self.step_by_step = True
            self.on_pause = True

            if self.display.cur_state_id - 1 >= 0:
                self.display.cur_state_id -= 1

        if key == arcade.key.RIGHT:

            self.step_by_step = True
            self.on_pause = True

            if self.display.cur_state_id + 1 == len(self.display.states):
                self.display.cur_state_id = 0

            else:
                self.display.cur_state_id += 1

        if key == arcade.key.ESCAPE:

            arcade.close_window()


class State:

    """

    A class that stores the information
    relevant to a certain step in the simulation,
    namely all the coordinates of the display variables
    such as zones, connections, drones, etc...

    """

    def __init__(
        self,
        zones: dict[str, tuple[int, int, str]],
        connections: dict[str, tuple[int, int, int, int]],
        drones: dict[int, tuple[int, int]],
        turn_nb: int,
        turn_log: str
    ) -> None:

        """

        Initializes the attributes of a State object.

        Parameters
        ----------
        zones: dict[str, tuple[int, int, str]]
            All the zones stored in a dictionary
            with the zone's name as the key
            and (the zone's x, the zone's y, the zone's color) as the value
            (x and y being the coordinates on the screen, not in a graph).
        connections: dict[str, tuple[int, int, int, int]]
            All the connections stored in a dictionary
            with the connection's name as the key
            and (the first zone's x, the first zone's y,
            the second zone's x, the second zone'y) as the value
            (which are also the coordinates on the screen).
        drones: dict[int, tuple[int, int]]
            All the drones stored in a dictionary
            with the drone's id as the key
            and (the drone's x, the drone's y) as the value
            (which are also the coordinates on the screen).
        turn_nb: int
            The turn number to which this state corresponds.
        turn_log: str
            The drone movements's log for this turn.

        """

        self.zones: dict[str, tuple[int, int, str]] = zones
        self.connections: dict[str, tuple[int, int, int, int]] = connections
        self.drones: dict[int, tuple[int, int]] = drones
        self.turn_nb: int = turn_nb
        self.turn_log: str = turn_log


class ArcadeDisplay:

    """

    The main display class that draws
    the simulation on the screen.

    """

    class Measures:

        """

        A helper class to do calculations for the coordinates
        of display variables and dimensions.

        """
        def __init__(self, zones: list[Zone]) -> None:

            """

            Initializes a Measures instance by calculating
            the base variables for the screen display.

            Parameters
            ----------
            zones: list[Zone]
                The zones of the drone map.

            """

            min_x: int = min([z.x for z in zones])
            min_y: int = min([z.y for z in zones])
            max_x: int = max([z.x for z in zones])
            max_y: int = max([z.y for z in zones])

            self.x_offset: int = (
                0 if min_x >= 0 else abs(min_x)
            )
            self.y_offset: int = (
                0 if min_y >= 0 else abs(min_y)
            )

            board_width: int = (
                max_x if min_x >= 0 else (max_x - min_x)
            ) + 2
            board_height: int = (
                max_y if min_y >= 0 else (max_y - min_y)
            ) + 2

            if WIN_HEIGHT // board_height < WIDTH // board_width:
                self.px_sz: int = WIN_HEIGHT // board_height

            else:
                self.px_sz = WIDTH // board_width

            self.zone_sz: int = (self.px_sz - 25) // 2
            self.padding: int = self.zone_sz // 5

            while (max_x + self.x_offset) * self.px_sz >= WIDTH:
                self.x_offset -= 1

            while (max_y + self.y_offset) * self.px_sz >= WIN_HEIGHT:
                self.y_offset -= 1

        def calculate_drone_scale(
            self,
            drone_texture: arcade.texture.texture.Texture,
            zones: list[Zone]
        ) -> None:

            """

            Calculates the correct scale
            for the drone image.

            Parameters
            ----------
            drone_texture: arcade.texture.texture.Texture
                The drone image loaded by the arcade library as a texture.
            zones: list[Zone]
                The zones of the drone map.

            """

            max_drones_scale: int = max([z.max_drones for z in zones])

            if max_drones_scale > 2:
                max_drones_scale //= 2

            scale: float = (
                (self.zone_sz - 4 - (5 * max_drones_scale))
                // max_drones_scale
            ) / drone_texture.width

            self.t_width: float = drone_texture.width * scale
            self.t_height: float = (drone_texture.height + 15) * scale

            while (
                self.t_width < 50 and
                self.t_height < 50 and
                max_drones_scale > 1
            ):

                max_drones_scale -= 1
                scale = (
                    (self.zone_sz - 4 - (5 * max_drones_scale))
                    // max_drones_scale
                ) / drone_texture.width
                self.t_width = drone_texture.width * scale
                self.t_height = (drone_texture.height + 15) * scale

        def calculate_drone_pos_on_con(
            self,
            coordinates: tuple[int, int, int, int],
            drones_occupying: list[Drone]
        ) -> dict[int, tuple[int, int]]:

            """

            Calculates the drones' positions
            on a particular connection based
            on the number of drones occupying it
            and the space available on the connection.

            Parameters
            ----------
            coordinates: tuple[int, int, int, int]
                The coordinates of the connection line drawn on the screen
                (for example: start_x, start_y, end_x, end_y).
            drones_occupying: list[Drone]
                The drones currently occupying the connection.

            Returns
            -------
            dict[int, tuple[int, int]]
                A dictionary containing the coordinates of each drone
                on the connection line, stored by id.

            """

            x_start: int
            y_start: int
            x_end: int
            y_end: int
            x_start, y_start, x_end, y_end = coordinates

            x_sign: int = 1
            y_sign: int = 1

            if x_start > x_end:
                x_sign = -1

            if y_start > y_end:
                y_sign = -1

            if x_start != x_end:
                x_start += (self.zone_sz // 2) * x_sign
                x_end += (self.zone_sz // 2) * (-x_sign)

            if y_start != y_end:
                y_start += (self.zone_sz // 2) * y_sign
                y_end += (self.zone_sz // 2) * (-y_sign)

            drone_pos: list[tuple[int, int]] = []

            nb_drones_on_con: int = int(
                abs(x_end - x_start) // self.t_width
                if (abs(x_end - x_start) // self.t_width)
                > (abs(y_end - y_start) // self.t_height)
                else abs(y_end - y_start) // self.t_height
            )

            if nb_drones_on_con < 1:
                nb_drones_on_con = 1

            drone_startx = x_start + ((
                abs(x_end - x_start) // nb_drones_on_con
            ) // 2) * x_sign
            drone_starty = y_start + ((
                abs(y_end - y_start) // nb_drones_on_con
            ) // 2) * y_sign

            for _ in range(nb_drones_on_con):

                drone_pos.append((drone_startx, drone_starty))
                drone_startx += (
                    abs(x_end - x_start) // nb_drones_on_con
                ) * x_sign
                drone_starty += (
                    abs(y_end - y_start) // nb_drones_on_con
                ) * y_sign

            diff: int = len(drone_pos) - len(drones_occupying)
            if diff <= 0:
                cur_pos: int = len(drone_pos)
            else:
                cur_pos = len(drone_pos) - diff // 2

            drone_coor: dict[int, tuple[int, int]] = {}

            for drone in drones_occupying:

                drone_coor[drone.id] = drone_pos[cur_pos - 1]
                cur_pos -= 1

                if cur_pos <= 0:
                    break

            return drone_coor

        def calculate_drone_pos_on_zone(
            self,
            zone_coor: tuple[int, int],
            display_drones: list[Drone]
        ) -> dict[int, tuple[int, int]]:

            """

            Calculates the drones' positions
            inside a certain zone based
            on the number of drones occupying it
            and the space available in the zone.

            Parameters
            ----------
            zone_coor: tuple[int, int]
                The coordinates of the zone on the screen
                (x and y as the point in the center of the zone).
            display_drones: list[Drone]
                The drones currently occupying the zone.

            Returns
            -------
            dict[int, tuple[int, int]]
                A dictionary containing the coordinates of each drone
                inside the zone, stored by id.

            """
            zone_x: int
            zone_y: int
            zone_x, zone_y = zone_coor

            drone_x: float = (
                zone_x - self.zone_sz // 2
                + 2 + self.t_width // 2
            )
            drone_y: float = (
                zone_y + self.zone_sz // 2
                - 2 - self.t_height // 2
            )

            drone_coor: dict[int, tuple[int, int]] = {}

            for drone in display_drones:

                if (
                    drone_x + self.t_width // 2
                    > zone_x + self.zone_sz // 2 - 2
                ):

                    drone_x = (
                        zone_x - self.zone_sz // 2
                        + 2 + self.t_width // 2
                    )
                    drone_y -= self.t_height - 5

                if (
                    drone_y - self.t_height // 2
                    < zone_y - self.zone_sz // 2 + 2
                ):

                    drone_y = (
                        zone_y + self.zone_sz // 2
                        - 2 - self.t_height // 2
                    )
                    drone_x = (
                        zone_x - self.zone_sz // 2
                        + 2 + self.t_width // 2
                    )

                drone_coor[drone.id] = (int(drone_x), int(drone_y))

                drone_x += self.t_width + 5

            return drone_coor

    def __init__(self, zones: list[Zone]) -> None:

        """

        Initializes the attributes of a ArcadeDisplay object.

        Parameters
        ----------
        zones: list[Zone]
            The zones of the drone map.

        """

        self.msr = self.Measures(zones)
        self.states: list[State] = []
        self.cur_state_id: int = 0
        self.drone_texture: arcade.texture.texture.Texture = (
            arcade.load_texture(DRONE_IMAGE)
        )
        self.msr.calculate_drone_scale(self.drone_texture, zones)

    def start_visu(self) -> None:

        """

        Starts the graphic visualisation of the simulation
        by creating an arcade Window and setting up an arcade View.

        """

        window: arcade.application.Window = (
            arcade.Window(WIDTH, HEIGHT, "LET'S FLY IN", resizable=True)
        )
        gameview: DisplayView = DisplayView(self)
        window.show_view(gameview)
        arcade.run()

    def draw_state(self) -> None:

        """

        Draws all the elements needed of a certain step of the simulation
        on the arcade window opened.

        """

        current_state: State = self.states[self.cur_state_id]

        arcade.draw_line(
            0,
            HEIGHT - MAX_WIDGET_HEIGHT,
            WIDTH,
            HEIGHT - MAX_WIDGET_HEIGHT,
            ColorPalette.get_color("african_violet"),
            30
        )
        arcade.draw_line(
            0,
            HEIGHT - MAX_WIDGET_HEIGHT,
            WIDTH,
            HEIGHT - MAX_WIDGET_HEIGHT,
            ColorPalette.get_color("cyber_grape"),
            3
        )

        arcade.draw_line(
            WIDTH // 3,
            HEIGHT - MAX_WIDGET_HEIGHT + 15,
            WIDTH // 3,
            HEIGHT,
            ColorPalette.get_color("african_violet"),
            30
        )
        arcade.draw_line(
            WIDTH // 3,
            HEIGHT - MAX_WIDGET_HEIGHT,
            WIDTH // 3,
            HEIGHT,
            ColorPalette.get_color("cyber_grape"),
            3
        )

        title_height = MAX_WIDGET_HEIGHT // (NB_COMMANDS + 2) + 40
        text_y: int = HEIGHT - title_height

        arcade.draw_text(
            "USER COMMANDS",
            WIDTH // 6,
            text_y,
            ColorPalette.get_color("african_violet"),
            28.0,
            anchor_x="center",
            font_name=CUSTOM_FONT
        )

        text_y -= 40
        commands_height = MAX_WIDGET_HEIGHT - title_height - 40

        for command in [
            " -> space : pause",
            " -> arrow up : speed up",
            " -> arrow down : slow down",
            " -> arrow left : previous step",
            " -> arrow right : next step",
            " -> escape : stop the simulation"
        ]:

            arcade.draw_text(
                command,
                WIDTH // 12,
                text_y,
                ColorPalette.get_color("african_violet"),
                24.0,
                font_name=CUSTOM_FONT
            )
            text_y -= commands_height // NB_COMMANDS

        logs: list[str] = current_state.turn_log.split(" ")

        text_y = HEIGHT - MAX_WIDGET_HEIGHT // 5 - 20

        arcade.draw_text(
            "CURRENT TURN ACTION",
            WIDTH - WIDTH // 3,
            text_y,
            ColorPalette.get_color("african_violet"),
            28.0,
            anchor_x="center",
            font_name=CUSTOM_FONT
        )
        text_y -= 40

        for log in logs:

            arcade.draw_text(
                log,
                WIDTH - WIDTH // 3,
                text_y,
                ColorPalette.get_color("african_violet"),
                24.0,
                anchor_x="center",
                font_name=CUSTOM_FONT
            )

            text_y -= 20

            if text_y < (HEIGHT - MAX_WIDGET_HEIGHT + 20):
                break

        for x1, y1, x2, y2 in current_state.connections.values():

            arcade.draw_line(
                x1,
                y1,
                x2,
                y2,
                arcade.color.BLACK,
                2
            )

        for (
            zone_name,
            (zone_x, zone_y, zone_color)
        ) in current_state.zones.items():

            arcade.draw_rect_filled(
                arcade.rect.XYWH(
                    zone_x,
                    zone_y,
                    self.msr.zone_sz + 10,
                    self.msr.zone_sz + 10
                ),
                ColorPalette.get_color("white")
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(
                    zone_x,
                    zone_y,
                    self.msr.zone_sz,
                    self.msr.zone_sz
                ),
                ColorPalette.get_color(zone_color),
                2
            )
            arcade.draw_text(
                zone_name,
                zone_x,
                zone_y - self.msr.zone_sz // 2 - 25,
                ColorPalette.get_color(zone_color),
                (10.0 + self.msr.zone_sz / 15),
                self.msr.zone_sz,
                anchor_x="center",
                font_name=CUSTOM_FONT
            )

        for drone_id, (drone_x, drone_y) in current_state.drones.items():

            arcade.draw_texture_rect(
                self.drone_texture,
                arcade.XYWH(
                    drone_x,
                    drone_y,
                    self.msr.t_width,
                    self.msr.t_height
                )
            )
            arcade.draw_text(
                str(drone_id),
                drone_x,
                drone_y - self.msr.t_height // 2,
                ColorPalette.get_color("black"),
                (5 + (self.msr.t_height / 8)),
                anchor_x="center",
                font_name=CUSTOM_FONT
            )

    def add_state(
        self,
        zones: list[Zone],
        connections: list[Connection],
        drones_delivered: list[Drone],
        turn_log: str
    ) -> None:

        """

        Adds a new State object to store the information
        relevant to a new step in the simulation
        to be able to call it later without having to refactor anything.

        Parameters
        ----------
        zones: list[Zone]
            The zones of the drone map.
        connections: list[Connection]
            The connections between the zones.
        drones_delivered: list[Drone]
            The drones that already reached the goal zone
            (as they are no longer tracked actively,
            this variable helps to display them nonetheless).
        turn_log: str
            The drone movement's log
            pertaining to the current step in the simulation.

        """
        zones_coor: dict[str, tuple[int, int, str]] = {}
        con_coor: dict[str, tuple[int, int, int, int]] = {}
        drone_coor: dict[int, tuple[int, int]] = {}

        for zone in zones:

            zone_x = (
                (zone.x + self.msr.x_offset)
                * self.msr.px_sz
                + self.msr.padding
                + (self.msr.zone_sz // 2)
            )
            zone_y = (
                (zone.y + self.msr.y_offset)
                * self.msr.px_sz
                + self.msr.padding
                + (self.msr.zone_sz // 2) + 50
            )
            zones_coor[zone.name] = (zone_x, zone_y, zone.color)

        for con in connections:

            con_coor[con.name] = (
                zones_coor[con.zone1.name][0],
                zones_coor[con.zone1.name][1],
                zones_coor[con.zone2.name][0],
                zones_coor[con.zone2.name][1]
            )

            drones_occupying: list[Drone] = [
                d for d in con.occupied
                if isinstance(d.current_zone, Connection)
            ]

            if not len(drones_occupying):
                continue

            drone_coor.update(self.msr.calculate_drone_pos_on_con(
                con_coor[con.name],
                drones_occupying,
            ))

        for zone in zones:

            display_drones = (
                zone.occupied if not zone.is_goal
                else drones_delivered
            )

            drone_coor.update(self.msr.calculate_drone_pos_on_zone(
                (zones_coor[zone.name][0], zones_coor[zone.name][1]),
                display_drones,
            ))

        self.states.append(State(
            zones_coor,
            con_coor,
            drone_coor,
            len(self.states) - 1,
            turn_log
        ))

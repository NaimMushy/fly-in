import arcade
import warnings
import tkinter as tk
from .zones import Zone, Connection
from .drones import Drone
from .color_palette import ColorPalette


root = tk.Tk()
root.withdraw()
WIDTH = root.winfo_screenwidth()
HEIGHT = root.winfo_screenheight()
root.quit()

NB_COMMANDS = 6
MAX_WIDGET_HEIGHT = HEIGHT // 4 + 40
WIN_HEIGHT = HEIGHT - MAX_WIDGET_HEIGHT
TARGET_FPS = 60
arcade.load_font("ByteBounce.ttf")
CUSTOM_FONT = "ByteBounce"

warnings.filterwarnings("ignore")


class DisplayView(arcade.View):

    def __init__(self, display: "Display") -> None:

        super().__init__()

        self.display: "Display" = display
        self.background_color = ColorPalette.get_color("white")
        self.target_fps: int = 60
        self.frame_count: int = 0
        self.on_pause: bool = False
        self.step_by_step: bool = False

    def on_update(self, delta_time: float = 1 / 60):

        if self.on_pause or self.step_by_step:
            return

        self.frame_count += 1

        if self.frame_count < self.target_fps:
            return

        self.frame_count = 0
        self.display.cur_state_id += 1

        if self.display.cur_state_id == len(self.display.states):
            self.display.cur_state_id = 0

    def on_draw(self):

        if self.on_pause and not self.step_by_step:
            return

        self.clear()
        self.display.draw_state()

    def on_key_press(self, key, modifiers):

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

    def __init__(
        self,
        zones: dict[str, tuple[int, int, str]],
        connections: dict[str, tuple[int, int, int, int]],
        drones: dict[int, tuple[int, int]],
        turn_nb: int,
        turn_log: str
    ) -> None:

        self.zones: dict[str, tuple[int, int, str]] = zones
        self.connections: dict[str, tuple[int, int, int, int]] = connections
        self.drones: dict[int, tuple[int, int]] = drones
        self.turn_nb: int = turn_nb
        self.turn_log: str = turn_log


class Display:

    class Measures:

        def __init__(self, zones: list[Zone]) -> None:

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
            cls,
            drone_texture,
            zones: list[Zone]
        ) -> tuple[float, float]:

            max_drones_scale = max([z.max_drones for z in zones])

            scale = (
                (cls.zone_sz - 4 - (5 * (max_drones_scale - 1)))
                // max_drones_scale
            ) / drone_texture.width

            text_scaled_width: float = drone_texture.width * scale
            text_scaled_height: float = (drone_texture.height + 15) * scale

            while (
                text_scaled_width < 10 and
                text_scaled_height < 10 and
                max_drones_scale > 1
            ):

                max_drones_scale -= 1
                scale = (
                    (cls.zone_sz - 4 - (5 * (max_drones_scale - 1)))
                    // max_drones_scale
                ) / drone_texture.width
                text_scaled_width = drone_texture.width * scale
                text_scaled_height = (drone_texture.height + 15) * scale

            return text_scaled_width, text_scaled_height

        def calculate_drone_pos_on_con(
            cls,
            coordinates: tuple[int, int, int, int],
            drones_occupying: list[Drone],
            width: float,
            height: float
        ) -> dict[int, tuple[int, int]]:

            x1: int
            y1: int
            x2: int
            y2: int
            x1, y1, x2, y2 = coordinates

            x_start: int = x1
            y_start: int = y1
            x_end: int = x2
            y_end: int = y2

            if x1 > x2:
                x_start = x2
                x_end = x1

            if y1 > y2:
                y_start = y2
                y_end = y1

            if x1 != x2:
                x_start += cls.zone_sz // 2
                x_end -= cls.zone_sz // 2

            if y1 != y2:
                y_start += cls.zone_sz // 2
                y_end -= cls.zone_sz // 2

            drone_pos: list[tuple] = []

            nb_drones_on_con = (
                (x_start - x_end) // width
                if ((x_start - x_end) // width) < ((y_start - y_end) // height)
                else (y_start - y_end) // height
            )

            if nb_drones_on_con < 1:
                nb_drones_on_con = 1

            drone_startx = x_start + (
                (x_end - x_start) // nb_drones_on_con
            ) // 2
            drone_starty = y_start + (
                (y_end - y_start) // nb_drones_on_con
            ) // 2

            for _ in range(nb_drones_on_con):

                drone_pos.append((drone_startx, drone_starty))
                drone_startx += ((x_end - x_start) // nb_drones_on_con)
                drone_starty += ((y_end - y_start) // nb_drones_on_con)

            cur_pos = len(drone_pos) - len(drone_pos) // len(drones_occupying)

            drone_coor: dict[int, tuple[int, int]] = {}

            for drone in drones_occupying:

                drone_coor[drone.id] = drone_pos[cur_pos - 1]
                cur_pos -= 1

                if cur_pos <= 0:
                    break

            return drone_coor

        def calculate_drone_pos_on_zone(
            cls,
            zone_coor: tuple[int, int],
            display_drones: list[Drone],
            width: float,
            height: float
        ) -> dict[int, tuple[int, int]]:

            zone_x: int
            zone_y: int
            zone_x, zone_y = zone_coor

            drone_x = zone_x - cls.zone_sz // 2 + 2 + width // 2
            drone_y = zone_y + cls.zone_sz // 2 - 2 - height // 2

            drone_coor: dict[int, tuple[int, int]] = {}

            for drone in display_drones:

                if drone_x + width // 2 > zone_x + cls.zone_sz // 2 - 2:

                    drone_x = zone_x - cls.zone_sz // 2 + 2 + width // 2
                    drone_y -= height - 5

                if drone_y - height // 2 < zone_y - cls.zone_sz // 2 + 2:

                    drone_y = zone_y + cls.zone_sz // 2 - 2 - height // 2
                    drone_x = zone_x - cls.zone_sz // 2 + 2 + width // 2

                drone_coor[drone.id] = (drone_x, drone_y)

                drone_x += width + 5

            return drone_coor

    def __init__(self, zones: list[Zone]) -> None:

        self.msr = self.Measures(zones)
        self.states: list[State] = []
        self.cur_state_id: int = 0
        self.drone_texture = arcade.load_texture("drone_pixel_art.avif")
        print(type(self.drone_texture))

        self.text_scaled_width: float
        self.text_scaled_height: float

        self.text_scaled_width, self.text_scaled_height = (
            self.msr.calculate_drone_scale(self.drone_texture, zones)
        )

    def start_visu(self) -> None:

        window = arcade.Window(WIDTH, HEIGHT, "LET'S FLY IN", resizable=True)
        gameview: DisplayView = DisplayView(self)
        window.show_view(gameview)
        arcade.run()

    def draw_state(self) -> None:

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
        text_y: int = HEIGHT - title_height + 20

        arcade.draw_text(
            "USER COMMANDS",
            WIDTH // 6,
            text_y,
            ColorPalette.get_color("african_violet"),
            20.0,
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
                16.0,
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
            20.0,
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
                16.0,
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
                zone_y - self.msr.zone_sz // 2 - 15,
                ColorPalette.get_color(zone_color),
                14.0,
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
                    self.text_scaled_width,
                    self.text_scaled_height
                )
            )
            arcade.draw_text(
                str(drone_id),
                drone_x,
                drone_y - self.text_scaled_height // 2,
                ColorPalette.get_color("black"),
                (5 + (self.text_scaled_height / 8)),
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
                self.text_scaled_width,
                self.text_scaled_height
            ))

        for zone in zones:

            display_drones = (
                zone.occupied if not zone.is_goal
                else drones_delivered
            )

            drone_coor.update(self.msr.calculate_drone_pos_on_zone(
                (zones_coor[zone.name][0], zones_coor[zone.name][1]),
                display_drones,
                self.text_scaled_width,
                self.text_scaled_height
            ))

        self.states.append(State(
            zones_coor,
            con_coor,
            drone_coor,
            len(self.states) - 1,
            turn_log
        ))

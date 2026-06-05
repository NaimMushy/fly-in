import arcade
# import time
import tkinter as tk
from .zones import Zone, Connection
from .drones import Drone

NB_COMMANDS = 4

root = tk.Tk()
root.withdraw()
WIDTH = root.winfo_screenwidth()
HEIGHT = root.winfo_screenheight()
root.quit()
WIN_HEIGHT = HEIGHT - (30 * (NB_COMMANDS + 1))


TARGET_FPS = 60


class DisplayView(arcade.View):

    def __init__(self, display: "Display") -> None:

        super().__init__()

        self.display: "Display" = display
        self.background_color = arcade.color.WHITE
        self.target_fps: int = 60
        self.frame_count: int = 0
        self.on_pause: bool = False

    def on_update(self, delta_time: float = 1 / 60):

        if self.on_pause:
            return
        self.frame_count += 1
        if self.frame_count < self.target_fps:
            return
        self.frame_count = 0
        self.display.cur_state_id += 1
        if self.display.cur_state_id == len(self.display.states):
            self.display.cur_state_id = 0

    def on_draw(self):

        if self.on_pause:
            return
        self.clear()
        self.display.draw_state()

    def on_key_press(self, key, modifiers):

        if key == arcade.key.SPACE:
            self.on_pause = not (self.on_pause)
        if key == arcade.key.UP:
            if self.target_fps / 1.5 >= 20:
                self.target_fps = int(self.target_fps / 1.5)
        if key == arcade.key.DOWN:
            if self.target_fps * 1.5 <= 180:
                self.target_fps = int(self.target_fps * 1.5)
        if key == arcade.key.ESCAPE:
            arcade.close_window()


class State:

    def __init__(self, zones: dict, connections: dict, drones: dict, turn_nb: int) -> None:

        self.zones: dict = zones
        self.connections: dict = connections
        self.drones: dict = drones
        self.turn_nb: int = turn_nb

    def display_information(self) -> None:

        print(f"==== TURN {self.turn_nb} ====\n")
        fst: bool = True

        for drone in [d for d in self.drones.keys() if not d.waiting]:

            if not fst:
                print(" ")

            print(f"D{drone.id}-{drone.occupying.name}", end="")
            fst = False

        print()


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
            ) + 1
            board_height: int = (
                max_y if min_y >= 0 else (max_y - min_y)
            ) + 1

            self.px_sz = (WIN_HEIGHT // board_height if WIN_HEIGHT // board_height < WIDTH // board_width else WIDTH // board_width) + 1
            self.zone_sz = (self.px_sz - 25) // 2
            self.padding = self.zone_sz // 2

    def __init__(self, zones: list[Zone]) -> None:

        self.msr = self.Measures(zones)
        self.states: list[State] = []
        self.cur_state_id: int = 0
        self.drone_texture = arcade.load_texture("drone_pixel_art.avif")
        max_drones_scale = max([z.max_drones for z in zones])
        scale = ((self.msr.zone_sz - 4 - (5 * (max_drones_scale - 1))) // max_drones_scale) / self.drone_texture.width
        self.text_scaled_width = self.drone_texture.width * scale
        self.text_scaled_height = (self.drone_texture.height + 20) * scale
        while self.text_scaled_width < 20 and self.text_scaled_height < 20 and max_drones_scale > 1:
            max_drones_scale -= 1
            scale = ((self.msr.zone_sz - 4 - (5 * (max_drones_scale - 1))) // max_drones_scale) / self.drone_texture.width
            self.text_scaled_width = self.drone_texture.width * scale
            self.text_scaled_height = (self.drone_texture.height + 20) * scale
        nb_drones_vertical = self.msr.zone_sz // self.text_scaled_height
        self.id_maxwidth = (self.msr.zone_sz - (nb_drones_vertical * self.text_scaled_height)) // nb_drones_vertical

    def start_visu(self) -> None:

        window = arcade.Window(WIDTH, HEIGHT, "FLY IN DRONES", resizable=True)
        gameview: DisplayView = DisplayView(self)
        window.show_view(gameview)
        arcade.run()

    def get_line_points(self, zone1: Zone, zone2: Zone, zones_coor: dict) -> tuple[int, int, int, int]:

        zone1_x, zone1_y = zones_coor[zone1.name]
        zone2_x, zone2_y = zones_coor[zone2.name]
        return zone1_x, zone1_y, zone2_x, zone2_y
#         x_offset = self.msr.zone_sz // 2 + 5
#         y_offset = self.msr.zone_sz // 2 + 5
#         if zone1.y == zone2.y:
# 
#             if zone1.x < zone2.x:
#                 return zone1_x + x_offset, zone1_y, zone2_x - x_offset, zone2_y
# 
#             return zone2_x + x_offset, zone2_y, zone1_x - x_offset, zone1_y
# 
#         elif zone1.y < zone2.y:
# 
#             if zone1.x == zone2.x:
#                 return zone1_x, zone1_y + y_offset, zone2_x, zone2_y - y_offset
# 
#             elif zone1.x < zone2.x:
#                 return zone1_x, zone1_y + y_offset, zone2_x, zone2_y - y_offset
# 
#             return zone1_x, zone1_y - y_offset, zone2_x, zone2_y + y_offset
# 
#         if zone1.x == zone2.x:
#             return zone1_x, zone1_y - y_offset, zone2_x, zone2_y + y_offset
# 
#         elif zone1.x < zone2.x:
#             return zone1_x, zone1_y - y_offset, zone2_x, zone2_y + y_offset
# 
#         return zone1_x, zone1_y + y_offset, zone2_x, zone2_y - y_offset

    def draw_state(self) -> None:

        current_state: State = self.states[self.cur_state_id]

        arcade.draw_line(
            WIDTH // 2,
            WIN_HEIGHT,
            WIDTH // 2,
            HEIGHT,
            arcade.color.BLACK,
            2
        )
        text_y: int = HEIGHT - 30
        print(HEIGHT, WIN_HEIGHT)
        arcade.draw_text("USER COMMANDS:", WIDTH // 4, text_y, arcade.color.BLACK, 14.0, anchor_x="center")
        for command in [" ➤ space: pause", " ➤ arrow up: speed up", " ➤ arrow down: slow down", " ➤ escape: stop the simulation"]:
            text_y -= 20
            arcade.draw_text(command, WIDTH // 8, text_y, arcade.color.BLACK, 10.0)

        for x1, y1, x2, y2 in current_state.connections.values():

            arcade.draw_line(
                x1,
                y1,
                x2,
                y2,
                arcade.color.BLACK,
                2
            )

        for zone_name, (zone_x, zone_y) in current_state.zones.items():

            arcade.draw_rect_filled(arcade.rect.XYWH(zone_x, zone_y, self.msr.zone_sz + 10, self.msr.zone_sz + 10), arcade.color.WHITE)
            arcade.draw_rect_outline(arcade.rect.XYWH(zone_x, zone_y, self.msr.zone_sz, self.msr.zone_sz), arcade.color.BRITISH_RACING_GREEN, 2)
            arcade.draw_text(zone_name, zone_x, zone_y - self.msr.zone_sz // 2 - 10, arcade.color.BLACK, 10.0, self.msr.zone_sz, anchor_x="center")

        for drone_id, (drone_x, drone_y) in current_state.drones.items():

            arcade.draw_texture_rect(
                self.drone_texture,
                arcade.XYWH(drone_x, drone_y, self.text_scaled_width, self.text_scaled_height)
            )
            arcade.draw_text(str(drone_id), drone_x, drone_y - self.text_scaled_height // 2 - 5, arcade.color.BLACK, 10.0, width=self.id_maxwidth, anchor_x="center")

    def add_state(self, zones: list[Zone], connections: list[Connection], drones_delivered: list[Drone]) -> None:

        zones_coor: dict[str, tuple[int, int]] = {}
        con_coor: dict[str, tuple[int, int, int, int]] = {}
        drone_coor: dict[int, tuple[int, int]] = {}

        for zone in zones:

            zone_x = (zone.x + self.msr.x_offset) * self.msr.px_sz + self.msr.padding + self.msr.zone_sz // 2
            zone_y = (zone.y + self.msr.y_offset) * self.msr.px_sz + self.msr.padding + self.msr.zone_sz // 2
            zones_coor[zone.name] = (zone_x, zone_y)

        for con in connections:

            x1, y1, x2, y2 = self.get_line_points(con.zone1, con.zone2, zones_coor)
            con_coor[con.name] = (x1, y1, x2, y2)
            drones_occupying: list[Drone] = [d for d in con.occupied if isinstance(d.current_zone, Connection)]
            if not len(drones_occupying):
                continue
            print(x1, y1, x2, y2)
            x_sign = 0
            y_sign = 0
            if x1 > x2:
                x_sign = -1
            elif x2 > x1:
                x_sign = 1
            if y1 > y2:
                y_sign = -1
            elif y2 > y1:
                y_sign = 1
            if x_sign != 0:
                x1 += (self.msr.zone_sz // 2 * x_sign)
                x2 += (self.msr.zone_sz // 2 * (-x_sign))
            if y_sign != 0:
                y1 += (self.msr.zone_sz // 2 * y_sign)
                y2 += (self.msr.zone_sz // 2 * (-y_sign))
            print(x1, y1, x2, y2)
            drone_pos: list[tuple] = []
            nb_drones_on_con = (
                (x2 - x1) if (x2 - x1) > (y2 - y1)
                else (y2 - y1)
            )
            print(nb_drones_on_con)
            drone_startx = x1 + ((x2 - x1) // nb_drones_on_con // 2)
            drone_starty = y1 + ((y2 - y1) // nb_drones_on_con // 2)
            for _ in range(nb_drones_on_con):
                drone_pos.append((drone_startx, drone_starty))
                drone_startx += (x2 - x1) // nb_drones_on_con
                drone_starty += (y2 - y1) // nb_drones_on_con
            cur_pos = nb_drones_on_con - (nb_drones_on_con - len(drones_occupying)) // 2
            for drone in drones_occupying:
                drone_coor[drone.id] = drone_pos[cur_pos]
                print(f"drone {drone.id} has been situated at pos {drone_pos[cur_pos]}\n")
                cur_pos -= 1
                if cur_pos < 0:
                    cur_pos = nb_drones_on_con - (nb_drones_on_con - len(con.occupied)) // 2

        for zone in zones:

            drone_x = zones_coor[zone.name][0] - self.msr.zone_sz // 2 + 2 + self.text_scaled_width // 2
            drone_y = zones_coor[zone.name][1] + self.msr.zone_sz // 2 - 2 - self.text_scaled_height // 2

            display_drones = (
                zone.occupied if not zone.is_goal
                else drones_delivered
            )
            for drone in display_drones:
                if drone_x + self.text_scaled_width // 2 > zones_coor[zone.name][0] + self.msr.zone_sz // 2 - 2:
                    drone_x = zones_coor[zone.name][0] - self.msr.zone_sz // 2 + 2 + self.text_scaled_width // 2
                    drone_y -= self.text_scaled_height - 5
                if drone_y - self.text_scaled_height // 2 < zones_coor[zone.name][1] - self.msr.zone_sz // 2 + 2:
                    drone_y = zones_coor[zone.name][1] + self.msr.zone_sz // 2 - 2 - self.text_scaled_height // 2
                    drone_x = zones_coor[zone.name][0] - self.msr.zone_sz // 2 + 2 + self.text_scaled_width // 2

                drone_coor[drone.id] = (drone_x, drone_y)
                drone_x += self.text_scaled_width + 5

        self.states.append(State(zones_coor, con_coor, drone_coor, len(self.states) - 1))

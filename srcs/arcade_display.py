import arcade
import time
from .zones import Zone, Connection
from .drones import DroneMonitor


class DisplayView(arcade.View):

    def __init__(self, display: "Display", monitor: DroneMonitor) -> None:

        super().__init__()

        self.display: "Display" = display
        self.monitor: DroneMonitor = monitor
        self.background_color = arcade.color.WHITE

    def on_update(self, delta_time):

        if not self.monitor.drones:
            return

        time.sleep(0.5)
        self.monitor.update_drones()

    def on_draw(self):

        if not self.monitor.drones:
            return

        self.clear()
        self.display.draw_zones()


class Display:

    def __init__(self, zones: list[Zone], connections: list[Connection], drone_monitor: DroneMonitor, px_sz: int = 100) -> None:

        self.zones: list[Zone] = zones
        self.connections: list[Connection] = connections
        self.px_sz: int = px_sz
        self.zone_sz: int = px_sz // 2
        self.padding: int = (self.px_sz - self.zone_sz) // 2
        self.calculate_board_sz()
        self.monitor: DroneMonitor = drone_monitor

    def start_visu(self):

        window = arcade.Window(self.board_width, self.board_height, "FLY IN DRONES")
        gameview: DisplayView = DisplayView(self, self.monitor)
        window.show_view(gameview)
        arcade.run()

    def calculate_board_sz(self) -> None:

        min_x: int = min([z.x for z in self.zones])
        min_y: int = min([z.y for z in self.zones])
        max_x: int = max([z.x for z in self.zones])
        max_y: int = max([z.y for z in self.zones])

        self.x_offset: int = (
            0 if min_x >= 0 else abs(min_x)
        )
        self.y_offset: int = (
            0 if min_y >= 0 else abs(min_y)
        )

        self.board_width: int = ((
            max_x if min_x >= 0 else (max_x - min_x)
        ) + 1) * self.px_sz
        self.board_height: int = ((
            max_y if min_y >= 0 else (max_y - min_y)
        ) + 1) * self.px_sz

    def get_line_points(self, zone1: Zone, zone2: Zone) -> tuple[int, int, int, int]:

        zone1_x, zone1_y = self.zones_coor[zone1.name]
        zone2_x, zone2_y = self.zones_coor[zone2.name]
        offset = self.zone_sz // 2 + 5
        if zone1.y == zone2.y:

            if zone1.x < zone2.x:
                return zone1_x + offset, zone1_y, zone2_x - offset, zone2_y

            return zone2_x + offset, zone2_y, zone1_x - offset, zone1_y
        
        elif zone1.y < zone2.y:

            if zone1.x == zone2.x:
                return zone1_x, zone1_y + offset, zone2_x, zone2_y - offset

            elif zone1.x < zone2.x:
                return zone1_x, zone1_y + offset, zone2_x, zone2_y - offset

            return zone1_x, zone1_y - offset, zone2_x, zone2_y + offset

        if zone1.x == zone2.x:
            return zone1_x, zone1_y - offset, zone2_x, zone2_y + offset

        elif zone1.x < zone2.x:
            return zone1_x, zone1_y - offset, zone2_x, zone2_y + offset

        return zone1_x, zone1_y + offset, zone2_x, zone2_y - offset
    
    def draw_zones(self) -> None:

        self.zones_coor = {}

        for zone in self.zones:

            zone_x = (zone.x + self.x_offset) * self.px_sz + self.padding + self.zone_sz // 2
            zone_y = (zone.y + self.y_offset) * self.px_sz + self.padding + self.zone_sz // 2
            self.zones_coor[zone.name] = (zone_x, zone_y)

        for con in self.connections:

            x1, y1, x2, y2 = self.get_line_points(con.zone1, con.zone2)

            arcade.draw_line(
                x1,
                y1,
                x2,
                y2,
                arcade.color.BLACK,
                2
            )

        texture = arcade.load_texture("drone_pixel_art.avif")
        scale = .01
        scaled_width = texture.width * scale
        scaled_height = texture.height * scale

        for zone in self.zones:

            arcade.draw_rect_filled(arcade.rect.XYWH(self.zones_coor[zone.name][0], self.zones_coor[zone.name][1], self.zone_sz, self.zone_sz), arcade.color.WHITE)
            arcade.draw_rect_outline(arcade.rect.XYWH(self.zones_coor[zone.name][0], self.zones_coor[zone.name][1], self.zone_sz, self.zone_sz), arcade.color.BRITISH_RACING_GREEN, 2)

            drone_startx = self.zones_coor[zone.name][0] - self.zone_sz // 2 + 2 + scaled_width // 2
            drone_starty = self.zones_coor[zone.name][1] + self.zone_sz // 2 - 2 - scaled_height // 2

            print(f"zone start coordinates : x = {self.zones_coor[zone.name][0] - self.zone_sz // 2} y = {self.zones_coor[zone.name][1] + self.zone_sz // 2}")
            print(f"drone start coordinates : x = {drone_startx, drone_starty}")
            display_drones = (
                zone.occupied if zone != self.monitor.drones[0].goal
                else self.monitor.drones_delivered
            )
            for drone in display_drones:
                if drone_startx + scaled_width > self.zones_coor[zone.name][0] + self.zone_sz - 2:
                    drone_startx = self.zones_coor[zone.name][0] - self.zone_sz // 2 + 2 + scaled_width // 2
                    drone_starty -= scaled_height - 5
                if drone_starty < self.zones_coor[zone.name][1] - self.zone_sz // 2 + 2:
                    drone_starty = self.zones_coor[zone.name][1] + self.zone_sz // 2 - 2 - scaled_height // 2

                arcade.draw_texture_rect(
                    texture,
                    arcade.XYWH(drone_startx, drone_starty, scaled_width, scaled_height)
                )
                # arcade.draw_point(drone_startx, drone_starty, arcade.color.RED, 5)
                drone_startx += scaled_width + 5

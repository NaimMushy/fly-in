import arcade
from .zones import Zone, Connection


class Display:

    def __init__(self, zones: list[Zone], connections: list[Connection], px_sz: int = 100) -> None:

        self.zones: list[Zone] = zones
        self.connections: list[Connection] = connections
        self.px_sz: int = px_sz
        self.zone_sz: int = px_sz // 2
        self.padding: int = (self.px_sz - self.zone_sz) // 2
        self.calculate_board_sz()

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

        arcade.open_window(self.board_width, self.board_height, "arcade test", resizable=True)

        arcade.set_background_color(arcade.color.WHITE)

        arcade.start_render()

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

        for zone in self.zones:

            arcade.draw_rect_filled(arcade.rect.XYWH(self.zones_coor[zone.name][0], self.zones_coor[zone.name][1], self.zone_sz, self.zone_sz), arcade.color.WHITE)
            arcade.draw_rect_outline(arcade.rect.XYWH(self.zones_coor[zone.name][0], self.zones_coor[zone.name][1], self.zone_sz, self.zone_sz), arcade.color.BRITISH_RACING_GREEN, 2)

        arcade.finish_render()

        arcade.run()

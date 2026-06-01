import arcade
from .zones import Zone


class Display:

    def __init__(self, zones: list[Zone], px_sz: int = 100) -> None:

        self.zones: list[Zone] = zones
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

    def draw_zones(self) -> None:

        arcade.open_window(self.board_width, self.board_height, "arcade test", resizable=True)

        arcade.set_background_color(arcade.color.WHITE)

        arcade.start_render()

        for zone in self.zones:

            zone_x = (zone.x + self.x_offset) * self.px_sz + self.padding + self.zone_sz // 2
            zone_y = (zone.y + self.y_offset) * self.px_sz + self.padding + self.zone_sz // 2
            arcade.draw_rect_outline(arcade.rect.XYWH(zone_x, zone_y, self.zone_sz, self.zone_sz), arcade.color.BRITISH_RACING_GREEN)

        arcade.finish_render()

        arcade.run()

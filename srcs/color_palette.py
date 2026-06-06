import arcade
import inspect


class ColorPalette:

    colors: dict[str, arcade.types.color.Color] = {
        name: value for name, value in inspect.getmembers(arcade.color)
        if name.isupper() and not name.startswith('_')
    }

    @classmethod
    def get_color(cls, color_to_get: str) -> arcade.types.color.Color:

        if color_to_get.upper() not in cls.colors.keys():
            return cls.colors["BLACK"]

        if any([
            color_name == color_to_get.upper()
            for color_name in cls.colors.keys()
        ]):
            return cls.colors[color_to_get.upper()]

        available_colors: list[str] = [
            color_name for color_name in cls.colors.keys()
            if color_to_get.upper() in color_name
        ]
        return cls.colors[available_colors[0]]

_ALIASES: dict[str, str] = {
    "grey": "gray",
    "colour": "color",
    "colours": "colors",
    "centre": "center",
    "watercolour": "watercolor",
    "harmonious": "harmonious",
    "rothko-like": "rothko",
    "rothko style": "rothko",
    "mondrian-like": "mondrian",
    "mondrian style": "mondrian",
    "pollock-like": "pollock",
    "abstract expressionist": "abstract_expressionism",
    "neoplasticism": "de_stijl",
    "color field": "color_field",
    "colour field": "color_field",
    "drip painting": "pollock",
    "action painting": "abstract_expressionism",
}


class StyleRegistry:
    def canonicalize(self, name: str) -> str:
        lower = name.lower().strip()
        return _ALIASES.get(lower, lower)

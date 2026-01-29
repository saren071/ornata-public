"""Parser for the Ornata Styling (OSTS) language."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.api.exports.definitions import ColorToken, ComponentRule, FontDef, Keyframe, Keyframes, MediaQuery, MediaRule, Property, StateBlock, Stylesheet

class _Parser:
    """Recursive descent parser for OSTS."""

    def __init__(self, filename: str, text: str) -> None:
        from ornata.api.exports.definitions import Lexer
        self.lx = Lexer(text, filename)

    def parse(self) -> Stylesheet:
        """Parse the entire stylesheet and return a ``Stylesheet`` node."""
        from ornata.api.exports.definitions import Stylesheet

        colors: dict[str, ColorToken] = {}
        fonts: dict[str, FontDef] = {}
        keyframes: dict[str, Keyframes] = {}
        media_rules: list[MediaRule] = []
        component_rules: list[ComponentRule] = []

        while True:
            self.lx.skip_ws_and_comments()
            if not self.lx.peek():
                break
            if self.lx.peek() == "@":
                directive = self._parse_directive_name()
                if directive == "colors":
                    colors.update(self._parse_colors())
                elif directive == "fonts":
                    fonts.update(self._parse_fonts())
                elif directive == "keyframes":
                    name = self._parse_identifier()
                    keyframes[name] = self._parse_keyframes(name)
                elif directive == "media":
                    media_rules.append(self._parse_media_rule())
                else:
                    from ornata.styling.language import diag
                    diag.warn(f"{self.lx.filename}:{self.lx.line}:{self.lx.col}: unknown directive '@{directive}'")
                    self._skip_block()
            else:
                component_rules.append(self._parse_component_rule())
        return Stylesheet(
            filename=self.lx.filename,
            colors=colors,
            fonts=fonts,
            keyframes=keyframes,
            media_rules=media_rules,
            rules=component_rules,
        )

    def _parse_directive_name(self) -> str:
        """Parse the identifier following ``@``."""

        self.lx.advance()  # consume '@'
        return self._parse_identifier()

    def _parse_identifier(self) -> str:
        """Parse an identifier allowing dashes and underscores."""

        self.lx.skip_ws_and_comments()
        start = self.lx.pos

        if start >= len(self.lx.text):
            raise ValueError(f"{self.lx.filename}:{self.lx.line}:{self.lx.col}: unexpected EOF while parsing identifier")

        while True:
            ch = self.lx.peek()
            if not ch or not (ch.isalnum() or ch in {"-", "_", "/"}):
                break
            self.lx.advance()

        if self.lx.pos == start:
            raise ValueError(f"{self.lx.filename}:{self.lx.line}:{self.lx.col}: expected identifier")
        return self.lx.text[start:self.lx.pos].strip()

    def _expect(self, char: str) -> None:
        """Expect a specific character raising ``ValueError`` otherwise."""

        self.lx.skip_ws_and_comments()
        if self.lx.peek() != char:
            raise ValueError(f"{self.lx.filename}:{self.lx.line}:{self.lx.col}: expected '{char}'")
        self.lx.advance()

    def _parse_colors(self) -> dict[str, ColorToken]:
        """Parse a ``@colors`` block."""
        from ornata.api.exports.definitions import ColorToken

        result: dict[str, ColorToken] = {}
        self._expect("{")
        while True:
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == "}":
                self.lx.advance()
                break
            name = self._parse_identifier()
            self._expect(":")
            value = self._parse_value(until={";", "}"})
            self._expect(";")
            result[name] = ColorToken(name, value, self.lx.span())
        return result

    def _parse_fonts(self) -> dict[str, FontDef]:
        """Parse a ``@fonts`` block."""
        from ornata.api.exports.definitions import FontDef

        fonts: dict[str, FontDef] = {}
        self._expect("{")
        while True:
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == "}":
                self.lx.advance()
                break
            name = self._parse_identifier()
            # Font blocks historically omitted the colon separator, so allow either form
            if self.lx.peek() == ":":
                self.lx.advance()
            self._expect("{")
            size = None
            weight = None
            family = None
            while True:
                self.lx.skip_ws_and_comments()
                if self.lx.peek() == "}":
                    self.lx.advance()
                    break
                key = self._parse_identifier()
                self._expect(":")
                raw = self._parse_value(until={";", "}"})
                if self.lx.peek() == ";":
                    self.lx.advance()
                if key == "size":
                    try:
                        size = float(raw)
                    except ValueError:
                        from ornata.styling.language import diag
                        diag.warn(f"{self.lx.filename}:{self.lx.line}:{self.lx.col}: invalid font size '{raw}'")
                elif key == "weight":
                    weight = raw
                elif key == "family":
                    family = raw.strip('"')
            if self.lx.peek() == ";":
                self.lx.advance()
            fonts[name] = FontDef(name, size, weight, family, self.lx.span())
        return fonts

    def _parse_keyframes(self, name: str) -> Keyframes:
        """Parse a ``@keyframes`` block."""
        from ornata.api.exports.definitions import Keyframe, Keyframes

        self._expect("{")
        frames: list[Keyframe] = []
        while True:
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == "}":
                self.lx.advance()
                break
            selector = self._parse_identifier()
            if self.lx.peek() == "%":
                self.lx.advance()
                selector = f"{selector}%"
            position = self._keyframe_position(selector)
            self._expect("{")
            props: dict[str, Any] = {}
            while True:
                self.lx.skip_ws_and_comments()
                if self.lx.peek() == "}":
                    self.lx.advance()
                    break
                key = self._parse_identifier()
                self._expect(":")
                value = self._parse_value(until={";", "}"})
                if self.lx.peek() == ";":
                    self.lx.advance()
                props[key] = value
            frames.append(Keyframe(position, props))
        return Keyframes(name, frames)

    def _parse_media_rule(self) -> MediaRule:
        """Parse a ``@media`` rule."""
        from ornata.api.exports.definitions import MediaRule

        queries = self._parse_media_queries()
        component_rules: list[ComponentRule] = []
        self._expect("{")
        while True:
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == "}":
                self.lx.advance()
                break
            component_rules.append(self._parse_component_rule())
        return MediaRule(queries, component_rules)

    def _parse_media_queries(self) -> list[MediaQuery]:
        """Parse the query list in ``@media``."""
        from ornata.api.exports.definitions import MediaQuery

        queries: list[MediaQuery] = []
        self.lx.skip_ws_and_comments()
        self._expect("(")
        while True:
            feature = self._parse_identifier()
            operator = "eq"
            if feature.startswith("min-"):
                operator = "min"
                feature = feature[4:]
            elif feature.startswith("max-"):
                operator = "max"
                feature = feature[4:]
            self._expect(":")
            value = self._parse_value(until={")", "and"})
            queries.append(MediaQuery(feature, operator, value))
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == ")":
                self.lx.advance()
                break
            next_char = self.lx.peek()
            if not next_char or not next_char.isalpha():
                break
            if self._parse_identifier().lower() != "and":
                break
            self._expect("(")
        return queries

    def _parse_component_rule(self) -> ComponentRule:
        """Parse a component selector and its blocks."""
        from ornata.api.exports.definitions import ComponentRule, StateBlock

        name = self._parse_identifier()
        span = self.lx.span()
        self._expect("{")
        blocks: list[StateBlock] = []
        default_props: list[tuple[str, str]] = []
        default_properties: list[Property] = []

        while True:
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == "}":
                self.lx.advance()
                break
            if self.lx.peek() == "[":
                blocks.append(self._parse_state_block(name))
                continue
            prop = self._parse_property()
            default_properties.append(prop)
            default_props.append((prop.name, prop.value))

        if default_props:
            blocks.insert(0, StateBlock(frozenset(), default_properties, span, default_props))
        return ComponentRule(name, blocks, span)

    def _parse_state_block(self, component: str) -> StateBlock:
        """Parse a state-specific block like ``[hover] { ... }``."""
        from ornata.api.exports.definitions import StateBlock

        self._expect("[")
        states: list[str] = []
        while True:
            state = self._parse_identifier()
            states.append(state)
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == ",":
                self.lx.advance()
                continue
            if self.lx.peek() == "]":
                self.lx.advance()
                break
            raise ValueError(f"{self.lx.filename}:{self.lx.line}:{self.lx.col}: expected ',' or ']' in state block")
        span = self.lx.span()
        self._expect("{")
        props: list[Property] = []
        raw: list[tuple[str, str]] = []
        while True:
            self.lx.skip_ws_and_comments()
            if self.lx.peek() == "}":
                self.lx.advance()
                break
            prop = self._parse_property()
            props.append(prop)
            raw.append((prop.name, prop.value))
        return StateBlock(frozenset(states), props, span, raw)

    def _parse_property(self) -> Property:
        """Parse a property declaration ending with ``;``."""
        from ornata.api.exports.definitions import Property

        name = self._parse_identifier()
        span = self.lx.span()
        self._expect(":")
        value = self._parse_value(until={";", "}"})
        if self.lx.peek() == ";":
            self.lx.advance()
        return Property(name, value, span)

    def _parse_value(self, *, until: set[str]) -> str:
        """Parse a property value until any character in ``until`` is reached."""

        buff: list[str] = []
        depth = 0
        quote: str | None = None
        while True:
            ch = self.lx.peek()
            if not ch:
                break
            if quote:
                buff.append(self.lx.advance())
                if ch == quote:
                    quote = None
                continue
            if ch in {'"', "'"}:
                quote = ch
                buff.append(self.lx.advance())
                continue
            if ch == "(":
                depth += 1
                buff.append(self.lx.advance())
                continue
            if ch == ")":
                if depth == 0 and ")" in until:
                    return "".join(buff).strip()
                depth = max(0, depth - 1)
                buff.append(self.lx.advance())
                continue
            if depth == 0:
                for stop in until:
                    if ch == stop or (stop.isalpha() and self.lx.text[self.lx.pos :].startswith(stop)):
                        return "".join(buff).strip()
            buff.append(self.lx.advance())
        return "".join(buff).strip()

    def _keyframe_position(self, selector: str) -> float:
        """Convert a keyframe selector into a numeric position."""

        if selector == "from":
            return 0.0
        if selector == "to":
            return 1.0
        if selector.endswith("%"):
            return float(selector[:-1]) / 100.0
        return float(selector)

    def _skip_block(self) -> None:
        """Skip a balanced ``{}`` block."""

        depth = 0
        while True:
            ch = self.lx.peek()
            if not ch:
                break
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    self.lx.advance()
                    break
            self.lx.advance()


def parse_stylesheet(name: str, text: str) -> Stylesheet:
    """Parse ``text`` and return a :class:`Stylesheet`."""

    parser = _Parser(name, text)
    return parser.parse()


__all__ = ["parse_stylesheet"]

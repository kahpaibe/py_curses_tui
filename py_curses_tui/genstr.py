from typing import Iterable, Optional, overload, Any
from dataclasses import dataclass, field


@dataclass
class GenStrSection:
    """A section of a GenStr, consisting of text with optional color and attribute."""

    text: str
    color_pair: Optional[int] = None
    attrs: list[int] = field(default_factory=list)

    def to_ainsi(self) -> str:
        """Convert the GenStrSection to a string with ANSI escape codes for colors and attributes."""
        color_code = f"\033[{self.color_pair}m" if self.color_pair is not None else ""
        attr_code = "".join(f"\033[{attr}m" for attr in self.attrs)
        reset_code = "\033[0m" if (self.color_pair is not None or self.attrs) else ""
        return f"{color_code}{attr_code}{self.text}{reset_code}"


class GenStr(list[GenStrSection]):
    """Generalized string: list of string sections with optional color and attribute."""

    @overload
    def __init__(self, desc: GenStrSection) -> None: ...

    @overload
    def __init__(self, desc: str) -> None: ...

    @overload
    def __init__(
        self,
        desc: tuple[str] | tuple[str, int | None] | tuple[str, int | None, list[int]],
    ) -> None: ...

    @overload
    def __init__(
        self,
        desc: Iterable[
            GenStrSection
            | str
            | tuple[str]
            | tuple[str, int | None]
            | tuple[str, int | None, list[int]]
        ],
    ) -> None: ...

    @overload
    def __init__(self, desc: "GenStr") -> None: ...

    def __init__(self, desc: Any) -> None:
        """Generalized string: list of string sections with optional color and attribute."""
        if isinstance(desc, GenStr):
            return super().__init__(desc)

        if isinstance(desc, GenStrSection):
            return super().__init__([desc])

        if isinstance(desc, str):
            return super().__init__([GenStrSection(desc)])

        if isinstance(desc, Iterable):
            # Try if it's an iterable of sections
            sections: list[GenStrSection | None] = [
                self._to_genstr_section(item) for item in desc
            ]
            if all(section is not None for section in sections):
                return super().__init__(
                    section for section in sections if section is not None
                )

            # There are some invalid items, try if it's a single section
            if isinstance(desc, tuple):
                section = self._to_genstr_section(desc)
                if section is not None:
                    return super().__init__([section])

        raise ValueError("Invalid GenStr description")

    @staticmethod
    def _to_genstr_section(item: Any) -> GenStrSection | None:
        """Convert an item to a GenStrSection if possible, otherwise return None."""

        if isinstance(item, GenStrSection):
            return item

        if isinstance(item, str):
            return GenStrSection(item)

        if isinstance(item, tuple):
            if len(item) == 1 and isinstance(item[0], str):
                return GenStrSection(item[0])
            elif (
                len(item) == 2
                and isinstance(item[0], str)
                and (isinstance(item[1], int) or item[1] is None)
            ):
                return GenStrSection(item[0], color_pair=item[1])
            elif (
                len(item) == 3
                and isinstance(item[0], str)
                and (isinstance(item[1], int) or item[1] is None)
                and (isinstance(item[2], list) or item[2] is None)
            ):
                return GenStrSection(item[0], color_pair=item[1], attrs=item[2])

        return None  # Invalid item format

    def __setitem__(
        self,
        index: int,
        item: GenStrSection
        | str
        | tuple[str]
        | tuple[str, int | None]
        | tuple[str, int | None, list[int]],
    ) -> None:
        """Set an item in the GenStr, converting it to a GenStrSection if necessary."""
        section = self._to_genstr_section(item)
        if section is None:
            raise ValueError("Invalid GenStrSection description for setting item")
        super().__setitem__(index, section)

    def insert(
        self,
        index: int,
        item: GenStrSection
        | str
        | tuple[str]
        | tuple[str, int | None]
        | tuple[str, int | None, list[int]],
    ) -> None:
        """Insert an item into the GenStr, converting it to a GenStrSection if necessary."""
        section = self._to_genstr_section(item)
        if section is None:
            raise ValueError("Invalid GenStrSection description for inserting item")
        super().insert(index, section)

    def append(
        self,
        item: GenStrSection
        | str
        | tuple[str]
        | tuple[str, int | None]
        | tuple[str, int | None, list[int]],
    ) -> None:
        """Append an item to the GenStr, converting it to a GenStrSection if necessary."""
        section = self._to_genstr_section(item)
        if section is None:
            raise ValueError("Invalid GenStrSection description for appending item")
        super().append(section)

    def extend(
        self,
        items: Iterable[
            GenStrSection
            | str
            | tuple[str]
            | tuple[str, int | None]
            | tuple[str, int | None, list[int]]
        ],
    ) -> None:
        """Extend the GenStr with items, converting them to GenStrSections if necessary."""
        for item in items:
            self.append(item)

    @classmethod
    def _coerce_to_genstr(cls, desc: Any) -> "GenStr | None":
        """Coerce a constructor-compatible descriptor into a GenStr, else return None."""
        if isinstance(desc, GenStr):
            return GenStr(desc)

        if isinstance(desc, GenStrSection):
            return GenStr([desc])

        if isinstance(desc, str):
            return GenStr([GenStrSection(desc)])

        # Handle tuple explicitly first so tuple descriptors are not treated as generic iterables.
        if isinstance(desc, tuple):
            section = cls._to_genstr_section(desc)
            if section is None:
                return None
            return GenStr([section])

        if isinstance(desc, Iterable):
            sections: list[GenStrSection | None] = [
                cls._to_genstr_section(item) for item in desc
            ]
            if all(section is not None for section in sections):
                return GenStr(section for section in sections if section is not None)

        return None

    @overload
    def __add__(self, other: GenStrSection) -> "GenStr": ...

    @overload
    def __add__(self, other: str) -> "GenStr": ...

    @overload
    def __add__(
        self,
        other: tuple[str] | tuple[str, int | None] | tuple[str, int | None, list[int]],
    ) -> "GenStr": ...

    @overload
    def __add__(
        self,
        other: Iterable[
            GenStrSection
            | str
            | tuple[str]
            | tuple[str, int | None]
            | tuple[str, int | None, list[int]]
        ],
    ) -> "GenStr": ...

    @overload
    def __add__(self, other: "GenStr") -> "GenStr": ...

    def __add__(self, other: Any) -> "GenStr":
        """Concatenate with any constructor-compatible GenStr descriptor."""
        other_genstr = self._coerce_to_genstr(other)
        if other_genstr is None:
            return NotImplemented
        return GenStr([*self, *other_genstr])

    @overload
    def __radd__(self, other: GenStrSection) -> "GenStr": ...

    @overload
    def __radd__(self, other: str) -> "GenStr": ...

    @overload
    def __radd__(
        self,
        other: tuple[str] | tuple[str, int | None] | tuple[str, int | None, list[int]],
    ) -> "GenStr": ...

    @overload
    def __radd__(
        self,
        other: Iterable[
            GenStrSection
            | str
            | tuple[str]
            | tuple[str, int | None]
            | tuple[str, int | None, list[int]]
        ],
    ) -> "GenStr": ...

    @overload
    def __radd__(self, other: "GenStr") -> "GenStr": ...

    def __radd__(self, other: Any) -> "GenStr":
        """Support reverse concatenation with constructor-compatible descriptors."""
        other_genstr = self._coerce_to_genstr(other)
        if other_genstr is None:
            return NotImplemented
        return GenStr([*other_genstr, *self])

    def __mul__(self, times: int) -> "GenStr":
        """Repeat sections while preserving GenStr return type."""
        return GenStr(super().__mul__(times))

    def __rmul__(self, times: int) -> "GenStr":
        """Support reflected repetition while preserving GenStr return type."""
        return self.__mul__(times)

    def to_ainsi(self) -> str:
        """Print GenStr as a string with ANSI escape codes for colors and attributes."""
        return "".join(section.to_ainsi() for section in self)

    def total_length(self) -> int:
        """Get the total length of the represented string."""
        return sum(len(section.text) for section in self)

    @staticmethod
    def padded_genstr(genstr: "GenStr", length: int) -> "GenStr":
        """Pad a GenStr with spaces to a total length. Will truncate if the GenStr is longer than the specified length."""
        current_len = genstr.total_length()
        if current_len >= length:
            # Truncate the GenStr to the specified length
            truncated_sections: list[GenStrSection] = []
            remaining_len = length
            for section in genstr:
                if remaining_len <= 0:
                    break
                if len(section.text) <= remaining_len:
                    truncated_sections.append(section)
                    remaining_len -= len(section.text)
                else:
                    truncated_sections.append(
                        GenStrSection(
                            section.text[:remaining_len],
                            color_pair=section.color_pair,
                            attrs=section.attrs,
                        )
                    )
                    remaining_len = 0
            return GenStr(truncated_sections)
        else:
            # Pad the GenStr with spaces to the right
            padding = " " * (length - current_len)
            return genstr + padding

    def padded(self, length: int) -> "GenStr":
        """Pad this GenStr with spaces to a total length. Will truncate if this GenStr is longer than the specified length."""
        return self.padded_genstr(self, length)

    @staticmethod
    def centered_genstr(genstr: "GenStr", length: int) -> "GenStr":
        """Center a GenStr with spaces to a total length. Will truncate if the GenStr is longer than the specified length."""
        current_len = genstr.total_length()
        if current_len >= length:
            # Truncate the GenStr to the specified length
            truncated_sections: list[GenStrSection] = []
            remaining_len = length
            for section in genstr:
                if remaining_len <= 0:
                    break
                if len(section.text) <= remaining_len:
                    truncated_sections.append(section)
                    remaining_len -= len(section.text)
                else:
                    truncated_sections.append(
                        GenStrSection(
                            section.text[:remaining_len],
                            color_pair=section.color_pair,
                            attrs=section.attrs,
                        )
                    )
                    remaining_len = 0
            return GenStr(truncated_sections)
        else:
            # Pad the GenStr with spaces on both sides to center it
            total_padding = length - current_len
            left_padding = total_padding // 2
            right_padding = total_padding - left_padding
            return (" " * left_padding) + genstr + (" " * right_padding)

    def centered(self, length: int) -> "GenStr":
        """Center this GenStr with spaces to a total length. Will truncate if this GenStr is longer than the specified length."""
        return self.centered_genstr(self, length)


if __name__ == "__main__":  # Tests
    import re

    stats = {"total": 0, "passed": 0}
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    # Colors for test output
    _GREEN = "\033[32m"
    _RED = "\033[31m"
    _ORANGE = "\033[38;5;208m"
    _BLUE = "\033[34m"
    _RESET = "\033[0m"

    def section(title: str) -> None:
        print(f"\n{_ORANGE}=== {title} ==={_RESET}")

    def ansi_text(obj: Any) -> str:
        if isinstance(obj, GenStr):
            return obj.to_ainsi()
        if isinstance(obj, GenStrSection):
            return obj.to_ainsi()
        return str(obj)

    def plain_text(obj: Any) -> str:
        return ansi_re.sub("", ansi_text(obj))

    def report(name: str, ok: bool, detail: str, preview: Optional[str] = None) -> None:
        stats["total"] += 1
        if ok:
            stats["passed"] += 1
        status = f"{_GREEN}PASS{_RESET}" if ok else f"{_RED}FAIL{_RESET}"
        print(f"[{status}] {name}")
        print(f"       {detail}")
        if preview is not None:
            print(f"       {_BLUE}preview{_RESET}: {preview}")

    def expect_genstr(
        name: str,
        value: Any,
        expected_plain: str,
        expected_len: int,
    ) -> None:
        is_type_ok = isinstance(value, GenStr)
        actual_plain = plain_text(value) if is_type_ok else str(value)
        actual_len = len(value) if is_type_ok else -1
        ok = (
            is_type_ok and actual_plain == expected_plain and actual_len == expected_len
        )
        actual_ansi = ansi_text(value) if is_type_ok else str(value)
        detail = (
            f"type={type(value).__name__}, plain={actual_plain!r}, len={actual_len}; "
            f"expected type=GenStr, plain={expected_plain!r}, len={expected_len}"
        )
        report(name, ok, f"{detail}; ansi={actual_ansi!r}", preview=actual_ansi)

    def expect_raises(name: str, exc_type: type[Exception], fn: Any) -> None:
        try:
            fn()
            report(
                name,
                False,
                f"expected {exc_type.__name__}, but no exception was raised",
            )
        except exc_type as exc:
            report(name, True, f"raised {exc_type.__name__}: {exc}")
        except Exception as exc:  # pragma: no cover - for debug visibility
            report(
                name,
                False,
                f"expected {exc_type.__name__}, but got {type(exc).__name__}: {exc}",
            )

    section("Initialization")
    expect_genstr(
        "GenStr(GenStrSection('str'))", GenStr(GenStrSection("str")), "str", 1
    )
    expect_genstr("GenStr('str')", GenStr("str"), "str", 1)
    expect_genstr("GenStr(('str',))", GenStr(("str",)), "str", 1)
    expect_genstr("GenStr(('str', 31))", GenStr(("str", 31)), "str", 1)
    expect_genstr("GenStr(('str', None, [1]))", GenStr(("str", None, [1])), "str", 1)
    expect_genstr(
        "GenStr(['a', ('b',), ('c', 32), ('d', 33, [1])])",
        GenStr(["a", ("b",), ("c", 32), ("d", 33, [1])]),
        "abcd",
        4,
    )
    expect_raises("GenStr(123)", ValueError, lambda: GenStr(123))  # type: ignore[arg-type]

    section("GenStrSection ANSI")
    plain = GenStrSection("plain").to_ainsi()
    color = GenStrSection("red", color_pair=31).to_ainsi()
    attr = GenStrSection("bold", attrs=[1]).to_ainsi()
    color_attr = GenStrSection("red+bold", color_pair=31, attrs=[1]).to_ainsi()
    report("plain section", plain == "plain", f"repr={plain!r}", preview=plain)
    report(
        "color section",
        color == "\033[31mred\033[0m",
        f"repr={color!r}",
        preview=color,
    )
    report(
        "attr section",
        attr == "\033[1mbold\033[0m",
        f"repr={attr!r}",
        preview=attr,
    )
    report(
        "color+attr section",
        color_attr == "\033[31m\033[1mred+bold\033[0m",
        f"repr={color_attr!r}",
        preview=color_attr,
    )

    section("Mutations")
    g = GenStr("test")
    g[0] = "new text"
    expect_genstr("setitem str", g, "new text", 1)
    g[0] = ("new text with color", 34)
    expect_genstr("setitem tuple(color)", g, "new text with color", 1)
    g[0] = ("new text with color and attr", 34, [1])
    expect_genstr("setitem tuple(color+attr)", g, "new text with color and attr", 1)
    expect_raises("setitem invalid", ValueError, lambda: g.__setitem__(0, 123))  # type: ignore[arg-type]

    g = GenStr("test")
    g.insert(0, "inserted text")
    g.insert(1, ("insert color", 35))
    g.insert(2, ("insert color+attr", 35, [1]))
    expect_genstr(
        "insert sequence",
        g,
        "inserted textinsert colorinsert color+attrtest",
        4,
    )

    g = GenStr("test")
    g.append("appended text")
    g.append(("append color", 36))
    g.append(("append color+attr", 36, [1]))
    expect_genstr(
        "append sequence",
        g,
        "testappended textappend colorappend color+attr",
        4,
    )

    g = GenStr("test")
    g.extend(
        [
            "extended 1",
            ("extended 2",),
            ("extended 3", 37),
            ("extended 4", 37, [1]),
        ]
    )
    expect_genstr(
        "extend sequence", g, "testextended 1extended 2extended 3extended 4", 5
    )
    expect_raises("extend invalid", ValueError, lambda: g.extend([123]))  # type: ignore[list-item]

    section("Operators")
    left = GenStr([("L", 32), ("+",)])
    right = GenStr([("R", 36), ("!", 33, [1])])
    expect_genstr("left + right", left + right, "L+R!", 4)
    expect_genstr(
        "left + [GenStrSection(...)]",
        left + [GenStrSection(" sections", color_pair=35)],
        "L+ sections",
        3,
    )
    expect_genstr("left + ' str'", left + " str", "L+ str", 3)
    expect_genstr(
        "left + (' tuple', 34, [1])", left + (" tuple", 34, [1]), "L+ tuple", 3
    )
    expect_genstr(
        "left + iterable",
        left + [(" i1", 33), (" i2", 36, [1])],
        "L+ i1 i2",
        4,
    )
    expect_genstr("'prefix ' + left", "prefix " + left, "prefix L+", 3)
    expect_genstr("left * 3", left * 3, "L+L+L+", 6)
    expect_genstr("3 * left", 3 * left, "L+L+L+", 6)
    expect_raises("left + 123", TypeError, lambda: left + 123)  # type: ignore[operator]
    expect_raises("left * '3'", TypeError, lambda: left * "3")  # type: ignore[arg-type]

    section("Padding and Centering")
    expect_genstr(
        "padded_genstr pads right",
        GenStr.padded_genstr(GenStr("test"), 7),
        "test   ",
        2,
    )
    expect_genstr(
        "padded_genstr exact length",
        GenStr.padded_genstr(GenStr("test"), 4),
        "test",
        1,
    )
    expect_genstr(
        "padded_genstr truncates long",
        GenStr.padded_genstr(GenStr("longtext"), 4),
        "long",
        1,
    )
    expect_genstr(
        "centered_genstr centers",
        GenStr.centered_genstr(GenStr("hi"), 6),
        "  hi  ",
        3,
    )
    expect_genstr(
        "centered_genstr truncates long",
        GenStr.centered_genstr(GenStr("overflow"), 5),
        "overf",
        1,
    )
    expect_genstr(
        "padded instance helper",
        GenStr("ok").padded(5),
        "ok   ",
        2,
    )
    expect_genstr(
        "centered instance helper",
        GenStr("ok").centered(5),
        " ok  ",
        3,
    )

    print("\n=== Summary ===")
    failed = stats["total"] - stats["passed"]
    print(f"Passed: {stats['passed']} / {stats['total']}")
    if failed == 0:
        print("All checks passed. Output and behavior look good.")
    else:
        print(f"Failures: {failed}")
        raise SystemExit(1)

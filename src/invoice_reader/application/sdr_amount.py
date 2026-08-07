"""Parse SDR amounts written with decimal points or decimal commas."""

from decimal import Decimal, InvalidOperation
import re


_AMOUNT_PATTERN = re.compile(r"^[+-]?[0-9]+(?:[.,][0-9]+)*$")


def parse_sdr_amount(raw_value: str) -> Decimal:
    """Return an exact numeric SDR amount for a supported local number format."""
    compact_value = raw_value.strip().replace(" ", "").replace("\u00a0", "")
    if not compact_value or _AMOUNT_PATTERN.fullmatch(compact_value) is None:
        raise ValueError(f"SDR amount 不是有效数字：{raw_value}")

    sign = ""
    unsigned_value = compact_value
    if compact_value[0] in "+-":
        sign, unsigned_value = compact_value[0], compact_value[1:]

    decimal_text = _to_decimal_text(unsigned_value)
    try:
        return Decimal(f"{sign}{decimal_text}")
    except InvalidOperation as error:
        raise ValueError(f"SDR amount 不是有效数字：{raw_value}") from error


def normalize_sdr_amount(raw_value: str) -> str:
    """Return the approval-display form, always using a decimal point."""
    return format(parse_sdr_amount(raw_value), "f")


def _to_decimal_text(unsigned_value: str) -> str:
    has_comma = "," in unsigned_value
    has_point = "." in unsigned_value
    if has_comma and has_point:
        decimal_separator = "," if unsigned_value.rfind(",") > unsigned_value.rfind(".") else "."
        grouping_separator = "." if decimal_separator == "," else ","
        without_grouping = unsigned_value.replace(grouping_separator, "")
        if without_grouping.count(decimal_separator) != 1:
            raise ValueError(f"SDR amount 分隔符格式无效：{unsigned_value}")
        return without_grouping.replace(decimal_separator, ".")

    separator = "," if has_comma else "." if has_point else ""
    if not separator:
        return unsigned_value
    groups = unsigned_value.split(separator)
    if len(groups) == 2:
        return f"{groups[0]}.{groups[1]}"
    if all(len(group) == 3 for group in groups[1:]):
        return "".join(groups)
    if all(len(group) == 3 for group in groups[1:-1]):
        return f"{''.join(groups[:-1])}.{groups[-1]}"
    raise ValueError(f"SDR amount 分隔符格式无效：{unsigned_value}")

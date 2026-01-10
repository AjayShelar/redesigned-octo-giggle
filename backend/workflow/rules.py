from typing import Any, Tuple


def _get_value(data: dict, field: str) -> Any:
    return data.get(field)


def evaluate_rule(condition_type: str, params: dict, data: dict) -> Tuple[bool, str]:
    field = params.get("field")
    value = params.get("value")
    values = params.get("values") or params.get("options")
    requires = params.get("requires")

    if condition_type == "field_present":
        if not field:
            return False, "Missing field parameter"
        v = _get_value(data, field)
        passed = v is not None and v != ""
        return passed, f"{field} is required"

    if condition_type == "field_equals":
        if not field:
            return False, "Missing field parameter"
        v = _get_value(data, field)
        if requires:
            if v == value:
                req_val = _get_value(data, requires)
                if not req_val:
                    return False, f"{requires} is required when {field} is {value}"
            return True, ""
        if v != value:
            return False, f"{field} must equal {value}"
        return True, ""

    if condition_type == "field_in":
        if not field or not isinstance(values, list):
            return False, "Missing field or values"
        v = _get_value(data, field)
        passed = v in values
        return passed, f"{field} must be one of {values}"

    if condition_type in {"field_gt", "field_gte", "field_lt", "field_lte"}:
        if not field:
            return False, "Missing field parameter"
        v = _get_value(data, field)
        if v is None:
            return False, f"{field} is required"
        try:
            v_num = float(v)
            cmp_num = float(value)
        except (TypeError, ValueError):
            return False, f"{field} must be a number"

        if condition_type == "field_gt" and not (v_num > cmp_num):
            return False, f"{field} must be > {value}"
        if condition_type == "field_gte" and not (v_num >= cmp_num):
            return False, f"{field} must be >= {value}"
        if condition_type == "field_lt" and not (v_num < cmp_num):
            return False, f"{field} must be < {value}"
        if condition_type == "field_lte" and not (v_num <= cmp_num):
            return False, f"{field} must be <= {value}"
        return True, ""

    return False, f"Unsupported condition type: {condition_type}"

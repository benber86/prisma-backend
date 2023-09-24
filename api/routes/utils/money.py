def format_dollar_value(value: float) -> str:
    if value > 1e9:
        return f"${value/1e6:.1f}b"
    elif value > 1e6:
        return f"${value/1e6:.1f}m"
    elif value > 1e3:
        return f"${value/1e3:.1f}k"
    else:
        return f"${value}"

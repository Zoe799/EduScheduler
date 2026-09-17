def format_time(value):
    """
    Convert MySQL TIME values into HH:MM format.

    Examples:
        09:00:00 -> 09:00
        9:00:00  -> 09:00
        timedelta -> HH:MM
    """

    if value is None:
        return ""


    # MySQL connector may return timedelta
    if hasattr(value, "seconds"):

        total_seconds = value.seconds

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        return f"{hours:02d}:{minutes:02d}"


    text = str(value)


    parts = text.split(":")


    if len(parts) >= 2:

        try:

            hour = int(parts[0])
            minute = int(parts[1])

            return (
                f"{hour:02d}:"
                f"{minute:02d}"
            )

        except ValueError:
            pass


    return text
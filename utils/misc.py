
def get_ordinal(n):
    """Get Ordianal Number."""

    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'

    return str(n) + suffix

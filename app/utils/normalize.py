#Not in use currently
def normalize_value(value: str) -> str:
    """
    Ensures tags are consistently formatted:
    - trimmed
    - lowercase

    Prevents duplicates like "Cotton", " cotton ", "COTTON".
    """
    return value.strip().lower()
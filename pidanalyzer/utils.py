def strip_quotes(filepath: str) -> str:
    """Strips single or double quotes and extra whitespace from a string."""
    return filepath.strip().strip("'").strip('"')

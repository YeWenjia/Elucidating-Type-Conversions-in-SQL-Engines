"""Table - result of query execution"""


class Table:
    """Represents a table with columns and rows"""
    
    def __init__(self, cols, rows):
        self.cols = cols  # Internal names (may have #N suffixes for uniqueness)
        self.rows = rows

    def _display_name(self, col):
        """Convert internal name (with #N suffix) to display name"""
        # Remove #N suffix if present
        if '#' in col:
            return col.rsplit('#', 1)[0]
        return col

    def __str__(self):
        # Show display names (without #N suffixes) to user
        display_cols = [self._display_name(col) for col in self.cols]
        _str = ' | '.join(display_cols)+"\n"
        _str += '------------------------\n'
        _str += '\n'.join(list(map(lambda x: ' | '.join(map(lambda y: str(y), x)), self.rows)))
        return _str

    def __eq__(self, other):
        return self.cols == other.cols and self.rows == other.rows

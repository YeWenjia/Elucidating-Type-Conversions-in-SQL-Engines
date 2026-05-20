from datetime import datetime

from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.syntax.expression.BValue import BValue


def test_sqlite_compare_accepts_iso_date_text_from_driver():
    interpreter_rows = [[BValue(7782), BValue(datetime(1981, 6, 9)), BValue(False)]]
    sqlite_rows = [(7782, "1981-06-09", 0)]

    assert Engine().Compare(interpreter_rows, sqlite_rows, Sqlite())

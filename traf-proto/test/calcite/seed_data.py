"""
Canonical Calcite/SCOTT fixture data for calcite2.jsonlines tests.

Schema (shared across all 397 benchmark entries):
  EMP, DEPT, BONUS, EMPNULLABLES, EMPNULLABLES_20, EMP_B

Column order matches the "schema" block of every entry. NOT NULL constraints
declared in the benchmark are respected: EMP/EMP_B rows carry non-null values
for every column except MGR (KING is president, no manager). EMPNULLABLES and
EMPNULLABLES_20 carry explicit NULLs to exercise nullable semantics.
"""

from datetime import date


DEPT = [
    (10, "ACCOUNTING"),
    (20, "RESEARCH"),
    (30, "SALES"),
    (40, "OPERATIONS"),
]

# (EMPNO, DEPTNO, ENAME, JOB, MGR, HIREDATE, SAL, COMM, SLACKER)
EMP = [
    (7369, 20, "SMITH",  "CLERK",     7902, date(1980, 12, 17),  800,    0, False),
    (7499, 30, "ALLEN",  "SALESMAN",  7698, date(1981,  2, 20), 1600,  300, False),
    (7521, 30, "WARD",   "SALESMAN",  7698, date(1981,  2, 22), 1250,  500, False),
    (7566, 20, "JONES",  "MANAGER",   7839, date(1981,  4,  2), 2975,    0, False),
    (7654, 30, "MARTIN", "SALESMAN",  7698, date(1981,  9, 28), 1250, 1400, False),
    (7698, 30, "BLAKE",  "MANAGER",   7839, date(1981,  5,  1), 2850,    0, False),
    (7782, 10, "CLARK",  "MANAGER",   7839, date(1981,  6,  9), 2450,    0, False),
    (7788, 20, "SCOTT",  "ANALYST",   7566, date(1987,  4, 19), 3000,    0, True),
    (7839, 10, "KING",   "PRESIDENT", None, date(1981, 11, 17), 5000,    0, False),
    (7844, 30, "TURNER", "SALESMAN",  7698, date(1981,  9,  8), 1500,    0, False),
    (7876, 20, "ADAMS",  "CLERK",     7788, date(1987,  5, 23), 1100,    0, False),
    (7900, 30, "JAMES",  "CLERK",     7698, date(1981, 12,  3),  950,    0, False),
    (7902, 20, "FORD",   "ANALYST",   7566, date(1981, 12,  3), 3000,    0, False),
    (7934, 10, "MILLER", "CLERK",     7782, date(1982,  1, 23), 1300,    0, False),
]

# Same shape as EMP, but nullable — one row exercises NULLs in JOB/HIREDATE/SAL/COMM/SLACKER.
EMPNULLABLES = [
    (7369, 20, "SMITH",  "CLERK",     7902, date(1980, 12, 17),  800, None,  False),
    (7499, 30, "ALLEN",  "SALESMAN",  7698, date(1981,  2, 20), 1600,  300,  False),
    (7521, 30, "WARD",   "SALESMAN",  7698, date(1981,  2, 22), 1250,  500,  False),
    (7566, 20, "JONES",  "MANAGER",   7839, date(1981,  4,  2), 2975, None,  False),
    (7654, 30, "MARTIN", "SALESMAN",  7698, date(1981,  9, 28), 1250, 1400,  False),
    (7698, 30, "BLAKE",  "MANAGER",   7839, date(1981,  5,  1), 2850, None,  False),
    (7782, 10, "CLARK",  "MANAGER",   7839, date(1981,  6,  9), 2450, None,  False),
    (7788, 20, "SCOTT",  "ANALYST",   7566, date(1987,  4, 19), 3000, None,  True),
    (7839, 10, "KING",   "PRESIDENT", None, date(1981, 11, 17), 5000, None,  False),
    (7844, 30, "TURNER", "SALESMAN",  7698, date(1981,  9,  8), 1500,    0,  False),
    (7876, 20, "ADAMS",  "CLERK",     7788, date(1987,  5, 23), 1100, None,  False),
    (7900, 30, "JAMES",  None,        7698, None,                950, None,  None),
    (7902, 20, "FORD",   "ANALYST",   7566, date(1981, 12,  3), 3000, None,  False),
    (7934, 10, "MILLER", "CLERK",     7782, date(1982,  1, 23), None, None,  False),
]

EMPNULLABLES_20 = [row for row in EMPNULLABLES if row[1] == 20]

# EMP with a BIRTHDATE column appended (all NOT NULL).
EMP_B = [
    row + (date(1950 + (row[0] % 30), ((row[0] % 12) or 1), ((row[0] % 28) or 1)),)
    for row in EMP
]

BONUS = []  # Calcite's canonical BONUS fixture is empty.


TABLE_ROWS = {
    "dept": DEPT,
    "emp": EMP,
    "empnullables": EMPNULLABLES,
    "empnullables_20": EMPNULLABLES_20,
    "emp_b": EMP_B,
    "bonus": BONUS,
}

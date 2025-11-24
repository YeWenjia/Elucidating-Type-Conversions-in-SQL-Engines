from lark import Lark, Transformer, v_args

# Define the SQL grammar
sql_grammar = """
?start: select_stmt

?select_stmt: "SELECT" columns "FROM" table (where_clause)? (order_by_clause)? (limit_clause)?

columns: "*"                  -> all_columns
       | column ("," column)* -> column_list

column: CNAME

table: CNAME

?where_clause: "WHERE" condition

?condition: condition "AND" condition   -> and_condition
          | condition "OR" condition    -> or_condition
          | column "=" value            -> eq_condition
          | column "!=" value           -> neq_condition
          | column ">" value            -> gt_condition
          | column "<" value            -> lt_condition
          | column ">=" value           -> gte_condition
          | column "<=" value           -> lte_condition

value: CNAME | ESCAPED_STRING | SIGNED_NUMBER

order_by_clause: "ORDER BY" column ("ASC" | "DESC")?

limit_clause: "LIMIT" SIGNED_NUMBER

%import common.CNAME               // Column and table names
%import common.ESCAPED_STRING       // String values in quotes
%import common.SIGNED_NUMBER        // Numbers
%import common.WS
%ignore WS                          // Ignore whitespace
"""

# Step 2: Create Transformer to Process the Parse Tree
# This transformer will process SQL queries and represent them in a structured format (like a dictionary).

@v_args(inline=True)  # Pass arguments inline
class SQLTransformer(Transformer):
    def select_stmt(self, columns, table, where=None, order_by=None, limit=None):
        return {
            "type": "SELECT",
            "columns": columns,
            "table": table,
            "where": where,
            "order_by": order_by,
            "limit": limit
        }

    def all_columns(self):
        return "*"

    def column_list(self, *columns):
        return list(columns)

    def column(self, name):
        return str(name)

    def table(self, name):
        return str(name)

    def and_condition(self, left, right):
        return {"AND": [left, right]}

    def or_condition(self, left, right):
        return {"OR": [left, right]}

    def eq_condition(self, column, value):
        return {"=": (column, value)}

    def neq_condition(self, column, value):
        return {"!=": (column, value)}

    def gt_condition(self, column, value):
        return {">": (column, value)}

    def lt_condition(self, column, value):
        return {"<": (column, value)}

    def gte_condition(self, column, value):
        return {">=": (column, value)}

    def lte_condition(self, column, value):
        return {"<=": (column, value)}

    def value(self, val):
        # Return value based on type (string, number, or identifier)
        if val.type == "CNAME":
            return str(val)
        elif val.type == "SIGNED_NUMBER":
            return int(val) if '.' not in val else float(val)
        elif val.type == "ESCAPED_STRING":
            return str(val)[1:-1]  # Remove surrounding quotes

    def order_by_clause(self, column, order=None):
        return {"column": column, "order": "ASC" if order is None else str(order)}

    def limit_clause(self, limit):
        return int(limit)


# Step 3: Create the parser and pass the transformer
parser = Lark(sql_grammar, parser="lalr", transformer=SQLTransformer())

# Step 4: Function to Parse and Transform SQL Query
def parse_sql(query):
    return parser.parse(query)

# Example usage
sql_query = "SELECT name, age FROM users WHERE age > 21 ORDER BY name DESC LIMIT 10"
parsed_query = parse_sql(sql_query)
print(parsed_query)
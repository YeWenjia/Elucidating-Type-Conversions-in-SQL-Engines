# import sqlparse
import sqlparse as sqlparse
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.NName import *
# from interpreter.syntax.expression.Bop import Bop
from interpreter.syntax.expression.Op import Lt, Eq, Plus, Op
from interpreter.syntax.expression.Or import Or
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.ImplAscr import ImplAscr
# from interpreter.syntax.expression.Trash import Binop, Uop
# from sqlparse.sql import IdentifierList, Identifier
from sqlparse.sql import *
from sqlparse.tokens import *
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression.Expression import *

from interpreter.syntax.expression.Empty import Empty
from interpreter.syntax.expression.Ins import Ins
from interpreter.syntax.expression.aggregation import Count, Sum, Avg, Max, Min

# nested in where, rename column not table

# db = {
#     "tablea": Table(["name", "age"], [["Alice", 25], ["Bob", 30]]),
#     "tableb": Table(["fullname", "realage"], [["Bob", 30], ["Alice", 25]]),
#     "tablec": Table(["newage", "newname"], [[30, "Bob"], [25,"Alice"]])
# }

# dbt = {
#     "tablea": TableType([NameType("name", SType()), NameType("age", ZType())]),
#     "tableb": TableType([NameType("fullname", SType()), NameType("realage", ZType())]),
#     "tablec": TableType([NameType("newage", ZType()), NameType("newname", SType())])
# }

db = {
    "TA": Table(["name", "height", "age"], []),
    "TB": Table(["realage", "fullname", "fullheight"], []),
    "TC": Table(["newage", "newheight", "newname"], []),
    "TD": Table(["name", "score", "grade"], [])
}

dbt = {
    "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
    "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
    "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())]),
    "TD": RelationType([NameType("name", SType()), NameType("score", ZType()), NameType("grade", SType())])
}


class Parser:
    def __init__(self, use_decimal=True):
        self.use_decimal = use_decimal

    def extract_aggregates(self, expr):
        """Recursively extract all aggregate functions from an expression."""
        aggregates = []
        
        if isinstance(expr, (Count, Sum, Avg, Max, Min)):
            aggregates.append(expr)
        elif isinstance(expr, (And, Or)):
            aggregates.extend(self.extract_aggregates(expr.l))
            aggregates.extend(self.extract_aggregates(expr.r))
        elif isinstance(expr, BNeg):
            aggregates.extend(self.extract_aggregates(expr.b))
        elif isinstance(expr, Op):
            aggregates.extend(self.extract_aggregates(expr.e1))
            aggregates.extend(self.extract_aggregates(expr.e2))
        elif isinstance(expr, Ascr):
            aggregates.extend(self.extract_aggregates(expr.e))
        elif isinstance(expr, ImplAscr):
            aggregates.extend(self.extract_aggregates(expr.e))
        # Base cases like NName, BValue don't contain aggregates
        
        return aggregates

    def aggregates_equal(self, agg1, agg2):
        """Check if two aggregate expressions are semantically equal."""
        if type(agg1) != type(agg2):
            return False
        if isinstance(agg1, Count):
            if agg1.expr is None and agg2.expr is None:
                return True  # Both are COUNT(*)
            if agg1.expr is not None and agg2.expr is not None:
                return str(agg1.expr) == str(agg2.expr)
            return False
        elif isinstance(agg1, (Sum, Avg, Max, Min)):
            return str(agg1.expr) == str(agg2.expr)
        return False

    def get_next(self, tokens):
        if tokens[0].ttype is Whitespace:
            return self.get_next((tokens[1:]))
        elif tokens[0].ttype is Token.Text.Whitespace.Newline and tokens[0].value == '\n':
            return self.get_next((tokens[1:]))
        else:
            return tokens[0], tokens[1:]

    def rv_white(self, tokens):
        res = tokens
        for index, token in enumerate(tokens):
            if token.ttype is Whitespace:
                left = tokens[:index]
                right = tokens[index + 1:]
                res = left + right
        return res

    def parse_exp(self, subtoken):
        # Check if the token itself is a Function (aggregate function)
        if isinstance(subtoken, Function):
            # Extract function name and arguments
            func_name = subtoken.get_name().upper() if subtoken.get_name() else None
            if func_name in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']:
                # Get the parameters (inside the parentheses)
                # subtoken.tokens usually has [Identifier(name), Parenthesis(...)]
                for tok in subtoken.tokens:
                    if isinstance(tok, Parenthesis):
                        # Extract content inside parentheses
                        inner_tokens = tok.tokens[1:-1]  # Skip opening and closing parens
                        # Remove whitespace
                        inner_tokens = [t for t in inner_tokens if t.ttype is not Whitespace]
                        
                        if func_name == 'COUNT':
                            # Handle COUNT(*) special case
                            if len(inner_tokens) == 1 and inner_tokens[0].ttype is Wildcard:
                                return Count(None)  # COUNT(*)
                            elif len(inner_tokens) > 0:
                                arg_expr = self.parse_exp(inner_tokens[0])
                                return Count(arg_expr)
                            else:
                                return Count(None)
                        elif func_name == 'SUM':
                            if len(inner_tokens) > 0:
                                arg_expr = self.parse_exp(inner_tokens[0])
                                return Sum(arg_expr)
                        elif func_name == 'AVG':
                            if len(inner_tokens) > 0:
                                arg_expr = self.parse_exp(inner_tokens[0])
                                return Avg(arg_expr)
                        elif func_name == 'MAX':
                            if len(inner_tokens) > 0:
                                arg_expr = self.parse_exp(inner_tokens[0])
                                return Max(arg_expr)
                        elif func_name == 'MIN':
                            if len(inner_tokens) > 0:
                                arg_expr = self.parse_exp(inner_tokens[0])
                                return Min(arg_expr)
        
        if subtoken.is_group:
            for index, subsub in enumerate(subtoken):
                # if subsub.value.lower() in ['power','sqrt']:
                #     function_name = subsub.value.lower()
                #     if function_name == 'power':
                #         arg_list = subtoken[index+1]
                #         arg_list = arg_list[1]
                #         arg_list = rv_white(arg_list)
                #         e1 = arg_list[0]
                #         e2 = arg_list[2]
                #         # print(self.parse_exp(e1))
                #         # print(self.parse_exp(e2))
                #         # print(syntax.Binop("^", self.parse_exp(e1), self.parse_exp(e2)))
                #         return Binop("power", self.parse_exp(e1), self.parse_exp(e2))
                #     elif function_name == 'sqrt':
                #         arg_list = subtoken[index+1]
                #         arg_list = arg_list[1]
                #         e = arg_list
                #         return Uop("sqrt", self.parse_exp(e))
                if subsub.ttype is Operator and subsub.value == '+':
                    left = subtoken[:index]
                    right = subtoken[index + 1:]
                    right = self.get_next(right)
                    return Plus(self.parse_exp(left[0]), self.parse_exp(right[0]))
                elif subsub.value.upper() == 'CAST':
                    result_name = subtoken.value
                    subtoken = subtoken[index + 1:]
                    cast_as = subtoken[0]
                    cast_as = cast_as[1]
                    hasdot = False
                    for idot, dot in enumerate(cast_as):
                        if dot.value == '.':
                            cast_exp = NName(
                                self.parse_exp(cast_as[idot - 1]).name + '.' + self.parse_exp(cast_as[idot + 1]).name)
                            hasdot = True
                            break
                    if hasdot != True:
                        cast_exp = self.parse_exp(cast_as[0])
                    for i, sub in enumerate(cast_as):
                        if sub.ttype is Keyword and sub.value.upper() == 'AS':
                            right = cast_as[i + 1:]
                            cast_type, right = self.get_next(right)
                            if cast_type.ttype is Token.Name.Builtin and cast_type.value.upper() == 'INT':
                                # e = (self.parse_exp(cast_exp))
                                # print(e)
                                return Ascr((cast_exp), ZType())
                            elif cast_type.ttype is Token.Name.Builtin and cast_type.value.upper() == 'FLOAT':
                                return Ascr((cast_exp), RType())
                            elif cast_type.value.upper() == 'DOUBLE':
                                return Ascr((cast_exp), RType())
                            elif cast_type.value.upper() == 'DECIMAL(10,2)':
                                return Ascr((cast_exp), RType())
                            elif cast_type.value.upper() == 'DECIMAL(10,1)':
                                return Ascr((cast_exp), RType())
                            elif cast_type.value.upper() == 'DECIMAL':
                                return Ascr((cast_exp), RType())
                            elif cast_type.ttype is Token.Name.Builtin and cast_type.value.upper() == 'TEXT':
                                return Ascr((cast_exp), SType())
                            elif cast_type.ttype is Token.Name.Builtin and cast_type.value.upper() == 'SIGNED':
                                # e = (self.parse_exp(cast_exp))
                                # print(e)
                                return Ascr((cast_exp), ZType())
                            elif cast_type.ttype is Token.Name.Builtin and cast_type.value.upper() == 'CHAR':
                                return Ascr((cast_exp), SType())
                            elif cast_type.value.upper() == 'VARCHAR(255)':
                                return Ascr((cast_exp), SType())
            if subsub.ttype is sqlparse.tokens.Name:
                if subtoken.value.upper() == 'NULL':
                    return Nullv(None)
                else:
                    return NName(str(subtoken.value))
            if subtoken[0].ttype is Punctuation and subtoken[0].value == '(':
                return self.parse_conditions(subtoken[1:])
        else:
            if subtoken.ttype is sqlparse.tokens.Literal.Number.Integer:
                return Natural(int(subtoken.value))
            elif subtoken.ttype is sqlparse.tokens.Literal.Number.Float:
                return Real(float(subtoken.value), self.use_decimal)
            elif subtoken.ttype is Keyword and subtoken.value.upper() == 'TRUE':
                return Boolean(bool(subtoken.value))
            elif subtoken.ttype is Keyword and subtoken.value.upper() == 'FALSE':
                return Boolean(False)
            elif subtoken.value.upper() == 'NULL':
                return Nullv(None)
            elif subtoken.ttype is Token.Literal.String.Double:
                if subtoken.value == 'NULL':
                    return Nullv(None)
                else:
                    s = subtoken.value.strip('"')
                    # s = str(s)
                    return SString(s)
            elif subtoken.ttype is Token.Literal.String.Single:
                if subtoken.value == 'NULL':
                    return Nullv(None)
                else:
                    s = subtoken.value.strip("'")
                    # s = str(s)
                    return SString(s)
            elif subtoken.ttype is sqlparse.tokens.Name:
                return NName(str(subtoken.value))

    def parse_alias(self, token):
        columns = []
        more = False
        if token.is_group:
            for sub in token:
                if sub.ttype is Punctuation and sub.value == ',':
                    more = True
            if more:
                for i, subtoken in enumerate(token):
                    if subtoken.ttype is sqlparse.tokens.Whitespace:
                        continue
                    elif subtoken.ttype is Punctuation and subtoken.value == ',':
                        continue
                    elif subtoken.ttype is Punctuation and subtoken.value == ';':
                        continue
                    elif subtoken.is_group:
                        is_alisa = False
                        for index, ssubtoken in enumerate(subtoken):
                            if ssubtoken.ttype is sqlparse.tokens.Keyword and ssubtoken.value.upper() == 'AS':
                                is_alisa = True
                                name, inext = self.get_next(subtoken[index + 1:])
                                prv = subtoken[:index]
                                # here
                                result_name = name.value
                                hasdot = False
                                for idot, dot in enumerate(prv):
                                    if dot.value == '.':
                                        columns.append(Alias(
                                            NName(self.parse_exp(prv[idot - 1]).name + '.' + self.parse_exp(
                                                prv[idot + 1]).name),
                                            str(result_name)))
                                        hasdot = True
                                        break
                                if hasdot != True:
                                    columns.append(Alias(self.parse_exp(prv[0]), str(result_name)))
                                token = token[i:]
                                break
                            else:
                                continue
                        if not is_alisa:
                            result_name = subtoken.value
                            columns.append(Alias(self.parse_exp(subtoken), str(result_name)))
                            token = token[i:]
                        # print(Alias(self.parse_exp(subtoken), str(result_name)))
                    else:
                        result_name = subtoken.value
                        columns.append(Alias(self.parse_exp(subtoken), str(result_name)))
                        token = token[i:]
            else:
                is_alisa = False
                if token.is_group:
                    for index, subtoken in enumerate(token):
                        if subtoken.ttype is sqlparse.tokens.Keyword and subtoken.value.upper() == 'AS':
                            is_alisa = True
                            name, inext = self.get_next(token[index + 1:])
                            prv = token[:index]
                            result_name = name.value

                            hasdot = False
                            for idot, dot in enumerate(prv):
                                if dot.value == '.':
                                    columns.append(
                                        Alias(
                                            NName(self.parse_exp(prv[idot - 1]).name + '.' + self.parse_exp(
                                                prv[idot + 1]).name),
                                            str(result_name)))
                                    hasdot = True
                                    break
                            if hasdot != True:
                                columns.append(Alias(self.parse_exp(prv[0]), str(result_name)))
                            break
                        else:
                            continue
                    if not is_alisa:
                        result_name = token.value
                        columns.append(Alias(self.parse_exp(token), str(result_name)))
                else:
                    result_name = token.value
                    columns.append(Alias(self.parse_exp(token), str(result_name)))
        else:
            result_name = token.value
            columns.append(Alias(self.parse_exp(token), str(result_name)))

        return columns

    def parse_condition(self, token):
        if token.is_group:
            if token[0].ttype is Punctuation and token[0].value == '(':
                return self.parse_conditions(token[1:])
            for index, subtoken in enumerate(token):
                if subtoken.ttype is Token.Operator.Comparison and subtoken.value == '<':
                    left_tokens = token[:index]
                    left_node, left_tokens = self.get_next(left_tokens)
                    e1 = self.parse_exp(left_node)
                    right_index = token[index + 1:]
                    right_node, right_tokens = self.get_next(right_index)
                    e2 = self.parse_exp(right_node)
                    return Lt(e1, e2)
                elif subtoken.ttype is Token.Operator.Comparison and subtoken.value == '>':
                    # a > b is equivalent to b < a
                    left_tokens = token[:index]
                    left_node, left_tokens = self.get_next(left_tokens)
                    e1 = self.parse_exp(left_node)
                    right_index = token[index + 1:]
                    right_node, right_tokens = self.get_next(right_index)
                    e2 = self.parse_exp(right_node)
                    return Lt(e2, e1)  # Flip operands for >
                elif subtoken.ttype is Token.Operator.Comparison and subtoken.value == '=':
                    left_tokens = token[:index]
                    left_node, left_tokens = self.get_next(left_tokens)
                    e1 = self.parse_exp(left_node)
                    right_index = token[index + 1:]
                    right_node, right_tokens = self.get_next(right_index)
                    e2 = self.parse_exp(right_node)
                    return Eq(e1, e2)
        else:
            return self.parse_exp(token)

    def compose_and(self, eqs):
        if len(eqs) == 1:
            return eqs[0]
        else:
            return And(eqs[0], self.compose_and(eqs[1:]))

    def parse_exps(self, token):
        columns = []
        more = False
        if token.is_group:
            if token[0].ttype is Punctuation and token[0].value == '(':
                tks = token[1]
                token = tks
            for sub in token:
                if sub.ttype is Punctuation and sub.value == ',':
                    more = True
            if more:
                for i, subtoken in enumerate(token):
                    if subtoken.ttype is sqlparse.tokens.Whitespace:
                        continue
                    elif subtoken.ttype is Punctuation and subtoken.value == ',':
                        continue
                    elif subtoken.ttype is Punctuation and subtoken.value == ';':
                        continue
                    elif subtoken.ttype is Punctuation and subtoken.value == '(':
                        continue
                    elif subtoken.ttype is Punctuation and subtoken.value == ')':
                        continue
                    elif subtoken.is_group:
                        hasdot = False
                        for idot, dot in enumerate(subtoken):
                            if dot.value == '.':
                                columns.append(
                                    NName(
                                        self.parse_exp(subtoken[idot - 1]).name + '.' + self.parse_exp(
                                            subtoken[idot + 1]).name))
                                hasdot = True
                                break
                        if hasdot != True:
                            columns.append(self.parse_exp(subtoken))
                        token = token[i:]
                    else:
                        columns.append(self.parse_exp(subtoken))
                        token = token[i:]
            else:
                if token.is_group:
                    hasdot = False
                    for idot, dot in enumerate(token):
                        if dot.value == '.':
                            columns.append(
                                NName(
                                    self.parse_exp(token[idot - 1]).name + '.' + self.parse_exp(token[idot + 1]).name))
                            hasdot = True
                            break
                    if hasdot != True:
                        columns.append(self.parse_exp(token))
                else:
                    columns.append(self.parse_exp(token))
        else:
            columns.append(self.parse_exp(token))

        return columns

    def parse_conditions(self, tokens):
        for index, token in enumerate(tokens):
            if token.ttype is Keyword and token.value.upper() == 'AND':
                left = tokens[:index]
                right = tokens[index + 1:]
                return And(self.parse_conditions(left), self.parse_conditions(right))
            elif token.ttype is Keyword and token.value.upper() == 'OR':
                left = tokens[:index]
                right = tokens[index + 1:]
                return Or(self.parse_conditions(left), self.parse_conditions(right))
            elif token.ttype is Keyword and token.value.upper() == 'NOT':
                right = tokens[index + 1:]
                return BNeg(self.parse_conditions(right))
        for id, tk in enumerate(tokens):
            # if tk.ttype is Keyword and tk.value.upper() == 'IN':
            #     lft = tokens[:id]
            #     rgt = tokens[id+1:]
            #     q = parse_select(rgt)
            #     lft = self.get_next(lft)
            #     lft_exps = self.parse_exps(lft[0])
            #     rgt_exps = q.get_expressions()
            #     eqs =[]
            #     for j,e1 in enumerate(lft_exps):
            #         e2 = rgt_exps[j]
            #         eqs.append(Eq(e1, e2))
            #     con = compose_and(eqs)
            #     return Empty(Sel(con,q))
            if tk.ttype is Keyword and tk.value.upper() == 'IN':
                lft = tokens[:id]
                rgt = tokens[id + 1:]
                q = self.parse_select(rgt)
                lft = self.get_next(lft)
                lft_exps = self.parse_exps(lft[0])
                return Ins(lft_exps, q)
            elif tk.value.upper() == 'EXISTS':
                rgt = tokens[id + 1:]
                return Empty(self.parse_select(rgt))
            elif tk.ttype is Keyword and tk.value.upper() == 'IS':
                rgt = tokens[id + 1:]
                rgt = self.get_next(rgt)
                if rgt[0].value.upper() != 'NULL':
                    continue
                else:
                    lft = tokens[:id]
                    lft = self.get_next(lft)
                    lft_exp = self.parse_exp(lft[0])
                    return IsNull(lft_exp)

        token, tokens = self.get_next(tokens)
        return self.parse_condition(token)

    def parse_from(self, tokens):
        print(f"Parsing FROM tokens: {tokens}")
        # First, check for JOINs in the FROM tokens
        # JOINs should be processed before WHERE/GROUP BY/HAVING
        for index, token in enumerate(tokens):
            if token.ttype is Keyword and token.value.upper() in ('JOIN', 'INNER JOIN'):
                # Handle JOIN or INNER JOIN with ON condition
                left = tokens[:index]
                right = tokens[index + 1:]
                
                # Find the ON keyword in right tokens
                on_index = None
                for r_idx, r_token in enumerate(right):
                    if r_token.ttype is Keyword and r_token.value.upper() == 'ON':
                        on_index = r_idx
                        break
                
                if on_index is None:
                    # No ON clause - this might be an error, but treat as cross join
                    return Setop("X", self.parse_from([left]), self.parse_from(right))
                
                # Extract right table (between JOIN and ON)
                right_table_tokens = right[:on_index]
                # Extract ON condition (after ON keyword)
                remaining_tokens = right[on_index + 1:]
                
                # Find where the ON condition ends (at WHERE, GROUP BY, or HAVING)
                on_end_index = len(remaining_tokens)
                for r_idx, r_token in enumerate(remaining_tokens):
                    # Check if token is WHERE/HAVING keyword
                    found_terminator = False
                    if r_token.ttype is Keyword and r_token.value.upper() in ('WHERE', 'HAVING'):
                        found_terminator = True
                    elif r_token.ttype is Keyword and r_token.value.upper() == 'GROUP BY':
                        found_terminator = True
                    # Also check if it's a grouped token starting with WHERE/HAVING/GROUP
                    elif r_token.is_group and len(r_token.tokens) > 0:
                        first_sub = r_token.tokens[0]
                        if first_sub.ttype is Keyword and first_sub.value.upper() in ('WHERE', 'HAVING', 'GROUP'):
                            found_terminator = True
                    
                    if found_terminator:
                        on_end_index = r_idx
                        break
                
                on_condition_tokens = remaining_tokens[:on_end_index]
                after_on_tokens = remaining_tokens[on_end_index:]
                
                # Parse the components
                left_query = self.parse_from(left)
                right_query = self.parse_from(right_table_tokens)
                cross_product = Setop("X", left_query, right_query)
                
                # Parse the ON condition
                on_condition = self.parse_conditions(on_condition_tokens)
                
                # Create the JOIN result (ON condition applied to CROSS product)
                join_result = Sel(on_condition, cross_product)
                
                # If there are WHERE/GROUP BY/HAVING after ON, handle them
                if after_on_tokens:
                    # Recursively process remaining clauses
                    return self.parse_from_with_base(join_result, after_on_tokens)
                
                return join_result
            elif token.ttype is Keyword and token.value.upper() == 'INNER':
                # Check if next token is JOIN (handle INNER JOIN as two separate tokens)
                if index + 1 < len(tokens):
                    next_token = tokens[index + 1]
                    if next_token.ttype is Keyword and next_token.value.upper() == 'JOIN':
                        # Handle INNER JOIN with ON condition
                        left = tokens[:index]
                        right = tokens[index + 2:]  # Skip both INNER and JOIN
                        
                        # Find the ON keyword in right tokens
                        on_index = None
                        for r_idx, r_token in enumerate(right):
                            if r_token.ttype is Keyword and r_token.value.upper() == 'ON':
                                on_index = r_idx
                                break
                        
                        if on_index is None:
                            # No ON clause - treat as cross join
                            return Setop("X", self.parse_from(left), self.parse_from(right))
                        
                        # Extract right table (between JOIN and ON)
                        right_table_tokens = right[:on_index]
                        # Extract ON condition (after ON keyword)
                        remaining_tokens = right[on_index + 1:]
                        
                        # Find where the ON condition ends (at WHERE, GROUP BY, or HAVING)
                        on_end_index = len(remaining_tokens)
                        for r_idx, r_token in enumerate(remaining_tokens):
                            # Check if token is WHERE/HAVING keyword
                            found_terminator = False
                            if r_token.ttype is Keyword and r_token.value.upper() in ('WHERE', 'HAVING'):
                                found_terminator = True
                            elif r_token.ttype is Keyword and r_token.value.upper() == 'GROUP BY':
                                found_terminator = True
                            # Also check if it's a grouped token starting with WHERE/HAVING/GROUP
                            elif r_token.is_group and len(r_token.tokens) > 0:
                                first_sub = r_token.tokens[0]
                                if first_sub.ttype is Keyword and first_sub.value.upper() in ('WHERE', 'HAVING', 'GROUP'):
                                    found_terminator = True
                            
                            if found_terminator:
                                on_end_index = r_idx
                                break
                        
                        on_condition_tokens = remaining_tokens[:on_end_index]
                        after_on_tokens = remaining_tokens[on_end_index:]
                        
                        # Parse the components
                        left_query = self.parse_from(left)
                        right_query = self.parse_from(right_table_tokens)
                        cross_product = Setop("X", left_query, right_query)
                        
                        # Parse the ON condition
                        on_condition = self.parse_conditions(on_condition_tokens)
                        
                        # Create the JOIN result (ON condition applied to CROSS product)
                        join_result = Sel(on_condition, cross_product)
                        
                        # If there are WHERE/GROUP BY/HAVING after ON, handle them
                        if after_on_tokens:
                            # Recursively process remaining clauses
                            return self.parse_from_with_base(join_result, after_on_tokens)
                        
                        return join_result
            elif token.ttype is Punctuation and token.value == ',':
                # Handle comma-separated tables (cross product)
                left = tokens[:index]
                right = tokens[index + 1:]
                return Setop("X", self.parse_from(left), self.parse_from(right))
        
        # No JOIN found, proceed with WHERE/GROUP BY/HAVING detection
        is_where = False
        is_group_by = False
        is_having = False
        where_tokens = None
        group_by_tokens = None
        having_tokens = None
        from_tokens = None
        
        for index, token in enumerate(tokens):
            # Check for WHERE (top-level keyword or grouped)
            is_where_here = False
            if token.ttype is Keyword and token.value.upper() == 'WHERE':
                is_where_here = True
            elif token.is_group and len(token.tokens) > 0:
                # Check if this group starts with WHERE keyword
                first_tok = token.tokens[0]
                if first_tok.ttype is Keyword and first_tok.value.upper() == 'WHERE':
                    is_where_here = True
                # Also check if the value string starts with WHERE (for nested groups)
                elif hasattr(token, 'value') and token.value.strip().upper().startswith('WHERE'):
                    is_where_here = True
            
            if is_where_here:
                is_where = True
                from_tokens = tokens[:index]
                # Extract WHERE condition
                if token.is_group:
                    # Check if first token is WHERE keyword
                    if len(token.tokens) > 0 and token.tokens[0].ttype is Keyword and token.tokens[0].value.upper() == 'WHERE':
                        where_tokens = token.tokens[1:]  # Skip the WHERE keyword
                    else:
                        # The whole group is the WHERE clause, parse it
                        where_tokens = [token]
                else:
                    # Next token contains the condition
                    for w_idx in range(index + 1, len(tokens)):
                        if tokens[w_idx].ttype is not Whitespace:
                            where_tokens = [tokens[w_idx]]
                            break
                
                # Check for GROUP BY / HAVING after WHERE
                # Look in remaining tokens after the WHERE clause
                remaining_idx_start = index + 1
                for rem_idx in range(remaining_idx_start, len(tokens)):
                    rem_token = tokens[rem_idx]
                    if rem_token.ttype is Keyword and rem_token.value.upper() == 'GROUP BY':
                        is_group_by = True
                        # Get grouping columns
                        for g_idx in range(rem_idx + 1, len(tokens)):
                            if tokens[g_idx].ttype is not Whitespace:
                                group_by_tokens = [tokens[g_idx]]
                                # Check for HAVING after GROUP BY
                                for h_idx in range(g_idx + 1, len(tokens)):
                                    h_token = tokens[h_idx]
                                    if h_token.is_group and len(h_token.tokens) > 0:
                                        if h_token.tokens[0].ttype is Keyword and h_token.tokens[0].value.upper() == 'HAVING':
                                            is_having = True
                                            having_tokens = h_token.tokens[1:]
                                            break
                                    elif h_token.ttype is Keyword and h_token.value.upper() == 'HAVING':
                                        is_having = True
                                        for hh_idx in range(h_idx + 1, len(tokens)):
                                            if tokens[hh_idx].ttype is not Whitespace:
                                                having_tokens = [tokens[hh_idx]]
                                                break
                                        break
                                break
                        break
                break
            
            # Check for GROUP BY without WHERE
            if not is_where:
                is_group_here = False
                if token.ttype is Keyword and token.value.upper() == 'GROUP BY':
                    is_group_here = True
                
                if is_group_here:
                    is_group_by = True
                    from_tokens = tokens[:index]
                    # Get grouping columns
                    for g_idx in range(index + 1, len(tokens)):
                        if tokens[g_idx].ttype is not Whitespace:
                            group_by_tokens = [tokens[g_idx]]
                            # Check for HAVING
                            for h_idx in range(g_idx + 1, len(tokens)):
                                h_token = tokens[h_idx]
                                if h_token.is_group and len(h_token.tokens) > 0:
                                    if h_token.tokens[0].ttype is Keyword and h_token.tokens[0].value.upper() == 'HAVING':
                                        is_having = True
                                        having_tokens = h_token.tokens[1:]
                                        break
                                elif h_token.ttype is Keyword and h_token.value.upper() == 'HAVING':
                                    is_having = True
                                    for hh_idx in range(h_idx + 1, len(tokens)):
                                        if tokens[hh_idx].ttype is not Whitespace:
                                            having_tokens = [tokens[hh_idx]]
                                            break
                                    break
                            break
                    break
        
        # If no WHERE/GROUP BY found, all tokens are FROM tokens
        if from_tokens is None:
            from_tokens = tokens
        
        # Start with base query from FROM clause (table names or subqueries)
        query = self.parse_select(from_tokens)
        
        # Apply WHERE clause if present
        if is_where:
            query = Sel(self.parse_conditions(where_tokens), query)
        
        # Apply GROUP BY clause if present
        if is_group_by:
            # Parse grouping expressions from group_by_tokens
            grouping_exprs = self.parse_exps(group_by_tokens[0]) if group_by_tokens else []
            # For GroupBy, we need to extract beta from the parent Proj
            # For now, we'll use an empty beta and let the caller handle it
            # This is a simplified approach - the beta comes from SELECT clause
            query = GroupBy(Beta([]), grouping_exprs, query)
        
        # Apply HAVING clause if present (wraps GroupBy in Sel)
        if is_having:
            query = Sel(self.parse_conditions(having_tokens), query)
        
        return query

    def parse_from_with_base(self, base_query, tokens):
        """Helper method to apply WHERE/GROUP BY/HAVING to an existing base query (e.g., after JOIN)."""
        is_where = False
        is_group_by = False
        is_having = False
        where_tokens = None
        group_by_tokens = None
        having_tokens = None
        remaining_tokens = tokens
        
        # Remove whitespace
        remaining_tokens = [t for t in remaining_tokens if t.ttype is not Whitespace]
        
        if not remaining_tokens:
            return base_query
        
        # Check for WHERE
        first_token = remaining_tokens[0]
        if first_token.ttype is Keyword and first_token.value.upper() == 'WHERE':
            is_where = True
            # Find WHERE condition
            if len(remaining_tokens) > 1:
                where_tokens = [remaining_tokens[1]]
                remaining_tokens = remaining_tokens[2:] if len(remaining_tokens) > 2 else []
        elif first_token.is_group and len(first_token.tokens) > 0:
            if first_token.tokens[0].ttype is Keyword and first_token.tokens[0].value.upper() == 'WHERE':
                is_where = True
                where_tokens = first_token.tokens[1:]
                remaining_tokens = remaining_tokens[1:]
        
        # Check for GROUP BY in remaining tokens
        for idx, token in enumerate(remaining_tokens):
            if token.ttype is Keyword and token.value.upper() == 'GROUP BY':
                is_group_by = True
                if idx + 1 < len(remaining_tokens):
                    group_by_tokens = [remaining_tokens[idx + 1]]
                    # Check for HAVING
                    if idx + 2 < len(remaining_tokens):
                        for h_idx in range(idx + 2, len(remaining_tokens)):
                            h_token = remaining_tokens[h_idx]
                            if h_token.ttype is Keyword and h_token.value.upper() == 'HAVING':
                                is_having = True
                                if h_idx + 1 < len(remaining_tokens):
                                    having_tokens = [remaining_tokens[h_idx + 1]]
                                break
                break
        
        query = base_query
        
        # Apply WHERE clause if present
        if is_where and where_tokens:
            query = Sel(self.parse_conditions(where_tokens), query)
        
        # Apply GROUP BY clause if present
        if is_group_by and group_by_tokens:
            grouping_exprs = self.parse_exps(group_by_tokens[0])
            query = GroupBy(Beta([]), grouping_exprs, query)
        
        # Apply HAVING clause if present
        if is_having and having_tokens:
            query = Sel(self.parse_conditions(having_tokens), query)
        
        return query

    def parse_select(self, tokens) -> Query:
        for index, token in enumerate(tokens):
            if token.ttype is Keyword and token.value.upper() == 'INTERSECT':
                left = tokens[:index]
                right = tokens[index + 1:]
                # rightnode, right = self.get_next(right)
                return Setop("∩", self.parse_select(left), self.parse_select(right))
            elif token.ttype is Keyword and token.value.upper() == 'UNION':
                left = tokens[:index]
                right = tokens[index + 1:]
                # rightnode, right = self.get_next(right)
                return Setop("∪", self.parse_select(left), self.parse_select(right))
            elif token.ttype is Keyword and token.value.upper() == 'EXCEPT':
                left = tokens[:index]
                right = tokens[index + 1:]
                # rightnode, right = self.get_next(right)
                return Setop("-", self.parse_select(left), self.parse_select(right))
            elif token.ttype is Keyword and token.value.upper() == 'MINUS':
                left = tokens[:index]
                right = tokens[index + 1:]
                # rightnode, right = self.get_next(right)
                return Setop("-", self.parse_select(left), self.parse_select(right))
            elif token.ttype is Keyword and token.value.upper() == 'CROSS JOIN':
                left = tokens[:index]
                right = tokens[index + 1:]
                # rightnode, right = self.get_next(right)
                return Setop("X", self.parse_select(left), self.parse_select(right))
            else:
                continue

        token, tokens = self.get_next(tokens)
        tokens = [token] + tokens
        if tokens[0].ttype is DML and tokens[0].value.upper() == 'SELECT':
            tokens = tokens[1:]
            beta_param, tokens = self.get_next(tokens)
            
            # Check if SELECT * (wildcard)
            is_wildcard = False
            if beta_param.ttype is Wildcard or (hasattr(beta_param, 'value') and beta_param.value == '*'):
                is_wildcard = True
            
            beta_param_objs = self.parse_alias(beta_param) if not is_wildcard else []
            token, tokens = self.get_next(tokens)
            tokens = tokens[1:]
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                # Parse the FROM clause (which may include WHERE, GROUP BY, HAVING)
                from_query = self.parse_from(tokens)
                
                # If the result contains a GroupBy, we need to update its beta
                # Check if from_query is GroupBy or Sel(HAVING, GroupBy(...))
                if isinstance(from_query, GroupBy):
                    # Update the GroupBy's beta with the SELECT expressions
                    if is_wildcard:
                        # SELECT * with GROUP BY - this is unusual but just return the GroupBy
                        # It should error in typechecker as you can't SELECT * with GROUP BY
                        return from_query
                    from_query.beta = Beta(beta_param_objs)
                    # Return the GroupBy directly - no need to wrap in Proj
                    # GroupBy handles the projection internally
                    return from_query
                elif isinstance(from_query, Sel) and isinstance(from_query.query, GroupBy):
                    # HAVING case: Sel wrapping GroupBy
                    if is_wildcard:
                        # SELECT * with GROUP BY HAVING - unusual, return as-is
                        return from_query
                    
                    # Check if HAVING uses aggregates not in SELECT
                    having_condition = from_query.cond
                    having_aggregates = self.extract_aggregates(having_condition)
                    
                    # Extract aggregates already in SELECT
                    select_aggregates = []
                    for alias in beta_param_objs:
                        select_aggregates.extend(self.extract_aggregates(alias.e))
                    
                    # Find aggregates in HAVING that are NOT in SELECT
                    missing_aggregates = []
                    for having_agg in having_aggregates:
                        found = False
                        for select_agg in select_aggregates:
                            if self.aggregates_equal(having_agg, select_agg):
                                found = True
                                break
                        if not found:
                            # Check if already in missing list (avoid duplicates)
                            already_added = False
                            for missing_agg in missing_aggregates:
                                if self.aggregates_equal(having_agg, missing_agg):
                                    already_added = True
                                    break
                            if not already_added:
                                missing_aggregates.append(having_agg)
                    
                    # Extend beta with missing aggregates
                    extended_beta_objs = beta_param_objs.copy()
                    for i, agg in enumerate(missing_aggregates):
                        # Generate unique column name for this aggregate
                        agg_col_name = f"__having_agg_{i}"
                        extended_beta_objs.append(Alias(agg, agg_col_name))
                    
                    # Update GroupBy's beta with extended beta
                    from_query.query.beta = Beta(extended_beta_objs)
                    
                    # If we added missing aggregates, wrap in Proj to remove them
                    if len(missing_aggregates) > 0:
                        # Create outer Proj that only selects original columns
                        return Proj(Beta(beta_param_objs), from_query)
                    else:
                        # No missing aggregates - return as-is
                        return from_query
                else:
                    # Normal case without GROUP BY
                    if is_wildcard:
                        # SELECT * - return from_query without projection
                        return from_query
                    else:
                        return Proj(Beta(beta_param_objs), from_query)
        elif isinstance(token, Identifier):
            asbool = False
            for j, sub in enumerate(token):
                if sub.ttype is Keyword and sub.value.upper() == 'AS':
                    asbool = True
                    lefttable = token[:j]
                    righttable = token[j + 1:]
                    righttable = self.get_next(righttable)
                    newtablename = str(righttable[0].value)
                    oldtable = self.parse_select(lefttable)
                    oldcolnames = oldtable.get_col_names()
                    aliascols = list(map(lambda x: Alias(NName(x), f'{newtablename}.{x}'), oldcolnames))
                    return Proj(Beta(aliascols), oldtable)
            if not asbool:
                for j, sub in enumerate(token):
                    if sub.ttype is Token.Text.Whitespace:
                        lefttable = token[:j]
                        righttable = token[j + 1:]
                        righttable = self.get_next(righttable)
                        newtablename = str(righttable[0].value)
                        oldtable = self.parse_select(lefttable)
                        oldcolnames = oldtable.get_col_names()
                        aliascols = list(map(lambda x: Alias(NName(x), f'{newtablename}.{x}'), oldcolnames))
                        return Proj(Beta(aliascols), oldtable)
        if token.is_group:
            if token[0].ttype is Punctuation and token[0].value == '(':
                tokens = token[1:]
                return self.parse_select(tokens)
            # elif isinstance(token, Identifier):
            #     tablename = str(token.get_name())
            #     return Rel(tablename, db[tablename].cols)
            elif token[0].ttype is Name:
                tablename = str(token[0].value)
                return Rel(tablename, db[tablename].cols)
            elif isinstance(token, IdentifierList):
                return self.parse_select(token)
        else:
            tablename = str(token.value)
            return Rel(tablename, db[tablename].cols)

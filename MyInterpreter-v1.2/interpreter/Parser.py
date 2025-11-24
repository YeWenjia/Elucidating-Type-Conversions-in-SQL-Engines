# import sqlparse
import sqlparse as sqlparse
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.NName import *
# from interpreter.syntax.expression.Bop import Bop
from interpreter.syntax.expression.Op import Lt, Eq, Plus
from interpreter.syntax.expression.Or import Or
# from interpreter.syntax.expression.Trash import Binop, Uop
# from sqlparse.sql import IdentifierList, Identifier
from sqlparse.sql import *
from sqlparse.tokens import *
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression.Expression import *

from interpreter.syntax.expression.Empty import Empty
from interpreter.syntax.expression.Ins import Ins

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
    "TC": Table(["newage", "newheight", "newname"], [])
}

dbt = {
    "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
    "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
    "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
}


class Parser:
    def __init__(self, use_decimal=True):
        self.use_decimal = use_decimal

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
        is_where = False
        for index, token in enumerate(tokens):
            if token.is_group:
                if token[0].ttype is Keyword and token[0].value.upper() == 'WHERE':
                    is_where = True
                    where_tokens = token[1:]
                    from_tokens = tokens[:index]
                    return Sel(self.parse_conditions(where_tokens), self.parse_select(from_tokens))
            else:
                continue
        if not is_where:
            return self.parse_select(tokens)

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
            elif token.ttype is Punctuation and token.value == ',':
                left = tokens[:index]
                right = tokens[index + 1:]
                return Setop("X", self.parse_select(left), self.parse_select(right))
            else:
                continue

        token, tokens = self.get_next(tokens)
        tokens = [token] + tokens
        if tokens[0].ttype is DML and tokens[0].value.upper() == 'SELECT':
            tokens = tokens[1:]
            beta_param, tokens = self.get_next(tokens)
            beta_param_objs = self.parse_alias(beta_param)
            token, tokens = self.get_next(tokens)
            tokens = tokens[1:]
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                # print(Proj(Beta(beta_param_objs), parse_from(tokens)))
                return Proj(Beta(beta_param_objs), self.parse_from(tokens))
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

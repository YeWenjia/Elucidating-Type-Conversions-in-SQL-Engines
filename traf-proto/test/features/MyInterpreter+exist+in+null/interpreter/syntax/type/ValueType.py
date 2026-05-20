import math
from decimal import Decimal
# Type
class ValueType:
    def cast(self, t):
        pass

    def upcast(self, t):
        pass

    def diff(self, t, sql):
        pass


class RType(ValueType):
    def __init__(self):
        self.tag = "Real"

    def __str__(self):
        return "Real"

    def __eq__(self, other):
        return self.tag == other.tag

    def diff(self, t, sql):
        if t.tag == "Real":
            return 0
        else:
            return 2

    def upcast(self, t):
        if t.tag == "Real":
            return True
        else:
            return False

    def cast(self, t):
        if t.tag == "Real":
            return True
        elif t.tag == "Int":
            return True
        elif t.tag == "String":
            return True
        else:
            return False

    def castFromString(self, v, sql):
        return sql.castSToReal(v)

    def icastFromString(self, v, sql):
        return sql.icastSToReal(v)

    def castFromInt(self, v, sql):
        return sql.castIToReal(v)

    def castFromReal(self, v, sql):
        return Decimal(v) 

    def castFromBool(self, v, sql):
        return sql.castBToReal(v)

    # def icastFromReal(self, v, sql):
    #     return v

    # def icastFromInt(self, v, sql):
    #     return sql.castIToReal(v)


class ZType(ValueType):
    def __init__(self):
        self.tag = "Int"

    def __str__(self):
        return "Int"

    def __eq__(self, other):
        return self.tag == other.tag

    def diff(self, t, sql):
        if t.tag == "Real":
            if sql.tag in ["Postgres", "Mssql"]:
                return 1
            else:
                return 0
        elif t.tag == "Int":
            return 0
        else:
            return 2

    def upcast(self, t):
        if t.tag == "Real":
            return True
        elif t.tag == "Int":
            return True
        else:
            return False

    def cast(self, t):
        if t.tag == "Real":
            return True
        elif t.tag == "Int":
            return True
        elif t.tag == "String":
            return True
        elif t.tag == "Bool":
            return True
        else:
            return False

    def castFromString(self, v, sql):
        return sql.castSToInt(v)

    def icastFromString(self, v, sql):
        return sql.icastSToInt(v)

    def castFromInt(self, v, sql):
        return sql.castIToInt(v)

    def castFromReal(self, v, sql):
        if sql.tag in ["Postgres", "Mysql", "Oracle"]:
            if v >= 0:
                return int(v+Decimal('0.5'))
            else:
                return int(v-Decimal('0.5'))
            # return round(v)
        else:
            return int(v)

    def castFromBool(self, v, sql):
        return sql.castBToInt(v)

    # def icastFromReal(self, v, sql):
    #     return int(v)


class BType(ValueType):
    def __init__(self):
        self.tag = "Bool"

    def __str__(self):
        return "Bool"

    def __eq__(self, other):
        return self.tag == other.tag

    def diff(self, t, sql):
        if t.tag == "Bool":
            return 0
        else:
            return 2

    def upcast(self, t):
        if t.tag == "Bool":
            return True
        else:
            return False

    def cast(self, t):
        if t.tag == "Bool":
            return True
        elif t.tag == "String":
            return True
        elif t.tag == "Int":
            return True
        else:
            return False

    def castFromString(self, v, sql):
        return sql.castSToBool(v)

    def icastFromString(self, v, sql):
        return sql.icastSToBool(v)

    def castFromInt(self, v, sql):
        return sql.castIToBool(v)

    def castFromReal(self, v, sql):
        return sql.castRToBool(v)

    def castFromBool(self, v, sql):
        return sql.castBToBool(v)

    # def icastFromReal(self, v, sql):
    #     return sql.icastRToBool(v)


class SType(ValueType):
    def __init__(self):
        self.tag = "String"

    def __str__(self):
        return "String"

    def __eq__(self, other):
        return self.tag == other.tag

    def diff(self, t, sql):
        if t.tag == "String":
            return 0
        elif t.tag == "Int":
            return 1
        elif t.tag == "Real":
            return 1
        else:
            return 2

    def upcast(self, t):
        if t.tag == "String":
            return True
        else:
            return False

    def cast(self, t):
        if t.tag == "String":
            return True
        # elif t.tag == "Real":
        #     return True
        # elif t.tag == "Int":
        #     return True
        else:
            return False

    def castFromString(self, v, sql):
        return v

    def icastFromString(self, v, sql):
        return v

    def castFromInt(self, v, sql):
        return sql.castIToString(v)

    def castFromReal(self, v, sql):
        # if sql.tag in ["Postgres", "Oracle", "Mysql", "Mssql"]:
        if sql.tag in ["Oracle"]:
            if v == int(v):
                v = int(v)
                return str(v)
            else:
                return str(v)
        else:
            return str(v)


    def castFromBool(self, v, sql):
        return sql.castBToString(v)

    # def icastFromReal(self, v, sql):
    #     return str(v)


class UType(ValueType):
    def __init__(self):
        self.tag = "Unknown"

    def __str__(self):
        return "?"

    def __eq__(self, other):
        return self.tag == other.tag

    def diff(self, t, sql):
        if t.tag == "Unknown":
            return 0
        else:
            if sql.tag == 'Sqlite':
                return 1
            else:
                return 2

    def cast(self, t):
        if t.tag == "Unknown":
            return True
        else:
            return False

    def upcast(self, t):
        if t.tag == "Unknown":
            return True
        else:
            return False

    def castFromString(self, v, sql):
        return v

    def castFromInt(self, v, sql):
        return v

    def castFromReal(self, v, sql):
        return v

    def castFromBool(self, v, sql):
        return v

class NumType(ValueType):
    def __init__(self):
        self.tag = "Number"


    def __str__(self):
        return "Number"

    def __eq__(self, other):
        return self.tag == other.tag

    def diff(self, t, sql):
        if t.tag == "NumType":
            return 0
        elif t.tag == "Real":
            return 0
        else:
            return 2

    def upcast(self, t):
        if t.tag == "NumType":
            return True
        else:
            return False

    def cast(self, t):
        if t.tag == "NumType":
            return True
        elif t.tag == "Int":
            return True
        elif t.tag == "String":
            return True
        elif t.tag == "Real":
            return True
        else:
            return False

    def castFromString(self, v, sql):
        return sql.castSToNumber(v)

    def castFromInt(self, v, sql):
        return v

    def castFromReal(self, v, sql):
        return v

    def castFromBool(self, v, sql):
        return sql.castBToNumber(v)

class FuncType():
    def __init__(self, dom, cod):
        self.dom = dom
        self.cod = cod

# print(RType())
import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re


class PostgresOps(AbstractOps):
    def truth_value(self, v):
        value = v.erase()
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if getattr(v, "unknown", False) and isinstance(value, str):
            text = value.strip().lower()
            if text in ("1", "t", "tr", "tru", "true", "y", "ye", "yes", "on"):
                return True
            if text in ("0", "f", "fa", "fal", "fals", "false", "n", "no", "of", "off"):
                return False
            raise TypeError(f'invalid input syntax for type boolean: "{value}"')
        return value

    def clean(self, T: RelationType) -> RelationType:
        return RelationType(
            list(map(lambda x: NameType(x.name, SType()) if x.type.tag == "Unknown" else x, T.nametypes)))

    def ty(self, e: Expression):
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match e:
            case Real():
                return RType()
            case Natural():
                return ZType()
            case SString():
                return UType()
            case Boolean():
                return BType()
            case Nullv():
                return UType()
            case DateTime():
                return DTType()
            case _:
                raise TypeError(f"Type not found: {e}")

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        t3s = self.ty_op(op)
        match (t1, t2):
            case (UType(), UType()):
                t = self.best_candidate(SType(), SType(), t3s)
                return t
            case (UType(), _):
                t = self.best_candidate(t2, t2, t3s)
                self.icast(e1, t.dom[0])
                return t
            case (_, UType()):
                t = self.best_candidate(t1, t1, t3s)
                self.icast(e2, t.dom[1])
                return t
            case (_, _):
                return self.best_candidate(t1, t2, t3s)
            
    def resolve_agg_func(self, e: Expression, t: ValueType, agg_func: str) -> FuncType:
        match agg_func:
            case "COUNT":
                return FuncType(t, ZType())
            case "SUM":
                if isinstance(t, ZType):
                    return FuncType(t, ZType())
                elif isinstance(t, RType):
                    return FuncType(t, RType())
                else:
                    raise TypeError(f"SUM requires numeric type, got {t}")
            case "AVG":
                if isinstance(t, ZType) or isinstance(t, RType):
                    return FuncType(t, RType())
                else:
                    raise TypeError(f"AVG requires numeric type, got {t}")
            case "MAX" | "MIN":
                return FuncType(t, t)
            case _:
                raise Exception(f"Unsupported aggregate function: {agg_func}")

    def check_boolean(self, t, e=None):
        match t:
            case BType():
                return t
            case UType():
                literal = self._boolean_context_literal(e)
                if literal is not None:
                    self.truth_value(literal)
                return t
            case _:
                raise TypeError(f"argument of boolean expression must be type boolean, not type {t}")

    def _boolean_context_literal(self, e):
        if isinstance(e, Ascr) and isinstance(e.e, BValue):
            return e.e
        if isinstance(e, BValue):
            return e
        return None

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType()), FuncType([DTType(), DTType()], BType()),
                        FuncType([BType(), BType()], BType())]
            case "=":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType()), FuncType([DTType(), DTType()], BType()),
                        FuncType([BType(), BType()], BType())]
            case "LIKE":
                return [FuncType([SType(), SType()], BType())]
            case "+":
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType())]
            case "-":
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType())]
            case "*":
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType())]
            case "/":
                # Division always returns Real in PostgreSQL
                return [FuncType([ZType(), ZType()], RType()), FuncType([RType(), RType()], RType())]
            case _:
                raise Exception(f"Operation not found: {op}")

    def best_candidate(self, t1, t2, t3s):
        #print(f"Finding best candidate for {t1}, {t2} among {t3s}")
        ms = list(map(lambda x: self.cost(t1, x.dom[0]) + self.cost(t2, x.dom[1]), t3s))
        min_val = min(ms)
        if ms.count(min_val) == 1:
            argmin = ms.index(min_val)
            candidate = t3s[argmin]
            if self.type_implicit_cast(t1, candidate.dom[0]) and self.type_implicit_cast(t2, candidate.dom[1]):
                #print(f"Best candidate is {candidate} with cost {min_val}")
                return candidate
            else:
                raise TypeError(f"Best candidate {candidate} does not match the types {t1}, {t2}")
        elif ms.count(min_val) > 1:
            raise TypeError(f"Ambiguous best candidate for the given types {t1}, {t2}")
        else:
            raise TypeError(f"No best candidate for the given types {t1}, {t2}")

    def cost(self, t1, t2) -> int:
        match (t1, t2):
            case (t1, t2) if t1 == t2:
                return 0
            case (ZType(), RType()) | (SType(), ZType()) | (SType(), RType()):
                return 1
            case _:
                return 2

    def icast(self, e, t):
        if isinstance(e, NName):
            return e
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match (e, t):
            case (Nullv(), _):
                return e
            case (Natural(), RType()):
                v = Real(float(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), RType()):
                v = Real(Decimal(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), SType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (v, t) if self.ty(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), ZType()) if re.match(r'^(-)?\d+$', e.v):
                v = Natural(int(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), RType()) if re.match(r'^(-)?(\d+(\.\d+)?)$', e.v):
                v = Real(Decimal(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), BType()) if e.v.lower() == 'true' or e.v.lower() == 'false':
                v = Boolean(e.v.lower() == 'true')
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), BType()) if e.v in (0, 1):
                v = Boolean(bool(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), SType()) | (Real(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (DateTime(), DTType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (DateTime(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), DTType()):
                from datetime import datetime
                try:
                    v = DateTime(datetime.strptime(e.v, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    try:
                        v = DateTime(datetime.strptime(e.v, '%Y-%m-%d'))
                    except ValueError:
                        v = DateTime(e.v)
                v.unknown = t.tag == 'Unknown'
                return v
        raise TypeError(f"icast fails {e} to {t}")

    def biconv(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType):
        if self.uicast(e1, t1, t2):
            return t2
        elif self.uicast(e2, t2, t1):
            return t1
        else:
            raise TypeError(f"biconv fails {e1}, {t1}, {e2}, {t2}")

    def uicast(self, e, t1, t2):
        match t1:
            case t1 if self.type_implicit_cast(t1, t2):
                return True
            case UType():
                self.icast(e, t2)
                return True
        return False

    def explicit_cast_feasibility(self, e: Expression, tp: ValueType, t: ValueType):
        match e:
            case BValue() | Natural() | Real() | SString() | Boolean():
                self.cast(e, t)
                return True
            case _:
                return True
        return False

    def cast(self, e: Expression, t: ValueType):
        """
        This function represents an explicit cast in the paper. It is used to cast a value to a specific type.
        """
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match (e, t):
            case (Boolean(), ZType()):
                v = Natural(1 if e.v else 0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), ZType()):
                if e.v >= 0:
                    i = int(e.v + Decimal('0.5'))
                    v = Natural(i)
                    v.unknown = t.tag == 'Unknown'
                    return v
                else:
                    i = int(e.v - Decimal('0.5'))
                    v = Natural(i)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (v, t):
                return self.icast(v, t)
        raise TypeError(f"cast fails {e} to {t}")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        return Ascr(e, t)

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        if v1.v is None or v2.v is None:
            return BValue(None)
        else:
            match (op):
                case ("<"):
                    return BValue(v1.erase() < v2.erase())
                case ("="):
                    return BValue(v1.erase() == v2.erase())
                case ("LIKE"):
                    import re
                    # Convert SQL LIKE pattern to regex
                    pattern = str(v2.erase())
                    # Replace % and _ with placeholders to protect them during escaping
                    pattern = pattern.replace('%', '\x00')  # Use null char as placeholder for %
                    pattern = pattern.replace('_', '\x01')  # Use SOH char as placeholder for _
                    # Escape special regex chars
                    pattern = re.escape(pattern)
                    # Replace placeholders with regex equivalents
                    pattern = pattern.replace('\x00', '.*')  # % matches any sequence
                    pattern = pattern.replace('\x01', '.')   # _ matches single char
                    # Match the entire string (DOTALL so % matches newlines)
                    pattern = '^' + pattern + '$'
                    result = re.match(pattern, str(v1.erase()), re.DOTALL) is not None
                    return BValue(result)
                case ("+"):
                    r = v1.erase() + v2.erase()
                    return BValue(r)
                case ("-"):
                    r = v1.erase() - v2.erase()
                    return BValue(r)
                case ("*"):
                    r = v1.erase() * v2.erase()
                    return BValue(r)
                case ("/"):
                    r = v1.erase() / v2.erase()
                    return BValue(r)
                case _:
                    raise TypeError(f"operation {op} not support")


class Postgres(Engine):
    typechecker = Typechecker(PostgresOps())

    run = Runtime(PostgresOps())

    def __init__(self):
        self.tag = "Postgres"

    def __str__(self):
        return "Postgres"

    def comparev(self, v1, v2):
        if isinstance(v2, Decimal) and type(v1) == float:
            return np.isclose(v1, float(v2))
        elif isinstance(v1, Decimal) and type(v2) == Decimal:
            return np.isclose(float(v1), float(v2))
        elif isinstance(v1, Decimal) and type(v2) == float:
            return np.isclose(v2, float(v1))
        elif type(v2) == float and type(v1) == float:
            return np.isclose(v1, v2)
        else:
            return v1 == v2

    def infer_schema(self, connection):
        """
        Infer schema from PostgreSQL database using information_schema.
        
        Args:
            connection: psycopg2 connection object
            
        Returns:
            dict: Mapping of table names to RelationType objects
        """
        cursor = connection.cursor()
        schema = {}
        
        # Get all table names from current schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        for table_name in tables:
            # Get column information for each table
            cursor.execute("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            name_types = []
            
            for col_name, data_type, udt_name in columns:
                # Map PostgreSQL types to interpreter types
                interpreter_type = self._map_postgres_type_to_interpreter(data_type, udt_name)
                name_types.append(NameType(col_name, interpreter_type))
            
            # Store with uppercase table name to match existing convention
            schema[table_name.upper()] = RelationType(name_types)
        
        cursor.close()
        return schema

    def _map_postgres_type_to_interpreter(self, data_type: str, udt_name: str):
        """
        Map PostgreSQL data types to interpreter types.
        
        Args:
            data_type: SQL standard type name (e.g., 'integer', 'character varying')
            udt_name: PostgreSQL-specific type name (e.g., 'int4', 'varchar')
            
        Returns:
            ValueType: Corresponding interpreter type (ZType, RType, SType, BType)
        """
        # Integer types
        if data_type in ('integer', 'bigint', 'smallint') or udt_name in ('int2', 'int4', 'int8'):
            return ZType()
        
        # Real/Float types
        elif data_type in ('real', 'double precision', 'numeric', 'decimal') or udt_name in ('float4', 'float8', 'numeric'):
            return RType()
        
        # Boolean type
        elif data_type == 'boolean' or udt_name == 'bool':
            return BType()
        
        # String types (default)
        elif data_type in ('character varying', 'character', 'text') or udt_name in ('varchar', 'char', 'text', 'bpchar'):
            return SType()
        
        # Date/Time types
        elif data_type in ('date', 'timestamp', 'time', 'interval'):
            return DTType()
        
        # Unknown/Other types - default to String
        else:
            return SType()

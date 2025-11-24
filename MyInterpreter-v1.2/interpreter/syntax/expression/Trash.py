# from interpreter.syntax.expression.Ascr import Ascr
# from interpreter.syntax.expression.BValue import BValue
# from interpreter.syntax.expression.Expression import Expr
#
# from interpreter.syntax.type.Type import *
# import math
#
#
# def get_binop(op: str):
#     if op == "power":
#         return tuple((RType(), RType(), RType()))
#     else:
#         raise Exception(op + " not supported")
#
# def get_uop(op: str):
#     if op == "sqrt":
#         return tuple((RType(), RType()))
#     else:
#         raise Exception(op + " not supported")
#
# # def get_cop(op: str, sql):
# #     if op == "<" and (sql.tag in ["Postgres", "Mssql"]):
# #         return [(ZType(), ZType()), (RType(), RType()), (SType(), SType())]
# #     elif op == "<" and (sql.tag in ["Mysql", "Oracle"]):
# #         return [(RType(), RType()), (SType(), SType())]
# #     elif op == "<" and (sql.tag == "Sqlite"):
# #         return [(RType(), RType()), (SType(), SType()), (UType(), UType())]
# #     elif op == "=" and (sql.tag in ["Postgres", "Mssql"]):
# #         return [(ZType(), ZType()), (RType(), RType()), (SType(), SType())]
# #     elif op == "=" and (sql.tag in ["Mysql", "Oracle"]):
# #         return [(RType(), RType()), (SType(), SType())]
# #     elif op == "=" and (sql.tag == "Sqlite"):
# #         return [(RType(), RType()), (SType(), SType()), (UType(), UType())]
#
# class Binop(Expr):
#     def __init__(self, op, e1, e2):
#         self.op = op
#         self.e1 = e1
#         self.e2 = e2
#
#     def __eq__(self, other):
#         return self.op == other.op and self.e1 == other.e1 and self.e2 == other.e2
#
#     def __str__(self):
#         return "POWER(" + str(self.e1) + "," + str(self.e2) + ")"
#
#     def run(self, row, attrnames, sql):
#         e1 = self.e1.run(row, attrnames, sql)
#         e2 = self.e2.run(row, attrnames, sql)
#         if self.op == "power":
#             return BValue(math.pow(e1.erase(), e2.erase()))
#         else:
#             raise Exception("Binop " + str(self.op) + " not supported")
#
#     def typecheck(self, tablet, sql):
#         t1 = self.e1.typecheck(tablet, sql)
#         t2 = self.e2.typecheck(tablet, sql)
#         t = get_binop(self.op)
#         if sql.BImCast(self.e1, self.e2, t1, t2, t[0], t[1]):
#             return t[2]
#         else:
#             raise Exception("Program does not type check")
#
#     def trans(self, tablet, sql):
#         ee1 = self.e1.trans(tablet, sql)
#         ee2 = self.e2.trans(tablet, sql)
#         t = get_binop(self.op)
#         return Binop(self.op, Ascr(ee1, t[0]), Ascr(ee2, t[1]))
#
#
# class Uop(Expr):
#     def __init__(self, op, e):
#         self.op = op
#         self.e = e
#
#     def __str__(self):
#         return "SQRT(" + str(self.e) + ")"
#
#     def __eq__(self, other):
#         return self.op == other.op and self.e == other.e
#
#     def run(self, row, attrnames, sql):
#         e = self.e.run(row, attrnames, sql)
#         if self.op == "sqrt":
#             return BValue(math.sqrt(e.erase()))
#         else:
#             raise Exception("Unop " + str(self.op) + " not supported")
#
#     def typecheck(self, tablet, sql):
#         t1 = self.e.typecheck(tablet, sql)
#         t2 = get_uop(self.op)
#         if sql.UImCast(self.e, t1, t2[0]):
#             return t2[1]
#         else:
#             raise Exception("Program does not type check")
#
#     def trans(self, tablet, sql):
#         ee = self.e.trans(tablet, sql)
#         t = get_uop(self.op)
#         return Uop(self.op, Ascr(ee, t[0]))
#
#
# # from interpreter.syntax.expression.Expression import Expr
# # from interpreter.syntax.expression.BValue import BValue
# # from interpreter.syntax.expression.Ascr import Ascr
# # from interpreter.syntax.type.Type import UType
# #
# #
# # class Bop(Expr):
# #     def __init__(self, op, e1, e2):
# #         self.op = op
# #         self.e1 = e1
# #         self.e2 = e2
# #
# #     def __eq__(self, other):
# #         return self.op == other.op and self.e1 == other.e1 and self.e2 == other.e2
# #
# #     def __str__(self):
# #         return str(self.e1) + "+" + str(self.e2)
# #
# #     def run(self, row, attrnames, sql):
# #         e1 = self.e1.run(row, attrnames, sql)
# #         e2 = self.e2.run(row, attrnames, sql)
# #         if self.op == "+":
# #               r = e1.erase() + e2.erase()
# #               return BValue(r)
# #         else:
# #             raise Exception("Bop " + str(self.op) + " not supported")
# #
# #     def typecheck(self, tablet, sql):
# #         t1 = self.e1.typecheck(tablet, sql)
# #         t2 = self.e2.typecheck(tablet, sql)
# #         t = sql.get_addition()
# #         r = sql.overload(self.e1, self.e2, t1, t2, t)
# #         if sql.tag == 'Sqlite':
# #             return UType()
# #         else:
# #             return r[0]
# #
# #     def trans(self, tablet, sql):
# #         ee1 = self.e1.trans(tablet, sql)
# #         ee2 = self.e2.trans(tablet, sql)
# #         t1 = self.e1.typecheck(tablet, sql)
# #         t2 = self.e2.typecheck(tablet, sql)
# #         t = sql.get_addition()
# #         r = sql.overload(self.e1, self.e2, t1, t2, t)
# #         return Bop(self.op, Ascr(ee1, r[0]), Ascr(ee2, r[1]))
#
#
#
#
#


#
# from interpreter.syntax.expression.BValue import BValue
# from interpreter.syntax.expression.BExpr import *
# from interpreter.syntax.type.Type import BType, ZType
#
#
# class BNeg(BExpr):
#     def __init__(self, b):
#         self.b = b
#
#     def __str__(self):
#         return "¬(" + str(self.b) + ")"
#
#     def __eq__(self, other):
#         return self.b == other.b
#
#     def run(self, row, attrnames, sql):
#         b = self.b.run(row, attrnames, sql)
#         if b.erase() == 1:
#             return BValue(0)
#         elif b.erase() == 0:
#             return BValue(1)
#         else:
#             return BValue(not b.erase())
#
#     def typecheck(self, tablet, sql):
#         b = self.b.typecheck(tablet, sql)
#         if b.tag == "Bool":
#             return BType()
#         elif sql.tag in ["Sqlite","Mysql"]:
#             return ZType()
#         else:
#             raise Exception("Program does not type check")
#
#     def trans(self, tablet, sql):
#         bb = self.b.trans(tablet, sql)
#         return BNeg(bb)

# from interpreter.syntax.expression.BValue import BValue
# from interpreter.syntax.type.Type import BType, ZType
# from interpreter.syntax.expression.BExpr import *
#
# class And(BExpr):
#     def __init__(self, l, r):
#         self.l = l
#         self.r = r
#
#     def __str__(self):
#         return "(" + str(self.l) + " ∧ " + str(self.r) + ")"
#
#     def __eq__(self, other):
#         return self.l == other.l and self.r == other.r
#
#     def run(self, row, attrnames, sql):
#         l = self.l.run(row, attrnames, sql)
#         r = self.r.run(row, attrnames, sql)
#         if l.erase() == 1 and r.erase() == 1 :
#             return BValue(1)
#         elif l.erase() == 0 or r.erase() == 0 :
#             return BValue(0)
#         else:
#             return BValue(l.erase() and r.erase())
#
#     def typecheck(self, tablet, sql):
#         t1 = self.l.typecheck(tablet, sql)
#         t2 = self.r.typecheck(tablet, sql)
#         if t1.tag == t2.tag == "Bool":
#             return BType()
#         elif sql.tag in ["Sqlite","Mysql"]:
#             return ZType()
#         else:
#             raise Exception("Program does not type check")
#
#     def trans(self, tablet, sql):
#         ll = self.l.trans(tablet, sql)
#         rr = self.r.trans(tablet, sql)
#         return And(ll, rr)


# from interpreter.syntax.expression.BValue import BValue
# from interpreter.syntax.type.Type import BType, ZType
# from interpreter.syntax.expression.BExpr import *
#
# class Or(BExpr):
#     def __init__(self, l, r):
#         self.l = l
#         self.r = r
#
#     def __str__(self):
#         return "(" + str(self.l) + " ∨ " + str(self.r) + ")"
#
#     def __eq__(self, other):
#         return self.l == other.l and self.r == other.r
#
#     def run(self, row, attrnames, sql):
#         l = self.l.run(row, attrnames, sql)
#         r = self.r.run(row, attrnames, sql)
#         if l.erase() == 1 or r.erase() == 1 :
#             return BValue(1)
#         elif l.erase() == 0 and r.erase() == 0 :
#             return BValue(0)
#         else:
#             return BValue(l.erase() or r.erase())
#
#     def typecheck(self, tablet, sql):
#         t1 = self.l.typecheck(tablet, sql)
#         t2 = self.r.typecheck(tablet, sql)
#         if t1.tag == t2.tag == "Bool":
#             return BType()
#         elif sql.tag in ["Sqlite","Mysql"]:
#             return ZType()
#         else:
#             raise Exception("Program does not type check")
#
#     def trans(self, tablet, sql):
#         ll = self.l.trans(tablet, sql)
#         rr = self.r.trans(tablet, sql)
#         return Or(ll, rr)

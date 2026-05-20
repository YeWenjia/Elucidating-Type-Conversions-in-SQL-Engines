from lark import Transformer, Lark

simple_grammar = """
    start: "hello" NAME "!"
    NAME: /[a-zA-Z]+/
    %import common.WS
    %ignore WS
"""

parser = Lark(simple_grammar)

text = "hello John!"
tree = parser.parse(text)
# print(tree.pretty())

class SimpleTransformer(Transformer):
    def start(self, items):
        print(items)
        return {"greeting": items[0]}  # items[1] is the NAME

transformer = SimpleTransformer()
parsed = transformer.transform(tree)  # Apply transformation to the parse tree
print(parsed)
#this file is to store the \Gamma of the paper


class SchemaType:
    def __init__(self, tabletypes):
        self.tabletypes = tabletypes

    def __str__(self):
        return "[" + ",".join([str(x) for x in self.tabletypes]) + "]"

    def __eq__(self, other):
        return self.tabletypes == other.tabletypes

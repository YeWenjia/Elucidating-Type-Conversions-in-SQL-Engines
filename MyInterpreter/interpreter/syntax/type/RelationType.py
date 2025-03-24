# This is T in the paper
class RelationType:
    def __init__(self, nametypes):
        self.nametypes = nametypes

    def __str__(self):
        return "[" + ",".join([str(x) for x in self.nametypes]) + "]"

    def __eq__(self, other):
        return self.nametypes == other.nametypes

    def getLast(self):
        return self.nametypes[-1]

    def getTypeByName(self, name):
        # res = filter(lambda x: x.name == name, self.nametypes)
        # print("h1" + str(filter(lambda x: x.name == name, self.nametypes)))
        # print("h2" + str(res))
        # print(len(list(res)))
        # print(str(TableType(res)))
        # print(TableType(self.nametypes))
        res = []
        # print(name)
        print(self.nametypes)
        for nametype in self.nametypes:
            # print(nametype)
            if nametype.name == name:
                res += [nametype]
        # print("type:"+ str(res[0].type))
        # return res[0].type
        if (len(list(res))) >= 1:
            return res[0].type
        else:
            raise Exception("Type not found")


# This is a pair N \mapsto \tau in the paper
class NameType:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return str(self.name) + ": " + str(self.type)

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type

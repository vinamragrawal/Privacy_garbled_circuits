
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

# Vinamra Agrawal - va1215

#Define a table
class Table:
    def __init__(self):
        self.lookup_map = dict()

    def get_key(self, inputs):
        if (len(inputs) == 1):
            return inputs[0]
        else:
            return (inputs[0],inputs[1])

    def add_entry(self, inputs, value):
        self.lookup_map[self.get_key(inputs)] = value
        return

    def get_entry(self, inputs):
        return self.lookup_map[self.get_key(inputs)]

#Define a Gate
class Gate:
    def __init__(self):
        self.type = "null"
        self.id = "null"
        self.input = []
        self.garbled_table = Table()

    def evaluate(self, inputs):
        if  (self.type == "AND"):
            return all(inputs)
        if (self.type == "NAND"):
            return not(all(inputs))
        if (self.type == "OR"):
            return any(inputs)
        if (self.type == "NOR"):
            return not(any(inputs))
        if (self.type == "XOR"):
            return inputs[0] ^ inputs[1]
        if (self.type == "XNOR"):
            return not(inputs[0] ^ inputs[1])
        if (self.type == "NOT"):
            return not inputs[0]
        raise Exception('Unsupported Gate Type')

#Define a Circuit
class Circuit:
    def __init__(self):
        self.Name = "null"
        self.Gates = []
        self.Wires = []
        self.Alice = []
        self.Bob = []
        self.Outputs = []

    def parseJson(self, json_circuit):
        self.Name = json_circuit["name"]
        self.Outputs = json_circuit["out"]

        if ("alice" in json_circuit):
            self.Alice = json_circuit["alice"]
            self.Wires.extend(self.Alice)
        if ("bob" in json_circuit):
            self.Bob = json_circuit["bob"]
            self.Wires.extend(self.Bob)

        for json_gate in json_circuit["gates"]:
            gate = Gate()
            gate.id = json_gate["id"]
            gate.type = json_gate["type"]
            gate.input = json_gate["in"]
            self.Gates.append(gate)
            self.Wires.append(json_gate["id"])

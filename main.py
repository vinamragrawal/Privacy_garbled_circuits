
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

# Vinamra Agrawal - va1215

import json	# load
import sys	# argv

import ot	# alice, bob
import util	# ClientSocket, log, ServerSocket
import yao	# Circuit
import random #Generate Random numbers for p values
from cryptography.fernet import Fernet, MultiFernet # encryption
import pickle #coding and decoding

#import pdb; pdb.set_trace()

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

def create_garble_tables(circuit, p_values, keys):
    for gate in circuit.Gates:
        if (gate.type == "NOT"):
            for input in create_all_possible_combination(1):
                p_val = input[0] ^ p_values[gate.input[0]]
                input_keys = keys[gate.input[0]][p_val]
                f = MultiFernet([Fernet(input_keys), Fernet(input_keys)])
                output_value = gate.evaluate(input) ^ p_values[gate.id]
                output_value = (output_value, keys[gate.id][output_value])
                output_value = f.encrypt(pickle.dumps(output_value))
                gate.garbled_table.add_entry([p_val], output_value )
        else:
            for input in create_all_possible_combination(2):
                ps = list(map(lambda x: input[x] ^ p_values[gate.input[x]],
                              [0,1]))
                input_keys = list(map(lambda x, y: keys[x][y], gate.input, ps))
                f = MultiFernet(list(map(lambda x: Fernet(x), input_keys)))
                output_value = gate.evaluate(input) ^ p_values[gate.id]
                output_value = (output_value, keys[gate.id][output_value])
                output_value = f.encrypt(pickle.dumps(output_value))
                gate.garbled_table.add_entry(ps, output_value)

def create_all_possible_combination(len):
    l = [0,1]
    if (len == 0):
        return []
    if (len == 1):
        return [[i] for i in l]
    if (len == 2):
        return [(i, j) for i in l for j in l]
    if (len == 3):
        return [(i, j, k) for i in l for j in l for k in l]

def lookup_gate(id, Gates):
    for gate in Gates:
        if (gate.id == id):
            return gate
    return "null"

def evaluate_circuit(know_values, output_key, Gates):
    #any wire value is either know value or a gate id
    if output_key in know_values:
        return know_values[output_key]
    else:
        gate = lookup_gate(output_key, Gates)
        inputs = [ evaluate_circuit(know_values, x, Gates)[0] for x in gate.input]
        output = gate.garbled_table.get_entry(inputs)
        f = MultiFernet([ Fernet(evaluate_circuit(know_values, x, Gates)[1])
                                                          for x in gate.input])
        output = pickle.loads(f.decrypt(output))
        return output

def evaluate(Alice_values, Bob_values, circuit, output_pvalues):
    know_values = {}

    #Map know values
    know_values.update(dict(zip(circuit.Alice, Alice_values)))
    know_values.update(dict(zip(circuit.Bob, Bob_values)))

    results = [evaluate_circuit(know_values, output, circuit.Gates)[0]
              for output in circuit.Outputs]
    return list(map(lambda x, y: x ^ y, results, output_pvalues))

def write_output(circuit, f, Alice_values, Bob_values, outputs):
    f.write("  Alice" + str(circuit.Alice) + " = ")
    for val in Alice_values:
        f.write(str(val) + " ")
    f.write(" Bob" + str(circuit.Bob) + " = ")
    for val in Bob_values:
        f.write(str(val) + " ")
    f.write("  Outputs" + str(circuit.Outputs) + " = ")
    for val in outputs:
        f.write(str(val) + " ")
    f.write("\n")
    return



# Alice is the circuit generator (client) __________________________________

def alice(filename):
  socket = util.ClientSocket()

  with open(filename) as json_file:
    json_circuits = json.load(json_file)

  for json_circuit in json_circuits['circuits']:
      circuit = Circuit()
      circuit.parseJson(json_circuit)
      print(circuit.Name)

      #Create random p values
      p_values = {}
      for wire in circuit.Wires:
          p_values[wire] = random.randint(0,1)

      #Generate keys for each wire
      keys = {}
      for wire in circuit.Wires:
          keys[wire] = (Fernet.generate_key(), Fernet.generate_key())

      #Create table
      create_garble_tables(circuit, p_values, keys)

      #Send all combinations to Bob
      for Alice_values in create_all_possible_combination(len(circuit.Alice)):
          Alice_pvalues = list(map(lambda x, y: x ^ p_values[y],
                                    Alice_values, circuit.Alice))
          Alice_pvalues = list(map(lambda x, y: (x, keys[y][x]),
                                    Alice_pvalues, circuit.Alice))
          output_pvalues = list(map(lambda x: p_values[x], circuit.Outputs))

          #Check if bob values exist
          if (not len(circuit.Bob)):
              output = socket.send_wait((circuit, Alice_pvalues, [],  output_pvalues))
              print(Alice_values, [], output)
          else:
              for Bob_values in create_all_possible_combination(len(circuit.Bob)):
                  Bob_pvalues = list(map(lambda x, y: x ^ p_values[y], Bob_values, circuit.Bob))
                  Bob_pvalues = list(map(lambda x, y: (x, keys[y][x]), Bob_pvalues, circuit.Bob))
                  output = socket.send_wait((circuit, Alice_pvalues, Bob_pvalues,  output_pvalues))
                  print(Alice_values, Bob_values, output)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
  socket = util.ServerSocket()
  util.log(f'Bob: Listening ...')
  while True:
      value = socket.receive()
      circuit = value[0]
      Alice_pvalues = value[1]
      Bob_pvalues = value[2]
      output_pvalues = value[3]

      output = evaluate(Alice_pvalues, Bob_pvalues, circuit, output_pvalues)
      socket.send(output)

# local test of circuit generation and evaluation, no transfers_____________

def local_test(filename):
  with open(filename) as json_file:
    json_circuits = json.load(json_file)

  f = open("output.txt", "a")
  f.write("python3 main.py alice " + filename + "\n")

  for json_circuit in json_circuits['circuits']:
      circuit = Circuit()
      circuit.parseJson(json_circuit)
      f.write("\n======= "+ circuit.Name + " =======\n")

      #Create random p values
      p_values = {}
      for wire in circuit.Wires:
          p_values[wire] = random.randint(0,1)

      #Generate keys for each wire
      keys = {}
      for wire in circuit.Wires:
          keys[wire] = (Fernet.generate_key(), Fernet.generate_key())

      #Create table
      create_garble_tables(circuit, p_values, keys)

      #Try evaluate
      for Alice_values in create_all_possible_combination(len(circuit.Alice)):
           Alice_pvalues = list(map(lambda x, y: x ^ p_values[y],
                                     Alice_values, circuit.Alice))
           Alice_pvalues = list(map(lambda x, y: (x, keys[y][x]),
                                     Alice_pvalues, circuit.Alice))
           output_pvalues = list(map(lambda x: p_values[x], circuit.Outputs))

           if (not len(circuit.Bob)):
               outputs = evaluate(Alice_pvalues, [], circuit, output_pvalues)
               write_output(circuit, f, Alice_values, [], outputs)

           for Bob_values in create_all_possible_combination(len(circuit.Bob)):
               Bob_pvalues = list(map(lambda x, y: x ^ p_values[y], Bob_values, circuit.Bob))
               Bob_pvalues = list(map(lambda x, y: (x, keys[y][x]), Bob_pvalues, circuit.Bob))
               outputs = evaluate(Alice_pvalues, Bob_pvalues, circuit, output_pvalues)

               # Write output
               write_output(circuit, f, Alice_values, Bob_values, outputs)

# main _____________________________________________________________________

def main():
  behaviour = sys.argv[1]
  if   behaviour == 'alice': alice(filename=sys.argv[2])
  elif behaviour == 'bob':   bob()
  elif behaviour == 'local': local_test(filename=sys.argv[2])

if __name__ == '__main__':
  main()

# __________________________________________________________________________

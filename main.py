
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

# Vinamra Agrawal - va1215

import json	# load
import sys	# argv

import ot	# alice, bob
import util	# ClientSocket, log, ServerSocket
import yao	# Define Circuit
import random #Generate Random numbers for p values
from cryptography.fernet import Fernet, MultiFernet # encryption
import pickle #coding and decoding

#import pdb; pdb.set_trace()

def create_garble_tables(circuit, p_values, keys):
    for gate in circuit.Gates:
        if (gate.type == "NOT"):
            for input in util.create_all_possible_combination(1):
                p_val = input[0] ^ p_values[gate.input[0]]
                input_keys = keys[gate.input[0]][p_val]
                f = MultiFernet([Fernet(input_keys), Fernet(input_keys)])
                output_value = gate.evaluate(input) ^ p_values[gate.id]
                output_value = (output_value, keys[gate.id][output_value])
                output_value = f.encrypt(pickle.dumps(output_value))
                gate.garbled_table.add_entry([p_val], output_value )
        else:
            for input in util.create_all_possible_combination(2):
                ps = list(map(lambda x: input[x] ^ p_values[gate.input[x]],
                              [0,1]))
                input_keys = list(map(lambda x, y: keys[x][y], gate.input, ps))
                f = MultiFernet(list(map(lambda x: Fernet(x), input_keys)))
                output_value = gate.evaluate(input) ^ p_values[gate.id]
                output_value = (output_value, keys[gate.id][output_value])
                output_value = f.encrypt(pickle.dumps(output_value))
                gate.garbled_table.add_entry(ps, output_value)

def evaluate_circuit(know_values, output_key, Gates):
    #any wire value is either know value or a gate id
    if output_key in know_values:
        return know_values[output_key]
    else:
        gate = util.lookup_gate(output_key, Gates)
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


# Alice is the circuit generator (client) __________________________________

def alice(filename):
  socket = util.ClientSocket()

  with open(filename) as json_file:
    json_circuits = json.load(json_file)

  for json_circuit in json_circuits['circuits']:
      circuit = yao.Circuit()
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

      #Generate value and key for all possible bob values for circuit
      all_bob_values = ot.generate_all_bob_values(circuit.Bob, p_values, keys)

      #Send all combinations to Bob
      for Alice_values in util.create_all_possible_combination(len(circuit.Alice)):
          Alice_pvalues = list(map(lambda x, y: x ^ p_values[y],
                                    Alice_values, circuit.Alice))
          Alice_pvalues = list(map(lambda x, y: (x, keys[y][x]),
                                    Alice_pvalues, circuit.Alice))
          output_pvalues = list(map(lambda x: p_values[x], circuit.Outputs))

          str = socket.send_wait((circuit, Alice_pvalues, output_pvalues, p_values, keys))

          #Check if bob values exist
          if (not len(circuit.Bob)):
              output = socket.send_wait([])
              print(Alice_values, [], output)
          else:
              for Bob_values in util.create_all_possible_combination(len(circuit.Bob)):
                  output = socket.send_wait([])
                  print(Alice_values, Bob_values, output)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
  socket = util.ServerSocket()
  util.log(f'Bob: Listening ...')
  while True:
      value = socket.receive()
      circuit = value[0]
      Alice_pvalues = value[1]
      output_pvalues = value[2]
      p_values = value[3]
      keys = value[4]
      socket.send("Done")

      #Check if bob values exist
      if (not len(circuit.Bob)):
          socket.receive()
          output = evaluate(Alice_pvalues, Bob_pvalues, circuit, output_pvalues)
          socket.send(output)
      else:
          for Bob_values in util.create_all_possible_combination(len(circuit.Bob)):
              socket.receive()
              Bob_pvalues = list(map(lambda x, y: x ^ p_values[y], Bob_values, circuit.Bob))
              Bob_pvalues = list(map(lambda x, y: (x, keys[y][x]), Bob_pvalues, circuit.Bob))
              output = evaluate(Alice_pvalues, Bob_pvalues, circuit, output_pvalues)
              socket.send(output)
              # output = socket.send_wait((circuit, Alice_pvalues, Bob_pvalues,  output_pvalues))
              # print(Alice_values, Bob_values, output)

      # output = evaluate(Alice_pvalues, Bob_pvalues, circuit, output_pvalues)
      # socket.send(output)

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
      for Alice_values in util.create_all_possible_combination(len(circuit.Alice)):
           Alice_pvalues = list(map(lambda x, y: x ^ p_values[y],
                                     Alice_values, circuit.Alice))
           Alice_pvalues = list(map(lambda x, y: (x, keys[y][x]),
                                     Alice_pvalues, circuit.Alice))
           output_pvalues = list(map(lambda x: p_values[x], circuit.Outputs))

           if (not len(circuit.Bob)):
               outputs = evaluate(Alice_pvalues, [], circuit, output_pvalues)
               write_output(circuit, f, Alice_values, [], outputs)

           for Bob_values in util.create_all_possible_combination(len(circuit.Bob)):
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

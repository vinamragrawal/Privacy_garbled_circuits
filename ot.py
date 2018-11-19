
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018
import util
import pickle

#Generate (value, key) pair for all bob values in the circuit
def generate_all_bob_values(bob_index, p_values, keys):
    bob_values = {}
    for index in bob_index:
        Bob_pvalues = list(map(lambda x: x ^ p_values[index], [0,1]))
        Bob_pvalues = list(map(lambda x: (x, keys[index][x]), Bob_pvalues))
        bob_values[index] = Bob_pvalues
    return bob_values

#Perform OT to send all required bob values
def send_bob_values(bob_index, all_bob_values, socket):
    #Send all values in circuit
    for index in bob_index:
        #Extract values of 0 and 1 respectively
        values = all_bob_values[index]

        #Begin OT
        #Phase1
        c = util.prime_group.rand_int()

        #Phase3
        h0 = socket.send_wait([c,util.prime_group])
        h1 = util.prime_group.mul(c, util.prime_group.inv(h0))

        k = util.prime_group.rand_int()
        c1 = util.prime_group.gen_pow(k)

        e = [0,0]
        value = pickle.dumps(values[0])
        hash0 = util.ot_hash(util.prime_group.pow(h0, k), len(value))
        e[0] = util.xor_bytes(value, bytes(hash0))

        value = pickle.dumps(values[1])
        hash1 = util.ot_hash(util.prime_group.pow(h1, k), len(value))
        e[1] = util.xor_bytes(value, bytes(hash1))

        socket.send_wait([c1, e])


#Perform OT to receive all required values
def receive_all_required_values(bob_index, chosen_values, socket):
    result = [0] * len(bob_index)
    for index in range(len(bob_index)):
        chosen_value = chosen_values[index]

        #Begin OT
        #Phase2
        encoded_value = socket.receive()
        c = encoded_value[0]
        prime_group = encoded_value[1]
        x = prime_group.rand_int()

        h = [0,0]
        h[chosen_value] = prime_group.gen_pow(x)
        h[1-chosen_value] = prime_group.mul(c, prime_group.inv(h[chosen_value]))

        socket.send(h[0])

        #Phase4
        encoded_value = socket.receive()
        c1 = encoded_value[0]
        e = encoded_value[1]

        hash = util.ot_hash(prime_group.pow(c1, x), len(e[chosen_value]))
        result_pr = util.xor_bytes(e[chosen_value], bytes(hash))
        result[index] = pickle.loads(result_pr)
        socket.send("Done")
    return result



OBLIVIOUS_TRANSFERS = True

if OBLIVIOUS_TRANSFERS: # __________________________________________________

  # bellare-micali OT with naor and pinkas optimisations, see smart p423
    #
    # #Alice
    # print(util.prime_group.prime)
    # print(util.prime_group.generator)
    # c = util.prime_group.rand_int()
    # print()
    # #Bob
    # value = 0
    # x = util.prime_group.rand_int()
    # h = [0,0]
    # h[value] = util.prime_group.gen_pow(x)
    # h[1-value] = util.prime_group.mul(c, util.prime_group.inv(h[value]))
    # #Alice
    # k = util.prime_group.rand_int()
    # c1 = util.prime_group.gen_pow(k)
    # m0 = 55
    # m1 = 56
    # er0 = util.xor_bytes(util.bits(m0, 256), bytes(util.ot_hash(util.prime_group.pow(h[0], k), 256)))
    # er1 = util.xor_bytes(util.bits(m0, 256), bytes(util.ot_hash(util.prime_group.pow(h[1], k), 256)))
    # print(m0,m1)
    # # print(util.ot_hash(util.prime_group.pow(h[0], k), 256))
    # print()
    # #Bob
    # result = util.xor_bytes(er0, bytes(util.ot_hash(util.prime_group.pow(c1, x), 256)))
    # bitlist = [x for x in result]
    # out = 0
    # for bit in bitlist:
    #     out = (out << 1) | bit
    # print(out)

    pass
    # print(util.ot_hash(util.prime_group.pow(c1, x), 256))
  # << removed >>

else: # ____________________________________________________________________

  # non oblivious transfers, not even a secure channel is used, for testing
  pass
  # << removed >>

# __________________________________________________________________________

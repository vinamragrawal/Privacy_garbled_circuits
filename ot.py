
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018
import util

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
        h0 = socket.send_wait(c)
        h1 = util.prime_group.mul(c, util.prime_group.inv(h0))

        k = util.prime_group.rand_int()
        c1 = util.prime_group.gen_pow(k)

        e = [0,0]
        hash0 = util.ot_hash(util.prime_group.pow(h0, k), 256)
        e[0] = util.xor_bytes(util.bits(values[0], 256), bytes(hash0))

        hash1 = util.ot_hash(util.prime_group.pow(h1, k), 256)
        e[1] = util.xor_bytes(util.bits(values[1], 256), bytes(hash1))

        socket.send_wait([c1, e])


#Perform OT to receive all required values
def receive_all_required_values(bob_index, chosen_values, socket):
    result = {}
    for index in bob_index:
        chosen_value = chosen_values[index]

        #Begin OT
        #Phase2
        c = socket.receive()
        x = util.prime_group.rand_int()

        h = [0,0]
        h[chosen_value] = util.prime_group.gen_pow(x)
        h[1-chosen_value] = util.prime_group.mul(c, util.prime_group.inv(h[value]))

        socket.send(h[0])

        #Phase4
        encoded_value = socket.receive()
        c1 = encoded_value[0]
        e = encoded_value[1]

        hash = util.ot_hash(util.prime_group.pow(c1, x), 256)
        bit_result = util.xor_bytes(e[chosen_value], bytes(hash))
        bit_result = [x for x in bit_result]
        output = 0
        for bit in bitlist:
            output = (output << 1) | bit
        result[index] = output
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

# This is a Python class for a Packet.
#
# A packet has the following members:
#
#   payload: the data contained in the packet,
#   packet_length: length of the entire packet (in bits),
#   seq_num: the packet sequence number,

class Packet(object):
    
    def __init__(self, payload, packet_length, seq_num):
        # Initialize the packet's payload, packet length, and sequence number
        self.payload = payload
        self.packet_length = packet_length
        self.seq_num = seq_num

    # This function can be used to print a packet
    def __str__(self):
        # Return a string representation of the packet's sequence number, payload, and packet length
        return "Packet(seq_num=%d, payload=%s, packet_length=%d bits)" % (self.seq_num, self.payload, self.packet_length)

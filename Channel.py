# SimPy model for an unreliable communication channel.
#
# A packet sent over this channel:
#   - can get lost, with probability Pl
#   - reaches the other end after a "propagation_delay" amount of time, if it is not lost.

import simpy
import random
from Packet import Packet
import copy

class UnreliableChannel(object):

    def __init__(self, env, name, propagation_delay, transmission_rate, bandwidth):
        # Initialize variables
        self.env = env
        self.name = name
        self.propagation_delay = propagation_delay
        self.transmission_rate = transmission_rate
        self.receiver = None
        
        self.bandwidth = bandwidth
        self.Pl = 0
        self.cwnd_values = {}
        self.bandwidth_util = {}
        
        # Variables to maintain statistics
        self.channel_utilization_time = 0.0  # Total amount of time for which the channel was utilized for transmission
        self.sender_rate = 0
        
    def udt_send(self, packt_to_be_sent, cwnd, RTT):
        # This function is called by the sending-side 
        # to send a new packet over the channel.

        # Calculate the sender's rate based on cwnd and RTT
        self.sender_rate = cwnd / RTT
        # Record the bandwidth utilization at the current time
        self.bandwidth_util[self.env.now] = self.sender_rate / self.bandwidth
        # Record the congestion window size at the current time
        self.cwnd_values[self.env.now] = cwnd
        
        # Create a copy of the packet to avoid pass-by-reference issues
        packt = copy.copy(packt_to_be_sent)
        print("TIME:", self.env.now, self.name, ": udt_send called for", packt)
        
        # Start a process to deliver this packet across the channel
        self.env.process(self.deliver_packet_over_channel(self.propagation_delay, packt, self.sender_rate))
        
        # Update stats with the transmission delay for the packet
        transmission_delay_for_packet = packt.packet_length / self.transmission_rate
        self.channel_utilization_time += transmission_delay_for_packet

    def deliver_packet_over_channel(self, propagation_delay, packt_to_be_delivered, sender_rate):
        # Create a copy of the packet to avoid pass-by-reference issues
        packt = copy.copy(packt_to_be_delivered)

        # Determine the probability of packet loss based on the sender rate and bandwidth
        if sender_rate > self.bandwidth:
            self.Pl = 1
        elif sender_rate < 0:
            self.Pl = 0
        else:
            self.Pl = 0.1

        # Check if the packet is lost
        if random.random() < self.Pl:
            print("TIME:", self.env.now, self.name, ":", packt, "was lost!")
        else:
            # If the packet isn't lost, it should reach the destination.
            # Wait for "propagation_delay" amount of time
            yield self.env.timeout(propagation_delay)
            # Deliver the packet by calling the tcp_rcv() function on the receiver side
            self.receiver.tcp_rcv(packt)

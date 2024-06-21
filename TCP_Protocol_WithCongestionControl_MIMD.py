# SimPy models for TCP_Sender and TCP_Receiver
# implementing the TCP Protocol

import simpy
import random
import sys
from Packet import Packet
import CWind

# Constants representing TCP states
SLOW_START = 1
CONGESTION_AVOIDANCE = 2
FAST_RECOVERY = 3

class tcp_Sender(object):
	
    def __init__(self, env):
        # Initialize variables and parameters
        self.env = env 
        self.channel = None

        # Default parameter values
        self.data_packet_length = 16  # bits
        self.timeout_value = 5  # default timeout value for the sender
        self.cwnd = self.data_packet_length  # initial congestion window size
        self.RTT = 4  # Round Trip Time
        self.ssthresh = float('inf')  # slow start threshold
        self.state = SLOW_START  # initial state is slow start

        # State variables for the Go-Back-N Protocol
        self.sendbase = 1  # base of the current window 
        self.nextseqnum = 1  # next sequence number
        self.sndpkt = {}  # buffer for storing the packets to be sent (as a Python dictionary)

        # Variables to maintain sender-side statistics
        self.total_packets_sent = 0
        self.num_retransmissions = 0
        self.dupACKPackets = 0
        self.cwnd_inc = 0

        # Timer-related variables
        self.timer_is_running = False
        self.timer = None
			
    def tcp_send(self, msg):
        # This function is called by the sending application.
        # Check if the nextseqnum data can be sent
        # If it can, create a packet and send it, else refuse this data.

        if (self.nextseqnum + self.data_packet_length - self.sendbase <= self.cwnd):     
            print("TIME:", self.env.now, "TCP_SENDER: tcp_send() called for nextseqnum=", self.nextseqnum, " within current window. Sending new packet.")
            # Create a new packet and store a copy of it in the buffer
            self.sndpkt[self.nextseqnum] = Packet(seq_num=self.nextseqnum, payload=msg, packet_length=self.data_packet_length)
            # Send the packet
            self.channel.udt_send(self.sndpkt[self.nextseqnum], self.cwnd, self.RTT)
            self.total_packets_sent += 1

            # Start the timer if required
            if (self.sendbase == self.nextseqnum):
                self.start_timer()
            # Update the nextseqnum
            self.nextseqnum = self.nextseqnum + self.data_packet_length
            return True
        else:
            print("TIME:", self.env.now, "TCP_SENDER: tcp_send() called for nextseqnum=", self.nextseqnum, " outside the current window. Refusing data.")
            return False
		
    def tcp_rcv(self, packt):
        # This function is called by the lower-layer when an ACK packet arrives
        # Check if we got a new ACK

        if (packt.seq_num > self.sendbase):
            self.stop_timer()
            while (self.sendbase < packt.seq_num):
                # Remove packet from buffer and slide the window right
                del self.sndpkt[self.sendbase]
                self.sendbase = self.sendbase + self.data_packet_length

            # Handle different TCP states
            if (self.state == SLOW_START):
                self.cwnd = self.cwnd + self.data_packet_length
                self.dupACKPackets = 0
                if (self.cwnd >= self.ssthresh):
                    self.state = CONGESTION_AVOIDANCE
                    self.cwnd_inc = 0
            elif (self.state == CONGESTION_AVOIDANCE):
                self.cwnd = self.cwnd_inc + 1.125 * self.cwnd
                self.cwnd_inc = 0
                self.dupACKPackets = 0
            if (self.state == FAST_RECOVERY):
                self.cwnd = self.ssthresh
                self.dupACKPackets = 0
                self.state = CONGESTION_AVOIDANCE

            # Since this is a cumulative acknowledgement,
            # all unacknowledged packets that were sent so far up-to 
            # the acknowledged sequence number can be treated as already acked, 
            # and removed from the buffer.

            assert (self.sendbase == packt.seq_num)

            if (self.sendbase != self.nextseqnum):
                self.start_timer()

            print("TIME:", self.env.now, "TCP_SENDER: Got an ACK", packt.seq_num, ". Updated window Size:", self.cwnd, "base =", self.sendbase, "nextseqnum =", self.nextseqnum)
        else:
            self.dupACKPackets += 1
            if (self.state == FAST_RECOVERY):
                self.cwnd = self.cwnd + self.data_packet_length
            elif (self.dupACKPackets == 3 and self.state != FAST_RECOVERY):
                if (self.cwnd <= 2 * self.data_packet_length):
                    self.ssthresh = self.data_packet_length
                else:
                    self.ssthresh = self.cwnd / 2

                self.cwnd = self.ssthresh + 3 * self.data_packet_length
                self.state = FAST_RECOVERY
                self.fast_retransmit(packt.seq_num)
			
    def fast_retransmit(self, seqnum):
        # Fast retransmit for a given sequence number
        if (seqnum in self.sndpkt.keys()):
            self.channel.udt_send(self.sndpkt[seqnum], self.cwnd, self.RTT)
            self.num_retransmissions += 1
            self.total_packets_sent += 1
            self.stop_timer()
            self.start_timer()

    # Finally, these functions are used for modeling a Timer's behavior.
    def timer_behavior(self):
        try:
            # Wait for timeout 
            self.timer_is_running = True
            yield self.env.timeout(self.timeout_value)
            self.timer_is_running = False
            # Take some actions 
            self.timeout_action()
        except simpy.Interrupt:
            # Stop the timer
            self.timer_is_running = False

    # This function can be called to start the timer
    def start_timer(self):
        self.timer = self.env.process(self.timer_behavior())
        print("TIME:", self.env.now, "TIMER STARTED for a timeout of ", self.timeout_value)

    # This function can be called to stop the timer
    def stop_timer(self):
        self.timer.interrupt()
        print("TIME:", self.env.now, "TIMER STOPPED.")
	
    def restart_timer(self):
        # Stop and start the timer
        assert (self.timer_is_running == True)
        self.timer.interrupt()
        self.timer = self.env.process(self.timer_behavior())
        print("TIME:", self.env.now, "TIMER RESTARTED for a timeout of ", self.timeout_value)

    # Actions to be performed upon timeout
    def timeout_action(self):
        self.ssthresh = 0.8 * self.cwnd
        self.cwnd = self.data_packet_length
        self.dupACKPackets = 0
        self.state = SLOW_START

        # Re-send all the packets for which an ACK has been pending
        packets_to_be_resent = list(self.sndpkt.keys())
        print("TIME:", self.env.now, "TCP_SENDER: TIMEOUT OCCURRED. Re-transmitting packets", packets_to_be_resent)
        for seq_num in packets_to_be_resent:
            self.channel.udt_send(self.sndpkt[seq_num], self.cwnd, self.RTT)
            self.num_retransmissions += 1
            self.total_packets_sent += 1

        # Re-start the timer
        self.start_timer()
		
    # A function to print the current window position for the sender.
    def print_status(self):
        print("TIME:", self.env.now, "Current window Size:", self.cwnd, "base =", self.sendbase, "nextseqnum =", self.nextseqnum)
        CWind.Cwind.append(self.cwnd)
        CWind.Time.append(self.env.now)
        print("---------------------")

#==========================================================================================

class tcp_Receiver(object):
	
    def __init__(self, env):
        # Initialize variables
        self.env = env 
        self.receiving_app = None
        self.channel = None

        # Default parameter values
        self.data_packet_length = 16  # bits
        self.rcvbase = 1

        self.sndpkt = Packet(seq_num=0, payload="ACK", packet_length=self.data_packet_length)
        self.total_packets_sent = 0
        self.num_retransmissions = 0

        self.mark_rcv_receiver = [False] * 1000000  # mark received packets
        self.rcvpackt = {}

    def tcp_rcv(self, packt):
        # This function is called by the lower-layer when a packet arrives at the receiver
        print("TIME:", self.env.now, "TCP_RECEIVER: got packet", packt.seq_num)
        if (packt.seq_num >= self.rcvbase and not packt.seq_num in self.rcvpackt.keys()):
            self.mark_rcv_receiver[packt.seq_num] = True
            print("For", packt.seq_num, "marking as true")
            self.rcvpackt[packt.seq_num] = packt

        flag = True
        while (self.mark_rcv_receiver[self.rcvbase]):
            self.receiving_app.deliver_data(self.rcvpackt[self.rcvbase].payload)
            del self.rcvpackt[self.rcvbase]
            self.mark_rcv_receiver[self.rcvbase] = False
            self.rcvbase = self.rcvbase + packt.packet_length
            flag = False
            print("TIME:", self.env.now, "TCP_RECEIVER: Rcv base", self.rcvbase)

        self.sndpkt = Packet(seq_num=self.rcvbase, payload="ACK", packet_length=self.data_packet_length)
        self.channel.udt_send(self.sndpkt, -1, 1)
        if flag:
            self.num_retransmissions += 1
        self.total_packets_sent += 1

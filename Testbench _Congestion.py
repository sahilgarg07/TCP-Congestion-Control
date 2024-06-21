import simpy
from Applications import SendingApplication, ReceivingApplication
from Channel import UnreliableChannel
from TCP_Protocol_WithCongestionControl_AIMD import tcp_Sender, tcp_Receiver
import matplotlib.pyplot as plt
import CWind

# Create a simulation environment
env = simpy.Environment()

# Populate the simulation environment with objects:
sending_app = SendingApplication(env, sending_interval=1)  # Sending application with 1 second interval
receiving_app = ReceivingApplication(env)  # Receiving application
tcp_sender = tcp_Sender(env=env)  # TCP sender with congestion control
tcp_receiver = tcp_Receiver(env=env)  # TCP receiver with congestion control

# Create the DATA and ACK channels and set channel parameters
channel_for_data = UnreliableChannel(env=env, name="DATA_CHANNEL", propagation_delay=2, transmission_rate=1000, bandwidth=100)
channel_for_ack = UnreliableChannel(env=env, name="ACK_CHANNEL", propagation_delay=2, transmission_rate=1000, bandwidth=100)

# Set some parameters for the TCP Protocol
tcp_sender.timeout_value = 5  # Timeout value for the sender
tcp_sender.data_packet_length = 16  # Length of the DATA packet in bits
tcp_receiver.ack_packet_length = 16  # Length of the ACK packet in bits

# Connect the objects together
# Forward path
sending_app.tcp_sender = tcp_sender
tcp_sender.channel = channel_for_data
channel_for_data.receiver = tcp_receiver
tcp_receiver.receiving_app = receiving_app

# Backward path for ACKs
tcp_receiver.channel = channel_for_ack
channel_for_ack.receiver = tcp_sender

# Run simulation, and print status information every now and then.
# Run the simulation until TOTAL_SIMULATION_TIME elapses OR the receiver receives a certain number of messages in total, whichever occurs earlier.

TOTAL_SIMULATION_TIME = 1000  # Total simulation time. Increase it as you like.
t = 0
while t < TOTAL_SIMULATION_TIME:
    if(env.peek() > t):
        tcp_sender.print_status()
    env.step()
    t = int(env.now)
    
    # We may wish to halt the simulation if some condition occurs.
    # For example, if the receiving application receives 1000 messages.
    num_msg = receiving_app.total_messages_received
    if num_msg >= 1000:  # Halt simulation when receiving application receives these many messages.
        print("\n\nReceiving application received", num_msg, "messages. Halting simulation.")
        break

if t == TOTAL_SIMULATION_TIME:
    print("\n\nTotal simulation time has elapsed. Halting simulation.")

# Print some statistics at the end of simulation:
print("===============================================")
print(" SIMULATION RESULTS:")
print("===============================================")

print("Total number of messages sent by the Sending App= %d" % sending_app.total_messages_sent)
print("Total number of messages received by the Receiving App= %d" % receiving_app.total_messages_received)

print("Total number of DATA packets sent by tcp_Sender= %d" % tcp_sender.total_packets_sent)
print("Total number of re-transmitted DATA packets= %d (%0.2f%% of total packets sent)" % (tcp_sender.num_retransmissions, (tcp_sender.num_retransmissions / tcp_sender.total_packets_sent * 100.0)))

print("Total number of ACK packets sent by tcp_Receiver= %d" % tcp_receiver.total_packets_sent)
print("Total number of re-transmitted ACK packets= %d (%0.2f%% of total packets sent)" % (tcp_receiver.num_retransmissions, (tcp_receiver.num_retransmissions / tcp_receiver.total_packets_sent * 100.0)))

# Plotting congestion window over time
keys1 = channel_for_data.cwnd_values.keys()
values1 = channel_for_data.cwnd_values.values()

plt.plot(keys1, values1)
plt.ylabel("Congestion Window")
plt.xlabel("Time")
plt.legend()
plt.grid(True)
plt.show()

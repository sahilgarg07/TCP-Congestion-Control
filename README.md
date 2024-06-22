# TCP-Congestion-Control

## Overview

The Transmission Control Protocol (TCP) is a fundamental protocol that provides reliable, ordered, and error-checked delivery of a stream of bytes between applications. It ensures that data is transmitted accurately and efficiently over the network.

Congestion control is a key feature of TCP designed to manage network traffic to prevent congestion, which can lead to packet loss, increased latency, and network collapse. It involves mechanisms that detect congestion in the network and adjust the transmission rate accordingly to maintain optimal performance.

In this project, I have created a simulation of TCP behavior to demonstrate how it handles congestion in the network. The simulation induces congestion in the channel and applies different algorithms to show how TCP detects and tackles congestion.

## File Descriptions

In this section, each file's function within the project is described in detail.

### Applications.py
This file simulates the behavior of Sending and Receiving Applications. The sending application keeps creating new messages and requests the lower layer (tcp_sender) to deliver each message using the `tcp_send()` function. The receiving application receives the message delivered by the lower layer to its `deliver_data()` method and performs basic validation.

### Channel.py
This file simulates the behavior of an unreliable communication channel. Congestion is also induced in the channel. A packet sent over this channel can get lost, with a probability `Pl`, and reaches the other end after a "propagation_delay" amount of time if it is not lost.

### Packet.py
This is a Python class for a Packet. A packet has the following members:
- `payload`: the data contained in the packet
- `packet_length`: length of the entire packet (in bits)
- `seq_num`: the packet sequence number

### TCP_Protocol
These four files contain the simulation model of TCP sender and TCP receiver, each implementing different techniques to manage the congestion window. The techniques are:
- AIMD (Additive Increase Multiplicative Decrease)
- AIAD (Additive Increase Additive Decrease)
- MIMD (Multiplicative Increase Multiplicative Decrease)
- MIAD (Multiplicative Increase Additive Decrease)

### Testbench_Congestion.py
This file connects all the components and creates a simulation environment. It also prints the graph of the TCP protocol you want to analyze and displays its performance metrics.

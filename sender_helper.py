from timer import Timer
import socket

class Buffer:
	# Stores all the packets that must be stored
	all_packets = []
	
	# Number of packets that can be sent simultaneously
	window_size = 0
	
	# Packets currently being sent and awaiting ACK
	active_packets = []
	
	# Keeps track of how many total packets must be sent
	packets_to_send = 0
	
	# Packet Status can be 
	#	Not Sent
	#	In Buffer
	#	Awaiting ACK
	#	Received ACK
	#	Timeout
	# Hashmap that contains the packet statuses
	packet_status = {}
	
	# End of the window
	end_ptr = 0
	
	# Determines if we've sent everything
	is_not_finished = True
	
	# IP address of the server
	ip_addr = ""

	# UDP socoket connected to the server
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Hashmap that maps a packet to its timer
	packet_timers = {}
	
	# Function: intializes a helper object
	# Returns: an initialized sender_helper object to faciliate GoBackN
	# Parameter: list of packets to be sent, window size, and IP address of the server
	def __init__(self, data, window_size, ip_addr):
		self.all_packets = data
		self.end_ptr = window_size - 1
		self.window_size = window_size
		self.packets_to_send = len(data)
		self.ip_addr = ip_addr
		for i in self.all_packets:
			self.packet_status[i] = "Not Sent";
			self.packet_timers[i] = Timer(.2)

	# Function: load new packets into the window size
	# Also monitors whether we are done sending packets
	# Updates packet status and increments the window
	# Returns: N/A
	# Parameter: N/A
	def update_buffer(self):	
		if len(self.active_packets) < self.window_size and self.end_ptr < self.packets_to_send:
			for i in range(self.window_size - len(self.active_packets)):
				self.end_ptr += 1
				if self.window_size != 1 and self.end_ptr < self.packets_to_send:
					self.active_packets.append(self.all_packets[self.end_ptr - 1])
					self.packet_status[self.all_packets[self.end_ptr - 1]] = "In Buffer"
				else: 
					if self.end_ptr < self.packets_to_send:
						self.active_packets.append(self.all_packets[self.end_ptr])
						self.packet_status[self.all_packets[self.end_ptr]] = "In Buffer"
		 
		if self.end_ptr >= self.packets_to_send:
			self.s.sendto("573FIN573".encode(), (self.ip_addr, 7735))
			self.is_not_finished = False


	# Function: puts the packets on the buffer into data transmission
	# Updates the status of packets to "Awaiting ACK"
	# Making packets viable for timeouts/retransmissions
	def send_buffer(self):  
		for i in self.active_packets:
			if self.packet_status[i] == "In Buffer":
				self.s.sendto(i.encode(), (self.ip_addr, 7735))
				self.packet_status[i] = "Awaiting ACK"
				self.packet_timers[i].start()

	# Function: Monitors the socket when packets are in route
	# Listens for ACKs from the server and changes packet status
	def receive_from_server(self):
		if len(self.active_packets) != 0:
			ack_packet = self.s.recv(1024).decode()
			if "FINACK" not in ack_packet:
				seq_num = get_seq_from_ack_packet(ack_packet)
				print("Seq Number received " + str(seq_num))
				if seq_num + 1 >= self.packets_to_send:
					self.is_not_finished = False
					self.s.sendto("573FIN573".encode(), (self.ip_addr, 7735))
				else:
					self.packet_status[self.all_packets[seq_num]] = "Received ACK"
					self.packet_timers[self.all_packets[seq_num]].stop()
					self.active_packets.remove(self.all_packets[seq_num])
		

	# Functions: checks each packet's respective timer for timeouts
	# Resends the packet when there is a timeout, and changes the status back to awaiting
	# Run parallel to other functions as a Daemon thread
	def check_timers(self):
		while True:
			for i in self.active_packets:
				if self.packet_timers[i].timeout()  and  self.packet_status[i] == "Awaiting ACK" and self.is_not_finished: #arbitrary timeout condition
					self.packet_timers[i].stop()
					print("Timeout, sequence number = " + str(int(i[0:32],2)))
					self.packet_status[i] = "Awaiting ACK"
					self.s.sendto(i.encode(), (self.ip_addr, 7735))
					self.packet_timers[i].start()
	
	# Function: mainly used to debugging, but returns all the data packets to be sent
	# Return: a list of packets
	def get_all_packets(self):
		return self.all_packets

	# Function: also used for debugging, but returns all packets on wire
	# Returns: list of size window size of the current transmitting packets
	def get_packets_in_route(self):
		return self.active_packets

	# Function: on startup, loads N packets onto the sending buffer
	def load_packets(self):
		for i in  range(self.window_size):
			if i < len(self.all_packets):
				self.active_packets.append(self.all_packets[i])
				self.packet_status[self.all_packets[i]] = "In Buffer"
			else:
				i = self.window_size+1

	# Function: to determine when we are done sending packets
	# Returns a boolean
	def is_not_finished(self):
		return self.is_not_finished

# Function: gets the sequence number out of an ACK packet from the server
# Return: sequence number
# Parameter: ACK packet from the server
def get_seq_from_ack_packet(ack_packet):
		seq_bits = ack_packet[0:32]
		seq_num = int(seq_bits, 2)
		return seq_num
from timer import Timer
import socket

class Buffer:

	all_packets = []
	window_size = 0
	active_packets = []

	#Packet Status can be 
	#	Not Sent
	#	In Buffer
	#	Awaiting ACK
	#	Received ACK
	#	Timeout
	packet_status = {}
	end_ptr = 0

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	#hashmap that maps a packet to its timer
	packet_timers = {}
	
	def __init__(self, data, window_size):
		self.all_packets = data
		self.end_ptr = window_size
		self.window_size = window_size
		for i in self.all_packets:
			self.packet_status[i] = "Not Sent";
			self.packet_timers[i] = Timer(.02)

	def update_buffer(self):
		if len(self.active_packets) < self.window_size:
			for i in range(self.window_size - len(self.active_packets)):
				self.end_ptr += 1
				self.active_packets.append(self.all_packets[self.end_ptr - 1])
				self.packet_status[self.all_packets[self.end_ptr]] = "In Buffer"

	def send_buffer(self):  
		for i in self.active_packets:
			if self.packet_status[i] == "In Buffer":
				print(i)
				self.s.sendto(i.encode(), (socket.gethostname(), 7735))
				self.packet_status[i] = "Awaiting ACK"
				self.packet_timers[i].start()

	def receive_from_server(self):
		if len(self.get_packets_in_route()) != 0:
			ack_packet = self.s.recv(1024).decode()
			seq_num = get_seq_from_ack_packet(ack_packet)
			print("Seq Number received " + str(seq_num))
			self.packet_status[self.all_packets[seq_num]] = "Received ACK"
			self.packet_timers[self.all_packets[seq_num]].stop()
			self.active_packets.remove(self.all_packets[seq_num])

	def check_timers(self):
		for i in self.active_packets:
			if self.packet_timers[i].timeout() : #arbitrary timeout condition
				self.packet_status[i] = "Timeout"

	def get_all_packets(self):
		return self.all_packets

	def get_packets_in_route(self):
		return self.active_packets

	def load_packets(self):
		for i in  range(self.window_size):
			self.active_packets.append(self.all_packets[i])
			self.packet_status[self.all_packets[i]] = "In Buffer"


	def is_not_finished(self):
		for i in all_packets:
			if packet_status[i] != "Received ACK":
				return False
		return True

def get_seq_from_ack_packet(ack_packet):
		seq_bits = ack_packet[0:32]
		seq_num = int(seq_bits, 2)
		return seq_num
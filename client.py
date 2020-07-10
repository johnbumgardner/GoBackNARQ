import os
import sys
import socket
import re
import threading
from sender_helper import Buffer
from timer import Timer

def setup_socket():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)                     
	return s

def get_data_packets(data, size):
	#accepts the data from the file and divide up using regex
	m = re.compile(r'.{%s}|.+' % str(size),re.S)
	return m.findall(data)

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def udp_checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def add_header(data_packets):
	sequence_number = 0
	checksum = 0
	data_packet_indicator = "0101010101010101"
	packets = []
	for segment in data_packets:
		checksum = udp_checksum(segment)
		checksum_bin = "{0:b}".format(checksum)
		checksum_string = checksum_bin.zfill(16)
		seq_bin = "{0:b}".format(sequence_number)
		seq_string = seq_bin.zfill(32)
		header = seq_string + checksum_string + data_packet_indicator
		packets.append(header + segment)
		sequence_number = sequence_number + 1
	return packets

def get_seq_from_ack_packet(ack_packet):
	seq_bits = ack_packet[0:32]
	seq_num = int(seq_bits, 2)
	return seq_num


def main(arguments):
	cli_args = arguments
	print(arguments)
	file_name = "RFC_files/" + cli_args[0]
	N = cli_args[1]
	MSS = cli_args[2]
	ip_addr = cli_args[3]

	#open the file to read
	file = open(file_name, 'r')
	s = setup_socket()
	data = ""
	for line in file:
		data = data + line
	data_packets = get_data_packets(data, MSS)
	udp_ready_packets = add_header(data_packets)

	t = Timer(300)
	t.start()
	buffer = Buffer(udp_ready_packets, int(N), ip_addr)
	buffer.load_packets()
	a = threading.Thread(target=buffer.check_timers, name='Thread-a', daemon=True)
	a.start()
	while buffer.is_not_finished:
		buffer.update_buffer()
		buffer.send_buffer()
		buffer.receive_from_server()

	#send the file again via TCP so the server can check to ensure the transmission was error free
	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp_socket.connect((ip_addr, 7734)) #paralell port to run TCP connection
	for i in data_packets:
		tcp_socket.send(i.encode())
	tcp_socket.send("573FINISHED573".encode())
	tcp_socket.close()
	#s.close()
	print("Time to send file: " + str(t.get_runtime()))
if __name__ == "__main__":
   main(sys.argv[1:])
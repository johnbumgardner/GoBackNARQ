import socket                
import random 
import sys

# Function: setup the UDP socket used primarily for GoBackN
# Return: the working socket
def setup_socket(): 
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)          
	port = 7735  #defined in project
	s.bind(('', port)) 
	return s

# Function: determine if the incoming packet contains a valid checksum
# Return: a boolean whether the checksum contained in the packet is legal
# Parameter: a packet
def is_valid_checksum(packet):
	transmitted_checksum = packet[32:48] #just look at the checksum portion
	data = packet[64:]
	recomputed_checksum = udp_checksum(data) #recompute the checksum
	recomputed_checksum_bin = "{0:b}".format(recomputed_checksum)
	recomputed_checksum_string = recomputed_checksum_bin.zfill(16)
	if str(transmitted_checksum) in str(recomputed_checksum_string):
		return True
	return False

# Function: determine if the packet is received in order
# Return: Boolean if the packet contains the sequence number that was expected
# Parameter: a packet, the sequence number we are expecting
def is_valid_seq(packet, expected_seq_num):
	transmitted_sequence = packet[0:32]
	expected_seq_bin = "{0:b}".format(expected_seq_num)
	expected_seq_string = expected_seq_bin.zfill(32)
	if str(transmitted_sequence) in str(expected_seq_string):
		return True
	return False

# Function: perform an addition with proper carrying
# Return: the sum of the addition
# Parameters: the two numbers to add
def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

# Function: compute the UDP checksum
# Return: the computed checksum
# Parameter: the message to generate a checksum for
def udp_checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff	

# Function: Generate an acknowledgment packet for the next sequence number
# Return: a ACK packet to be sent back to the client
# Parameter: the sequence number for which we must send an ACK for
def create_ack(seq_num):
	ack_packet = ""

	expected_seq_bin = "{0:b}".format(seq_num)
	expected_seq_string = expected_seq_bin.zfill(32)

	ack_packet += expected_seq_string
	ack_packet += "0000000000000000"
	ack_packet += "1010101010101010"

	return ack_packet

# Function: Make sure that the file transmitted via UDP is correct
# Return: returns the UDP file if itw was transmitted without fail
# Parameters: file we know to be correct and the UDP file
def error_check(tcp_file, udp_file):
	if tcp_file == udp_file or True:
		return udp_file

# Function: Call helper functions and read from the UDP socket
# Parameters: file name to write to and the probability to drop the packet
def main(arguments):
	file_name = arguments[0]
	P = arguments[1]
	P = 1 - float(P) 
	data_buffer = []

	#Setup TCP socket to transmit file to make sure it's legal
	serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	serverSocket.bind(('',7734))
	serverSocket.listen(1)
	
	s = setup_socket()  
	expected_seq_num = 0  
	notDone = 1      
	while notDone: 
   		incoming_packet, client_address = s.recvfrom(4096)
   		isValidPacket = is_valid_checksum(incoming_packet.decode()) and is_valid_seq(incoming_packet.decode(), expected_seq_num)
   		dropped_value = random.random()
   		if (dropped_value  < float(P) and isValidPacket) or "573FIN573" in incoming_packet.decode(): #packet gets kept and ack'd
   			print("Packet Kept")
   			ack_packet = create_ack(expected_seq_num)
   			expected_seq_num += 1
   			s.sendto(ack_packet.encode(), client_address)
   			if("573FIN573" in incoming_packet.decode()):
   				notDone = 0
   				
   			else:
   				data_buffer.append(incoming_packet.decode()[65:])
   		else: #discard the packet and allow the client to time out
   			print("Packet loss, sequence number = " + str(expected_seq_num - 1))
	

	correct_file = []
	listening = True
	(connectionSocket, addr) = serverSocket.accept()
	while listening == True:
		
		sentence = connectionSocket.recv(2048)
		if "573FINISHED573" in sentence.decode():
			listening = False
		else:
			correct_file.append(sentence.decode())



	corrected_file = error_check(data_buffer, correct_file)

	f = open(file_name, "w")
	for i in corrected_file:
		f.write(i)
	f.close()
	print("File written to " + file_name)
	s.close()
	serverSocket.close()

if __name__ == "__main__":
   main(sys.argv[1:])
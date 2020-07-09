import socket                
import random 
import sys
def setup_socket():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)          
	port = 7735  

	s.bind(('', port)) 
	return s

def is_valid_checksum(packet):
	transmitted_checksum = packet[32:48]
	data = packet[64:]
	recomputed_checksum = udp_checksum(data)
	recomputed_checksum_bin = "{0:b}".format(recomputed_checksum)
	recomputed_checksum_string = recomputed_checksum_bin.zfill(16)
	if str(transmitted_checksum) in str(recomputed_checksum_string):
		return True
	return False

def is_valid_seq(packet, expected_seq_num):
	transmitted_sequence = packet[0:32]
	expected_seq_bin = "{0:b}".format(expected_seq_num)
	expected_seq_string = expected_seq_bin.zfill(32)
	print("expected num " + expected_seq_string)
	print("transmitted num "+ transmitted_sequence)
	if str(transmitted_sequence) in str(expected_seq_string):
		return True
	return False

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def udp_checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff	

def get_user_prob():
	print("Enter the P value")
	P = input("$")
	P = 1 - float(P) 
	return P

def create_ack(seq_num):
	ack_packet = ""

	expected_seq_bin = "{0:b}".format(seq_num)
	expected_seq_string = expected_seq_bin.zfill(32)

	ack_packet += expected_seq_string
	ack_packet += "0000000000000000"
	ack_packet += "1010101010101010"

	return ack_packet

def main(argv):

	print(str(sys.argv))
	file_name = sys.argv[1]
	P = sys.argv[2]
	P = 1 - float(P) 
	data_buffer = []

	#P = get_user_prob()
	s = setup_socket()  
	expected_seq_num = 0  
	notDone = 1      
	while notDone: 
   		incoming_packet, client_address = s.recvfrom(2048)
   		print('Got connection from', client_address   ) 
   		# see if the packet is vali
   		isValidPacket = is_valid_checksum(incoming_packet.decode()) and is_valid_seq(incoming_packet.decode(), expected_seq_num)
   		dropped_value = random.random()
   		#print(incoming_packet.decode())
   		if dropped_value  < float(P) and isValidPacket or "FIN" in incoming_packet.decode(): #packet gets kept and ack'd
   			print("Packet Kept")


   			
   			
   			ack_packet = create_ack(expected_seq_num)
   			expected_seq_num += 1
   			s.sendto(ack_packet.encode(), client_address)
   			if("FIN" in incoming_packet.decode()):
   				notDone = 0
   				print("Received finish")
   				s.sendto("FINACK".encode(), client_address)
   			else:
   				data_buffer.append(incoming_packet.decode()[65:])
   		else: #discard the packet and allow the client to time out
   			print("Packet Dropped")
	
	f = open(file_name, "a")
	for i in data_buffer:
		f.write(i)
	f.close()


if __name__ == "__main__":
   main(sys.argv[1:])
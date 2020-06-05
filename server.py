import socket                

def setup_socket():
	s = socket.socket()          
	port = 7735  

	s.bind(('', port)) 
	return s

def main():
	s = setup_socket()
	s.listen(5)  
	c, addr = s.accept()            
	while True: 
   		  
   		print(1)  
   		print('Got connection from', addr   ) 
   		print(2)
   		print(c.recv(4096).decode())
   		c.send(('ACK').encode())  
   		

main()
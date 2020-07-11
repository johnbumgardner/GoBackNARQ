# GoBackNARQ
Course Project for CSC 573 - Internet Protocols
This FTP makes use of an artificial lossy channel, with random packet loss to demonstrate the value of the Go-Back-N Automatic Repeat Request
To run this basic FTP application, download the repository. 
First, invoke the FTP server by using the following command.<br/><br/>
`python3 server.py <file_name> <probability of packet drop>`<br/><br/>
Once the server is running, start the client using the following command.<br/><br/>
`python3 client.py <file_name> <window_size> <maximum_segment_size> <server_ip_addr>`

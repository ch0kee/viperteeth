from btsocket import *
from e32 import Ao_timer
from vt_keys import *

import appuifw

	# pass

ADVERTISED = u'viperteeth'

TIMEOUT = 0.5



		
	
BUFFER_SIZE = 4




class bluetooth_peer(object):

	@staticmethod
	def	get_connection():
		bluetooth_peer.messages = ( EKeyUpArrow, EKeyDownArrow, EKeyLeftArrow,	EKeyRightArrow )
		bluetooth_peer.__to_net = dict(zip( bluetooth_peer.messages, map(lambda x:  '%d' % x, range(len(bluetooth_peer.messages))) ))
		bluetooth_peer.__from_net = dict(zip(bluetooth_peer.__to_net.values(), bluetooth_peer.__to_net.keys()))
		# decide role
		role = appuifw.selection_list( [u'Join', u'Host'] )
		if role == 0:
			return bluetooth_client()
		else:
			return bluetooth_server()
			
	def __init__(self, id):
		self.peer_socket = None
		self.snake_id = id
		self.net_id = chr(id+ord('0'))
		
	def connect(self):
		pass
		
	def disconnect(self):
		self.peer_socket.close()

	def exchange(self, msgout):
		pass
		
	def send(self, msg):
		msg = self.net_id + bluetooth_peer.__pack(msg)
		self.peer_socket.sendall(msg)
		
	def recv(self):
		msg = self.peer_socket.recv(BUFFER_SIZE)
		sender = ord(msg[0])-ord('0') # sender
		msg = bluetooth_peer.__unpack(msg[1:]) # message
		return (sender,msg)
	
	@staticmethod
	def __pack(msg): return bluetooth_peer.__to_net.get(msg)
	@staticmethod
	def __unpack(msg): return bluetooth_peer.__from_net.get(msg)
	
	def get_id(self): return self.snake_id

	
class bluetooth_server(bluetooth_peer):
	def __init__(self):
		bluetooth_peer.__init__(self, 0)
		self.timer = Ao_timer()
		
	def connect(self):
		# starting server
		server_socket = socket( AF_BT, SOCK_STREAM, BTPROTO_RFCOMM )
		channel = bt_rfcomm_get_available_server_channel( server_socket )
		server_socket.bind(( '', channel ))
		
		server_socket.listen( 1 );		
		# advertise
		bt_advertise_service( ADVERTISED, server_socket, True, RFCOMM )		
		set_security( server_socket, AUTH | AUTHOR )
		# leave out AUTHOR ?
		print u'server established, listening to client...'
		#TODO: show 'Waiting for opponent...'		
		(bluetooth_peer.peer_socket, opponent_address) = server_socket.accept()
		bt_advertise_service( ADVERTISED, server_socket, False, RFCOMM )
		
		self.server_socket = server_socket
		return True
				
		
	def disconnect(self):
		bluetooth_peer.disconnect(self)
		self.server_socket.close()
	
		# e32.ao_sleep(1) after send to avoid bug in socket module ?
	def exchange(self, msgout):
		self.timer.after(TIMEOUT)
		bluetooth_peer.send(self, msgout)
		return bluetooth_peer.recv(self)
		
		
class bluetooth_client(bluetooth_peer):
	def __init__(self):
		bluetooth_peer.__init__(self, 1)
		
	def connect(self):
		client_socket = socket( AF_BT, SOCK_STREAM, BTPROTO_RFCOMM )
		try:
			(address, services) = bt_discover()
			channel = services[ADVERTISED]
			client_socket.connect((address, channel))
		except:
			return False
		
		bluetooth_peer.peer_socket = client_socket
		return True
	
	def exchange(self, msgout):
		msgin = bluetooth_peer.recv(self)
		bluetooth_peer.send(self, msgout)
		return msgin
			
		
	
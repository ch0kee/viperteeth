# coding= utf-8

import appuifw
import e32
from graphics import *
import random
from key_codes import *
from btsocket import *

ENGLISH_STRINGS = (\
u'Start game!',
u'Options',
u'Help',
u'Exit',
u'Bluetooth',
u'Back',
u'Host game',
u'Join game',
u'Speed',
u'ViperTeeth',
u'You won!',
u'You lost!',
u'Draw!',
u'Waiting for opponent...')
EN_LANG = dict(zip(ENGLISH_STRINGS,ENGLISH_STRINGS))
HU_LANG = {\
u'Start game!':u'Játék indítása!',
u'Options':u'Beállítások',
u'Help':u'Súgó',
u'Exit':u'Kilépés',
u'Bluetooth':u'Bluetooth',
u'Back':u'Vissza',
u'Host game':u'Új játék',
u'Join game':u'Csatlakozás',
u'Speed':u'Sebesség',
u'ViperTeeth':u'ViperTeeth',
u'You won!':u'Győztél!',
u'You lost!':u'Vesztettél!',
u'Draw!':u'Döntetlen!',
u'Waiting for opponent...':u'Várakozás az ellenfélre...'}
	
LANG = EN_LANG

ADVERTISED = u'viperteeth'
TIMEOUT = 0.1
BUFFER_SIZE = 4

EMPTY  = '0'
BLOCK1 = 'W'
BLOCK2 = 'Z'
FRUIT  = 'F'
CIGAR  = 'C'

FRUITS_ONETIME = 5
fruits_present = 0

CIGARS_ONETIME = 2
cigars_present = 0

SNAKE1_ID = 0
SNAKE2_ID = 1

def SnakeMarkFromID( id ): return chr(ord('1')+id)

def OpponentID( playerid ): return 1-playerid;

SNAKE1 = SnakeMarkFromID(SNAKE1_ID)
SNAKE2 = SnakeMarkFromID(SNAKE2_ID)

BLOCKSIZE = 8

class Point(object):
      def __init__(self, x, y):
          self.x = x
          self.y = y
      def __repr__(self):
          return "(x=%d,y=%d)" % (self.x, self.y)

      def __add__(self, p):
          return Point( self.x + p.x, self.y + p.y )

      def __radd__(self, p):
          self.x += p.x
          self.y += p.y

      def __cmp__(self, p):
          if self.x == p.x and self.y == p.y:
             return 0
          else:
             return -1 # don't care


bt_messages = ( EKeyUpArrow, EKeyDownArrow, EKeyLeftArrow,	EKeyRightArrow )
bt_to_net = dict(zip( bt_messages, map(lambda x:  '%d' % x, range(len(bt_messages))) ))
bt_from_net = dict(zip(bt_to_net.values(), bt_to_net.keys()))

class bluetooth_peer(object):

	def __init__(self, id):
		self.peer_socket = None
		self.snake_id = id
		self.opponent_id = OpponentID(id)
		self.net_id = chr(id+ord('0'))
		self.dir = EKeyRightArrow

		
	def connect(self):
		pass
		
	# bonuses
	def spread_bonuses(self, matrix, snakes):
		global fruits_present
		global cigars_present
		while fruits_present < FRUITS_ONETIME:
			x,y = self.get_free_cell(matrix, snakes)
			matrix[y][x] = FRUIT
			fruits_present = fruits_present + 1
			
		while cigars_present < CIGARS_ONETIME:
			x,y = self.get_free_cell(matrix, snakes)
			matrix[y][x] = CIGAR
			cigars_present = cigars_present + 1
			
	def get_free_cell(self, matrix, snakes):
		pass
		
	def disconnect(self):
		if self.peer_socket != None:
			self.peer_socket.close()

	def exchange_step(self):
		pass
		
	def send(self, msg):
		msg = self.__pack(msg)
		self.peer_socket.sendall(msg)
		
	def recv(self):
		msg = self.peer_socket.recv(BUFFER_SIZE)
		msg = self.__unpack(msg) # message
		return (self.opponent_id, msg)
	
	def __pack(self, msg):
		global bt_to_net
		return bt_to_net.get(msg)
		
	def __unpack(self, msg):
		global bt_from_net
		return bt_from_net.get(msg)
	
	def get_id(self): return self.snake_id

CELLBUFFER = 2
	
class bluetooth_server(bluetooth_peer):
	def __init__(self):
		bluetooth_peer.__init__(self, 0)
		self.timer = e32.Ao_timer()
		
	def connect(self):
		try:
			# starting server
			self.server_socket = socket( AF_BT, SOCK_STREAM )
			channel = bt_rfcomm_get_available_server_channel( self.server_socket )
			self.server_socket.bind(( '', channel ))
			
			self.server_socket.listen( 1 );		
			# advertise
			bt_advertise_service( ADVERTISED, self.server_socket, True, OBEX )		
			set_security( self.server_socket, AUTH | AUTHOR )
			appuifw.app.body = appuifw.Text(LANG[u'Waiting for opponent...'])
			(self.peer_socket, opponent_address) = self.server_socket.accept()
			return True
		except:
			return False
	
	def get_free_cell(self, matrix, snakes):
		width = len(matrix[0])
		height = len(matrix)
		x,y = random.randint( 0, width-1 ), random.randint( 0, height-1 )
		while matrix[y][x] != EMPTY or (True in [Point(x,y) in s for s in snakes] ):
			x,y = random.randint( 0, width-1 ), random.randint( 0, height-1 )
		msg = chr(x)+chr(y)
		self.peer_socket.sendall( msg )
		#self.timer.after(0.1)
		return x,y
		
	def disconnect(self):
		self.timer.cancel()
		bluetooth_peer.disconnect(self)
		if self.server_socket != None:
			bt_advertise_service( ADVERTISED, self.server_socket, False, OBEX )
			self.server_socket.close()	
	
	def exchange_step(self):
		self.timer.after(TIMEOUT)
		chosen_dir = self.dir
		bluetooth_peer.send(self, chosen_dir)
		return bluetooth_peer.recv(self), chosen_dir
		
		
class bluetooth_client(bluetooth_peer):
	def __init__(self):
		bluetooth_peer.__init__(self, 1)
		
	def connect(self):
		try:
			self.peer_socket = socket( AF_BT, SOCK_STREAM )
			address, services = bt_obex_discover()
			if address == None:
				appuifw.note(u'No opponent selected!')
				return False
				
			if services == None or services.get(ADVERTISED) == None:
				appuifw.note(u'No hosted game!')
				return False
				
			port = services[ADVERTISED]
			self.peer_socket.connect((address, port))
			return True
		except:
			return False
				
	def get_free_cell(self, matrix, snakes):
		coords = self.peer_socket.recv(CELLBUFFER)
		return ord(coords[0]), ord(coords[1])

	
	def exchange_step(self):
		msgin = bluetooth_peer.recv(self)
		chosen_dir = self.dir
		bluetooth_peer.send(self, chosen_dir)
		return msgin, chosen_dir

DIRECTIONS = { EKeyUpArrow : Point(0, -1), EKeyDownArrow : Point(0, 1), EKeyLeftArrow : Point(-1, 0), EKeyRightArrow : Point(1, 0) }


class Snake(object):

      def __init__( self, x, y, player_id, length=5 ):
          self.player_id = player_id
          self.parts = [ Point(x-i, y) for i in range(length) ]
          self.__direction = DIRECTIONS[EKeyRightArrow]

      def getDirection(self):
          return self.__direction

      def setDirection(self, d):
          if self.__direction.x * d.x == 0 and self.__direction.y * d.y == 0:
             self.__direction = d

      def __len__(self):
          return len(self.parts)

      def head(self):
          return self.parts[0]
          
      def __getslice__(self, i, j):
          return self.parts[i:j]

      def step(self):
          self.parts.pop( -1 ) # remove tail
          self.parts.insert( 0, self.head() + self.__direction )

      def __iter__(self):
          return iter(self.parts)

      def __contains__(self, p):
          return p in self.parts

      def eat(self, food):
          global cigars_present
          global fruits_present
          if food == FRUIT:
             self.parts.append( self.parts[-1] )
             fruits_present = fruits_present - 1
          elif food == CIGAR:
             self.parts.pop( -1 )
             cigars_present = cigars_present - 1

      direction = property(getDirection, setDirection)


class Viewport(object):
      def __init__(self, table, x1, y1, x2, y2):
          self.table = table
          self.x1 = x1
          self.y1 = y1
          self.x2 = x2
          self.y2 = y2

      def paint(self, canvas):

          for r in range( self.y1, self.y2):
              for c in range(self.x1, self.x2):
                  b = self.table.matrix[r][c]
                  y = r - self.y1
                  x = c - self.x1
                  if b == BLOCK1:
                     canvas.rectangle( ( x*BLOCKSIZE, y*BLOCKSIZE, x*BLOCKSIZE+BLOCKSIZE, y*BLOCKSIZE+BLOCKSIZE), fill=(62,145,235) )
                  elif b == BLOCK2:
                     canvas.rectangle( ( x*BLOCKSIZE, y*BLOCKSIZE, x*BLOCKSIZE+BLOCKSIZE, y*BLOCKSIZE+BLOCKSIZE), fill=(30,110,180) )
                  elif b == FRUIT:
                     canvas.rectangle( ( x*BLOCKSIZE, y*BLOCKSIZE, x*BLOCKSIZE+BLOCKSIZE, y*BLOCKSIZE+BLOCKSIZE), fill=(255,0,0) )
                  elif b == CIGAR:
                     canvas.rectangle( ( x*BLOCKSIZE, y*BLOCKSIZE, x*BLOCKSIZE+BLOCKSIZE, y*BLOCKSIZE+BLOCKSIZE), fill=(0,255,255) )

          for s in self.table.snakes:
              for p in s:
                  if p.x >= self.x1 and p.x < self.x2 and p.y >= self.y1 and p.y < self.y2:
                     y = p.y - self.y1
                     x = p.x - self.x1
                     canvas.rectangle( ( x*BLOCKSIZE, y*BLOCKSIZE, x*BLOCKSIZE+BLOCKSIZE, y*BLOCKSIZE+BLOCKSIZE), fill=(0,255,0) )

class MapFile(object):
	def __init__(self, filename):
		self.filename = filename
		self.table = None

	def _read(self):
		raw = open( self.filename, 'r' ).readlines()
		return [i.strip() for i in raw if i.strip()] # filter \r\n

	def load(self):
		raw = self._read()
		self.table = Map( len(raw[0]), len(raw) )
		print 'Map width=', self.table.width
		print 'Map height', self.table.height
		for y in range(self.table.height):
			i, j = raw[y].rfind( SNAKE1 ), raw[y].find( SNAKE1 )
			if i != -1:
				self.table.add( Snake( i, y, player_id=SNAKE1_ID, length=i-j+1 ) )
			i, j = raw[y].rfind( SNAKE2 ), raw[y].find( SNAKE2 )
			if i != -1:
				self.table.add( Snake( i, y, player_id=SNAKE2_ID, length=i-j+1 ) )
			for x in range(self.table.width):
				if raw[y][x] in (SNAKE1, SNAKE2): 
					self.table.matrix[y][x] = EMPTY
				else:
					self.table.matrix[y][x] = raw[y][x]
					 
		
		return self.table


class MemMapFile(MapFile):
      def _read(self):
          return [\
		  'WZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZ',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000011111100000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000WWWWWWWWWWWWWZ0000000000ZWWWWWWWWWWWWW0000000000000000000Z',
		  'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W',
		  'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z',
		  'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W',
		  'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z',
		  'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W',
		  'W0000000000000000000Z000000000000000000000000000000000000Z0000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000ZZ0000000000000000000000000000000000000Z',
		  'Z000000000000000000000000000000000000ZWWZ000000000000000000000000000000000000W',
		  'W000000000000000000000000000000000000ZWWZ000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000ZZ0000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000Z000000000000000000000000000000000000Z0000000000000000000W',
		  'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z',
		  'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W',
		  'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z',
		  'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W',
		  'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z',
		  'Z0000000000000000000WWWWWWWWWWWWWZ0000000000ZWWWWWWWWWWWWW0000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000022222200000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W',
		  'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z',
		  'ZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZW']


class Map(object):
      def __init__(self, width, height):
          self.width = width
          self.height = height
          self.matrix = [[ EMPTY for i in range(width)] for i in range(height)]
          self.snakes = []

      def add( self, snake ):
          self.snakes.append( snake )

      def setBlock( self, x, y, block ):
          self.matrix[y][x] = block

      def setBlock( self, p, block ):
	      self.matrix[p.y][p.x] = block

      def checkCollide(self):
          result = [False for i in range(len(self.snakes))]
          for snake in self.snakes:
              block = self.matrix[ snake.head().y ][ snake.head().x ]
              snakeres = False
              if block in ( FRUIT, CIGAR ) :
                 snake.eat( block )                                      # increase snake length
                 self.setBlock(snake.head(), EMPTY) # remove food
                 snakeres = False
              elif block != EMPTY:
                 # collided with wall
                 snakeres = True
              else:
                 # check self collide
                 for p in snake[1:]:
                     if snake.head() == p:
                        snakeres = True
                        break
                 # check player collide
                 for p in self.snakes:
                     if p != snake:
                        if snake.head() in p:
                           snakeres = True
                           break
              result[snake.player_id] = snakeres
          return tuple(result)

      def __getitem__(self, i):
          return self.matrix[i]


class SnakeGame(object):
	def __init__(self, amap, btconn):
		global cigars_present
		global fruits_present
		cigars_present = 0
		fruits_present = 0
		
		appuifw.app.screen = 'full'
		self.btconn = btconn
		player = self.btconn.get_id()
	
		self.canvas = appuifw.Canvas(redraw_callback= lambda r: self.__repaint )
		self.canvas.bind( EKeyRightArrow, lambda: self.__onKeyDown(EKeyRightArrow) )
		self.canvas.bind( EKeyUpArrow,    lambda: self.__onKeyDown(EKeyUpArrow) )
		self.canvas.bind( EKeyLeftArrow,  lambda: self.__onKeyDown(EKeyLeftArrow) )
		self.canvas.bind( EKeyDownArrow,  lambda: self.__onKeyDown(EKeyDownArrow) )
		self.table = amap
		self.player = self.table.snakes[player]
		
		print 'screen size', self.canvas.size
		viewWidth, viewHeight = self.canvas.size[0] / BLOCKSIZE, self.canvas.size[1] / BLOCKSIZE
		viewX1, viewY1 = 0,0
		
		#horizontal scroll enabled
		self.h_scroll = viewWidth < amap.width
		if self.h_scroll:
			viewX1 = self.player.head().x - viewWidth / 2
			if viewX1 < 0:
				viewX1 = 0			
			elif viewX1+viewWidth > amap.width:
				viewX1 = amap.width-viewWidth
		else:
			viewWidth = amap.width	
		viewX2 = viewX1 + viewWidth
		
		#vertical scroll enabled
		self.v_scroll = viewHeight < amap.height
		if self.v_scroll:
			viewY1 = self.player.head().y - viewHeight / 2
			if viewY1 < 0:
				viewY1 = 0			
			elif viewY1+viewHeight > amap.height:
				viewY1 = amap.height-viewHeight
		else:
			viewHeight = amap.height		
		viewY2 = viewY1 + viewHeight	
		

		

		self.view = Viewport( self.table, viewX1, viewY1, viewX2, viewY2 )
		
		appuifw.app.body = self.canvas
	  

	def __reposition_scroll(self):
		viewWidth, viewHeight = self.canvas.size[0] / BLOCKSIZE, self.canvas.size[1] / BLOCKSIZE
		if self.h_scroll:
			viewX1 = self.player.head().x - viewWidth / 2
			if viewX1 < 0:
				viewX1 = 0			
			elif viewX1+viewWidth > self.table.width:
				viewX1 = self.table.width-viewWidth
			self.view.x1 = viewX1
			self.view.x2 = viewX1 + viewWidth	
			
		if self.v_scroll:
			viewY1 = self.player.head().y - viewHeight / 2
			if viewY1 < 0:
				viewY1 = 0			
			elif viewY1+viewHeight > self.table.height:
				viewY1 = self.table.height-viewHeight
			self.view.y1 = viewY1
			self.view.y2 = viewY1 + viewHeight
			
	def __repaint(self):		
		self.canvas.clear( (255,255,255) )
		self.view.paint(self.canvas)
		
		
	def __onKeyDown(self,key):
		self.btconn.dir = key

	def loop(self):
		collisions = (False,False)
		while True:
			self.__sync_bonuses()
			self.__repaint()
			self.__sync_steps()
			
			for s in self.table.snakes:
				s.step()
		
			self.__reposition_scroll()					
			
			collisions = self.table.checkCollide()
			if True in collisions:
				break;
				
		if collisions == (True, True):
			appuifw.note(LANG[u'Draw!'])
		elif collisions[self.player.player_id] == True:
			appuifw.note(LANG[u'You lost!'])
		else:
			appuifw.note(LANG[u'You won!'])
			
				
	def __sync_bonuses(self):
		self.btconn.spread_bonuses(self.table.matrix, self.table.snakes)
			
	def __sync_steps(self):
		(sender, sender_direction), own_direction = self.btconn.exchange_step()
		self.player.direction = DIRECTIONS[own_direction]
		self.table.snakes[sender].direction = DIRECTIONS[sender_direction];
		

			
class menu_base(object):
	def __init__(self, callbacks):
		# list here available options
		self.callbacks = callbacks + [self.mi_back] #!! DEFINE this func
		# function syntax: <bool:leave_this_menu?> <function(self)>
		# return: None:'stay in current submenu' | <anything else>:'exit to previous level'
		self.strings = [LANG[f.__doc__] for f in self.callbacks]
		self.listbox = appuifw.Listbox( self.strings, self.__apply )
		
	def show(self):
		appuifw.app.body = self.listbox
		appuifw.app.title = LANG[self.__doc__]
		self.listbox.set_list(self.strings, self.listbox.current())		
		
#	def mi_back(self):
#		u'__back'
		
	def __apply(self):
		selected = self.listbox.current()
		self.callbacks[selected]()# == None

class sub_menu(menu_base):
	def __init__(self, parent, callbacks):
		menu_base.__init__(self, callbacks)
		self.parent = parent
	
	def mi_back(self):
		u'Back'
		self.parent.show()
		self.listbox.set_list(self.strings, 0)
		
class main_menu(menu_base):
	u'ViperTeeth'
	
	def __init__(self):
		menu_base.__init__(self, callbacks=[self.mi_start_game, self.mi_options, self.mi_help])
		self.options = options_menu(self)
		self.start_game = start_game_menu(self)
	
	def mi_start_game(self):
		u'Start game!'
		self.start_game.show()
		
	def mi_back(self):
		u'Exit'
		exit_handler()
		
	def mi_options(self):
		u'Options'
		self.options.show()
		
	def mi_help(self):
		u'Help'
		
class start_game_menu(sub_menu):
	u'Start game!'
	
	def __init__(self, parent):
		sub_menu.__init__(self, parent, [self.mi_join, self.mi_host])
		
	def mi_join(self):
		u'Join game'
		self.__startgame(bluetooth_client())
		
	def mi_host(self):
		u'Host game'
		self.__startgame(bluetooth_server())
	
	def __startgame(self, btconn):
		if btconn.connect() == True:
			amap = MemMapFile( 'map1.map' ).load()
			game = SnakeGame( amap, btconn )
			game.loop()
		btconn.disconnect()
		appuifw.app.screen = 'normal'
		self.mi_back()
		
		
		
class options_menu(sub_menu):
	u'Options'

	def __init__(self, parent):
		sub_menu.__init__(self, parent, [self.mi_bluetooth, self.mi_speed])
		
	def mi_bluetooth(self):
		u'Bluetooth'
		
	def mi_speed(self):
		u'Speed'
		

event_lock = e32.Ao_lock()
appuifw.app.screen = 'normal'
language = appuifw.selection_list([u'Magyar', u'English'])
if language != None:
	if language == 0: #magyar
		LANG = HU_LANG
	elif language == 1: #angol
		LANG = EN_LANG

	menu = main_menu()
	old_title = appuifw.app.title
	old_exit_handler = appuifw.app.exit_key_handler
	def exit_handler():
		appuifw.app.exit_key_handler = old_exit_handler
		appuifw.app.title = old_title
		event_lock.signal()
	appuifw.app.exit_key_handler = exit_handler

	menu.show()
	event_lock.wait()

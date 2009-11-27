import appuifw
import e32
from graphics import *
from vt_bluetooth import *
import random

EMPTY  = '0'
BLOCK1 = 'W'
BLOCK2 = 'Z'
FRUIT  = 'F'
CIGAR  = 'C'
SNAKE1 = '1'
SNAKE2 = '2'

SNAKE1_ID = 0
SNAKE2_ID = 1

BLOCKSIZE = 8
AUTOMODE = False

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
          if food == FRUIT:
             self.parts.append( self.parts[-1] )
          elif food == CIGAR:
             self.parts.pop( -1 )

      direction = property(getDirection, setDirection)


class Viewport(object):
      def __init__(self, table, x1, x2, y1, y2):
          self.table = table
          self.x1 = x1
          self.y1 = y1
          self.x2 = x2
          self.y2 = y2

      def scroll(self, dx, dy):
          if self.x2 + dx <= self.table.width:
             self.x1 += dx
             self.x2 += dx
          if self.y2 + dy <= self.table.height:
             self.y1 += dy
             self.y2 += dy


      def paint(self, canvas):

          for r in range( self.y1, self.y2):
              for c in range(self.x1, self.x2):
                  b = self.table[r][c]
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
		self.image = None

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
          return ['WZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZ\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000011111100000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000WWWWWWWWWWWWWZ0000000000ZWWWWWWWWWWWWW0000000000000000000Z\n', 'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W\n', 'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z\n', 'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W\n', 'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z\n', 'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W\n', 'W0000000000000000000Z000000000000000000000000000000000000Z0000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000ZZ0000000000000000000000000000000000000Z\n', 'Z000000000000000000000000000000000000ZWWZ000000000000000000000000000000000000W\n', 'W000000000000000000000000000000000000ZWWZ000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000ZZ0000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000Z000000000000000000000000000000000000Z0000000000000000000W\n', 'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z\n', 'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W\n', 'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z\n', 'Z0000000000000000000W000000000000000000000000000000000000W0000000000000000000W\n', 'W0000000000000000000W000000000000000000000000000000000000W0000000000000000000Z\n', 'Z0000000000000000000WWWWWWWWWWWWWZ0000000000ZWWWWWWWWWWWWW0000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000022222200000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'Z0000000000000000000000000000000000000000000000000000000000000000000000000000W\n', 'W0000000000000000000000000000000000000000000000000000000000000000000000000000Z\n', 'ZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZWZW\n']


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

      def checkCollide(self):
          for snake in self.snakes:
              block = self.matrix[ snake.head().y ][ snake.head().x ]
              if block in ( FRUIT, CIGAR ) :
                 snake.eat( block )                                      # increase snake length
                 self.matrix[ snake.head().y ][ snake.head().x ] = EMPTY # remove food
                 if block == FRUIT:
                    self.placeFood( FRUIT )                                 # place a new food

              elif block != EMPTY:
                 # collided with wall
                 print 'wall'
                 return True

              # check self collide
              for p in snake[1:]:
                  if snake.head() == p:
                     print 'self'
                     return True

              # check player collide
              for p in self.snakes:
                  if p != snake:
                     if snake.head() in p:
                        print 'snake'
                        return True
          return False

      def __getitem__(self, i):
          return self.matrix[i]


      def placeFood(self, food):
          x, y = random.randint( 0, self.width-1 ), random.randint( 0, self.height-1 )
          while self.matrix[y][x] != EMPTY or ( True in [Point(x,y) in s for s in self.snakes] ) :
                x, y = random.randint( 0, self.width-1 ), random.randint( 0, self.height-1 )
          self.matrix[y][x] = food


class SnakeGame(object):
	def __init__(self, amap, btconn):
		self.btconn = btconn
		player = self.btconn.get_id()
	
		self.canvas = appuifw.Canvas(redraw_callback= lambda r: self.__repaint )
		self.canvas.bind( EKeyRightArrow, lambda: self.__onKeyDown(EKeyRightArrow) )
		self.canvas.bind( EKeyUpArrow,    lambda: self.__onKeyDown(EKeyUpArrow) )
		self.canvas.bind( EKeyLeftArrow,  lambda: self.__onKeyDown(EKeyLeftArrow) )
		self.canvas.bind( EKeyDownArrow,  lambda: self.__onKeyDown(EKeyDownArrow) )
	  
		print 'screen size', self.canvas.size
		viewWidth, viewHeight = self.canvas.size[0] / BLOCKSIZE, self.canvas.size[1] / BLOCKSIZE
		if viewWidth > amap.width: viewWidth = amap.width
		if viewHeight > amap.height: viewHeight = amap.height
	  
		self.table = amap
		self.player = self.table.snakes[player]

		viewX1 = self.player.head().x - viewWidth / 2
		if viewX1 < 0: viewX1 = 0
		viewY1 = self.player.head().y - viewWidth / 2
		if viewY1 < 0: viewY1 = 0
		viewX2 = viewX1 + viewWidth
		viewY2 = viewY1 + viewHeight

		self.table.placeFood( FRUIT )
		self.table.placeFood( CIGAR )
		self.view = Viewport( self.table, viewX1, viewX2, viewY1, viewY2 )
		self.distance = 0
		
		
		appuifw.app.body = self.canvas
		appuifw.app.screen = 'full'
	  

	def score(self, i):
		return len(self.table.snakes[i]) * 10

	def __repaint(self):		
		self.canvas.clear( (255,255,255) )
		self.view.paint(self.canvas)

		txt = u'%d' % (self.distance)
		textrect=self.canvas.measure_text( txt, font='title')[0]
		self.canvas.rectangle( (0, 0, textrect[2]-textrect[0], textrect[3]-textrect[1] ), fill=(0,0,0))
		self.canvas.text((-textrect[0], -textrect[1] ), txt, (0,192,0), "title" )		
		
		
	def __onKeyDown(self,key): self.player.direction = DIRECTIONS[key]

	def loop(self):
		self.synchronize()
		while True:
	
			self.player.step()

			if self.player.direction == DIRECTIONS[EKeyRightArrow]:
				self.distance = self.table.width - self.player.head().x -1
				if self.table.width != self.view.x2 and self.player.head().x >= (self.view.x1 + self.view.x2) / 2:
					self.view.scroll( self.player.direction.x, self.player.direction.y )

			elif self.player.direction == DIRECTIONS[EKeyDownArrow]:
				self.distance = self.table.height - self.player.head().y -1
				if self.table.height != self.view.y2 and self.player.head().y >= (self.view.y1 + self.view.y2) / 2:
					self.view.scroll( self.player.direction.x, self.player.direction.y )

			elif self.player.direction == DIRECTIONS[EKeyLeftArrow]:
				self.distance = self.player.head().x
				if 0 != self.view.x1 and self.player.head().x <= (self.view.x1 + self.view.x2) / 2:
					self.view.scroll( self.player.direction.x, self.player.direction.y )

			elif self.player.direction == DIRECTIONS[EKeyUpArrow]:
				self.distance = self.player.head().y
				if 0 != self.view.y1 and self.player.head().y <= (self.view.y1 + self.view.y2) / 2:
					self.view.scroll( self.player.direction.x, self.player.direction.y )
			if self.table.checkCollide():
				print 'collide'
				break
			self.synchronize()
			
	def synchronize(self):
		self.__repaint(self)
		(sender, direction) = self.btconn.exchange( self.player.direction )
		

			
class menu_base(object):
	def __init__(self, callbacks):
		# list here available options
		self.callbacks = callbacks + [self.mi_back] #!! DEFINE this func
		# function syntax: <bool:leave_this_menu?> <function(self)>
		# return: None:'stay in current submenu' | <anything else>:'exit to previous level'
		self.strings = [f.__doc__ for f in self.callbacks]
		self.listbox = appuifw.Listbox( self.strings, self.__apply )
		
	def show(self):
		appuifw.app.body = self.listbox
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
	def __init__(self):
		menu_base.__init__(self, callbacks=[self.mi_start_game, self.mi_options, self.mi_help])
		self.options = options_menu(self)
		self.bluetooth_connection = None
	
	def mi_start_game(self):
		u'Start Game'		
		self.bluetooth_connection = bluetooth_peer.get_connection()
		if self.bluetooth_connection.connect() == True:
			playing=1
			while playing:
				amap = MemMapFile( 'map1.map' ).load()
				game = SnakeGame( amap )
				game.loop()
				playing = appuifw.query(u'Play again?','query')
			self.bluetooth_connection.disconnect()
		else: #error
			pass
		
		appuifw.app.screen = 'normal'
		self.show()
		
	def mi_back(self):
		u'Exit'
		exit_handler()
		
	def mi_options(self):
		u'Options'
		self.options.show()
		
	def mi_help(self):
		u'Help'
		
class options_menu(sub_menu):
	def __init__(self, parent):
		sub_menu.__init__(self, parent, [self.mi_bluetooth, self.mi_game_speed])
		
	def mi_bluetooth(self):
		u'Bluetooth'
		
	def mi_game_speed(self):
		u'Game speed'		
		
event_lock = e32.Ao_lock()
appuifw.app.screen = 'normal'
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

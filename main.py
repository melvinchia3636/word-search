from base64 import b64decode
import requests
from tkinter import *
from tkinter.font import Font
import math
import numpy

class VerticalScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)            

        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = Frame(canvas, background='#FFFFFF')
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)
        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

class WordSearch(Tk):
	def __init__(self):
		super().__init__()
		self.title('Word Search')
		self.config(background='#FFFFFF')
		self.distance = lambda x1, y1, x2, y2: math.sqrt((x2-x1)**2+(y2-y1)**2)
		self.initBoard()

	def _getBoard(self):
		data = requests.get('https://word-search-puzzles.appspot.com/get_puzzle?clslang=en').json()

		k = data['width']
		m = data['height']
		l = data['cells']
		h = b64decode(data['words'].encode('ascii'))
		n = [data['cells'][i:i+k] for i in range(0, len(data['cells']), k)]
		word_list = []
		word_coords = []

		for i in range(0, len(h), 2):
			l = h[i]
			p = h[i+1]
			c = int(l%k) | 0
			g = int(l/k) | 0
			l = int(p%k) | 0
			p = int(p/k) | 0
			q = 0 if c == l else -1 if 0 > l - c else 1
			t = 0 if g == p  else -1 if 0 > p - g else 1
			word_coords.append([(g, c)])
			word = n[g][c]
			while c != l or g != p:
				c += q
				g += t
				word += n[g][c]
			word_list.append(word)
			word_coords[-1].append((g, c))
		word = list(zip(word_list, word_coords))
		return n, word, k, m

	def _checkClick(self, event):
		y, x = event.y//self.word_size, event.x//self.word_size
		if self.is_first_click:
			self.current_temp.append((self.on_click_y, self.on_click_x))
			self.is_first_click = False
			self.board_wrapper.unbind('<Motion>')
			for _, index, label in self.word_grid:
				if self.current_temp == index or list(reversed(self.current_temp)) == index:
					label.config(foreground='green')
					y1, x1, y2, x2 = [*self.current_temp[0], *self.current_temp[1]]
					self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), x2*self.word_size+(self.word_size/2), y2*self.word_size+(self.word_size/2), width=2)
			self.board_wrapper.delete(self.line)
			self.current_temp.clear()
		else:
			self.is_first_click = True
			self.current_temp.append((y, x))
			self.board_wrapper.bind('<Motion>', self._drawLine)

	def initBoard(self):
		self.is_first_click, self.current_temp = False, []
		self.word_size = 20
		self.board, self.word_list, self.WIDTH, self.HEIGHT = self._getBoard()
		self.board_container = Frame(self, background='#FFFFFF')
		self.board_wrapper = Canvas(self.board_container, height=self.word_size*self.HEIGHT-2, width=self.word_size*self.WIDTH-2, background='#FFFFFF', highlightthickness=0)
		self.current_distance = 0
		self.line = self.board_wrapper.create_line(0, 0, 0, 0)
		self.word_container = VerticalScrolledFrame(self, height=500, width=150, background='#FFFFFF')
		self.word_grid = self._generateWord()
		self._placeGrid()

	def _generateWord(self):
		return [i+tuple([Label(self.word_container.interior, text=i[0], background='#FFFFFF')]) for i in self.word_list]

	def _getTopRightDiagonal(self, x, y):
		cur_x, cur_y = x, y
		res = []
		while cur_x < self.WIDTH and cur_y >=0:
			res.append((cur_y, cur_x))
			cur_x+=1; cur_y-=1
		return res

	def _getBottomRightDiagonal(self, x, y):
		cur_x, cur_y = x, y
		res = []
		while cur_x < self.WIDTH and cur_y >=0:
			res.append((cur_y, cur_x))
			cur_x+=1; cur_y+=1
		return res

	def _drawLine(self, event):
		y1, x1 = self.current_temp[0]
		a = [x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2)]
		b = [x1*self.word_size+(self.word_size/2), 0]
		c = [event.x, event.y]
		a,b,c = self.distance(*a, *b), self.distance(*b, *c), self.distance(*c, *a)
		if self.distance(x1, y1, event.x//self.word_size, event.y//self.word_size).is_integer():
			self.current_distance = int(self.distance(x1, y1, event.x//self.word_size, event.y//self.word_size))
		try: self.degree = math.degrees(math.acos((a**2 + c**2 - b**2)/(2*a*c)))
		except: pass
		if -22.5<self.degree<22.5:
			self.board_wrapper.delete(self.line)
			self.on_click_x, self.on_click_y = x1, y1-self.current_distance
			self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), self.on_click_x*self.word_size+(self.word_size/2), self.on_click_y*self.word_size+(self.word_size/2))
		if 22.5<self.degree<67.5:
			cur_x, cur_y, is_over = event.x//self.word_size, event.y//self.word_size, False
			if (cur_y, cur_x) in self._getTopRightDiagonal(x1, y1):
				self.board_wrapper.delete(self.line)
				self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), cur_x*self.word_size+(self.word_size/2), cur_y*self.word_size+(self.word_size/2))
			elif self.current_distance:
				self.board_wrapper.delete(self.line)
				try: cur_y, cur_x = self._getTopRightDiagonal(x1, y1)[self.current_distance]
				except: cur_y, cur_x = self._getTopRightDiagonal(x1, y1)[-1]; is_over = True
				self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), cur_x*self.word_size+(self.word_size/2), cur_y*self.word_size+(self.word_size/2))
			self.on_click_x, self.on_click_y = cur_x, cur_y
			if not is_over: self.current_distance = self._getTopRightDiagonal(x1, y1).index((cur_y, cur_x))
		if 67.5<self.degree<112.5:
			self.board_wrapper.delete(self.line)
			self.on_click_x, self.on_click_y = x1+self.current_distance, y1
			self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), self.on_click_x*self.word_size+(self.word_size/2), self.on_click_y*self.word_size+(self.word_size/2))
		if 112.5<self.degree<157.5:
			cur_x, cur_y, is_over = event.x//self.word_size, event.y//self.word_size, False
			if (cur_y, cur_x) in self._getBottomRightDiagonal(x1, y1):
				self.board_wrapper.delete(self.line)
				self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), cur_x*self.word_size+(self.word_size/2), cur_y*self.word_size+(self.word_size/2))
			elif self.current_distance:
				self.board_wrapper.delete(self.line)
				try: cur_y, cur_x = self._getBottomRightDiagonal(x1, y1)[self.current_distance]
				except: cur_y, cur_x = self._getBottomRightDiagonal(x1, y1)[-1]; is_over = True
				self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), cur_x*self.word_size+(self.word_size/2), cur_y*self.word_size+(self.word_size/2))
			self.on_click_x, self.on_click_y = cur_x, cur_y
			if not is_over: self.current_distance = self._getBottomRightDiagonal(x1, y1).index((cur_y, cur_x))
		if 158.5<self.degree<202.5:
			self.board_wrapper.delete(self.line)
			self.on_click_x, self.on_click_y = x1, y1+self.current_distance
			self.line = self.board_wrapper.create_line(x1*self.word_size+(self.word_size/2), y1*self.word_size+(self.word_size/2), self.on_click_x*self.word_size+(self.word_size/2), self.on_click_y*self.word_size+(self.word_size/2))

	def _placeGrid(self):
		self.word_container.pack(side=LEFT, padx=20, pady=20, fill=Y)
		self.board_container.pack(side=RIGHT, padx=(0, 20), fill=Y)
		self.board_wrapper.pack(expand=True, pady=20)
		for i in range(len(self.word_grid)):
			self.word_grid[i][-1].pack()
		for i in range(self.HEIGHT):
			for j in range(self.WIDTH):
				self.board_wrapper.create_text(j*self.word_size+self.word_size/2, i*self.word_size+self.word_size/2, text=self.board[i][j], font=Font(size=15, family='Times New Roman'))
		self.board_wrapper.bind('<Button-1>', self._checkClick)

if __name__ == '__main__':
	root = WordSearch()
	root.mainloop()
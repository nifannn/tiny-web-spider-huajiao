import sys
import time

class ProgressBar(object):
	"""ProgressBar"""
	def __init__(self, total = 100, current = 0):
		self.total = total
		self.current = current
		self.percentage = self.current * 100 // self.total
		self.length = self.percentage // 2
		self.content = 'Progress:  [' + '#' * self.length + '.' * (50 - self.length) + ']  ' + str(self.percentage) + '%' +'\r'

	def show(self):
		sys.stdout.write(' ' * len(self.content) + '\r')
		sys.stdout.flush()
		sys.stdout.write(self.content)
		sys.stdout.flush()
		time.sleep(0.2)

	def present(self):
		print(self.content)

	def modify(self, newcurrent, newtotal):
		self.total = newtotal
		self.current = newcurrent
		self.percentage = self.current * 100 // self.total
		self.length = self.percentage // 2
		self.content = 'Progress:  [' + '#' * self.length + '.' * (50 - self.length) + ']  ' + str(self.percentage) + '%' + '\r'

	def update(self, newcurrent):
		self.current = newcurrent
		self.percentage = self.current * 100 // self.total
		self.length = self.percentage // 2
		self.content = 'Progress:  [' + '#' * self.length + '.' * (50 - self.length) + ']  ' + str(self.percentage) + '%' + '\r'
		self.show()

	def increase(self, increment = 1):
		self.current = self.current + increment
		self.percentage = self.current * 100 // self.total
		self.length = self.percentage // 2
		self.content = 'Progress:  [' + '#' * self.length + '.' * (50 - self.length) + ']  ' + str(self.percentage) + '%' + '\r'
		self.show()

	def restart(self):
		self.current = 0
		self.percentage = self.current * 100 // self.total
		self.length = self.percentage // 2
		self.content = 'Progress:  [' + '#' * self.length + '.' * (50 - self.length) + ']  ' + str(self.percentage) + '%' + '\r'


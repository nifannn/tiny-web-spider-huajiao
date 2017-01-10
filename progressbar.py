import sys
import time

class ProgressBar(object):
	"""ProgressBar"""
	def __init__(self, total = 100, current = 0):
		self.total = total
		self.current = current
		self.percentage = current * 100 // total
		self.length = percentage // 2
		self.content = 'Progress:  [' + '#' * self.length + '.' * (50 - self.length) + ']  ' + str(self.percentage) + '%'

	def show(self):
		sys.stdout.write(' ' * len(self.content))
		sys.stdout.flush()
		sys.stdout.write(self.content)
		sys.stdout.flush()
		time.sleep(1)

	def present(self):
		print(self.content)

	def modify(self, newcurrent = self.current, newtotal = self.total):
		pass

	def update():
		pass

	def increase():
		pass

	def restart():
		pass
		
import sys
import requests
from bs4 import BeautifulSoup
import re
import time

def getCategories():
	pass

def getPageNumbers(category):
	pass

def filterLiveIds(category, page):
	pass

def getUserId(liveId):
	pass

def getUserRecord(userId):
	pass

def updateUserRecord(userRecord):
	pass

def spiderUserRecord():
	for category in getCategories():
		for page in getPageNumbers(category):
			for livdId in filterLiveIds(category, page):
				userId = getUserId(liveId)
				userRecord = getUserRecord(userId)
				if userRecord:
					updateUserRecord(userRecord)

def spiderLiveRecord():
	pass

def getLiveInfo():
	pass

def getUserInfo():
	pass

def main(argv):
	usage = 'Usage: python spider.py [Usage|spiderUserRecord|spiderLiveRecord|getLiveInfo|getUserInfo]'
	if len(argv) < 2 or argv[1] == 'Usage':
		print(usage)
		exit()
	elif argv[1] == 'spiderLiveRecord':
		starttime = time.time()
		spiderLiveRecord()
		enttime = time.time()
		duration = time.strftime('%H:%M:%S', time.gmtime(endtime - starttime))
		print('This operation lasts ' + duration + '.')
		print(getLiveInfo())
	elif argv[1] == 'spiderUserRecord':
		starttime = time.time()
		spiderUserRecord()
		endtime = time.time()
		duration = time.strftime('%H:%M:%S', time.gmtime(endtime - starttime))
		print('This operation lasts ' + duration + '.')
		print(getUserInfo())
	elif argv[1] == 'getLiveInfo':
	    print(getLiveInfo())
	elif argv[1] == 'getUserInfo':
		print(getUserInfo())
	else:
	    print(usage)
	    exit()

if __name__ == '__main__':
	main(sys.argv)

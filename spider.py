import sys
import requests
from bs4 import BeautifulSoup
import re
import time

def getCategories():
	url = 'http://www.huajiao.com'
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	links = soup.find('ul',{'class':'hd-nav'}).find_all('a', href=re.compile('^(/category/)'))
	return [re.findall('[0-9]+',link['href'])[0] for link in links]

def getPageNumbers(category):
	url = 'http://www.huajiao.com/category/' + str(category)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	texts = soup.find('ul', {'class':'pagination'}).get_text('|',strip=True)
	return re.findall('[0-9]+',texts)

def filterLiveIds(category, page):
	url = 'http://www.huajiao.com/category/' + str(category)
	payload = {'pageno': page}
	html = requests.get(url, params=payload)
	soup = BeautifulSoup(html.text, 'html.parser')

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

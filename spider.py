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
	tags = soup.find_all('a', href=re.compile('^(/l/)'))
	return [re.findall('[0-9]+', tag['href'])[0] for tag in tags]

def getUserId(liveId):
	url = 'http://www.huajiao.com/l/' + str(liveId)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	link = soup.find('a', href=re.compile('^(/user/)'))['href']
	return re.findall('[0-9]+', link)[0]

def getUserRecord(userId):
	url = 'http://www.huajiao.com/user/' + str(userId)
	html = requests.get(url)
	soup = BeautifulSoup(html, 'html.parser')
	userRecord = dict()
	try:
		userInfoBlock = soup.find('div', id='userInfo')
		userRecord['avatar'] = userInfoBlock.find('div', class_='avatar').contents[0]['src']
		tmp = userInfoBlock.h3.get_text('|', strip=True).split('|')
		userRecord['username'] = ''.join(tmp[0:-1])
		userRecord['level'] = tmp[-1]
		tmp = userInfoBlock.find_all('p')
		userRecord['userid'] = re.findall('[0-9]+', tmp[0].string)[0]
		userRecord['about'] = tmp[1].string
		userRecord['follow'] = tmp[2].string
		userRecord['follower'] = tmp[3].string
		userRecord['like'] = tmp[4].string
		userRecord['experience'] = tmp[5].string
		return userRecord

	except:
		print('get User Record Error, user Id: ' + str(userId))
		return 0

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

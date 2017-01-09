import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import pymysql
import datetime

# get categories from index
def getCategories():
	url = 'http://www.huajiao.com'
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	links = soup.find('ul',{'class':'hd-nav'}).find_all('a', href=re.compile('^(/category/)'))
	return [re.findall('[0-9]+',link['href'])[0] for link in links]

# get page numbers from category
def getPageNumbers(category):
	url = 'http://www.huajiao.com/category/' + str(category)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	texts = soup.find('ul', {'class':'pagination'}).get_text('|',strip=True)
	return re.findall('[0-9]+',texts)

# get live ids with category and page number
def filterLiveIds(category, page):
	url = 'http://www.huajiao.com/category/' + str(category)
	payload = {'pageno': page}
	html = requests.get(url, params=payload)
	soup = BeautifulSoup(html.text, 'html.parser')
	tags = soup.find_all('a', href=re.compile('^(/l/)'))
	return [re.findall('[0-9]+', tag['href'])[0] for tag in tags]

# get user id from live id
def getUserId(liveId):
	url = 'http://www.huajiao.com/l/' + str(liveId)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	link = soup.find('a', href=re.compile('^(/user/)'))['href']
	try:
		return re.findall('[0-9]+', link)[0]
	except:
		print('live room disappeared, live id: ' + str(liveId))
		return 0

# get user data from user id
def getUserRecord(userId):
	url = 'http://www.huajiao.com/user/' + str(userId)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	userRecord = dict()
	try:
		userInfoBlock = soup.find('div', id='userInfo')
		userRecord['avatar'] = userInfoBlock.find('div', class_='avatar').contents[0]['src']
		tmp = userInfoBlock.h3.get_text('|', strip=True).split('|')
		userRecord['username'] = ''.join(tmp[0:-1])
		userRecord['level'] = tmp[-1]
		tmp = userInfoBlock.find_all('p')
		userRecord['userid'] = re.findall('[0-9]+', tmp[0].string)[0]
		if tmp[1].string:
			userRecord['about'] = tmp[1].string
		else:
			userRecord['about'] = ''
		userRecord['follow'] = tmp[2].string
		userRecord['follower'] = tmp[3].string
		userRecord['praise'] = tmp[4].string
		userRecord['experience'] = tmp[5].string
		return userRecord

	except:
		print('get User Record Error, user Id: ' + str(userId))
		return 0

# connect to mysql server
def MysqlConn():
	config = {'host':'127.0.0.1', 
	          'user':'root', 
	          'password':'passwd', 
	          'db':'ZhiBo',
	          'charset':'utf8mb4',
	          'cursorclass':pymysql.cursors.DictCursor}
	conn = pymysql.connect(**config)
	return conn

# get current local time
def getNowTime():
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

# update user data
def updateUserRecord(userRecord):
	conn = MysqlConn()
	try:
		with conn.cursor() as cursor:
			colname = '(UserId, UserName, Level, About, Follow, Follower, Praise, Experience, Avatar, UpdateTime)'
			sql = 'replace into Huajiao_User ' + colname + ' values (' + '%s,' * 9 + '%s)'
			value = (userRecord['userid'],userRecord['username'],userRecord['level'],
				     userRecord['about'],userRecord['follow'],userRecord['follower'],
				     userRecord['praise'],userRecord['experience'],userRecord['avatar'],
				     getNowTime())
			cursor.execute(sql, value)
		
		conn.commit()
	except:
		print('update user record error, user id: ' + str(userRecord['userid']))
	finally:
		conn.close()

# scrape user records frame
def spiderUserRecord():
	for category in getCategories():
		for page in getPageNumbers(category):
			for liveId in filterLiveIds(category, page):
				userId = getUserId(liveId)
				if userId:
					userRecord = getUserRecord(userId)
					if userRecord:
						updateUserRecord(userRecord)

			time.sleep(2)
		time.sleep(10)

# get user ids from mysql
def getUserIdfromDB():
	conn = MysqlConn()
	with conn.cursor() as cursor:
		sql = 'select UserId from Huajiao_User'
		cursor.execute(sql)
		results = cursor.fetchall()

	conn.close()
	return [result['UserId'] for result in results]

# get live data from user id
def getLiveRecords(userId):
	url = 'http://webh.huajiao.com/User/getUserFeeds'
	payload = {'uid': userId}
	html = requests.get(url, params=payload)
	try:
		if html.json()['data']:
			return html.json()['data']['feeds']
		else:
			return 0
	except:
		print('get json data error, user id: ' + str(userId))
		return 0

# update live data
def updateLiveRecord(record):
	colname = '(LiveId, UserId, UserName, PublishTime, Duration, Location, Title, Watches, Praises, UpdateTime)'
	sql = 'replace into Huajiao_Live ' + colname + ' values (' + '%s, ' * 9 + '%s) '
	value = (record['feed']['relateid'], record['author']['uid'], record['author']['nickname'],
		     record['feed']['publishtime'], record['feed']['duration'] if 'duration' in record['feed'].keys() else 0, 
		     record['feed']['location'], record['feed']['title'], record['feed']['watches'], 
		     record['feed']['praises'], getNowTime())

	conn = MysqlConn()
	try:
		with conn.cursor() as cursor:
			cursor.execute(sql, value)

		conn.commit()
	except:
		print('update live record error, user id: ' + str(record['author']['uid']) + ' live id: ' + str(record['feed']['relateid']))
	finally:
		conn.close()

# scrape live records frame
def spiderLiveRecord():
	for userId in getUserIdfromDB():
		liverecords = getLiveRecords(userId)
		if liverecords:
			for liverecord in liverecords[::-1]:
				updateLiveRecord(liverecord)

		time.sleep(0.1)

# get live table info from mysql
def getLiveTblInfo():
	conn = MysqlConn()
	with conn.cursor() as cursor:
		sql = 'select count(LiveId), max(UpdateTime) from Huajiao_Live'
		cursor.execute(sql)
		result = cursor.fetchone()

	conn.close()
	count = result['count(LiveId)']
	latestupdatetime = result['max(UpdateTime)'].strftime('%Y-%m-%d %H:%M:%S')
	tblinfo = 'Number of Live Records: ' + str(count) + ' \n' + 'Latest Update Time: ' + latestupdatetime
	return tblinfo

# get user table info from mysql
def getUserTblInfo():
	conn = MysqlConn()
	with conn.cursor() as cursor:
		sql = 'select count(UserId), max(UpdateTime) from Huajiao_User'
		cursor.execute(sql)
		result = cursor.fetchone()

	conn.close()
	count = result['count(UserId)']
	latestupdatetime = result['max(UpdateTime)'].strftime('%Y-%m-%d %H:%M:%S')
	tblinfo = 'Number of User Records: ' + str(count) + ' \n' + 'Latest Update Time: ' + latestupdatetime
	return tblinfo

def main(argv):
	usage = 'Usage: python spider.py [Usage|spiderUserRecord|spiderLiveRecord|getLiveTblInfo|getUserTblInfo]'
	if len(argv) < 2 or argv[1] == 'Usage':
		print(usage)
		exit()
	elif argv[1] == 'spiderLiveRecord':
		starttime = time.time()
		spiderLiveRecord()
		endtime = time.time()
		duration = time.strftime('%H:%M:%S', time.gmtime(endtime - starttime))
		print('Run time: ' + duration)
		print(getLiveTblInfo())
	elif argv[1] == 'spiderUserRecord':
		starttime = time.time()
		spiderUserRecord()
		endtime = time.time()
		duration = time.strftime('%H:%M:%S', time.gmtime(endtime - starttime))
		print('Run time: ' + duration)
		print(getUserTblInfo())
	elif argv[1] == 'getLiveTblInfo':
	    print(getLiveTblInfo())
	elif argv[1] == 'getUserTblInfo':
		print(getUserTblInfo())
	else:
	    print(usage)
	    exit()

if __name__ == '__main__':
	main(sys.argv)

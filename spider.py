import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import pymysql
import datetime
import getpass
import progressbar

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
def getUserId(liveId, logs):
	url = 'http://www.huajiao.com/l/' + str(liveId)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	link = soup.find('a', href=re.compile('^(/user/)'))['href']
	try:
		return re.findall('[0-9]+', link)[0]
	except:
		logs.append(getNowTime() + ' live room disappeared, live id: ' + str(liveId))
		return 0

# get user data from user id
def getUserRecord(userId, logs):
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
		logs.append(getNowTime() + ' get User Record Error, user Id: ' + str(userId))
		return 0

# input login info
def getMysqlPass():
	status = {'times':0, 'conn':0}
	while status['conn'] != 1 and status['times'] <= 5:
		logininfo = {'host':'', 'user': '', 'db':''}
		for key in ['host', 'db', 'user']:
			logininfo[key] = input('Mysql ' + key + ': ')
		logininfo['password'] = getpass.getpass('Mysql password: ')
		try:
			MysqlConn(logininfo)
			status['conn'] = 1
		except:
			status['conn'] = 0
			print('connection failure')
		status['times'] = status['times'] + 1

	if status['conn'] == 1:
		print('connection success')
		return logininfo
	else:
		print('too many failures, bye')
		exit()

# connect to mysql server
def MysqlConn(logininfo):
	config = {'charset':'utf8mb4',
	          'cursorclass':pymysql.cursors.DictCursor}
	config.update(logininfo)
	conn = pymysql.connect(**config)
	return conn

# get current local time
def getNowTime():
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

# update user data
def updateUserRecord(userRecord, logininfo, logs):
	conn = MysqlConn(logininfo)
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
		logs.append(getNowTime() + ' update user record error, user id: ' + str(userRecord['userid']))
	finally:
		conn.close()

# scrape user records frame
def spiderUserRecord():
	logininfo = getMysqlPass()
	categories = getCategories()
	bar = progressbar.ProgressBar(total = len(categories))
	bar.show()
	logs = []
	
	for cnt, category in enumerate(categories):
		pages = getPageNumbers(category)
		for page in pages:
			for liveId in filterLiveIds(category, page):
				userId = getUserId(liveId, logs)
				if userId:
					userRecord = getUserRecord(userId, logs)
					if userRecord:
						updateUserRecord(userRecord, logininfo, logs)

			bar.increase(1 / len(pages))
			time.sleep(0.2)	
		bar.update(cnt + 1)
		time.sleep(1)
	bar.present()

	for log in logs:
		print(log)
	return logininfo

# get user ids from mysql
def getUserIdfromDB(logininfo):
	conn = MysqlConn(logininfo)
	with conn.cursor() as cursor:
		sql = 'select UserId from Huajiao_User'
		cursor.execute(sql)
		results = cursor.fetchall()

	conn.close()
	return [result['UserId'] for result in results]

# get live data from user id
def getLiveRecords(userId, logs):
	url = 'http://webh.huajiao.com/User/getUserFeeds'
	payload = {'uid': userId}
	html = requests.get(url, params=payload)
	try:
		if html.json()['data']:
			return html.json()['data']['feeds']
		else:
			return 0
	except:
		logs.append(getNowTime() + ' get json data error, user id: ' + str(userId))
		return 0

# update live data
def updateLiveRecord(record, logininfo, logs):
	colname = '(LiveId, UserId, UserName, PublishTime, Duration, Location, Title, Watches, Praises, UpdateTime)'
	sql = 'replace into Huajiao_Live ' + colname + ' values (' + '%s, ' * 9 + '%s) '
	value = (record['feed']['relateid'], record['author']['uid'], record['author']['nickname'],
		     record['feed']['publishtime'], record['feed']['duration'] if 'duration' in record['feed'].keys() else 0, 
		     record['feed']['location'], record['feed']['title'], record['feed']['watches'], 
		     record['feed']['praises'], getNowTime())

	conn = MysqlConn(logininfo)
	try:
		with conn.cursor() as cursor:
			cursor.execute(sql, value)

		conn.commit()
	except:
		logs.append(getNowTime() + ' update live record error, user id: ' + str(record['author']['uid']) + ' live id: ' + str(record['feed']['relateid']))
	finally:
		conn.close()

# scrape live records frame
def spiderLiveRecord():
	logininfo = getMysqlPass()
	userIds = getUserIdfromDB(logininfo)
	bar = progressbar.ProgressBar(total = len(userIds))
	bar.show()
	logs = []

	for userId in userIds:
		liverecords = getLiveRecords(userId, logs)
		if liverecords:
			for liverecord in liverecords[::-1]:
				updateLiveRecord(liverecord, logininfo, logs)

		bar.increase()
		time.sleep(0.1)
	bar.present()

	for log in logs:
		print(log)
	return logininfo

# get live table info from mysql
def getLiveTblInfo(logininfo):
	conn = MysqlConn(logininfo)
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
def getUserTblInfo(logininfo):
	conn = MysqlConn(logininfo)
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
		logininfo = spiderLiveRecord()
		endtime = time.time()
		duration = time.strftime('%H:%M:%S', time.gmtime(endtime - starttime))
		print('Run time: ' + duration)
		print(getLiveTblInfo(logininfo))
	elif argv[1] == 'spiderUserRecord':
		starttime = time.time()
		logininfo = spiderUserRecord()
		endtime = time.time()
		duration = time.strftime('%H:%M:%S', time.gmtime(endtime - starttime))
		print('Run time: ' + duration)
		print(getUserTblInfo(logininfo))
	elif argv[1] == 'getLiveTblInfo':
	    print(getLiveTblInfo(getMysqlPass()))
	elif argv[1] == 'getUserTblInfo':
		print(getUserTblInfo(getMysqlPass()))
	else:
	    print(usage)
	    exit()

if __name__ == '__main__':
	main(sys.argv)

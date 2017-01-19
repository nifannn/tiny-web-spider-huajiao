import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import pymysql
import datetime
import getpass
import progressbar

# logs
class Logs(object):
	"""docstring for logs"""
	def __init__(self, commandName):
		self.content = dict()
		self.content['Command'] = commandName

	def start(self):
		self.starttimestamp = time.time()
		self.content['StartTime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.starttimestamp))
		self.content['Record'] = []

	def end(self, logininfo):
		self.endtimestamp = time.time()
		self.content['EndTime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.endtimestamp))
		if self.starttimestamp:
			self.content['Duration'] = time.strftime("%H:%M:%S", time.gmtime(self.endtimestamp-self.starttimestamp)) 
		else:
			self.content['Duration'] = 0
		self.content['UserTblInfo'] = getUserTblInfo(logininfo)
		self.content['LiveTblInfo'] = getLiveTblInfo(logininfo)
		
	def present(self):
		for key in ['Command', 'StartTime', 'EndTime', 'Duration', 'UserTblInfo', 'LiveTblInfo']:
			print(key)
			print(self.content[key])
		print('Record: ')
		for rcd in self.content['Record']:
			print(rcd)
	
	def output(self, filepath):
		with open(filepath, 'a') as f:
			for key in ['Command', 'StartTime', 'EndTime', 'Duration', 'UserTblInfo', 'LiveTblInfo']:
				f.write(key + ': \n')
				f.write(self.content[key] + '\n')
			f.write('Record: \n')
			for rcd in self.content['Record']:
				f.write(rcd + '\n')
			f.write('\n')

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
	try:
		texts = soup.find('ul', {'class':'pagination'}).get_text('|',strip=True)
		return re.findall('[0-9]+',texts)
	except:
		return [1]

# get live ids with category and page number
def filterLiveIds(category, page, logs):
	url = 'http://www.huajiao.com/category/' + str(category)
	payload = {'pageno': page}
	html = requests.get(url, params=payload)
	soup = BeautifulSoup(html.text, 'html.parser')
	tags = soup.find_all('a', href=re.compile('^(/l/)'))
	if tags:
		return [re.findall('[0-9]+', tag['href'])[0] for tag in tags]
	else:
		logs.append('No live room currently, category: ' + str(category) + ', page: ' + str(page))
		return [0]

# get user id from live id
def getUserId(liveId, logs):
	url = 'http://www.huajiao.com/l/' + str(liveId)
	html = requests.get(url)
	soup = BeautifulSoup(html.text, 'html.parser')
	try:
		link = soup.find('a', href=re.compile('^(/user/)'))['href']
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
def spiderUserRecord(logininfo, logs):
	categories = getCategories()
	bar = progressbar.ProgressBar(total = len(categories))
	bar.show()
	
	for cnt, category in enumerate(categories):
		pages = getPageNumbers(category)
		for page in pages:
			for liveId in filterLiveIds(category, page, logs):
				userId = getUserId(liveId, logs)
				if userId:
					userRecord = getUserRecord(userId, logs)
					if userRecord:
						updateUserRecord(userRecord, logininfo, logs)

			bar.increase(1 / len(pages))
			time.sleep(0.2)	
		bar.update(cnt + 1)
		time.sleep(0.4)
	bar.present()

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
def spiderLiveRecord(logininfo, logs):
	userIds = getUserIdfromDB(logininfo)
	bar = progressbar.ProgressBar(total = len(userIds))
	bar.show()

	for userId in userIds:
		liverecords = getLiveRecords(userId, logs)
		if liverecords:
			for liverecord in liverecords[::-1]:
				updateLiveRecord(liverecord, logininfo, logs)

		bar.increase()
		time.sleep(2)
	bar.present()


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
	filename = '~/Documents/githubdoc/tiny-web-spider-huajiao/log.text'
	if len(argv) < 2 or argv[1] == 'Usage':
		print(usage)
		exit()
	elif argv[1] == 'spiderLiveRecord':
		logininfo = getMysqlPass()
		spiderlog = Logs(argv[1])
		spiderlog.start()
		spiderLiveRecord(logininfo, spiderlog.content['Record'])
		spiderlog.end(logininfo)
		spiderlog.present()
		spiderlog.output(filename)
	elif argv[1] == 'spiderUserRecord':
		logininfo = getMysqlPass()
		spiderlog = Logs(argv[1])
		spiderlog.start()
		spiderUserRecord(logininfo, spiderlog.content['Record'])
		spiderlog.end(logininfo)
		spiderlog.present()
		spiderlog.output(filename)
	elif argv[1] == 'getLiveTblInfo':
		logininfo = getMysqlPass()
		spiderlog = Logs(argv[1])
		spiderlog.start()
		print(getLiveTblInfo(logininfo))
		spiderlog.end(logininfo)
		spiderlog.output(filename)
	elif argv[1] == 'getUserTblInfo':
		logininfo = getMysqlPass()
		spiderlog = Logs(argv[1])
		spiderlog.start()
		print(getUserTblInfo(logininfo))
		spiderlog.end(logininfo)
		spiderlog.output(filename)
	else:
	    print(usage)
	    exit()

if __name__ == '__main__':
	main(sys.argv)

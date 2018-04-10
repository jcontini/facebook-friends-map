import os, datetime, time, csv
from selenium import webdriver
from datetime import datetime
from sys import argv
os.system('clear')

os.environ["DEBUSSY"] = "1"

browser = webdriver.Firefox()

# --------------- Ask user to log in -----------------
def fb_login():
	print "Opening browser..."
	browser.get("https://www.facebook.com/")
	a = raw_input("Please log into facebook and press enter after the page loads...")

# --------------- Scroll to bottom of page -----------------
def scroll_to_bottom():
	print "Scrolling to bottom..."
	while True:
			try:
				browser.find_element_by_class_name('_4khu') # class after friend's list
				print "Reached end!"
				break
			except:
				browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
				time.sleep(0.25)
				pass

# --------------- Get list of all friends on page ---------------
def scan_friends():
	print 'Scanning page for friends...'
	friends = []
	friend_cards = browser.find_elements_by_xpath('//div[@id="pagelet_timeline_medley_friends"]//div[@class="fsl fwb fcb"]/a')

	for friend in friend_cards:
		if friend.get_attribute('data-hovercard') is None:
			print " %s (INACTIVE)" % friend.text
			friend_id = friend.get_attribute('ajaxify').split('id=')[1]
			friend_active = 0
		else:
			print " %s" % friend.text
			friend_id = friend.get_attribute('data-hovercard').split('id=')[1].split('&')[0]
			friend_active = 1

		friends.append({
			'name': friend.text.encode('ascii', 'ignore').decode('ascii'), #to prevent CSV writing issues
			'id': friend_id,
			'active': friend_active
			})

	print 'Found %r friends on page!' % len(friends)
	return friends

# ----------------- Load list from CSV -----------------
def load_csv(filename):
	inact = 0
	myfriends = []
	with open(filename, 'rb') as input_csv:
		reader = csv.DictReader(input_csv)
		for idx,row in enumerate(reader):
			if row['active'] is '1':
				myfriends.append({
					"name":row['B_name'],
					"uid":row['B_id']
					})
			else:
				print "Skipping %s (inactive)" % row['B_name']
				inact = inact + 1
	print "%d friends in imported list" % (idx+1)
	print "%d ready for scanning (%d inactive)" % (idx-inact+1, inact)

	return myfriends

# --------------- Scrape 1st degree connections ---------------
def scrape_1st_degrees():
	#Prep CSV Output File
	csvOut = '1st-degree_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
	writer = csv.writer(open(csvOut, 'wb'))
	writer.writerow(['A_id','A_name','B_id','B_name','active'])

	#Get your unique Facebook ID
	profile_icon = browser.find_element_by_css_selector("[data-click='profile_icon'] > a > span > img")
	myid = profile_icon.get_attribute("id")[19:]

	#Scan your Friends page (1st-degree connections)
	print "Opening Friends page..."
	browser.get("https://www.facebook.com/" + myid + "/friends")
	scroll_to_bottom()
	myfriends = scan_friends()

	#Write connections to CSV File
	for friend in myfriends:
			writer.writerow([myid,"Me",friend['id'],friend['name'],friend['active']])

	print "Successfully saved to %s" % csvOut

# --------------- Scrape 2nd degree connections. ---------------
#This can take several days if you have a lot of friends!!
def scrape_2nd_degrees():
	#Prep CSV Output File
	csvOut = '2nd-degree_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
	writer = csv.writer(open(csvOut, 'wb'))
	writer.writerow(['A_id', 'B_id', 'A_name','B_name','active'])

	#Load friends from CSV Input File
	script, filename = argv
	print "Loading list from %s..." % filename
	myfriends = load_csv(filename)

	for idx,friend in enumerate(myfriends):
		#Load URL of friend's friend page
		scrape_url = "https://www.facebook.com/"+ friend['uid'] + "/friends?source_ref=pb_friends_tl"
		browser.get(scrape_url)

		#Scan your friends' Friends page (2nd-degree connections)
		print "%d) %s" % (idx+1, scrape_url)
		scroll_to_bottom()
		their_friends = scan_friends()

		#Write connections to CSV File
		print 'Writing connections to CSV...'
		for person in their_friends:
			writer.writerow([friend['uid'],person['id'],friend['name'],person['name'],person['active']])

# --------------- Start Scraping ---------------
now = datetime.now()

fb_login()

if len(argv) is 1:
	scrape_1st_degrees()

elif len(argv) is 2:
	scrape_2nd_degrees()
	
else:
	print "Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the CSV file as the first argument."


#!/usr/bin/env python
import os, bs4, glob, csv
from dateutil.parser import parse
from datetime import datetime

files = glob.glob("Keep/*.html")
notes = []

#Prep CSV file
now = datetime.now()
csvout = "notes_%s.csv" % now.strftime("%Y-%m-%d_%H%M")
writer = csv.writer(open(csvout, 'wb'))
writer.writerow(['date', 'title', 'content', 'file'])

for file in files:
	page = open(file)
	soup = bs4.BeautifulSoup(page.read(), "html.parser")

	#Make Excel-Friendly date
	googDate = soup.select('.heading')[0].getText().strip()
	xlDate = datetime.strftime(parse(googDate), '%m/%d/%Y %H:%M')

	#Convert <br>'s to line breaks.
	for br in soup.select('.content')[0].find_all("br"):
		br.replace_with("\n")

	try:
		note = {
			"date": xlDate,
			"title": soup.select('.title')[0].getText(),
			"content": soup.select('.content')[0].getText()
		}

		print "\n" + ('-'*15) + file + ('-'*15)
		print 'Title: \"' + note['title'] + "\" // Date: " + note['date']
		print ('-'*15) + '-'*int(len(file)) + ('-'*15)
		print note['content']

		writer.writerow([note['date'],note['title'],note['content'], file])

	#In case a note has a blank title or content, continue anyway
	except Exception as e:
	        print "Note %s has blank title or content: %s." % (file, e)
		pass

print ('\n'+('-'*20)+'\nDone! %s notes saved to CSV.\n'+('-'*20)) % len(files)

#Github: https://github.com/jcontini

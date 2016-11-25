# Scrapers
Scrapers to free our data from web services. All currently require Python 2.7.

## Google Keep
Apparently there's no simple way to export your notes from Google Keep to a CSV or spreadsheet. This does that from a Google Takeout archive. Instructions:

1. Go to [Google Takeout](https://takeout.google.com/settings/takeout)
2. Make sure the 'Keep' checkbox is selected (you can deselect all others)
3. Download and export the archive to a folder that has the 'Keep' folder
4. Run ``python keep-scrape.py``. That should export your notes to a CSV.

**Requires**:
- [Beautiful Soup 4](https://pypi.python.org/pypi/beautifulsoup4)
- [DateUtils](https://pypi.python.org/pypi/dateutils)
- [UnicodeCSV](https://pypi.python.org/pypi/unicodecsv)

You can install these requirements with `pip install -r requirements.txt`.

## Facebook
Getting your list of friends is no longer possible via the Facebook Graph API, so you can use this. It has 2 modes: 1) Download a list of your connections, and 2) Download a list of your 2nd-degree connections for social network analysis. Both modes save data to a CSV in a format friendly for importing into graph databases.

### 1st degree connections (your friends)
1. Run ```python facebook-connections.py```
2. It will open a browser window. Fill out your username & password and log in.
3. Press Enter in the terminal after logging in.
4. You should see your Facebook friends page scroll to the bottom.
5. A CSV file will be created with the data (1st-degree_YYYY-MM-DD_HHMM.csv)

### 2st degree connections (your friends' friends)
Note: This could take days if you have lots of friends!

1. Get your 1st degree connections first, so you have the 1st-degree CSV file.
2. Put the 1st-degree CSV in the same folder as **python facebook-connections.py**
3. Run ```python facebook-connections.py 1st-degree_YYYY-MM-DD_HHMM.csv```, with the actual filename from the first step.
4. A browser window will open. Fill out your username & password and log in.
5. Press Enter in the terminal after logging in.
6. You should the script looping through your Facebook friends' friend pages.
7. A CSV file will be created with the data (2nd-degree_YYYY-MM-DD_HHMM.csv)

**Note**: This currently gets tripped up by the following situations, because the scroll_to_bottom() function doesn't accurately detect when it's at the bottom of the friends list. Please feel free to improve with a pull request!
- Friends that have their privacy settings to show no friends
- Friends with just followers public
- Rarely, some other situations

**Requires**:
- [Selenium](https://pypi.python.org/pypi/selenium)
- [Firefox](https://www.mozilla.org/en-US/firefox/new/) (or change the webdriver at top of the source code to something different)

# scrapers
Scrapers I put together with lots of help from Stack Overflow.

## keep-scrape.py
Apparently there's no simple way to export your notes from Google Keep to a CSV or spreadsheet. This does that from a Google Takeout archive. Instructions:

1. Go to [Google Takeout](https://takeout.google.com/settings/takeout)
2. Make sure the 'Keep' checkbox is selected (you can deselect all others)
3. Download and export the archive to a folder that has the 'Keep' folder
4. Place **keep-scrape.py** in the same folder that has the 'Keep' folder
5. Run ``python keep-scrape.py``. That should export your notes to a CSV.
# Facebook Scraper
This repository has tools that let you:
1. Download all photos you are tagged with proper dates
2. Download a CSV of your 1st & 2nd degree connections

## Installation
1. Clone this repository
2. `cd` into the cloned folder 
3. `pip install -r requirements.txt`

## Download tagged photos
To download your tagged photos, run this (with your FB username & password)

`python get-tagged-photos.py -u your@email.com -p yourpassword`

You should see Chrome open, login to Facebook, navigate to your photos page, and start flying through your tagged photos & videos. On the first pass it only creates an index for downloading later. This is saved as `tagged.json`.

Once the index is made, the script will loop through the index and start downloading every photo (skipping videos) and then update the EXIF 'Date Created' after it downloads each image. These will be saved to the /photos/ folder. You can then upload these images to a platform like Google Photos, and it should detect the dates properly. The dates are pulled from the date they were uploaded to Facebook.

If you already have the index and just need to download the images again, you can run the script in download-only mode like this:

`python get-tagged-photos.py --download`

## Get CSV of connections & IDs
Getting your list of friends is no longer possible via the Facebook Graph API, so you can use this. It has 2 modes:
1) Download a list of your connections, and 
2) Download a list of your 2nd-degree connections for social network analysis. Both modes save data to a CSV in a format friendly for importing into graph databases.

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
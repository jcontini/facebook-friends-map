# Facebook Friend Mapper

![Map Example](https://raw.githubusercontent.com/jcontini/facebook-scraper/master/example.jpg)

Create a map of your facebook friends! Useful for when you're passing through a city and can't remember all the people you want to grab coffee with.

## First: A Warning
When using this tool, Facebook can see that you're using an automated tool, which violates their terms. There is a risk that Facebook may decide to put a temporary or permanent ban on your account (though I haven't heard of this happening to anyone yet). I am not responsible for this or any other outcomes that may occur as a result of the use of this software.
 
## Pre-requisites
- Install the latest version of [Google Chrome Beta](https://www.google.com/chrome/beta/). This is because the script uses the latest version of the `chromedriver-binary`, which has to match the latest version of chrome.
- Make sure that `python 3` and `pipenv` are installed.

## Installation

1. Clone this repository
2. `cd` into the cloned folder 
3. Run `pipenv install` to install dependencies
4. On first run, the script will ask ask for Facebook username/password and Mapbox API Key. It saves these to the local `.env` file for use in subsequent runs (eg if you add more friends).

## Extract profile data & create the map
1. Run `pipenv shell` to activate the virtual environment. This is optional if you already have the required packages installed in your environment.
2. Run `python make.py` to run the full process of indexing, downloading, parsing, geocoding, and mapping your friends. You can optionally use any of these flags to perform only certain actions:

- `-- index` Sign in, create friends list index only
- `-- download` Download profile for each friend in index
- `-- parse` Extract profiles HTML into profiles.json
- `-- map` Geocode addresses & make the map!

## How it works
This tool will only extract the data that your friends have already explicitly made it available to you. If the amount or content of the data freaks you (like it did to me!), then it's a good reminder for us all to check our profiles/privacy settings to make sure that we only share what we want others to be able to see.

It works like this:
1. Open your friends list page (on m.facebook.com) and save to `db/friend_list.html`
2. Download your friend's profiles (on mbasic.facebook.com) to `db/profiles/`
3. Parse profiles for 'Current City' or 'Address' and add to location list.
4. Find the lat/long for each location (using Mapbox API) and save to  `db/points.geojson`.
5. Creates `friends-map.html`, a self-contained, moveable, searchable map of your friends all over the world!
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
4. Open the `.env` file for pipenv set your variables (fb_user, fb_pass, mapbox_token)

## Extract profile data & create the map
1. Run `pipenv shell` to activate the virtual environment. This is optional if you already have the required packages installed in your environment.
2. Run `python make.py` to run the full process of indexing, downloading, parsing, geocoding, and mapping your friends. You can optionally use any of these flags to perform only certain actions:

- `-- index` Sign in, create friends list index only
- `-- download` Download profile for each friend in index
- `-- parse` Extract profiles HTML into profiles.json
- `--geocode` Geocode addresses to coordinates
- `--map` Make the map!

## How it works
This tool will only extract the data that your friends have already explicitly made it available to you. If the amount or content of the data freaks you (like it did to me!), then it's a good reminder for us all to check our profiles/privacy settings to make sure that we only share what we want others to be able to see.

It works like this:
1. Open your friends list page (on m.facebook.com), save it (index.html) create a list of all of your friends as `index.json`
2. Download each of your friends profiles (on mbasic.facebook.com) and parse/organize all data as `profiles.json`
3. Look for the 'Current City' and 'Address' fields on each profile and save them to `friend_locations.json`.
4. Geocode each unique location and add Latitude/Longitude to `points.geojson`. It uses the Mapbox Geocoding API to do this, so you need a Mapbox API key. Be sure to either use pipenv environments with a `.env` file, or open `make.py` to manually put in your Mapbox API key.
5. Creates `friends-map.html`, using `template-map.html` as the base and your Mapbox API key to render the map. The result is a moveable, searchable map of your friends all over the world! All the data is included in the html file, so you can open it on your computer without a server.
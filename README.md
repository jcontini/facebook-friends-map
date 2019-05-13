# Facebook Friend Profile Scraper
## First: A Warning
Use of this tool likely violates Facebook's terms & conditions. When using it, Facebook will knows who you are (because you have to log in), and can pretty easily see that you're using a tool like this in an unsanctioned way. Therefore by using this software, you put your own Facebook profile at risk, as Facebook may decide to ban you from the platform altogether. I cannot be held responsible for this or any other outcomes that may occur as a result of the use of this software.

I personally built this to help centralize information about my contacts. Specifically, I wanted to make a map of all of my contacts (including Facebook friends), so that I could more easily see where they are living on the globe, and get in touch with them when I'm passing through.

## What it does
This tool should not be of much relevance to marketers, as it does not pull any activity related to posts, comments, or likes. Instead, it extracts only this profile data that your friends have already made accessible to you - if it is visible on their Facebook "About me" page:

- Photo URL
- Tagline
- About Me (Bio)
- Relationship
- Quotes
- Details
  - Birthday
  - Gender
  - Current City
  - Hometown
  - Languages
  - Websites
  - Social Media profiles
  - Interested in gender(s)
  - Religious Views
  - Political Views
  - (+ More)
- Work History
- Education History
- Family Members
- Life Events

Remember - this tool will only extract the above data if your friend has already explicitly made it available to you. If the amount or content of the data freaks you (like it did to me!), then it's a good reminder for us all to check our profiles/privacy settings to make sure that we only share what we want others to be able to see.

## Installation
You'll need to have python, pip, and [Google Chrome](https://www.google.com/chrome/) installed to use this tool. Once that's all set up:

1. Clone this repository
2. `cd` into the cloned folder 
3. Run `pipenv install` to install dependencies

I personally used Jupyter Notebook to run the script (you'll see the notebook file in the repo), but it's not required at all.

## Extract profile data
Run `pipenv shell` to activate the virtual environment. This is optional if you already have the required packages installed in your environment.

Then, simply run `python extract.py` to run the full process of indexing, downloading, and parsing your friend's profile data. You can optionally use any of these flags to perform only certain actions:

- `-- index` Sign in, create friends list index only
- `-- download` Download profile for each friend in index
- `-- parse` Extract profiles HTML into profiles.json

### facebook-connections.py
This was the original script that I built this repo for. It only created an index of 1st and 2nd degree connections, which is useful for creating a visual social graph. I haven't touched this code in years and am guessing that it doesn't work anymore, so am planning to delete it altogether in a later push. Leaving it here awhile longer in case anyone still uses it.
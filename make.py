#!/usr/bin/env python
# coding: utf-8

import argparse, json, sqlite3, os, glob, time, sys, requests, random, glob, webbrowser, utils
from lxml import html
from selenium import webdriver
from selenium.common import exceptions
from datetime import datetime
from geojson import Feature, FeatureCollection, Point
from sys import stdout
os.system('cls' if os.name == 'nt' else 'clear')

#Set up environment
if os.path.exists('.env'):
    fb_user = os.getenv('fb_user')
    fb_pass = os.getenv('fb_pass')
    mapbox_token = os.getenv('mapbox_token')
else:
    print("Welcome! Let's set up your environment. This will create a .env file in the same folder as this script, and set it up with your email, password, and Mapbox API Key. This is saved only on your device and only used to autofill the Facebook login form.\n")

    fb_user = input("Facebook Email Address: ")
    fb_pass = input("Facebook Password: ")
    print("\nTo plot your friends on a map, you need a (free) Mapbox API Key. If you don't already have one, follow instructions at https://docs.mapbox.com/help/glossary/access-token, then come back here to enter the access token\n")
    mapbox_token = input("Mapbox access token: ")

    f = open(".env","w+")
    f.write('fb_user="' + fb_user + '"\n')
    f.write('fb_pass="' + fb_pass + '"\n')
    f.write('mapbox_token="' + mapbox_token + '"\n')
    f.close()

    print("\nGreat! Details saved in .env, so you shouldn't need to do this again.\n")

# Prepare database
friends_html = 'db/friend_list.html'
profiles_dir = 'db/profiles/'
db_geojson = "db/points.geojson"

db_index = 'friend_list'
db_profiles = 'profiles'
db_locations = 'locations'

if not os.path.exists(profiles_dir):
    os.makedirs(profiles_dir)

# Configure browser
def start_browser():
    # Ensure mobile-friendly view for parsing
    useragent = "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36"

    #Firefox
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", useragent)
    options = webdriver.FirefoxOptions()
    options.set_preference("dom.webnotifications.serviceworker.enabled", False)
    options.set_preference("dom.webnotifications.enabled", False)
    #options.add_argument('--headless')

    browser = webdriver.Firefox(firefox_profile=profile,options=options)
    return browser

# Login
def sign_in():
    fb_start_page = 'https://m.facebook.com/'
    print("Logging in %s automatically..." % fb_user)
    browser.get(fb_start_page)
    email_id = browser.find_element_by_id("m_login_email")
    pass_id = browser.find_element_by_id("m_login_password")
    confirm_id = browser.find_element_by_name("login")
    email_id.send_keys(fb_user)
    pass_id.send_keys(fb_pass)
    confirm_id.click()
    time.sleep(3)

    # If 2FA enabled, prompt for OTP
    if "checkpoint" in browser.current_url:
        otp_id = browser.find_element_by_id("approvals_code")
        continue_id = browser.find_element_by_id("checkpointSubmitButton")

        fb_otp = input("Enter OTP: ")
        otp_id.send_keys(fb_otp)
        continue_id.click()

    time.sleep(3)
    return True

# Download friends list
def download_friends_list():
    browser.get("https://m.facebook.com/me/friends")
    time.sleep(3)
    print('Loading friends list...')
    scrollpage = 1
    while browser.find_elements_by_css_selector('#m_more_friends'):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        stdout.write("\r>> Scrolled to page %d" % (scrollpage))
        stdout.flush()
        scrollpage += 1
        time.sleep(0.5)

    with open (friends_html, 'w', encoding="utf-8") as f:
        f.write(browser.page_source)
        print("\n>> Saved friend list to '%s'" % friends_html)

# Parse friends list into JSON
def index_friends():
    friends = utils.db_read(db_index)
    already_parsed = []
    for i,d in enumerate(friends):
        already_parsed.append(d['id'])
    print('Loading saved friends list...')

    file_path = os.getcwd() + '/' + friends_html
    x = html.parse(file_path).xpath
    base = '(//*[@data-sigil="undoable-action"])'
    num_items = len(x(base))
    if num_items == 0:
        print("\nWasn't able to parse friends index. This probably means that Facebook updated their template. \nPlease raise issue on Github and I will try to update the script. \nOr if you can code, please submit a pull request instead :)\n")
        sys.exit()
    for i in range(1,num_items+1):
        b = base + '['+str(i)+']/'
        info = json.loads(x(b+'/div[3]/div/div/div[3]')[0].get('data-store'))
        stdout.flush()
        stdout.write("\rScanning friend list... (%d / %d)" % (i,num_items))
        if not info['id'] in already_parsed:
            name = x(b+'/div[2]//a')[0].text
            alias = '' if info['is_deactivated'] else x(b+'/div[2]//a')[0].get('href')[1:]
            d = {
                'id': info['id'],
                'name': name,
                'active': 0 if int(info['is_deactivated']) else 1,
                'alias': alias                
                }
            
            utils.db_write(db_index,d)

    print('\n>> Saved friends list (%s) to %s' % (num_items,db_index))

# Download profile pages
def download_profiles():
    print('Downloading profiles...')
    session_downloads = 0
    index = utils.db_read(db_index)
    for i,d in enumerate(index):
        if d['active']:
            fname = profiles_dir + str(d['id']) + '.html'
            if not os.path.exists(fname):
                print('- %s (# %s)' % (d['name'],d['id']))
                browser.get('https://mbasic.facebook.com/profile.php?v=info&id='+str(d['id']))
                session_downloads += 1
                time.sleep(random.randint(1,3))
                if session_downloads == 45:
                    print("Taking a voluntary break at " + str(session_downloads) + " profile downloads to prevent triggering Facebook's alert systems. I recommend you quit (Ctrl-C or quit this window) to play it safe and try coming back tomorrow to space it out. \nOr, press enter to continue at your own risk.")
                if browser.title == "You can't use this feature at the moment":
                    print("\n***WARNING***\n\nFacebook detected abnormal activity, so this script is going play it safe and take a break.\n- As of March 2020, this seems to happen after downloading ~45 profiles in 1 session.\n- I recommend not running the script again until tomorrow.\n- Excessive use might cause Facebook to get more suspicious and possibly suspend your account.\n\nIf you have experience writing scrapers, please feel free to recommend ways to avoid triggering Facebook's detection system :)")
                    sys.exit(1)
                if browser.find_elements_by_css_selector('#login_form') or browser.find_elements_by_css_selector('#mobile_login_bar'):
                    print('\nBrowser is not logged into facebook! Please run again to login & resume.')
                    sys.exit(1)
                else:
                    with open (fname, 'w', encoding="utf-8") as f:
                        f.write(browser.page_source)

# Parse profile pages into JSON
def parse_profile(profile_file):
    xp_queries = {
        'tagline':      {'do':1,'txt':'//*[@id="root"]/div[1]/div[1]/div[2]/div[2]'},
        'about':        {'do':1,'txt':'//div[@id="bio"]/div/div/div'},
        'quotes':       {'do':1,'txt':'//*[@id="quote"]/div/div/div'},
        'rel':          {'do':1,'txt':'//div[@id="relationship"]/div/div/div'},
        'rel_partner':  {'do':1,'href':'//div[@id="relationship"]/div/div/div//a'},
        'details':      {'do':1,'table':'(//div[not(@id)]/div/div/table[@cellspacing]/tbody/tr//'},
        'work':         {'do':1,'workedu':'//*[@id="work"]/div[1]/div/div'},
        'education':    {'do':1,'workedu':'//*[@id="education"]/div[1]/div/div'},
        'family':       {'do':1,'fam':'//*[@id="family"]/div/div/div'},
        'life_events':  {'do':1,'years':'(//div[@id="year-overviews"]/div/div/div/div/div)'}
    }

    profile_id = int(os.path.basename(profile_file).split('.')[0])
    profile_path = 'file://' + os.getcwd() + '/' + profile_file
    x = html.parse(profile_path).xpath
    alias = x('//a/text()[. = "Timeline"][1]/..')[0].get('href')[1:].split('?')[0]
    d = {
        'id': profile_id,
        'name': x('//head/title')[0].text,
        'alias': alias if alias !='profile.php' else '',
        'meta_created' : time.strftime('%Y-%m-%d', time.localtime(os.path.getctime(profile_file))),
        'details': []
    }
    stdout.flush()
    stdout.write("\r>> Parsing: %s (# %s)                    " % (d['name'], d['id']))

    for k,v in xp_queries.items():
        if v['do'] == 1:
            if 'txt' in v:
                elements = x(v['txt'])
                if len(elements) > 0:
                    d[str(k)] = str(x(v['txt'])[0].text_content())
            elif 'href' in v:
                elements = x(v['href'])
                if len(elements) > 0:
                    d[str(k)] = x(v['href'])[0].get('href')[1:].split('refid')[0][:-1]
            elif 'table' in v:
                rows = x(v['table']+'td[1])')  
                for i in range (1, len(rows)+1):
                    key = x(v['table']+'td[1])'+'['+str(i)+']')[0].text_content()
                    val = x(v['table']+'td[2])'+'['+str(i)+']')[0].text_content()
                    d['details'].append({key:val})
            elif 'workedu' in v:
                d[str(k)] = []
                base = v['workedu']
                rows = x(base)
                for i in range (1, len(rows)+1):
                    # Prep the Work/Education object
                    dd = {}
                    workedu_base = base+'['+str(i)+']'+'/div/div[1]/div[1]'
                    dd['org'] = x(workedu_base)[0].text_content()

                    # Determine org URL
                    if str(k) == "work":
                        org_href = workedu_base + '/span/a' # work URL
                    else:
                        org_href = workedu_base + '/div/span/a' # edu URL

                    # Include org URL if exists
                    url_elements = x(org_href)
                    if len(url_elements) > 0:
                        dd['link'] = x(org_href)[0].get('href')[1:].split('refid')[0][:-1]
                    
                    dd['lines'] = []
                    lines = x(base+'['+str(i)+']'+'/div/div[1]/div')
                    for l in range (2, len(lines)+1):
                        line = x(base+'['+str(i)+']'+'/div/div[1]/div'+'['+str(l)+']')[0].text_content()
                        dd['lines'].append(line)

                    d[str(k)].append(dd)

            elif 'fam' in v:
                d[str(k)] = []
                base = v['fam']
                rows = x(base)
                for i in range (1, len(rows)+1):
                    xp_alias = x(base+'['+str(i)+']'+'//h3[1]/a')
                    alias = '' if len(xp_alias) == 0 else xp_alias[0].get('href')[1:].split('refid')[0][:-1]
                    d[str(k)].append({
                        'name': x(base+'['+str(i)+']'+'//h3[1]')[0].text_content(),
                        'rel': x(base+'['+str(i)+']'+'//h3[2]')[0].text_content(),
                        'alias': alias
                    })
            elif 'life_events' in k:
                d[str(k)] = []
                base = v['years']
                years = x(base)
                for i in range (1,len(years)+1):
                    year = x(base+'['+str(i)+']'+'/div[1]/text()')[0]
                    events = x(base+'['+str(i)+']'+'/div/div/a')
                    for e in range(1,len(events)+1):
                        event = x('('+base+'['+str(i)+']'+'/div/div/a)'+'['+str(e)+']')
                        d[str(k)].append({
                            'year': year,
                            'title': event[0].text_content(),
                            'link': event[0].get('href')[1:].split('refid')[0]
                        })
    return d

# Parse all unparsed profiles in db profile folder
def parse_profile_files():
    print('>> Scanning downloaded profile pages...')
    already_parsed = []
    profiles = utils.db_read(db_profiles)
    for profile in profiles:
        already_parsed.append(profile['id'])

    profile_files = glob.glob(profiles_dir+'*.html')
    for profile_file in profile_files:
        profile_id = int(os.path.basename(profile_file).split('.')[0])
        if not profile_id in already_parsed:
            profile = parse_profile(profile_file)
            utils.db_write(db_profiles,profile)
    
    print('>> %s profiles parsed to %s' % (len(profile_files),db_profiles))

# Create index of friends and their locations
def index_locations():
    print("Scanning profiles for location (eg. current city)...")
    profiles = utils.db_read(db_profiles)

    detail_fields = ['Current City','Mobile','Email','Birthday']
    
    for p in profiles:
        details = json.loads(p['details'])
        new_deets = {}
        for d in details:
            for k in d:
                if k in detail_fields:
                    new_deets[k] = d.get(k,'')
        utils.db_update(db_profiles,p['id'],new_deets)
    
    print('>> Updated friend locations')

# Get coordinates for all locations
def make_map():
    print('Geocoding locations from profiles...')
    url_base = 'https://api.mapbox.com/geocoding/v5/mapbox.places/'

    profiles = utils.db_read(db_profiles)
    locations = utils.db_read(db_locations)
    
    geo_dict = {}
    for location in locations:
        geo_dict[location['location']] = location['coordinates']
    
    features = []
    for d in profiles:
        city = d['Current City']
        if city is not None:
            stdout.flush()
            stdout.write("\r>> Geocoding %s                         \r" % (city))
            if city in geo_dict:
                coordinates = json.loads(geo_dict[city])
            else:
                r = requests.get(url_base + city + '.json', params={
                    'access_token': mapbox_token,
                    'types': 'place,address',
                    'limit': 1
                })
                try:
                    coordinates = r.json()['features'][0]['geometry']['coordinates']
                except IndexError:
                    pass

                utils.db_write(db_locations,{'location': city,'coordinates': coordinates})
                geo_dict[city] = str(coordinates)

            features.append(Feature(
                geometry = Point(coordinates),
                properties = {'name': d['name'],'location': city,'id': d['id']}
            ))

            collection = FeatureCollection(features)
            with open(db_geojson, "w") as f:
                f.write('%s' % collection)

    with open('template-map.html') as f:
        html=f.read()
        html=html.replace('{{mapbox_token}}', mapbox_token)
        html=html.replace('{{datapoints}}', str(collection))
    with open('friends-map.html', "w", encoding="utf-8") as f:
        f.write(html)
    print('>> Saved map to friends-map.html!')
    webbrowser.open_new('file://' + os.getcwd() + '/friends-map.html') 

# Shell application
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook friends profile exporter')
    parser.add_argument('--list', action='store_true', help='Download friends list')
    parser.add_argument('--index', action='store_true', help='Index friends list')
    parser.add_argument('--download', action='store_true', help='Download friends profiles')
    parser.add_argument('--parse', action='store_true', help='Parse profiles to database')
    parser.add_argument('--map', action='store_true', help='Make the map!')
    parser.add_argument('--json', action='store_true', help='Export database to JSON files')
    args = parser.parse_args()
    signed_in = False
    try:
        fullrun = True if len(sys.argv) == 1 else False

        if fullrun or args.list or args.index or args.download:
            browser = start_browser()

        #Download friends list
        if fullrun or args.list:
            signed_in = sign_in()
            download_friends_list()

        #Index friends list
        if fullrun or args.index:
            index_friends()

        #Download profiles
        if fullrun or args.download:
            if not signed_in: sign_in()
            download_profiles()

        #Parse profiles
        if fullrun or args.parse:
            parse_profile_files()

        #Geocode
        if fullrun or args.map:
            index_locations()
            make_map()

        #JSON Export (Optional)
        if fullrun or args.json:
            utils.db_to_json()

    except KeyboardInterrupt:
        print('\nThanks for using the script! Please raise any issues on Github.')
        pass
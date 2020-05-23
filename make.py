#!/usr/bin/env python
# coding: utf-8

import argparse, json, os, glob, time, sys, requests, random, glob, webbrowser, chromedriver_binary
from selenium.webdriver import Chrome, ChromeOptions
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
    print('>> Loaded credentials from .env file.')
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
friends_html = 'db/index.html'
profiles_dir = 'db/profiles/'
db_index = 'db/index.json'
db_profiles = 'db/profiles.json'
db_friend_locations = 'db/friend_locations.json'
db_geo = 'db/geo.json'
db_geojson = "db/points.geojson"

if not os.path.exists(profiles_dir):
    os.makedirs(profiles_dir)
if not os.path.exists(db_index):
    with open(db_index,'w') as f:
        f.write("[]")
if not os.path.exists(db_profiles):
    with open(db_profiles,'w') as f:
        f.write("[]")

def db_save(db,data):
    with open(db, 'w') as f:
        json.dump(data, f, indent=2)

def db_read(db):
    with open(db) as f:
        data = json.load(f)
        return data

# Configure browser
def start_browser():
    options = ChromeOptions() 
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_experimental_option("prefs",{"profile.managed_default_content_settings.images":2})

    browser = Chrome(options=options)
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
    return True

# Download friends list
def download_friends_list():
    browser.get("https://m.facebook.com/me/friends")
    time.sleep(3)
    print('Scrolling to bottom. Please wait, this takes a few mins...')
    while browser.find_elements_by_css_selector('#m_more_friends'):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    with open (friends_html, 'w', encoding="utf-8") as f:
        f.write(browser.page_source)
        print(">> Saved friend list to '%s'" % friends_html)

# Parse friends list into JSON
def index_friends():
    friends = db_read(db_index)
    already_parsed = []
    for i,d in enumerate(friends):
        already_parsed.append(d['id'])
    print('Opening saved friends list...')
    browser.get('file:///' + os.getcwd() + '/' + friends_html)
    base = '(//*[@data-sigil="undoable-action"])'
    num_items = len(browser.find_elements_by_xpath(base))
    if num_items == 0:
        print("\nWasn't able to parse friends index. This probably means that Facebook updated their template. \nPlease raise issue on Github and I will try to update the script. \nOr if you can code, please submit a pull request instead :)\n")
        sys.exit()
    for i in range(1,num_items+1):
        b = base + '['+str(i)+']/'
        info = json.loads(browser.find_element_by_xpath(b+'/div[3]/div/div/div[3]').get_attribute('data-store'))
        stdout.write("\rScanning friends... (%d / %d)" % (i,num_items))
        stdout.flush()
        if not info['id'] in already_parsed:
            alias = '' if info['is_deactivated'] else browser.find_element_by_xpath(b+'/div[2]//a').get_attribute('href')[8:]
            d = {
                'id': info['id'],
                'name': browser.find_element_by_xpath(b+'/div[2]//a').text,
                'is_deactivated': info['is_deactivated'],
                'alias': alias,
                'photo_url': browser.find_element_by_xpath(b+'div[1]/a/i').get_attribute('style').split('("')[1].split('")')[0],
                }
            print('\n>> Added %s (#%s)' % (d['name'],i))
            friends.append(d)

            db_save(db_index,friends)
    print('\nIndexed %s friends to %s' % (num_items,db_index))

# Download profile pages
def download_profiles():
    print('Downloading profiles...')
    session_downloads = 0
    index = db_read(db_index)
    for i,d in enumerate(index):
        if not d['is_deactivated']:
            fname = profiles_dir + str(d['id']) + '.html'
            if not os.path.exists(fname):
                print('- %s (# %s)' % (d['name'],d['id']),end="",flush=True)
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
def parse_profiles():
    profiles = []
    already_parsed = []
    profiles = db_read(db_profiles)
    for i,profile in enumerate(profiles):
        already_parsed.append(profile['id'])
    profile_files = glob.glob(profiles_dir+'*.html')

    sections = {
        'photo_url': {'src':'//div[@id="objects_container"]//a/img[@alt][1]'},
        'tagline': {'txt':'//*[@id="root"]/div[1]/div[1]/div[2]/div[2]'},
        'about': {'txt':'//div[@id="bio"]/div/div[2]/div'},
        'quotes': {'txt':'//*[@id="quote"]/div/div[2]/div'},
        'rel': {'txt':'//div[@id="relationship"]/div/div[2]'},
        'rel_partner': {'href':'//div[@id="relationship"]/div/div[2]//a'},
        'details': {'table':'(//div[2]/div//div[@title]//'},
        'work': {'workedu':'//*[@id="work"]/div[1]/div[2]/div'},
        'education': {'workedu':'//*[@id="education"]/div[1]/div[2]/div'},
        'family': {'fam':'//*[@id="family"]/div/div[2]/div'},
        'life_events': {'years':'(//div[@id="year-overviews"]/div[1]/div[2]/div[1]/div/div[1])'}
    }

    print('Parsing profile pages...')
    for i,r in enumerate(profile_files):
        profile_id = int(os.path.basename(r).split('.')[0])
        if not profile_id in already_parsed:
            print('%s/%s) #%s' % (i+1,len(profile_files),profile_id),end="",flush=True)
            profile_path = 'file://'+os.getcwd()+'/'+r
            browser.get(profile_path)
            x = browser.find_element_by_xpath
            xs = browser.find_elements_by_xpath
            d = {
                'id': profile_id,
                'name': browser.title,
                'alias': x('//a/text()[. = "Timeline"][1]/..').get_attribute('href')[8:].split('?')[0],
                'meta' : {
                    'created': time.strftime('%Y-%m-%d', time.localtime(os.path.getctime(r))),
                }
            }
            for k,v in sections.items():
                try:
                    if 'src' in v:
                        d[str(k)] = x(v['src']).get_attribute('src')
                    elif 'txt' in v:
                        d[str(k)] = x(v['txt']).text
                    elif 'href' in v:
                        d[str(k)] = x(v['href']).get_attribute('href')[8:].split('?')[0]
                    elif 'table' in v:
                        d['details'] = []
                        rows = xs(v['table']+'td[1])')
                        for i in range (1, len(rows)+1):
                            deets_key = x(v['table']+'td[1])'+'['+str(i)+']').text
                            deets_val = x(v['table']+'td[2])'+'['+str(i)+']').text
                            d['details'].append({deets_key:deets_val})
                    elif 'workedu' in v:
                        d[str(k)] = []
                        base = v['workedu']
                        rows = xs(base)
                        for i in range (1, len(rows)+1):
                            dd = {}
                            dd['link'] = x(base+'['+str(i)+']'+'/div/div[1]//a').get_attribute('href')[8:].split('&')[0].split('/')[0]
                            dd['org'] = x(base+'['+str(i)+']'+'/div/div[1]//a').text
                            dd['lines'] = []
                            lines = xs(base+'['+str(i)+']'+'/div/div[1]/div')
                            for l in range (2, len(lines)+1):
                                line = x(base+'['+str(i)+']'+'/div/div[1]/div'+'['+str(l)+']').text
                                dd['lines'].append(line)
                            d[str(k)].append(dd)
                    elif 'fam' in v:
                        d[str(k)] = []
                        base = v['fam']
                        rows = xs(base)
                        for i in range (1, len(rows)+1):
                            d[str(k)].append({
                                'name': x(base+'['+str(i)+']'+'//h3[1]').text,
                                'rel': x(base+'['+str(i)+']'+'//h3[2]').text,
                                'alias': x(base+'['+str(i)+']'+'//h3[1]/a').get_attribute('href')[8:].split('?')[0]
                            })
                    elif 'life_events' in k:
                        d[str(k)] = []
                        base = v['years']
                        years = xs(base)
                        for i in range (1,len(years)+1):
                            year = x(base+'['+str(i)+']'+'/div[1]').text
                            events = xs(base+'['+str(i)+']'+'/div/div/a')
                            for e in range(1,len(events)+1):
                                event = x('('+base+'['+str(i)+']'+'/div/div/a)'+'['+str(e)+']')
                                d[str(k)].append({
                                    'year': year,
                                    'title': event.text,
                                    'link': event.get_attribute('href')[8:].split('refid')[0]
                                })
                    
                except exceptions.NoSuchElementException:
                    pass
            
            print(' // %s (%s)' % (d['name'],d['alias']))
            profiles.append(d)

            try:
                db_save(db_profiles,profiles)
            except KeyboardInterrupt:
                print('Saving last record...')
                db_save(db_profiles,profiles)
                print('\nThanks for using the script! Please raise any issues at https://github.com/jcontini/facebook-scraper/issues.')
                sys.exit()
            
    print('>> %s profiles parsed to %s' % (len(profile_files),db_profiles))


# Geocode locations

def index_locations():
    print("Indexing locations...")
    with open(db_profiles) as f:
        profiles = json.load(f)
    with open(db_index) as f:
        index = json.load(f)
    locations = []
    for idx,r in enumerate(profiles):
        loc = ''
        for i,d in enumerate(r['details']):
            if d.get('Address'):
                loc = d.get('Address')
        for i,d in enumerate(r['details']):
            if d.get('Current City'):
                loc = d.get('Current City')  
        for i,d in enumerate(index):
            if r['id'] == d['id']:
                photo = d['photo_url']
        if loc:
            d = {
                'id': r['id'],
                'name': r['name'],
                'location': loc,
                'photo': photo
            }
            print(d['location'])
            locations.append(d)
        else:
            print('(no location)')
    
    with open(db_friend_locations,'w', encoding="utf-8") as f:
        json.dump(locations, f, indent=4)
    print('Indexed %s friends locations to %s' % (len(locations),db_friend_locations))


# In[ ]:


def geocode_locations():
    with open(db_friend_locations) as f:
        data = json.load(f)
    locations = []
    for i,r in enumerate(data):
        locations.append(r['location'])
    unique_locs = list(set(locations))
    url_base = 'https://api.mapbox.com/geocoding/v5/mapbox.places/'
    print('Geocoding locations from profiles...')
    geos = []
    for location in unique_locs:
        r = requests.get(url_base + location + '.json',
         params={
             'access_token': mapbox_token,
             'types': 'place,address',
             'limit': 1
         })
        coordinates = r.json()['features'][0]['geometry']['coordinates']
        print('%s : %s' % (location ,coordinates))
        geos.append({location:coordinates})
    
    with open(db_geo,'w') as f:
        json.dump(geos, f, indent=4)
    print('Indexed %s coordinates to %s' % (len(geos),db_geo))


# In[ ]:


def make_map():
    #Open friends-locations list
    with open(db_friend_locations) as f:
        friends = json.load(f)
    #Open location-coordinates list
    with open(db_geo) as f:
        locations = json.load(f)
    geo_dict = {}
    for loc in locations:
        for k_loc,v_coordinates in loc.items():
            geo_dict[k_loc] = v_coordinates

    features = []
    for i,friend in enumerate(friends):
        friend['coordinates'] = geo_dict[friend['location']] #Set friend coordinates based on location list
        print('%s) %s // %s' %(i,friend['name'],friend['coordinates']))
        features.append(Feature(
                geometry = Point(friend['coordinates']),
                properties = {
                    'name': friend['name'],
                    'location': friend['location'],
                    'id': friend['id']
                }
            ))
        collection = FeatureCollection(features)
        with open(db_geojson, "w") as f:
            f.write('%s' % collection)

    print('Added coordinates for %s friends!' % len(friends))

    with open('template-map.html') as f:
        html=f.read()
        html=html.replace('{{mapbox_token}}', mapbox_token)
        html=html.replace('{{datapoints}}', str(collection))
    with open('friends-map.html', "w", encoding="utf-8") as f:
        f.write(html)
    print('Saved map to friends-map.html!')
    webbrowser.open_new('file://' + os.getcwd() + '/friends-map.html') 


# Shell application
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook friends profile exporter')
    parser.add_argument('--index', action='store_true', help='Index friends list')
    parser.add_argument('--download', action='store_true', help='Download friends profiles')
    parser.add_argument('--parse', action='store_true', help='Parse profiles to JSON')
    parser.add_argument('--geocode', action='store_true', help='Geocode addresses to coordinates')
    parser.add_argument('--map', action='store_true', help='Make the map!')
    args = parser.parse_args()
    browser = start_browser()
    signed_in = False
    try:
        if not len(sys.argv) > 1:
        #Index friends list
            signed_in = sign_in()
            count_indexed = len(db_read(db_index))
            print(">> Loaded %s friends from index" %(count_indexed))
            if not signed_in: sign_in()
            download_friends_list()
            index_friends()

        #Download profiles
            # Get list of downloaded ids
            profile_files = glob.glob1(profiles_dir,'*.html')
            downloaded_ids = []
            for f in profile_files:
                downloaded_ids.append(int(f.replace('.html','')))
                
            # Get list of active indexed IDs
            indexed_profiles = db_read(db_index)
            if len(indexed_profiles) == 0:
                print(">> No profiles indexed. Please delete "+db_index+" and run again")
                sys.exit(1)
            indexed_ids = []
            for i in indexed_profiles:
                if i['is_deactivated'] == False:
                    indexed_ids.append(i['id'])

            # Do some counting
            count_inactive = len(indexed_profiles)-len(indexed_ids)
            inactive_downloaded = list(set(downloaded_ids) - set(indexed_ids))
            ids_to_download = list(set(indexed_ids) - set(downloaded_ids))

            print(">> %s Profiles active (%s deactivated)" % (len(indexed_ids),count_inactive))
            print(">> %s Profiles downloaded (including %s deactivated)" % (len(downloaded_ids),len(inactive_downloaded)))

            # If new profiles to download, get to it
            if len(ids_to_download) != 0:
                print(">> %s new profiles to download! Getting to it..." % (len(ids_to_download)))
                if not signed_in: sign_in()
                download_profiles()

        #Parse profiles
            profiles_db = db_read(db_profiles)
            if len(profiles_db) == len(profile_files):
                print(">> Profile parsing completed, moving on")
            else:
                parse_profiles()

        #Geocode
            index_locations()
            geocode_locations()
            make_map()

        #Run only specific tasks if specified in arguments    
        elif args.index:
            index_friends()
        elif args.download:
            if not signed_in: sign_in()
            download_profiles()
        elif args.parse:
            parse_profiles()
        elif args.geocode:
            index_locations()
            geocode_locations()
        elif args.map:
            make_map()

    except KeyboardInterrupt:
        print('\nThanks for using the script! Please raise any issues at https://github.com/jcontini/facebook-scraper/issues.')
        pass


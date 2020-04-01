#!/usr/bin/env python
# coding: utf-8

# # Facebook profile export & map

# In[2]:


import argparse, json, os, glob, time, sys, requests, random, glob
import chromedriver_binary
from selenium.webdriver import Chrome, ChromeOptions
from selenium.common import exceptions
from datetime import datetime
from geojson import Feature, FeatureCollection, Point

#Set up environment
if os.path.exists('.env'):
    fb_user = os.getenv('fb_user')
    fb_pass = os.getenv('fb_pass')
    mapbox_token = os.getenv('mapbox_token')
    print('Loaded credentials from .env file.')
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

# ## Extract friends profiles from Facebook

# In[ ]:

def start_browser():
    options = ChromeOptions() 
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    #options.add_argument('--headless')
    options.add_experimental_option("prefs",{"profile.managed_default_content_settings.images":2})

    browser = Chrome(options=options)
    return browser

# In[ ]:

def sign_in():
    fb_start_page = 'https://m.facebook.com/'
    print("Logging in %s automatically..." % fb_user)
    browser.get(fb_start_page)
    email_id = browser.find_element_by_id("m_login_email")
    pass_id = browser.find_element_by_id("m_login_password")
    email_id.send_keys(fb_user)
    pass_id.send_keys(fb_pass)
    pass_id.send_keys(u'\ue007')

    time.sleep(2)
    return True


# In[ ]:

def download_friends():
    browser.get("https://m.facebook.com/me/friends")
    time.sleep(3)
    print('Scrolling to bottom...')
    #Scroll to bottom
    while browser.find_elements_by_css_selector('#m_more_friends'):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    #Save friend list
    with open (friends_html, 'w') as f:
        f.write(browser.page_source)
        print('%s) Downloaded' % friends_html)


# In[ ]:

def index_friends():
    with open(db_index) as f:
        friends = json.load(f)
    already_parsed = []
    for i,d in enumerate(friends):
        already_parsed.append(d['id'])
    print('Indexing friends list...')
    browser.get('file:///' + os.getcwd() + '/' + friends_html)
    base = '(//*[@data-sigil="undoable-action"])'
    num_items = len(browser.find_elements_by_xpath(base))
    if num_items == 0:
        print("\nWasn't able to parse friends index. This probably means that Facebook updated their template. \nPlease raise at https://github.com/jcontini/facebook-scraper/issues and I will try to update the script. \nOr if you can code, please submit a pull request instead :)\n")
        sys.exit()
    print('Scanning %s friends...' % (num_items))
    for i in range(1,num_items+1):
        b = base + '['+str(i)+']/'
        info = json.loads(browser.find_element_by_xpath(b+'/div[3]/div/div/div[3]').get_attribute('data-store'))
        if info['id'] in already_parsed:
            print('%s) // Already indexed %s, skipping...' % (i,info['id']))
        else:
            alias = '' if info['is_deactivated'] else browser.find_element_by_xpath(b+'/div[2]//a').get_attribute('href')[8:]
            d = {
                'id': info['id'],
                'name': browser.find_element_by_xpath(b+'/div[2]//a').text,
                'is_deactivated': info['is_deactivated'],
                'alias': alias,
                'photo_url': browser.find_element_by_xpath(b+'div[1]/a/i').get_attribute('style').split('("')[1].split('")')[0],
                }
            print('%s) %s' % (i,d['name']))
            friends.append(d)

            with open(db_index, 'w') as f:
                json.dump(friends, f, indent=4)
    print('Indexed %s friends to %s' % (num_items,db_index))


# In[ ]:

def download_profiles():
    print('Downloading profiles from index...')
    session_downloads = 0
    with open(db_index, 'r') as f:
        data = json.load(f)
    for i,d in enumerate(data):
        print('%s) %s' % (i+1,d['name']),end="",flush=True)
        if d['is_deactivated']:
            print(' // Skipped (Profile deactivated)')
        else:
            fname = profiles_dir + str(d['id']) + '.html'
            if os.path.exists(fname):
                print(" // Skipped (Already Exists): %s" % (fname))
            else:
                browser.get('https://mbasic.facebook.com/profile.php?v=info&id='+str(d['id']))
                session_downloads += 1
                time.sleep(random.randint(1,3)) #Attempt to be a bit more stealthy
                if session_downloads == 45:
                    print("Taking a voluntary break at " + str(session_downloads) + " profile downloads, to prevent triggering Facebook's alert systems. I recommend you quit (Ctrl-C or quit this window) to play it safe and try coming back tomorrow to space it out. \nOr, press enter to continue at your own risk.")
                if browser.title == "You can't use this feature at the moment":
                    print("\n***WARNING***\n\nFacebook detected abnormal activity, so this script is going play it safe and take a break.\n- As of March 2020, this seems to happen after downloading ~45 profiles in 1 session.\n- I recommend not running the script again until tomorrow.\n- Excessive use might cause Facebook to get more suspicious and possibly suspend your account.\n\nIf you have experience writing scrapers, please feel free to recommend ways to avoid triggering Facebook's detection system :) ")
                    sys.exit(1)
                if browser.find_elements_by_css_selector('#login_form') or browser.find_elements_by_css_selector('#mobile_login_bar'):
                    print('\nBrowser is not logged into facebook! Please run again to login & resume.')
                    sys.exit(1)
                else:
                    with open (fname, 'w') as f:
                        f.write(browser.page_source)
                        print(' // Downloaded to %s' % fname)


# In[ ]:


def parse_profiles():
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
    
    with open(db_index) as f:
        friends_list = json.load(f)
    profiles = []
    with open(db_profiles) as f:
        profiles = json.load(f)
    already_parsed = []
    for i,profile in enumerate(profiles):
        already_parsed.append(profile['id'])
    print('Parsing profile pages...')
    for i,r in enumerate(friends_list):
        print('%s/%s) %s' % (i+1,len(friends_list),r['name']),end="",flush=True)
        if r['is_deactivated']:
            print(' // Profile deactivated, skipping...')
        elif r['id'] in already_parsed:
            print(' // Already parsed, skipping...')
        else:
            d = {'id': r['id'],'name': r['name'],'alias': r['alias']}
            profile = 'file://'+os.getcwd()+'/'+profiles_dir+str(d['id'])+'.html'
            print(' // '+profile.split('/')[-1])
            browser.get(profile)
            x = browser.find_element_by_xpath
            xs = browser.find_elements_by_xpath
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
            
            profiles.append(d)

            with open(db_profiles, 'w') as f:
                json.dump(profiles, f, indent=2)
            
    print('Indexed %s friends to %s' % (len(friends_list),db_profiles)) #update how it counts


# ## Geocode locations

# In[ ]:


def index_locations():
    with open(db_profiles) as f:
        profiles = json.load(f)
    with open(db_index) as f:
        index = json.load(f)
    locations = []
    for idx,r in enumerate(profiles):
        print('%s) %s (%s): ' % (idx+1,r['name'],r['id']),end="",flush=True)
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
    
    with open(db_friend_locations,'w') as f:
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
        print('-'*20)
    
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
    with open('friends-map.html', "w") as f:
        f.write(html)
    print('Saved map to friends-map.html!')


# ## Shell application

# In[17]:


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook friends profile exporter')
    parser.add_argument('--index', action='store_true', help='Index friends list')
    parser.add_argument('--download', action='store_true', help='Download friends profiles')
    parser.add_argument('--parse', action='store_true', help='Parse profiles to JSON')
    parser.add_argument('--geocode', action='store_true', help='Geocode addresses to coordinates')
    parser.add_argument('--map', action='store_true', help='Make the map!')

    args = parser.parse_args()
    signed_in = False
    browser = False
    try:
        if args.index:
            browser = start_browser()
            sign_in()
            download_friends()
            index_friends()
        elif args.download:
            browser = start_browser()
            sign_in()
            download_profiles()
        elif args.parse:
            browser = start_browser()
            parse_profiles()
        elif args.geocode:
            index_locations()
            geocode_locations()
        elif args.map:
            make_map()
        else:
            #Index friends list
            if not os.path.exists(db_index):
                browser = start_browser()
                signed_in = sign_in()
                download_friends()
                index_friends()
            else:
                print(">> Indexing completed, moving on. To re-index, delete " + db_index)
            #Download profiles
            with open(db_index, 'r') as f:
                index = json.load(f)
            profiles_active = 0
            for d in (index):
                if not d['is_deactivated']:
                    profiles_active += 1
            profiles_downloaded = len(glob.glob(profiles_dir+'*.html'))
            print(str(profiles_active)+" Active profiles indexed\n"+str(profiles_downloaded)+" Profiles downloaded")
            #TODO: Handle case where more profiles downloaded tha active (from pervious runs)
            if profiles_downloaded >= profiles_active: 
                print(">> Profile downloading completed, moving on")
            else:  
                if signed_in == False:
                    browser = start_browser()
                    signed_in = sign_in()
                download_profiles()
            #Parse profiles
            with open(db_profiles) as f:
                profiles = json.load(f)
            profiles_parsed = len(profiles)
            if profiles_parsed == profiles_downloaded:
                print(">> Profile parsing completed, moving on")
            else:
                if browser == False:
                    browser = start_browser()
                parse_profiles()
            #Geocode
            index_locations()
            geocode_locations()
            make_map()

    except KeyboardInterrupt:
        print('\nThanks for using the script! Please raise any issues at https://github.com/jcontini/facebook-scraper/issues.')
        pass


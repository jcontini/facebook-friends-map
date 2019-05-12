#!/usr/bin/env python
# coding: utf-8

# In[1]:


import argparse, json, os, glob, time, sys, pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from datetime import datetime

ts = datetime.now().strftime('%Y-%m-%d_%H%M')
friends_html = 'db/index.html'
profiles_dir = 'db/profiles/'
db_index = 'db/index.json'
db_profiles = 'db/profiles.json'

#Set up & check environment
if not os.path.exists(profiles_dir):
    os.makedirs(profiles_dir)
if not os.path.exists(db_index):
    with open(db_index,'w') as f:
        f.write("{}")
if not os.path.exists(db_profiles):
    with open(db_profiles,'w') as f:
        f.write("{}")

#Determine execution context
try:
    get_ipython()
    is_nb = 1
    print('Saving latest notebooks to Python...')
    get_ipython().system('jupyter nbconvert --to script *.ipynb')
except:
    is_nb = 0
    print('Script is running from shell')


# In[2]:


def analytics():
    with open(db_index) as f:
        friends_list = json.load(f)
    detail_files = sorted(glob.glob(profiles_dir + '*.html'), key=os.path.getmtime)
    
    print('-- Startup check --')
    print('# Friends: %s' % len(friends_list))
    print('# Profile Files: %s' % len(detail_files))
    print('# Profiles parsed: %s' % len(db_profiles))
    print('# Remaining files: %s' % (len(friends_list)-len(detail_files)))
    print('-'*20)


# In[3]:


def start_browser():
    #Setup browser
    print("Opening Browser...")
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument("--start-maximized")
    #options.add_argument("headless")
    options.add_experimental_option("prefs",{"profile.managed_default_content_settings.images":2})
    browser = Chrome(options=options)

    return browser


# In[4]:


def sign_in(browser):
    #Sign in
    fb_start_page = 'https://m.facebook.com/'
    if os.getenv('fb_pass', None):
        fb_user = os.getenv('fb_user')
        fb_pass = os.getenv('fb_pass')
        print("Logging in %s automatically..." % fb_user)
        browser.get(fb_start_page)
        email_id = browser.find_element_by_id("m_login_email")
        pass_id = browser.find_element_by_id("m_login_password")
        email_id.send_keys(fb_user)
        pass_id.send_keys(fb_pass)
        pass_id.send_keys(u'\ue007')
    else:
        browser.get(fb_start_page)
        input("Please log into facebook and press enter after the page loads...")
    time.sleep(3)


# In[5]:


def download_friends(browser):
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


# In[6]:


def index_friends(browser):
    print('Indexing friends list...')    
    data = []
    browser.get('file:///' + os.getcwd() + '/' + friends_html)
    base = '(//*[@class="_55wp _7om2 _5pxa"])'
    num_items = len(browser.find_elements_by_xpath(base))
    print('Scanning %s friends...' % (num_items))
    for i in range(1,num_items+1):
        b = base + '['+str(i)+']/'
        info = json.loads(browser.find_element_by_xpath(b+'div[2]/div[1]/div[2]/div[3]').get_attribute('data-store'))
        alias = '' if info['is_deactivated'] else browser.find_element_by_xpath(b+'div[2]/div[1]/*[1]/a').get_attribute('href')[8:]
        d = {
            'num': i,
            'id': info['id'],
            'name': browser.find_element_by_xpath(b+'div[2]/div[1]/*[1]/a').text,
            'is_deactivated': info['is_deactivated'],
            'alias': alias,
            'photo_url': browser.find_element_by_xpath(b+'div[1]/a/i').get_attribute('style').split('("')[1].split('")')[0],
            'mutual_friends': browser.find_element_by_xpath(b+'div[2]/div[1]/div[1]/div[1]/div[@data-sigil="m-add-friend-source-replaceable"]').text
            }
        print('%s) %s' % (i,d['name']))
        data.append(d)

        with open(db_index, 'w') as f:
            json.dump(data, f, indent=4)
    print('Indexed %s friends to %s' % (i,db_index))


# In[7]:


def download_profiles(browser):
    print('Downloading profiles from index...')
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
                time.sleep(1)
                if browser.find_elements_by_css_selector('#login_form') or browser.find_elements_by_css_selector('#mobile_login_bar'):
                    print('\nBrowser is not logged into facebook! Please run again to login & resume.')
                    sys.exit(1)
                else:
                    with open (fname, 'w') as f:
                        f.write(browser.page_source)
                        print(' // Downloaded to %s' % fname)


# In[8]:


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
    with open(db_profiles) as f:
        profiles = json.load(f)
    already_parsed = []
    for i,profile in enumerate(profiles):
        already_parsed.append(profile['id'])
        
    for i,r in enumerate(friends_list):
        print('%s) %s' % (i+1,r['name']),end="",flush=True)
        if r['is_deactivated']:
            print(' // Profile deactivated, skipping...')
        elif r['id'] in already_parsed:
            print(' // Already in profile database, skipping...')
        else:
            d = {'id': r['id'],'name': r['name'],'alias': r['alias']}
            profile = 'file://'+os.getcwd()+'/'+profiles_dir+str(d['id'])+'.html'
            print(' // '+profile)
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
            
    print('Indexed %s friends to %s' % (i,db_profiles))


# In[9]:


def json2csv():
    #Convert index JSON to CSV
    df = pd.read_json(db_index)
    df.to_csv('db/index'+ts+'.csv')
    print('Saved to db/index'+ts+'.csv')


# In[10]:


if is_nb:
    browser = start_browser()
    parse_profiles()


# In[11]:


if __name__ == '__main__' and is_nb == 0:
    parser = argparse.ArgumentParser(description='Facebook friends profile exporter')
    parser.add_argument('--index', action='store_true', help='Index friends list')
    parser.add_argument('--download', action='store_true', help='Download friends profiles')

    args = parser.parse_args()
    try:
        browser = start_browser()
        if args.download:
            download_profiles()
        else:
            sign_in(browser)
            download_friends(browser)
            if not args.index:
                download_profiles()
    except KeyboardInterrupt:
        print('\nThanks for using the script! Please raise any issues at https://github.com/jcontini/facebook-scraper/issues.')
        pass


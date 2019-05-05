#!/usr/bin/env python
# coding: utf-8

# # Goal: Save profiles > Get location > Make Map

import argparse, json, os, glob, time, sys, pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from datetime import datetime

ts = datetime.now().strftime('%Y-%m-%d_%H%M')
friends_html = 'db/index.html'
db_index = 'db/index.json'
db_details = 'db/profiles.json'
db_profiles_dir = 'db/profiles/'


def prep_env():
    #Set up & check environment
    if not os.path.exists(db_profiles_dir):
        os.makedirs(db_profiles_dir)
    if not os.path.exists(db_index):
        with open(db_index,'w') as f:
            f.write("{}")


def analytics():
    with open(db_index) as f:
        index_data = json.load(f)
    detail_files = sorted(glob.glob(db_profiles_dir + '*.html'), key=os.path.getmtime)
    
    print('-- Startup check --')
    print('# Indexed: %s' % len(index_data))
    print('# Profile Files: %s' % len(detail_files))
    print('# Remaining files: %s' % (len(index_data)-len(detail_files)))
    print('-'*20)


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


def download_profiles(browser):
    print('Downloading profiles from index...')
    with open(db_index, 'r') as f:
        data = json.load(f)
    for i,d in enumerate(data):
        print('%s) %s' % (i,d['name']),end="",flush=True)
        if d['is_deactivated']:
            print(' // Skipped (Profile deactivated)')
        else:
            fname = db_profiles_dir + str(d['id']) + '.html'
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


def parse_profiles(browser):
    print('this will parse profiles')

    '''
2. For each file
    1. Is already in DB?
        1. If yes, skip
        2. If no, add fields
            1. Education []
            2. Work []
            3. Places they've lived []
                1. Current City
                2. Hometown
                3. (other)
            4. Contact Info
                1. Mobile
                2. Address
                3. Facebook
                4. Email []
                5. Skype
                6. (other)
            5. Basic Info
                1. Birthday
                2. Gender
                3. Languages
                4. (other)
            6. About
                1. ()
            7. Relationship []
            8. Favorite Quotes []
'''


def json2csv():
    #Convert index JSON to CSV
    df = pd.read_json(db_index)
    df.to_csv('db/index'+ts+'.csv')
    print('Saved to db/index'+ts+'.csv')


get_ipython().system('jupyter nbconvert --no-prompt --to script get-profiles.ipynb')


#Full run
prep_env()
analytics()
browser = start_browser()
sign_in(browser)
#download_friends(browser)
#index_friends(browser)
download_profiles(browser)
#parse_profiles(browser)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook friends profile exporter')
    parser.add_argument('--index', action='store_true', help='Index friends list')
    parser.add_argument('--download', action='store_true', help='Download friends profiles')

    args = parser.parse_args()
    try:
        prep_env()
        browser = start_browser()
        if args.download:
            download_profiles()
        else:
            sign_in(browser)
            download_friends(browser)
            if not args.index:
                download_profiles()
    except KeyboardInterrupt:
        print('\nThanks for using the script! Please raise any issues at https://github.com/jcontini/fb-friends-export/issues.')
        pass


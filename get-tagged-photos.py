import argparse, sys, os, time, wget, json, piexif
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dateutil.parser import parse
print("\n" * 100)

def index_photos(username, password):
    #Set waits (go higher if slow internet)
    main_wait = 0.5
    stuck_wait = 3

    #Start Browser
    print("-"*20 + "\nOpening Browser...")
    wd_options = Options()
    wd_options.add_argument("--disable-notifications")
    wd_options.add_argument("--disable-infobars")
    wd_options.add_argument("--mute-audio")
    wd_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(chrome_options=wd_options)
    wait = WebDriverWait(driver, 10)
    driver.get("https://www.facebook.com")

    #Log In
    print("-"*20 + "\nLogging In...")
    email_id = driver.find_element_by_id("email")
    pass_id = driver.find_element_by_id("pass")
    email_id.send_keys(username)
    pass_id.send_keys(password)
    driver.find_element_by_id("loginbutton").click()

    #Nav to photos I'm tagged in page
    print("-"*20 + "\nScanning Photos...")
    driver.find_element_by_id("navItem_2305272732").click()
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "uiMediaThumbImg")))
    driver.find_elements_by_css_selector(".uiMediaThumbImg")[0].click()
    time.sleep(2)

    #Prep structure
    data = {}
    data['tagged'] = []

    while True:
        time.sleep(main_wait)
        try:
            user = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftAuthorName"]/a')))
            media_url = wait.until(EC.presence_of_element_located((By.XPATH, "//img[@class='spotlight']"))).get_attribute('src')
            is_video = "showVideo" in driver.find_element_by_css_selector(".stageWrapper").get_attribute("class")
        except selenium.common.exceptions.StaleElementReferenceException:
            continue

        doc = {
            'fb_url': driver.current_url,
            'fb_date': wait.until(EC.presence_of_element_located((By.CLASS_NAME, "timestampContent"))).text,
            'fb_caption': wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftCaption"]'))).text,
            'fb_tags': wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftTagList"]'))).text.replace('\u2014 ',''),
            'media_url': media_url,
            'media_type': 'video' if is_video else 'image',
            'user_name': user.text,
            'user_url': user.get_attribute('href'),
            'user_id': user.get_attribute('data-hovercard').split('id=')[1].split('&')[0]
        }

        #Check to see if photo didn't refresh or if last photo
        if len(data['tagged'])>0:
            if (doc['media_type'] == 'image') and (data['tagged'][-1]['media_url'] == doc['media_url']):
                print("-"*20 + "\nPhoto stuck. Waiting %s seconds..." % (stuck_wait),end="",flush=True)
                time.sleep(stuck_wait)
                photo_now = driver.find_element(By.XPATH, "//img[@class='spotlight']").get_attribute('src')
                if data['tagged'][-1]['media_url'] == photo_now:
                    print("-"*20 + "\nStill stuck. Clicking Next again...",end="",flush=True)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".snowliftPager.next"))).click()
                    print("-"*20 + "\nGot it. Scanning the page again...")
                    continue
                print('OK, that worked. Moving on...')

            if driver.current_url == data['tagged'][0]['fb_url']:
                print("-"*20 + "\nDone Indexing! Last Photo: %s" % (driver.current_url))
                break

        #Get album if present
        if len(driver.find_elements_by_xpath('//*[@class="fbPhotoMediaTitleNoFullScreen"]/div/a')) > 0:
            doc['album'] = driver.find_element_by_xpath('//*[@class="fbPhotoMediaTitleNoFullScreen"]/div/a').get_attribute('href')

        #Get Deets & move on
        print("%s) %s // %s" % (len(data['tagged'])+1, doc['fb_date'],doc['fb_tags']))
        data['tagged'].append(doc)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".snowliftPager.next"))).click()

        #Save JSON deets
        with open('tagged.json', 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

def download_photos():
    #Prep the download folder
    folder = 'photos/'
    if not os.path.exists(folder):
        os.makedirs(folder)
    print("-"*20 + "\nSaving photos to " + folder)
    #Download the photos
    with open('tagged.json') as json_file:
        data = json.load(json_file)
        for i,d in enumerate(data['tagged']):
            if d['media_type'] == 'image':
                #Save new file
                filename_date = parse(d['fb_date']).strftime("%Y-%m-%d")
                img_id = d['media_url'].split('_')[1]
                new_filename = folder + filename_date + '_' + img_id + '.jpg'
                if os.path.exists(new_filename):
                    print("-"*20 + "\nFile Exists, Skipping: %s" % (new_filename))
                else:
                    img_file = wget.download(d['media_url'], new_filename, False)

                    #Update EXIF Date Created
                    exif_dict = piexif.load(img_file)
                    exif_date = parse(d['fb_date']).strftime("%Y:%m:%d %H:%M:%S")
                    img_desc = d['fb_caption'] + '\n' + d['fb_tags'] + '\n' + d['fb_url'].split("&")[0]
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
                    exif_dict['0th'][piexif.ImageIFD.Copyright] = (d['user_name'] + ' (' + d['user_url']) + ')'
                    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = img_desc.encode('utf-8')

                    piexif.insert(piexif.dump(exif_dict), img_file)
                    print(str(i+1) + ') Added '+ new_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook Scraper')
    parser.add_argument('-u', type = str,help='FB Username')
    parser.add_argument('-p', type = str,help='FB Password')
    parser.add_argument('--download', action='store_true', help='Download photos')
    parser.add_argument('--index', action='store_true', help='Index photos')
    args = parser.parse_args()
    if args.index:
        index_photos(args.u,args.p)
    if args.download:
        download_photos()
    if not args.index and not args.download:
        index_photos(args.u,args.p)
        download_photos()
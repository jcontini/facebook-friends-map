import argparse, sys, os, time, wget, json, piexif, ssl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from dateutil.parser import parse

def download_photos():
    ssl._create_default_https_context = ssl._create_unverified_context
    #Prep the download folder
    folder = 'photos/'
    if not os.path.exists(folder):
        os.makedirs(folder)
    print('Saving photos to ' + folder)
    #Download the photos
    with open('tagged.json') as json_file:
        data = json.load(json_file)
        for i,d in enumerate(data['tagged']):
            if d['type'] == 'image':
                #Save new file
                filename_date = parse(d['fb_date']).strftime("%Y-%m-%d")
                img_id = d['img_url'].split('_')[1]
                new_filename = folder + filename_date + '_' + img_id + '.jpg'
                img_file = wget.download(d['img_url'], new_filename)

                #Update EXIF Date Created
                exif_dict = piexif.load(img_file)
                exif_date = parse(d['fb_date']).strftime("%Y:%m:%d %H:%M:%S")
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
                piexif.insert(piexif.dump(exif_dict), img_file)
                print('\n' + str(i+1) + ') '+ new_filename +' new date: ' + exif_date)

def main(username, password):
    #Start Browser
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("https://www.facebook.com")

    #Log In
    email_id = driver.find_element_by_id("email")
    pass_id = driver.find_element_by_id("pass")
    email_id.send_keys(username)
    pass_id.send_keys(password)
    driver.find_element_by_id("loginbutton").click()

    #Nav to photos I'm tagged in page
    driver.find_element_by_id("navItem_2305272732").click()
    time.sleep(4)
    driver.find_elements_by_css_selector(".uiMediaThumbImg")[0].click()

    #Prep structure
    data = {}
    data['tagged'] = []
    fb_urls = []
    wait = WebDriverWait(driver, 10)

    while True:
        #Finish up if reached end
        if driver.current_url in fb_urls:
            print('Done!')
            break

        user = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftAuthorName"]/a')))
        doc = {
            'fb_url': driver.current_url,
            'fb_date': wait.until(EC.presence_of_element_located((By.CLASS_NAME, "timestampContent"))).text,
            'fb_caption': wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftCaption"]'))).text,
            'fb_tags': wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftTagList"]'))).text.replace('\u2014 ',''),
            'user_name': user.text,
            'user_url': user.get_attribute('href'),
            'user_id': user.get_attribute('data-hovercard').split('id=')[1].split('&')[0]
        }

        is_video = "showVideo" in driver.find_element_by_css_selector(".stageWrapper").get_attribute("class")
        if is_video:
            doc['type'] = 'video'
        else:
            doc['type'] = 'image'
            doc['img_url'] = wait.until(EC.presence_of_element_located((By.XPATH, "//img[@class = 'spotlight']"))).get_attribute('src')

        #Get album if present
        if len(driver.find_elements_by_xpath('//*[@class="fbPhotoMediaTitleNoFullScreen"]/div/a')) > 0:
            doc['album'] = driver.find_element_by_xpath('//*[@class="fbPhotoMediaTitleNoFullScreen"]/div/a').get_attribute('href')

        #Get Deets & move on
        print(doc)
        fb_urls.append(doc['fb_url'])
        data['tagged'].append(doc)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".snowliftPager.next"))).click()

    #Save JSON of deets
    with open('tagged.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

    #Now download the photos!
    download_photos()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook Scraper')
    parser.add_argument('-u', type = str,help='FB Username')
    parser.add_argument('-p', type = str,help='FB Password')
    parser.add_argument('--download', action='store_true', help='Download photos')
    args = parser.parse_args()
    if args.download:
        download_photos()
    else:
        main(args.u,args.p)
import argparse, sys, time, csv, wget
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    #Get Photo URLs
    photo_urls = []
    photos = []

    while True:
        time.sleep(1)
        photo = {
            'img_url': driver.find_element_by_xpath("//img[@class = 'spotlight']").get_attribute('src'),
            'img_date': driver.find_element_by_xpath('//*[@id="fbPhotoSnowliftTimestamp"]/a[1]/abbr/span').text,
        }
        
        if photo['img_url'] in photo_urls:
            break

        else:
            print(photo)
            photos.append(photo)
            photo_urls.append(photo['img_url'])
            driver.find_element_by_xpath('//*[@id="facebook"]/body').send_keys(u'\ue014')

    #Download the photos & save an index of them to CSV
    writer = csv.writer(open('photo_urls.csv', 'wb'))
    for photo in photos:
        writer.writerow([photo['img_url'],photo['img_date']])
        dl = wget.download(photo['img_url'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', type = str,default = "NONE")
    parser.add_argument('-p', type = str,default = "NONE")
    args = parser.parse_args()
    main(args.u,args.p)
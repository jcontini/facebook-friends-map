import argparse, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
    #Nav to photos I'm tagged in
    driver.find_element_by_id("navItem_2305272732").click()
    time.sleep(3)
    driver.find_elements_by_css_selector(".uiMediaThumbImg")[0].click()
    #Get Photo URLs
    photo_urls = []
    while True:
        time.sleep(1)
        img_url = driver.find_element_by_xpath("//img[@class = 'spotlight']").get_attribute('src')
        if img_url in photo_urls:
            break
        else:
            photo_urls.append(img_url)
            print(img_url)
            driver.find_element_by_css_selector(".snowliftPager.next").click()
    #Save Photo URLs to CSV
    fd = open('photo_urls.csv','w')
    for photo_url in photo_urls:
        fd.write(photo_url)
    fd.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', type = str,default = "NONE")
    parser.add_argument('-p', type = str,default = "NONE")
    args = parser.parse_args()
    main(args.u,args.p)
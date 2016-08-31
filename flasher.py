import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from lxml import html
from lxml.html.soupparser import fromstring
from decimal import Decimal
import requests


class FlashStealer(object):
    def __init__(self, url, day):
        self.url = url
        self.day = day
    def init_driver(self):
        driver = webdriver.Firefox()
        driver.wait = WebDriverWait(driver, 5)
        return driver

    def lookup(self, driver):
        driver.get(self.url)
        try:
            # driver.implicitly_wait(2)
            hide_solds = driver.wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_ctl02_hideSold")))
            hide_solds.click()
        except TimeoutException:
            print("hide solds not loaded")
        try:
            view_all = driver.wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_ctl02_fsPagerTop_viewAllHyperLink")))
            view_all.click()
        except TimeoutException:
            print("view all not loaded")
        try:
            listing_table = driver.wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_ctl02_dgOfferListing")))
            hhtml = listing_table.get_attribute('innerHTML')
            return hhtml
        except TimeoutException:
            print("elements not found in page")

    def parsehtml(self, text):
        table = html.fromstring(text)

        rows = iter(table)
        headers = [col.text for col in next(rows)]
        headers = ['neighborhood', 'section', 'row', 'qty', 'price', 'notes']
        data = []
        for row in rows:
            # values = [col.text for col in row]
            values = []
            for col in row:
                coltext = col.text
                if coltext is not None:
                    if '$' in str(coltext):
                        coltext = Decimal(str(coltext).replace('$', ''))
                    values.append(coltext)
                else:
                    links = col.iterlinks()
                    for link in links:
                        try:
                            if 'Purchase' in link[2]:
                                values.append("https://www.flashseats.com/" + link[2])
                        except KeyError, e:
                            print "you're a retard"  
            data.append(dict(zip(headers, values)))
        print data
        return data

    def analyizeHtml(self, parsed):
        messages = ''
        for row in parsed:
            if row['price'] <= 100.00:
                # action area
                print "you should nab these bro"
                print row
                messages += """$%s - %s. <a href="%s">Buy here</a></br>""" % (row['price'], row['section'], row['notes'])

            elif row['price'] <= 130.00:
                print "these are luke warm"
                print row
        self.sendAlert(messages)

    def sendAlert(self, messages, **kwargs):
        headmessage = """
            <b>Tickets found for %s.</b></br>
        """ % (self.day)

        htmlmessage = headmessage + messages
        url = "https://boojers.hipchat.com/v2/room/3074083/notification?auth_token=xCLOriv4dBz0A7zqHBsBXDPveeZAmgbTvxsHhs9z"
        data = {
            'message': htmlmessage,
            'notify': "false",
            'color': kwargs.get('color', 'yellow')
        }
        requests.post(url, data=data)

    def run(self):
        driver = self.init_driver()
        table = self.lookup(driver)
        # time.sleep(2)
        driver.quit()
        parsed_html = self.parsehtml(table)
        analyizedHtml = self.analyizeHtml(parsed_html)

if __name__ == "__main__":
    urls = [
        ("https://www.flashseats.com/Default.aspx?pid=18&ec=9000000000014534&ss=0&fss=394317986", "Friday"),
        ("https://www.flashseats.com/Default.aspx?pid=18&ec=9000000000014535&ss=0&fss=1624262930", "Saturday"),
        ("https://www.flashseats.com/Default.aspx?pid=18&ec=9000000000014536&ss=0&fss=1697239191", "Sunday")
    ]

    for url, day in urls:
        fs = FlashStealer(url, day)
        fs.run()

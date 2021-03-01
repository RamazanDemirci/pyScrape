import json
import requests
#from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import pandas as pd
import os


def get_tff_fixture():
    # headers = {'User-Agent':
    #           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
    #page = "https://www.tff.org/default.aspx?pageID=322"
    #pageTree = requests.get(page, headers=headers)
    #pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    # launch url
    url = "http://kanview.ks.gov/PayRates/PayRates_Agency.aspx"

    # create a new Firefox session
    driver = webdriver.Firefox()
    driver.implicitly_wait(30)
    driver.get(url)

    python_button = driver.find_element_by_id(
        'MainContent_uxLevel1_Agencies_uxAgencyBtn_33')  # FHSU
    python_button.click()  # click fhsu link

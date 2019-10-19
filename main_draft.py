import os, pandas as pd, requests, warnings, html2text
from bs4 import BeautifulSoup as bs4
from cleaner import Address_Cleaning_Module
warnings.filterwarnings("ignore")

import os, csv, warnings
import numpy as np, pandas as pd
import requests, urllib
from bs4 import BeautifulSoup

os.path("E:\Real-Estate")

# Address Cleanup  Begin **********************
from cleaner import Address_Cleaning_Module, One_Line_Address, Prop_Desc_Cleaner
fields = ['address', 'address: Street 1', 'location', 'address: State', 'address: Zip','description']
header = ['Bldg','Street', 'City', 'State', 'Zip','Desc']
#header2 = ['Street', 'City', 'State', 'Zip']
header2 = ['Street', 'City', 'State', 'Zip']
wordDic = {'City of': '', 'Own': '', 'own': '', 'Com':'', 'com':'', '<br />':'',
            'Alberta' : 'AB', 'British Columbia' :'BC', 'Manitoba':'MB',
            'New Brunswick': 'NB', 'Newfoundland and Labrador': 'NL',
            'Nova Scotia': 'NS', 'Northwest Territories': 'NT',
            'Nunavut': 'NU', 'Ontario':'ON', 'Prince Edward Island': 'PEI',
            'Quebec': 'QC', 'Saskatchewan': 'SK', 'Yukon': 'YT'
            } # The dictionary has target_word : replacement_word pairs

Address =[]
df1 = pd.read_csv('properties_temp.csv', encoding="ISO-8859-1", usecols=fields)
#df1 = pd.read_csv('properties.csv', encoding='utf-8', usecols=fields)
df1 = df1.fillna('') # Replace 'NaN' or 'NA' values with Space
#df1 = df1.head(10)
df1 = df1.rename(columns={'address':'Bldg','address: Street 1':'Street','location':'City', 'address: State':'State','address: Zip':'Zip', 'description' : 'Desc'})
df1 = Address_Cleaning_Module(header, df1, wordDic) # Data Cleaning
df1, Address = One_Line_Address(df1, header2)

raw_sentence = Prop_Desc_Cleaner(df1)
# Address Cleanup  End **********************


for address in addresses: 
    html_content = requests.get("https://www.bing.ca/search?&q="+str(address)).text
    soup = bs4(html_content, "lxml")
    for li in soup.findAll('li', attrs={'class':'b_algo'}):
        html_content = requests.get(li.find('a').get("href")).text
        txt = html2text.HTML2Text().handle(html_content)
        
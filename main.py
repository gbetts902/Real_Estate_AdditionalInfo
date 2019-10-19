from cleaner import Address_Cleaning_Module, One_Line_Address, CA_PostCode_Validator#, Prop_Desc_Cleaner
import pandas as pd, re, csv, itertools, requests, warnings, html2text#, sqlite3
import dateutil.parser as dparser
from email.utils import parseaddr
from tr4w import TextRank4Keyword
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

fields = ['address', 'address: Street 1', 'location', 'address: State', 'address: Zip','description']
header = ['Bldg','Street', 'City', 'State', 'Zip','Desc']
header2 = ['Street', 'City', 'State', 'Zip']
wordDic = {'City of': '', 'Own': '', 'own': '', 'Com':'', 'com':'', '<br />':'',
           'nan':'', 'NONE':'', 'ood':'',
            'Alberta' : 'AB', 'British Columbia' :'BC', 'Manitoba':'MB',
            'New Brunswick': 'NB', 'Newfoundland and Labrador': 'NL',
            'Nova Scotia': 'NS', 'Northwest Territories': 'NT',
            'Nunavut': 'NU', 'Ontario':'ON', 'Prince Edward Island': 'PEI',
            'Quebec': 'QC', 'Saskatchewan': 'SK', 'Yukon': 'YT'
            } # The dictionary has target_word : replacement_word pairs

'''
conn = sqlite3.connect("properties_db.sqlite3")
c = conn.cursor()
c.execute("""
          CREATE TABLE IF NOT EXISTS listings (record_index PRIMARY KEY, textual_summaries text, sub_links text)
          """)
'''

with open("properties_new_rawinfo.csv", "a+", newline="", encoding="utf-8") as fp:
    csv.writer(fp).writerow(['Record_No', 'Raw_Important_Extracted_Info', 'Sublinks'])
            
with open("properties_new_clean.csv", "a+", newline="", encoding="utf-8") as fp:
    csv.writer(fp).writerow(['Record_No', 'Clean_Address', 'Description', 'Vacancy_Space', 'Acreage', 
                             'Space_Type', 'Rent', 'CAM_Tax', 'Total_Price', 'Sale_Or_Lease', 
                             'Class', 'Status', 'Availability', 'Email', 'Phone_Number', 
                             'Owner_Name', 'Tenants', 'Listing_Links', 'Summarized_Abstractive_Idea'])
    
df = pd.read_csv('properties.csv', encoding="ISO-8859-1")
df = df.rename(columns={'address':'Bldg','address: Street 1':'Street','location':'City', 'address: State':'State','address: Zip':'Zip', 'description' : 'Desc'})

for index, row in df.iterrows():
                
    print("\nAnalyzing Record " + str(index))
    
    sentence_outputs, full_text_outputs = [], []    
    
    record = pd.DataFrame(row).T
    
    df['Zip'][index] = CA_PostCode_Validator(row['Zip'])
    record = Address_Cleaning_Module(header, record, wordDic); record = One_Line_Address(record, header2)[0]
    #record['Clean_Desc'] = Prop_Desc_Cleaner(record)
                
    summaries, sub_links = [], []
    
    address = str(record['Clean_Address'].values[0]).replace(" ", "%20")
    
    html_content = requests.get("https://www.bing.ca/search?&q=" + address).text
    soup = BeautifulSoup(html_content, "lxml")
    
    for li in soup.findAll('li', attrs={'class':'b_algo'}):
        
        sub_link = li.find('a').get("href")
        
        print("\n^^^ Analyzing Sublink " + str(sub_link))
        
        try:
                
            sub_html_content = requests.get(sub_link).text
            
            h = html2text.HTML2Text()
            h.ignore_links = True; h.ignore_images = True
            txt = h.handle(sub_html_content)
            
            txt_to_compare, record_to_compare = [], []
            
            r_i = record.iloc[0]; 
            record_df = [r_i['address: Latitude'], r_i['address: Longitude'], r_i['vac_space'],
                         r_i['unit'], r_i['type'], r_i['class'], r_i['gla'], r_i['acreage'], 
                         r_i['status'], r_i['availability'], r_i['for_sale_or_lease'], r_i['net_rent'],
                         r_i['sales_price'], r_i['price'], r_i['cam_tax'], r_i['total_additional_rent'], 
                         r_i['operating_costs'], r_i['contact'], r_i['phone'], r_i['email'],
                         r_i['owner'], r_i['owner: First'], r_i['owner: Last'], r_i['tenants'], 
                         r_i['Clean_Address'], r_i['Desc'][0]]
            for element in record_df: [ record_to_compare.append(e) for e in str(element).split(" ") ]
            record_to_compare = [x for x in record_to_compare if x != 'nan']

            text_scraped = list(filter(lambda a: a != "", txt.split(" ")))
            text_scraped = [ re.sub(r'\B(?=[A-Z])', r' ', re.sub('[^A-Za-z0-9/\- @.+$()]', '', e)) for e in text_scraped ]
            for element in text_scraped: [ txt_to_compare.append(e) for e in str(element).split(" ") ]
            txt_to_compare = [x for x in txt_to_compare if x != '' and x != '\n']
            
            if len(set(record_to_compare) & set(txt_to_compare))/len(record_to_compare) > 0.25:
                
                print("*********************** Similarity Exists ***********************")
                
                to_summarize = " ".join(txt_to_compare)
                
                tr4w = TextRank4Keyword()
                tr4w.analyze(to_summarize, candidate_pos = ['NOUN', 'PROPN'], window_size=4, lower=False)
                keywords, probabilities = tr4w.get_keywords(35)
                
                for word in range(len(keywords)):
                    try:
                        idx = txt_to_compare.index(keywords[word])
                        if any(i.isdigit() for i in txt_to_compare[idx-1]): keywords[word] = txt_to_compare[idx-1] + " " + keywords[word]
                        if any(i.isdigit() for i in txt_to_compare[idx+1]): keywords[word] = keywords[word] + " " + txt_to_compare[idx+1]
                    except: pass
                
                summary = list(set(filter((None).__ne__, [ word.capitalize() if len(word) != 1 else None for word in keywords ])))                         
                
                print("### "+str(summary)+" ###")
                
                summaries.append(summary); sub_links.append(sub_link)
                
        except: pass       
        
    if sub_links != []:
            
        r_i = record.iloc[0]; 
        with open("properties_new_rawinfo.csv", "a+", newline="", encoding="utf-8") as fp:
            csv.writer(fp).writerow([r_i['Record_No'], summaries, sub_links])
        
        #not able to recognize tenants, owner name
        vac_space, acreage, space_type, rent, cam_tax, price, sale_or_lease, class_str, status, availability, email, phone_number = "", "", "", "", "", "", "", "", "", "", "", ""
        for word in list(itertools.chain.from_iterable(summaries)):
            if vac_space == "": vac_space = word if any(substring in word.lower() for substring in ["square", "sq", "feet", "ft", "meter"]) and any(i.isdigit() for i in word) else ""
            if acreage == "": acreage = word if any(substring in word.lower() for substring in ["acre", "ac", "hectare", "ha"]) and any(i.isdigit() for i in word) else ""
            if space_type == "": 
                if word.lower().find("office") != -1: space_type = "Office"
                if word.lower().find("retail") != -1: space_type = "Retail"
                if word.lower().find("industrial") != -1: space_type = "Industrial"
                if word.lower().find("land") != -1: space_type = "Land"
                if word.lower().find("multifamily") != -1: space_type = "Multifamily"
            if rent == "": rent = word if re.search("$.*/", word.lower()) and any(substring in word.lower() for substring in ["year", "yr", "month", "mo"]) else ""
            if cam_tax == "": cam_tax = word if re.search("$.*/.*sq", word.lower()) and any(substring in word.lower() for substring in ["year", "yr", "month", "mo"]) else ""
            if price == "": price = word if re.search(r'[$]\d{5}', word) else ""
            if sale_or_lease == "": 
                if word.lower().find("sale") != -1: sale_or_lease = "Sale"
                if word.lower().find("lease") != -1: sale_or_lease = "Lease"
            if class_str == "": 
                if word.upper() == "A": class_str = "A"
                if word.upper() == "B": class_str = "B"
                if word.upper() == "C": class_str = "C"
            if status == "": 
                if word.lower().find("existing") != -1: status = "Existing"
                if word.lower().find("firmly proposed") != -1: status = "Firmly Proposed"
                if word.lower().find("under construction") != -1: status = "Under Construction"
                if word.lower().find("previously owned") != -1: status = "Previously Owned"
                if word.lower().find("retrofit") != -1: status = "Retrofit"
            if availability == "": 
                if word.lower().find("immediately") != -1: availability = "Immediately"
                try: availability = dparser.parse(word, fuzzy=True).strftime('%m/%d/%Y')
                except: pass
            if email == "": email = parseaddr(word.lower())[1] if '@' in parseaddr(word.lower())[1] and '.' in parseaddr(word.lower())[1] else ""
            if phone_number == "": 
                try: phone_number = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', word.lower())[0]
                except: pass
                
        if vac_space == "": vac_space = r_i['vac_space']
        if acreage == "": acreage = r_i['acreage']
        if space_type == "": space_type = r_i['type']
        if rent == "": rent = r_i['net_rent']
        if cam_tax == "": cam_tax = r_i['cam_tax']
        if price == "": price = r_i['price']
        if sale_or_lease == "": sale_or_lease = r_i['for_sale_or_lease']
        if class_str == "": class_str = r_i['class']
        if status == "": status = r_i['status']
        if availability == "": availability = r_i['availability']
        if email == "": email = r_i['email']
        if phone_number == "": phone_number = r_i['phone']
        owner = r_i['owner']; tenants = r_i['tenants']
        listing_links = sub_links; abstractive_idea = "*TO DO*"
        
        with open("properties_new_clean.csv", "a+", newline="", encoding="utf-8") as fp:
            csv.writer(fp).writerow([r_i['Record_No'], r_i['Clean_Address'], r_i['Desc'], 
                                     vac_space, acreage, space_type, rent, cam_tax, price, 
                                     sale_or_lease, class_str, status, availability, email, 
                                     phone_number, owner, tenants, listing_links, abstractive_idea])
        
        '''
        conn = sqlite3.connect("properties_db.sqlite3")
        sql = """ INSERT INTO listings (record_index, textual_summaries, sub_links) VALUES (?,?,?,?) """
        c = conn.cursor()
        c.execute(sql, (r_i['Record_No'], textual_summaries, sub_links))
        '''
'''
cur = conn.cursor()
cur.execute("SELECT * FROM listings")
for row in cur.fetchall(): print(row)
'''
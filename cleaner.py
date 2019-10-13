import re, pandas as pd
from nltk import tokenize
#header = ['Bldg','Street', 'City', 'State', 'Zip']
#wordDic = {'City of': '', 'Own': '', 'own': '', 'Com':'', 'com':'', '<br />':''} # The dictionary has target_word : replacement_word pairs 

# Start of Data Cleaning Functions ###############
def Add_Space_After_Capitalized_Char(s):
    return  re.sub(r'\B(?=[A-Z])', r' ', s) # ILoveYou" ---> "I Love You"

def Multi_Word_Replace(text, wordDic):
    p = re.compile('|'.join(map(re.escape, wordDic)))
    def translate(match):
        return wordDic[match.group(0)]
    return (p.sub(translate, str(text)))

def Remove_Control_Characters(s): # \xa0
    return re.sub(r'\\x..', '', s)

def Filter_Permited_Characters(s): 
    return re.sub('[^A-Za-z0-9\- ]+', '', s)

def Remove_White_Characters(s):
    return re.sub('\s+', ' ', s).strip()

def CA_PostCode_Validator(Zip):
    Zip = str(Zip).upper()
    if (len(re.findall(r'[A-Z]{1}[0-9]{1}[A-Z]{1}\s*[0-9]{1}[A-Z]{1}[0-9]{1}',Zip)))==1:
        Zip = re.sub(r" ", "", Zip)
        group_size = 3
        Zip = re.sub(r'(\w{%d})(?!$)' % group_size, r'\1 ', Zip)
        #print("Valid", Zip)
        return(Zip)
    else:
        #print("invalid")
        return("NONE")

#pin = CA_PostCode_Validator('V3V7S5')
#pin = CA_PostCode_Validator('l3t1x5')
#pin = CA_PostCode_Validator('3t1x25')




def Address_Cleaning_Module(header, df, wordDic): # Remove unwanted wrods, charcaters, white spaces, Add Spaces where needed
    for field in header:
        for i in range(len(df)):
            #print (i,len(df),df['City'].iloc[i]  )
            #print(df.iloc[i])
            row = df.iloc[i]
            if row['Bldg'] == "":
                row['Bldg'] =  "NONE"
                row['Bldg'] =  Add_Space_After_Capitalized_Char(row['City']) # ILoveYou" ---> "I Love You"
            if row['City'] == "":
                row['City'] =  "NONE"
                row['City'] =  Add_Space_After_Capitalized_Char(str(row['City'])) # ILoveYou" ---> "I Love You"
            if row['Zip'] == "":
                row['Zip'] = "NONE"
                row['Zip'] = CA_PostCode_Validator(str(row['Zip']))
            row[field] = Multi_Word_Replace(str(row[field]), wordDic) # Replace unwanted words
            row[field] = Remove_Control_Characters(str(row[field])) # Removing \xa0
            row[field] = Filter_Permited_Characters(str(row[field])) # Removing Unnecessary charcaters
            row[field] = Remove_White_Characters(str(row[field])) # Remove leading and traling White Spaces
        
    return(df)
#df1 = Address_Cleaning_Module(header, df1, wordDic)

# Merging Address Fields and Removing Repeat Occrances
# Replacing Zip, State and City in Street Address


# Description Filed Cleaner
def Prop_Desc_Cleaner(df):
    Desc_Lst = []
    for i, row in df.iterrows():
    #for i in range(len(df)):
        p = df['Desc'][i]
        p = re.sub(r"<br />", "", p)
        p = re.sub(r"\xa0", "", p)
        p = re.sub(r"  ", "", p)
        #p = re.sub('[^A-Za-z0-9$%!?.,/\- ]+', '', p)
        p = re.sub('[^A-Za-z0-9$%!? @.]+', '', p)
        if (p == "" or p == 'Page Not Found'):
            p = "none"
        p = tokenize.sent_tokenize(p)
        Desc_Lst.append(p)
    return(Desc_Lst)



def One_Line_Address(df1, header2):
    df2 = pd.DataFrame()
    #df2 = df2.reindex(columns=header2)
    df2['Street'] = df1['Street'].replace(df1['Zip'],'', regex = True)
    df2['Street'] = df2['Street'].replace(df1['State'],'', regex = True)
    df2['Street']  = df2['Street'].replace(df1['City'],'', regex = True)
    
    # Replacing Zip, State and City and Street Address from Building Field
    #Bldg = df1['Bldg'].replace(df1['Zip'],'', regex = True)
    #Bldg  = Bldg.replace(df1['State'],'', regex = True)
    #Bldg  = Bldg.replace(df1['City'],'', regex = True)
    #Bldg  = Bldg.replace('DeltaSurreyLangley','', regex = True)
    #Bldg  = Bldg.replace('BurnabyNew Westminster','', regex = True)
    #df2['Bldg']  = Bldg.replace(df2['Street'],'', regex = True)
    df2['Bldg'] = ""
    df2['City'] = df1['City']
    df2['State'] = df1['State']
    df2['Zip']  = df1['Zip']
    df2['Address'] = df2[header2].apply(lambda x: ' '.join(x), axis=1)
    df2['Address'] = df2['Address'].map(lambda x: x.strip()) # Remove Leading Trailing Spaces
    df2['Record'] = df2.index
    df1["Clean_Address"] = df2['Address']
    df1["Record_No"] = df2['Record']
    return(df1, df2.values.tolist())
    








# End of Data Cleaning Functions ###############

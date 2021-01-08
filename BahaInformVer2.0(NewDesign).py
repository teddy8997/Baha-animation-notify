#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
from datetime import datetime
import time
import re
import warnings
import urllib.request
import csv
import schedule
import time
import threading
import os
warnings.filterwarnings("ignore")


# In[2]:

#主要是獲得傳入的url的回應，怕遇到403 error這種情形所以加入header
def get_html(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0')
    response = urllib.request.urlopen(req)
    html = response.read()
    return html


# In[3]:

#主要是將更新訊息推播至自己的line notify上
def lineNotify(token, msg):
    headers = {
        "Authorization": "Bearer " + token, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    return r.status_code


# In[4]:

#利用beautiful soup找尋巴哈動畫瘋 動畫的url,動畫名,動畫更新日,動畫集數 並且將這些資訊利用panda套件存成Dataframe
def product_df(req_bs):
    url = "https://ani.gamer.com.tw/"
    req_bs = bs(get_html(url), "html.parser")
    list_new = req_bs.find(class_ = "newanime-wrap timeline-ver").findAll(class_ = re.compile(r"anime-content-block"))
    output = []
    for i in range(len(list_new)-5):
        title = list_new[i].find(class_ = "anime-name_for-marquee").text
        url = list_new[i].find(class_ = "anime-card-block").get("href")
        try:
            episode = list_new[i].find(class_ = "anime-episode").find('p').text
        except AttributeError :
            episode = list_new[i].find(class_ = "label-edition color-OVA").text
        finally:
            output.append({
                "title" : title,
                "url" : url,
                "episode" : episode
            })
    df = pd.DataFrame(output)
    return df


# In[5]:


def jb():
    url = "https://ani.gamer.com.tw/"
    req_bs = bs(get_html(url), "html.parser") #利用beautiful soup把抓下來的網站排版
    d = product_df(req_bs) #將排版好的網站透過product_df篩選想要的資料產生data frame表

    b = pd.read_csv("baha2.csv", header=0).head().to_dict() #讀取前一次的csv並轉成dict類型和新抓取的資料做比對，這邊比對前五個動畫有無更新，若有更新將message跟token傳到lineNotify
    
    i = 0;
    for new_title in d['title'][0:6]:
        if new_title == b['title'][0]:
            break
        else:
            msg = "[巴哈姆特動畫瘋] "+ new_title + " " + d['episode'][i] + " " + "https://ani.gamer.com.tw/" + d['url'][i]
            token = '填入自己的token'
            lineNotify(token, msg)
        i = i + 1
    d.to_csv("baha2.csv") #更新這次抓的資料存成csv


# In[6]:

#因為第一次執行沒有bahacsv這個檔案所以我們要先做初始化，先去抓一次網站並產生baha.csv
def iniCsv():
    url = "https://ani.gamer.com.tw/"
    req_bs = bs(get_html(url), "html.parser")
    inti_d = product_df(req_bs)
    inti_d.to_csv("baha2.csv")


# In[7]:

#檢查有沒有baha.csv這個檔案，有的話就執行jb進行抓取網站並比對有無動畫更新，沒有的話就利用iniCsv初始化baha.csv
def check_Csv():
    filepath = "自己的路徑/baha2.csv"
    if os.path.isfile(filepath):
        jb()
    else:
        iniCsv()


# In[ ]:

#利用schedule套件讓這個程式每一個小時執行一次
schedule.every().hour.do(check_Csv)
while True:
    schedule.run_pending()
    time.sleep(1)


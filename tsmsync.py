import os
import subprocess
import re
import pymysql
import time
import datetime
import traceback
import json
idlist = []
nameList=[]
host="localhost"
user="root"
password="Abc123"
database="wowclassic"


def saveAuctionHistory(itemId,minPrice,avePrice,auctionNum,quanlity,scanTime):
    db = pymysql.connect(host=host,user=user,password=password,database=database,charset="utf8")
    cursor = db.cursor()
    try:
       data=(itemId,minPrice,avePrice,auctionNum,quanlity,scanTime,datetime.datetime.now())
       cursor.execute("insert into auction_history (item_id,min_price,ave_price,auction_num,quanlity,scan_time,add_time) values( %s,%s,%s,%s,%s,%s,%s)",data)
       db.commit()
    except Exception as exc:
       print ("EXCEPTION", exc)
       db.rollback()
    db.close()


def getcsvAuctionDBScan():
    
    file = open("E:\\pyworkspace\\tsmsync\\TradeSkillMaster.lua",encoding='utf-8')
    itemStrings =""
    findStart =False
    findEnd =False
    while 1:
        line = file.readline()
        if not line:
            break
        if line.find("itemString,minBuyout,marketValue") >0  or findStart==True:
           findStart =True 
           itemStrings = itemStrings+line.replace("i:","")

        if line.find("\",") >0  and  findStart==True:
           findEnd=True 
        if findEnd==True:
            break      
    itemStrings  = itemStrings.replace("\",","").split("\\n")
    #i:10035,288299,288299,5,5,1611557659
    #tem_id,min_price,ave_price,auction_num,quanlity,scan_time,is_del
    for s in itemStrings :
        if s.find("lastScan") <0 :
            auctionHistory = s.split(",")
            itemId= auctionHistory[0]
            minPrice= auctionHistory[1]
            avePrice= auctionHistory[2]
            auctionNum= auctionHistory[3]
            quanlity= auctionHistory[4]
            scanTime= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(auctionHistory[5])))
            saveAuctionHistory(itemId,minPrice,avePrice,auctionNum,quanlity,scanTime)

def initItemString():
    file = open("E:\\pyworkspace\\tsmsync\\TradeSkillMaster.lua",encoding='utf-8')
    itemStrings =""
    findStart =False
    findEnd =False
    while 1:
        line = file.readline()
        if not line:
            break
        if line.find("itemStrings") >0  or findStart==True:
           findStart =True 
           itemStrings = itemStrings+line
           #itemStrings =line[line.find("itemStrings"):500]
        if line.find("}") >0  and  findStart==True:
           findEnd=True 
        if findEnd==True:
            break   
        #print(itemStrings)    

def getItemId():
    file = open("E:\\pyworkspace\\tsmsync\\TradeSkillMaster.lua",encoding='utf-8')
    itemStrings =""
    findStart =False
    findEnd =False
    while 1:
        line = file.readline()
        if not line:
            break
        if line.find("itemStrings") >0  or findStart==True:
           findStart =True 
           itemStrings = itemStrings+line
        if line.find("}") >0  and  findStart==True:
           findEnd=True 
        if findEnd==True:
            break  

    it = re.finditer(r"\"(i.*?)\",", itemStrings) 
    for match in it: 
        strlist  = match.group(1).split("\x02")
        for s in strlist :
           idlist.append(s.replace("i:",""))

def getItemName():
    file = open("E:\\pyworkspace\\tsmsync\\TradeSkillMaster.lua",encoding='utf-8')
    itemStrings =""
    findStart =False
    findEnd =False
    while 1:
        line = file.readline()
        if not line:
            break
        if line.find("names") >0  or findStart==True:
           findStart =True 
           itemStrings = itemStrings+line
        if line.find("}") >0  and  findStart==True:
           findEnd=True 
        if findEnd==True:
            break  
    it = re.finditer(r"\"(.*?)\",", itemStrings) 
    for match in it: 
        strlist  = match.group(1).split("\x02")
        for s in strlist :
           nameList.append(s.replace("i:",""))

def getItemIdName():
    getItemId()
    getItemName()
    i=0;
    for strs in idlist:
        print(strs)
        i=i+1



def getItemDetail(item_id):
    from urllib.request import urlopen
    html = urlopen("https://www.scarlet5.com/mini/classicDB/getItemDetail?itemId="+str(item_id))
    content = html.read().decode('utf-8')
    jsonData = json.loads(content)
    if  ("result"  in  jsonData) : 
        name = jsonData["result"]["name"]
        locales_name = jsonData["result"]["localesName"]
        pinyin_name = jsonData["result"]["pinyinName"]
        locales_desc = jsonData["result"]["localesDescription"]
        item_class = jsonData["result"]["itemClass"]
        sub_class = jsonData["result"]["subClass"]
        item_level = jsonData["result"]["itemLevel"]
        icon = jsonData["result"]["icon"]
        quality = jsonData["result"]["quality"]
        inventory_type = jsonData["result"]["inventoryType"]
        saveItemDetail(item_id,name,locales_name,pinyin_name,locales_desc,item_class,sub_class,item_level,icon,quality,inventory_type)

def saveItemDetail(item_id,name,locales_name,pinyin_name,locales_desc,item_class,sub_class,item_level,icon,quality,inventory_type):
    db = pymysql.connect(host=host,user=user,password=password,database=database,charset="utf8")
    cursor = db.cursor()
    try:
       param=(name,locales_name,pinyin_name,locales_desc,item_class,sub_class,item_level,icon,quality,inventory_type,item_id)
       print(param)
       sql_update = "UPDATE `items` SET `name` =%s,`locales_name` = %s,`pinyin_name` = %s,`locales_desc` = %s,`item_class` = %s,`sub_class` = %s,`item_level` =%s,`icon` =%s,`quality` = %s,`inventory_type` =%s WHERE id =%s;"
       cursor.execute(sql_update,param)
       db.commit()
    except Exception as exc:
       print ("EXCEPTION", exc)
       db.rollback()
    db.close()

def refreshItems():
    db = pymysql.connect(host=host,user=user,password=password,database=database,charset="utf8")
    cursor = db.cursor()
    sql = "select id,name from items WHERE NAME ='';"
    row_count = cursor.execute(sql)
    for line in cursor.fetchall():
        getItemDetail(line[0])
    db.close()    

if __name__ == "__main__":
    #getcsvAuctionDBScan()
    refreshItems()

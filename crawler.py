# -*- coding:utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
import redis
import traceback
import datetime
import time
import gc
import sys
import pickle
from selenium import webdriver

if sys.version_info[0] < 3:
    raise Exception("need python3")

import parser

def dumpRatings(ratingList):
    out = open('rating.pkl', 'wb')
    pickle.dump(ratingList, out, pickle.HIGHEST_PROTOCOL)
    out.close()

def tryLoadRatings():
    ret = []
    try:
        pklfile = open('rating.pkl', 'rb')
        try:
            ret = pickle.load(pklfile)
        except:
            pass
        finally:
            pklfile.close()
    except:
        pass
    return ret

firstTime = True
prevRatings = tryLoadRatings()
if len(prevRatings) > 0:
    firstTime = False

r_server = redis.StrictRedis(host='localhost',port=6379,db=1)
redisListName = 'codeforces_rating'

# ircChannel = input('irc channel name? ')
ircChannel = '#icpc'

# WebDriver init
driver = webdriver.PhantomJS('phantomjs')
# end of WebDriver

def GetPageSource(desiredUrl):
    failed = False
    # WebDriver
    print("launching phantomjs for checking " + desiredUrl)
    try:
        for trial in range(0,3):
            try:
                driver.get(desiredUrl)
                if desiredUrl == driver.current_url:
                    break
            except:
                pass
        if desiredUrl != driver.current_url:
            failed = True
            print("can't open url %s (now %s)" % (desiredUrl,driver.current_url))
            return None
        source = driver.page_source
    except Exception as e:
        failed = True
        print("Exception: %s" % e)
        traceback.print_exc()
    #end of WebDriver

    if failed:
        return None

    return source

def GetRatings(page):
    url = 'http://codeforces.com/ratings/country/Korea, Republic of/page/' + str(page)
    source = GetPageSource(url)
    return parser.ParseRatingsPage(source)

while True:
    print("[{0}] collect!".format(datetime.datetime.now()))

    ratingList = []
    lastPage = 1
    i = 1
    handleSet = set()
    retry = False

    while i <= lastPage and i <= 10:
        print("[{0}] processing page {1}...".format(datetime.datetime.now(), i))
        try:
            parsed = GetRatings(i)
        except Exception as e:
            retry = True
            print("Exception: %s" % e)
            traceback.print_exc()
            break
        for (_, handle, _, _) in parsed['ratings']:
            if handle in handleSet:
                retry = True
                break
            handleSet.add(handle)

        if retry:
            break
        ratingList += parsed['ratings']
        lastPage = parsed['lastpage']
        i += 1

    if retry:
        print("retrying: duplicated handle")
        time.sleep(60)
        continue

    if not firstTime:
        prevMap={}
        for v in prevRatings:
            prevMap[v[1]] = v
        for v in ratingList:
            if v[1] not in prevMap:
                irc_message = "[Codeforces]\x0303 {0} at #{1} with {2}. (count: {3})".format(v[1], v[0], v[3], v[2])
            else:
                if v[2] == prevMap[v[1]][2]:
                    continue
                prevRating = int(prevMap[v[1]][3])
                newRating = int(v[3])
                if prevRating <= newRating:
                    sign = "\x0307+"
                else:
                    sign = "\x0304-"
                irc_message = "[Codeforces] {0} at #{1} with {4} -> \x0303 {2}\x0f ({5}). (count: {3})".format(
                    v[1], # id {0}
                    v[0], # rank {1}
                    v[3], # rating {2}
                    v[2], # count {3}
                    prevRating, # {4}
                    "{0}{1}\x0f".format(sign, abs(newRating - prevRating)) # {5}
                    )
            irc_channel = ircChannel

            msg = irc_channel + ' ' + irc_message
            print(msg)
            r_server.rpush(redisListName, msg)
        r_server.publish('irc-feed', redisListName)
    # end of firstTime check
    print ("finished")
    prevRatings = ratingList
    dumpRatings(ratingList)
    print ("dumped")
    firstTime = False

    if driver is not None:
        driver.quit()
        driver=None
        gc.collect()
    time.sleep(60*10)
    driver = webdriver.PhantomJS('phantomjs')




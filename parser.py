# -*- coding:utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from bs4 import BeautifulSoup
import re

def ParseRatingsPage(page):
    """
    Get ratings page and returns parsed information.
    returns {
        'ratings': [('1\xa0(23)','ainu7','40','3000'), ('-','kcm1700','50','2000'), ...],
        'lastpage': 2
    }
    """
    soup = BeautifulSoup(page)
    trs = soup.find('div', class_='ratingsDatatable').find('table').find_all('tr')
    result = []
    warn = False
    for tr in trs:
        if len(tr.find_all('th')) != 0:
            continue
        if len(tr.find_all('td')) != 4:
            warn = True
            continue
        row = tr.find_all('td')
        rank = row[0].get_text().strip()
        handle = row[1].get_text().strip()
        count = row[2].get_text().strip()
        rating = row[3].get_text().strip()
        result.append((rank, handle, count, rating))

    if warn:
        print ("possible layout change. please check!")

    last = soup.find_all('span', class_='page-index')[-1]
    return {
        'ratings': result,
        'lastpage': int(last['pageindex'])
    }
    return result


# -*- coding: utf-8 -*-
from __future__ import print_function

import random
import time
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

from sendemail import send_email

start_time = time.time()
service_url = "http://alishan.railway.gov.tw/Query/Query3"
status_url = 'http://alishan.railway.gov.tw/Query/QStatus3'

header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/59.0.3071.115 Safari/537.36',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'http://alishan.railway.gov.tw/Query/Query3'
}

data = [('__RequestVerificationToken', ''),
        ('IDNum', 'T22332233'),
        ('PhoneNum', '18112211111'),
        ('BoardDate', '2017/08/13'),
        ('StartStop', '369'),
        ('EndStop', '360'),
        ('TicketNum', '1')]
data = OrderedDict(data)


def query_tickets(origin_stop, dest_stops, session, visited):
    data['StartStop'] = origin_stop
    for stop in dest_stops:
        if stop in visited:
            if time.time() - visited[stop] < 3600:
                continue
            else:
                del visited[stop]
        single_query_stop(origin_stop, stop, session, visited)
        time.sleep(random.randint(10, 20))


def single_query_stop(origin_stop, stop, session, visited):
    r = session.get(service_url)
    soup = BeautifulSoup(r.text, "lxml")
    token = soup.find('input', {'type': 'hidden'})

    data[token['name']] = token['value']

    data['EndStop'] = str(stop)

    s = session.post(service_url, data=data)
    if s.status_code != 200:
        print(origin_stop, '=>', stop, "NOT OK!")
        return

    res_soup = BeautifulSoup(s.text, "lxml")
    result = res_soup.select('body > div.container.body-content')
    tag_h2 = res_soup.find_all('h2')

    if len(tag_h2) > 6:
        seat = BeautifulSoup(str(tag_h2[6]), 'lxml').find('h2').text.strip()
        if seat == u'\u7121\u5ea7\u4f4d':  # 無座位
            # print(origin_stop, '=>', stop, "No seat!")
            pass
        else: # something unexpected, just send the result to see what happened
            visited[stop] = time.time()
            send_email(''.join(str(line) for line in result))
    elif len(tag_h2) == 6:
        print(origin_stop, '=>', stop, "Yes!!!")
        visited[stop] = time.time()
        send_email(''.join(str(line) for line in result))

        if data['TicketNum'] == '2':
            return
        data['TicketNum'] = '2'  # query for 2 tickets, immediately
        single_query_stop(origin_stop, stop, session, visited)
        data['TicketNum'] = '1'


if __name__ == '__main__':
    session = requests.Session()
    session.headers.update(header)

    origin_jiayi = range(369, 362, -1)  # exclude jiayi, beimen, zhuqi
    origin_fenqihu = range(360, 369)  # exclude fenqihu

    debug = 0
    visited = dict()
    while True:
        # query_tickets(origin_stop='369', dest_stops=origin_fenqihu, session=session) # from fenqihu
        query_tickets(origin_stop='360', dest_stops=origin_jiayi, session=session, visited=visited) # from fenqihu
        time.sleep(1200)
        if debug == 1:
            break

    print('Time Elapsed Since Start: ', time.time() - start_time, 's')
    print('Quitting...')
    print('Have fun! Goodbye!')

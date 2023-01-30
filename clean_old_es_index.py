#! /srv/python2/bin/python
# lishaoyan@gmail.com, 2014.

""" clean the old elasticsearch index """

import requests
import os
import re
import sys
import logging
from datetime import datetime, timedelta

ESURL = "http://fluentd:fluentd@localhost:9200"
#INDEX_NAME = ['tomcat', 'tengine', 'redis', 'mysql']
INDEX_NAME = ['tomcat', 'sea', 'mysql', 'tengine', 'app', 'jiasule_cdn']
KEEP_DAYS = 5

# setup logger format and level
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger('')

# request session to keep alive
s = requests.Session()

# care index
reidx = re.compile('(.*?)-(\d+\.\d+\.\d+)')

# old day
OLD_DAY = (datetime.now() - timedelta(KEEP_DAYS)).strftime("%Y.%m.%d")

def get_old_indices():
    r = s.get(ESURL + '/_cat/indices')

    old_indices = []
    for line in r.text.split('\n'):
        cols = line.split()
        if len(cols) < 3: 
            continue

        m = reidx.match(cols[2])
        if m is None: continue

        grs = m.groups()
        if grs[0] in INDEX_NAME and grs[1] < OLD_DAY:
            old_indices.append(cols[2])

    return sorted(old_indices)


def delete_es_index(indexname):
    s.delete('%s/%s/' % (ESURL, indexname))

if  __name__ == '__main__':
    for idx in get_old_indices():
        print("delete old idx: %s" % idx)
        delete_es_index(idx)



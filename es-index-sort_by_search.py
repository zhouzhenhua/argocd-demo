#!/srv/python-3.6.5/bin/python3
# -*- coding:utf-8 -*-
# @Time    : 2019-9-15
# @Author  : zhouzh
# @File    : es-index-sort.py
# @Software: PyCharm

import re
import requests

# settings
es_addr = 'http://192.168.101.155:9200'
es_user = 'elastic'
es_passwd = ''
query_date = '2020.09.10'


def get_es_index_data(es_addr, es_user, es_passwd, query_date):
    url = '{}/_cat/indices/*{}?v&s=store.size:desc'.format(es_addr, query_date)
    r = requests.get(url, auth=(es_user, es_passwd), timeout=10)
    r.raise_for_status()
    return r.text


def main():
    result_list = []
    pri_store_size_sum = 0

    es_result = get_es_index_data(es_addr=es_addr, es_user=es_user, es_passwd=es_passwd, query_date=query_date)
    total_line = re.split(r'\n', es_result)
    for index, line in enumerate(total_line):
        if index == 0:
            title = line
            continue

        # 舍弃标题行 和 空白行
        if index != 0 and line:
            column = line.split()
            size = column[8]
            # store.size排序
            size_kb = handle_size(size)
            obj = {
                'size': size_kb,
                'line': line
            }
            result_list.append(obj)

            # pri.store.size累加
            last_col = handle_size(column[8])
            pri_store_size_sum += last_col

    result_list = sorted(result_list, reverse=True, key=lambda e: e.__getitem__('size'))
    print(title)
    for obj in result_list:
        print(obj['line'])

    # last_line = 'pri.sotre.size.sum:' + str(pri_store_size_sum / 1024 / 1024) + 'gb'
    last_line = 'sotre.size.sum:' + ('%.2f' % (pri_store_size_sum / 1024 / 1024)) + 'gb'
    print(last_line)


def handle_size(size):
    value = float(size[:-2])
    unit = size[-2:]

    if unit == 'gb':
        size_kb = value * 1024 * 1024
    elif unit == 'mb':
        size_kb = value * 1024
    else:
        size_kb = value
    return size_kb


if __name__ == '__main__':
    main()

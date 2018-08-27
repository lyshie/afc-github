#!/usr/bin/env python
# -*- coding: utf-8 -*-

from docx.api import Document
import re
import os
import sys
import csv

'''
[0]游泳3D
[1]1-5年級|（限收40人）
[2]7/30~8/10，共10次|週一~週五 下午15：40~17：00
[3]1580元|網路報名截止後可至學務處報名|截止日期:7/23
[4]游泳池
[5]進學國小游泳團隊
[6]2133007-828
'''


def get_grades(line):
    grades = re.sub(u'[\n\r\s]', '', line)
    matches = re.search(u'(.+)-(.+)年級', grades)

    assert matches, u'cannot match grades: {}'.format(grades)

    if matches:
        if re.search(u'(?:幼|大班)', matches.group(1)):
            result = u'K' + u''.join([str(x)
                for x in range(1, int(matches.group(2)) + 1)])
            return result
        else:
            result = u''.join([str(x) for x in range(
                int(matches.group(1)), int(matches.group(2)) + 1)])
            return result
    else:
        return u''


def get_upbound(line):
    upbound = re.sub(u'[\n\r\s]', '', line)
    matches = re.search(u'(\d+)人', upbound)

    assert matches, u'cannot match upbound: {}'.format(upbound)

    if matches:
        return matches.group(1)
    else:
        return u'15'


def get_cost(line):
    cost = re.sub(u'[\n\r\s]', '', line)
    matches = re.findall(u'(\d+)元', cost)

    assert matches, u'cannot match cost: {}'.format(cost)

    if matches:
        return max([int(x) for x in matches])
    else:
        return u'9999'


def get_datetime(line):
    datetime = re.sub(u'[\n\r\s]', u'', line)
    # print(u'[{}]'.format(datetime))

    ''' date '''
    pat_single = re.compile(u'每週([、一二三四五六日]+)')
    pat_range = re.compile(u'週([一二三四五六日]+)~週([一二三四五六日]+)')

    match_single = pat_single.search(datetime)
    match_range = pat_range.search(datetime)

    week_map = {
            u'一': 1,
            u'二': 2,
            u'三': 3,
            u'四': 4,
            u'五': 5,
            u'六': 6,
            u'日': 7,
            }

    dates = []
    time = ''

    if match_single:
        # print(u'{}'.format(match_single.group(1)))
        ws = match_single.group(1).split(u'、')
        dates = [week_map[x] for x in ws]
    elif match_range:
        #print(u'[{}][{}]'.format(match_range.group(1), match_range.group(2)))
        b = week_map[match_range.group(1)]
        e = week_map[match_range.group(2)]
        dates = range(b, e + 1)
    else:
        assert match_single or match_range, u'cannot match date: {}'.format(
                datetime)

        ''' time '''
    pat_time = re.compile(u'(\d+(?:[:：])\d+)~(\d+(?:[:：])\d+)')
    match_time = pat_time.search(datetime)

    if match_time:
        bt = re.sub(u'[:：]', u'', match_time.group(1))
        et = re.sub(u'[:：]', u'', match_time.group(2))
        time = u'({:0>4}-{:0>4})'.format(bt, et)
    else:
        assert match_time, u'cannot match time: {}'.format(datetime)

    result = ','.join([str(d) + time for d in dates])

    return result


def get_phone(line):
    phone = re.sub(u'[\n\r\s]+', u'、', line)
    phone = re.sub(u'\-', u'#', phone)

    return phone


def get_teacher(line):
    ts = re.split(u'[\n\r]+', line)
    pat = re.compile(u'(.+)[\(（](.+)[）\)]')

    result_teach = []
    result_desc = []

    for x in ts:
        m = pat.search(x)
        if m:
            result_teach.append(m.group(1))
            result_desc.append(m.group(2))
        else:
            result_teach.append(x)

    return (u"、".join(result_teach), u"；".join(result_desc))

def get_lowbound(line):
    result = u'9'

    if re.search(u'(?:琴|合奏|烏克)', line):
        result = u'6'

    return result


def main():
    doc = Document(sys.argv[1])
    table = doc.tables[0]

    items = []

    for i, row in enumerate(table.rows):
        text = (cell.text for cell in row.cells)

        line = [x for x in text]

        grades = get_grades(line[1])
        upbound = get_upbound(line[1])
        lowbound = get_lowbound(line[0])
        datetime = get_datetime(line[2])
        cost = get_cost(line[3])
        phone = get_phone(line[6])
        teach, desc = get_teacher(line[5])

        chunk = {'課程編號': str(i).encode("UTF-8"),
                '課程名稱': re.sub(u'[\n\r\s]', u'', line[0]).encode("UTF-8"),
                '課程敘述': re.sub(u'^[\d\s]+?元', u'', line[3]).encode("UTF-8"),
                '教室': re.sub(u'[\n\r\s]', u'', line[4]).encode("UTF-8"),
                '收費價格': str(cost).encode("UTF-8"),
                '教師': teach.encode("UTF-8"),
                '教師說明': desc.encode("UTF-8"),
                '教師聯絡電話': phone.encode("UTF-8"),
                '開課年級': grades.encode("UTF-8"),
                '下限人數': lowbound.encode("UTF-8"),
                '上限人數': upbound.encode("UTF-8"),
                '上課日期時間': datetime.encode("UTF-8"),
                }

        items.append(chunk)

    keys = re.split(u'[\s]+', "課程編號    課程名稱    課程敘述    教室    收費價格    教師    教師說明    教師聯絡電話    開課年級    下限人數    上限人數    上課日期時間")

    with open("course.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for item in items:
            writer.writerow(item)


if __name__ == '__main__':
    main()

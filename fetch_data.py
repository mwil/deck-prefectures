#! /usr/bin/env python3

import argparse
import json
import regex
import requests

from collections import defaultdict

from bs4 import BeautifulSoup

WIKI_URL = 'https://en.wikipedia.org'
PREF_URL = 'https://en.wikipedia.org/wiki/Prefectures_of_Japan'
CAPS_URL = 'https://en.wikipedia.org/wiki/List_of_capitals_in_Japan'

################################################################################
def superstrip(string):
    del_chars = '¹²³'

    string = regex.sub('|'.join(del_chars), '', string.strip())

    sub_chars = [('ū', 'u'), ('ō', 'o')]

    for schar in sub_chars:
        string = regex.sub(*schar, string)

    return string
################################################################################

################################################################################
def postprocess(result):
    for pref, item in result.items():
        try:
            item['Population'] = int(
                    regex.sub(',', '', item['Population']))
            item['Area'] = float(
                    regex.sub(',', '', item['Area']))
            item['Density'] = float(
                    regex.sub(',', '', item['Density']))
        except KeyError:
            pass

        try:
            item['Pop.'] = int(
                    regex.sub(',', '', item['Pop.']))
        except KeyError:
            pass

    return result
################################################################################

################################################################################
def fetch_prefectures():
    header = []
    result = defaultdict(dict)

    req = requests.get(PREF_URL)

    html = req.content.decode("utf-8")
    soup = BeautifulSoup(html, "html5lib")

    table = soup.select('table.sortable')[0]

    for th in table.find_all('th'):
        header.append(superstrip(th.text))

    curr_pos = 0
    curr_pref = None

    for td in table.find_all('td'):
        text = superstrip(td.text)

        if curr_pos == 0:
            curr_pref = text

        result[curr_pref][header[curr_pos]] = text

        curr_pos += 1
        if curr_pos == len(header):
            curr_pos = 0

    result = postprocess(result)

    with open('data/prefs.json', 'w') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=4)
################################################################################

################################################################################
def fetch_capitals():
    # TODO: Footnote and link of Shinjuku is broken
    #       Some city names appear twice (KobeKobe)
    header = []
    result = defaultdict(dict)

    req = requests.get(CAPS_URL)

    html = req.content.decode("utf-8")
    soup = BeautifulSoup(html, "html5lib")

    table = soup.select('table.sortable')[0]

    for th in table.find_all('th'):
        header.append(superstrip(th.text))

    curr_pos = 0
    curr_pref = None

    for td in table.find_all('td'):
        text = superstrip(td.text)

        if curr_pos == 0:
            curr_pref = text

        result[curr_pref][header[curr_pos]] = text

        for a in td.find_all('a'):
            result[curr_pref][header[curr_pos]+'_a'] = \
                WIKI_URL + a['href']

        curr_pos += 1
        if curr_pos == len(header):
            curr_pos = 0

    result = postprocess(result)

    with open('data/caps.json', 'w') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=4)
################################################################################

################################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--pref", action='store_true')
    parser.add_argument("--caps", action='store_true')

    args = parser.parse_args()

    if args.pref:
        fetch_prefectures()

    if args.caps:
        fetch_capitals()

#! /usr/bin/env python3

# pylint: disable=too-many-locals

'''Generate the Japan SVG deck for Kitsun.'''

import argparse
import csv
import json

from collections import defaultdict
from operator import itemgetter
from pathlib import Path

import genanki
import regex

from SPARQLWrapper import SPARQLWrapper, JSON

from models import PREF_DECK, REG_MODEL, PREF_MODEL

ENDPOINT_URL = 'https://query.wikidata.org/sparql'


###############################################################################
def json_extract(jsdict):
    '''Interpret the Wikidata results.'''

    result = defaultdict(dict)

    keys = jsdict['head']['vars']

    # TODOS: use first hit instead of overwriting in dict

    for line in jsdict['results']['bindings']:
        for key in keys:
            item = line['name_en']['value']

            try:
                value = line[key]['value']
            except KeyError:
                result[item][key] = None
                continue

            if ('datatype' in line[key] and
                    line[key]['datatype'] ==
                    'http://www.w3.org/2001/XMLSchema#decimal'):
                value = float(value)

            if key in result[item] and result[item][key] != value:
                if (isinstance(result[item][key], list) and
                        value not in result[item][key]):
                    result[item][key].append(value)
                else:
                    result[item][key] = [result[item][key], value]
            else:
                result[item][key] = value

    return result
###############################################################################

###############################################################################
def strip_to_name(name):
    '''Replace unnecessary parts of the Wikidata results.'''

    return regex.sub(r'\s+Prefecture|\s+\(?region\)?', '', name)
###############################################################################

###############################################################################
def as_map_id(name):
    '''Aggressively strip everthing that might trip Kitsun.'''

    patterns = [
        ('ū', 'u'),
        ('Ō', 'O'),
        ('ō', 'o')]

    result = strip_to_name(name)

    for pattern in patterns:
        result = regex.sub(*pattern, result)

    return result

###############################################################################
def as_romaji(name):
    '''Replace strange characters coming from Wikipedia.'''

    patterns = [
        ('ū', 'uu'),
        ('Ō', 'Oo'),
        ('ō', 'ou')]

    result = strip_to_name(name)

    for pattern in patterns:
        result = regex.sub(*pattern, result)

    return result

###############################################################################
def all_representations(wiki_name):
    '''Collect all string representations in a single line.'''

    names = [strip_to_name(wiki_name)]

    if as_map_id(names[0]) not in names:
        names.append(as_map_id(names[0]))
    if as_romaji(names[0]) not in names:
        names.append(as_romaji(names[0]))

    return ', '.join(names)

###############################################################################
def fix_urls(dic):
    '''For fields that carry URLs, enclose them with the appropriate tags.'''

    for name, values in dic.items():
        for fieldname, value in values.items():
            if fieldname in ('url_wikipedia', 'url_official'):
                # dic[name][fieldname] = f'<a class="{fieldname}_a" href="{value}" target="_blank">'
                pass
            elif fieldname in ('img_flag', 'img_symbol', 'img_seal', 'img_impression'):
                dic[name][fieldname] = f'<img class="{fieldname}_img" src="{value}" />'

    return dic

###############################################################################

###############################################################################
def process_regions():
    '''
    Collect all information for the regions of Japan.
    '''

    with open('json/prefectures.json', 'r') as infile:
        db_prefs = json.load(infile)

    query = Path('sparql/regions.rq').read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    regions = json_extract(sparql.query().convert())

    # Hokkaido only has a single prefecture, fix to list
    regions['Hokkaidō (region)']['prefecture_en'] = [
        regions['Hokkaidō (region)']['prefecture_en']]

    ###########################################################################
    # Get the information from the prefectures ...
    for region, ritem in regions.items():
        population = 0
        area = 0.0

        ritem['title'] = strip_to_name(ritem['name_en'])
        ritem['name_en'] = all_representations(ritem['name_en'])

        ritem['contained_prefs'] = ', '.join(
            map(strip_to_name, ritem['prefecture_en']))
        ritem['map_ids'] = ', '.join(
            as_map_id(pref) for pref in ritem['prefecture_en'])

        for pref in ritem['prefecture_en']:
            population += db_prefs[pref]['stats_population_f']
            area += db_prefs[pref]['stats_area_f']

        regions[region]['stats_population'] = population
        regions[region]['stats_area'] = area
    ###########################################################################

    ###########################################################################
    regs_by_popu = sorted(regions.values(),
                          key=itemgetter('stats_population'),
                          reverse=True)
    regs_by_area = sorted(regions.values(),
                          key=itemgetter('stats_area'),
                          reverse=True)

    for _, ritem in regions.items():
        ritem['stats_population_density'] = '{:,.2f}'.format(
            ritem['stats_population']/ritem['stats_area'])
        ritem['stats_population_rank'] = list(
            map(itemgetter('name_kanji'), regs_by_popu)).index(
                ritem['name_kanji']) + 1
        ritem['stats_area_rank'] = list(
            map(itemgetter('name_kanji'), regs_by_area)).index(
                as_map_id(ritem['name_kanji'])) + 1

        ritem['index'] = ritem['stats_population_rank'] * 100
        ritem['tags'] = ('Region',)

        ritem['stats_population'] = '{:,d}'.format(int(ritem['stats_population']))
        ritem['stats_area'] = '{:,.2f}'.format(ritem['stats_area'])

        del ritem['prefecture_en']
    ###########################################################################

    ###########################################################################
    # Static fixes
    regions['Hokkaidō (region)']['url_wikipedia'] = 'https://en.wikipedia.org/wiki/Hokkaido'
    regions['Shikoku (region)']['url_wikipedia'] = 'https://en.wikipedia.org/wiki/Shikoku'
    regions['Kyūshū (region)']['url_wikipedia'] = 'https://en.wikipedia.org/wiki/Kyushu'
    ###########################################################################

    with open('json/regions.json', 'w') as outfile:
        json.dump(regions, outfile, ensure_ascii=False, indent=4)

    fieldnames = [
        'index', 'title',
        'name_en', 'name_kanji', 'name_kana',
        'contained_prefs', 'map_ids',
        'stats_population', 'stats_population_density', 'stats_population_rank',
        'stats_area', 'stats_area_rank',
        'url_wikipedia',
        'tags']

    # Write the Anki deck
    for _, fields in regions.items():
        PREF_DECK.add_note(
            genanki.Note(
                model=REG_MODEL,
                fields=[str(fields[fieldname]) for fieldname in fieldnames
                        if fieldname not in ('tags',)],
                tags=fields['tags'],
                guid=fields['index']))

    # Write the CSV file
    with open('csv/regions.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        regions = fix_urls(regions)

        writer.writeheader()
        writer.writerows(sorted(regions.values(), key=itemgetter('index')))
###############################################################################

###############################################################################
def process_prefectures(preprocess=False):
    '''
    Collect all information for the prefectures of Japan.
    '''

    with open('json/regions.json', 'r') as infile:
        db_regs = json.load(infile)

    query = Path('sparql/prefectures.rq').read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    prefectures = json_extract(sparql.query().convert())

    prefs_by_popu = sorted(prefectures.values(),
                           key=itemgetter('stats_population'),
                           reverse=True)
    prefs_by_area = sorted(prefectures.values(),
                           key=itemgetter('stats_area'),
                           reverse=True)

    for _, pitem in prefectures.items():
        reg_index = db_regs[pitem['in_region']]['index']

        pitem['title'] = strip_to_name(pitem['name_en'])
        pitem['map_ids'] = as_map_id(pitem['name_en'])

        pitem['name_en'] = all_representations(pitem['name_en'])
        pitem['in_region'] = strip_to_name(pitem['in_region'])

        pitem['stats_population_f'] = pitem['stats_population']
        pitem['stats_population'] = '{:,d}'.format(int(pitem['stats_population']))

        pitem['stats_area_f'] = pitem['stats_area']
        pitem['stats_area'] = '{:,.2f}'.format(pitem['stats_area'])

        pitem['stats_population_density'] = '{:,.2f}'.format(
            pitem['stats_population_f']/ pitem['stats_area_f'])

        pitem['stats_population_rank'] = list(
            map(itemgetter('name_kanji'), prefs_by_popu)).index(
                as_map_id(pitem['name_kanji'])) + 1
        pitem['stats_area_rank'] = list(
            map(itemgetter('name_kanji'), prefs_by_area)).index(
                as_map_id(pitem['name_kanji'])) + 1

        pitem['index'] = reg_index + pitem['stats_population_rank'] * 2
        pitem['tags'] = ('Prefecture', as_map_id(pitem['in_region']))

    prefectures['Hokkaidō Prefecture']['url_wikipedia'] = 'https://en.wikipedia.org/wiki/Hokkaido'

    with open('json/prefectures.json', 'w') as outfile:
        json.dump(prefectures, outfile, ensure_ascii=False, indent=4)

    if preprocess:
        # We only write the JSON file to fix the indices of the regions while
        # preprocessing the data. Also, we need the stats beforehand.
        return

    fieldnames = [
        'index', 'title',
        'name_en', 'name_kanji', 'name_kana',
        'in_region', 'capital', 'map_ids',
        'stats_population', 'stats_population_date',
        'stats_population_density', 'stats_population_rank',
        'stats_area', 'stats_area_rank',
        'url_official', 'url_wikipedia',
        'img_flag', 'img_symbol',
        'tags']

    # Export the numerical values to the JSON only
    for pitem in prefectures.values():
        del pitem['stats_population_f']
        del pitem['stats_area_f']

    # Write the Anki deck
    for _, fields in prefectures.items():
        PREF_DECK.add_note(
            genanki.Note(
                model=PREF_MODEL,
                fields=[str(fields[fieldname]) for fieldname in fieldnames
                        if fieldname not in ('tags',)],
                tags=fields['tags'],
                guid=fields['index']))

    # Write the CSV file
    with open('csv/prefectures.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        prefectures = fix_urls(prefectures)

        writer.writeheader()
        writer.writerows(sorted(prefectures.values(), key=itemgetter('index')))
###############################################################################


###############################################################################
def process_capitals():
    '''
    Collect all information for the capitals of Japan.
    '''

    query = Path('sparql/capitals.rq').read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    capitals = json_extract(sparql.query().convert())

    with open('json/prefectures.json', 'r') as infile:
        db_prefs = json.load(infile)

    for _, citem in capitals.items():
        pref_name = as_map_id(citem['in_prefecture'])

        citem['title'] = strip_to_name(citem['name_en'])
        citem['map_ids'] = ', '.join([pref_name, '{}-{}'.format(
            pref_name, as_map_id(citem['name_en']))])

        citem['name_en'] = all_representations(citem['name_en'])
        citem['index'] = db_prefs[citem['in_prefecture']]['index'] + 1

        citem['in_prefecture'] = strip_to_name(citem['in_prefecture'])
        citem['stats_population'] = int(citem['stats_population'])

        # Occasionally the area is in square meters instead ...
        if citem['stats_area'] > 10**7:
            citem['stats_area'] /= 10**6

        citem['stats_population_density'] = '{:,.2f}'.format(
            citem['stats_population']/ citem['stats_area'])
        citem['stats_population'] = '{:,d}'.format(int(citem['stats_population']))
        citem['stats_area'] = '{:,.2f}'.format(citem['stats_area'])

        # Only keep the first image, it should have the highest priority in Wikidata
        for key in ('url_official', 'img_impression'):
            if isinstance(citem[key], list):
                citem[key] = citem[key][0]

        citem['tags'] = ('Capital', as_map_id(citem['in_prefecture']))

    with open('json/capitals.json', 'w') as outfile:
        json.dump(capitals, outfile, ensure_ascii=False, indent=4)

    fieldnames = [
        'index', 'title',
        'name_en', 'name_kanji', 'name_kana',
        'in_prefecture', 'map_ids',
        'stats_population', 'stats_population_date', 'stats_population_density',
        'stats_area',
        'url_official', 'url_wikipedia',
        'img_flag', 'img_seal', 'img_impression',
        'tags']

    # TODOS: write the Anki file ...

    # Write the CSV file
    with open('csv/capitals.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        capitals = fix_urls(capitals)

        writer.writeheader()
        writer.writerows(sorted(capitals.values(), key=itemgetter('index')))
###############################################################################


################################################################################
def main():
    '''Main function.'''

    parser = argparse.ArgumentParser()

    parser.add_argument('--regs', action='store_true')
    parser.add_argument('--prefs', action='store_true')
    parser.add_argument('--caps', action='store_true')
    parser.add_argument('--all', action='store_true')

    args = parser.parse_args()

    if args.regs:
        process_regions()

    if args.prefs:
        process_prefectures()

    if args.caps:
        process_capitals()

    if args.all:
        # To get the statistics and indices of the regions right we need
        # all the information from the prefectures first! This is written
        # to a JSON file only, use preprocess to stop the Anki output!
        process_prefectures(preprocess=True)
        process_regions()
        process_prefectures()  # Fix the indices according to the regions
        process_capitals()

    genanki.Package(PREF_DECK).write_to_file('output.apkg')

if __name__ == '__main__':
    main()

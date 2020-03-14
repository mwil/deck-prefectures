#! /usr/bin/env python3

# pylint: disable=too-many-locals

'''
Generate the US SVG deck for Kitsun.
'''

import argparse
import csv
import json

from collections import defaultdict
from operator import itemgetter
from pathlib import Path

import genanki
import regex

from SPARQLWrapper import SPARQLWrapper, JSON

from us.models_us import REG_MODEL, STATE_DECK, STATE_MODEL

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
def strip_to_name(name):
    '''Replace unnecessary parts of the Wikidata results.'''

    return regex.sub(r'\s+Prefecture|\s+\(?region\)?', '', name)

###############################################################################
def as_map_id(name):
    '''Aggressively strip everthing that might trip Kitsun.'''

    return strip_to_name(name)

###############################################################################
def all_representations(wiki_name):
    '''Collect all string representations in a single line.'''

    names = [strip_to_name(wiki_name)]

    if as_map_id(names[0]) not in names:
        names.append(as_map_id(names[0]))

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
def process_regions():
    '''
    Collect all information for the regions of the US.
    '''

    with open('us/json/states.json', 'r') as infile:
        db_states = json.load(infile)

    query = Path('us/sparql/regions.rq').read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    regions = json_extract(sparql.query().convert())

    ###########################################################################
    # Get the information from the states ...
    for region, ritem in regions.items():
        population = 0
        area = 0.0

        ritem['title'] = strip_to_name(ritem['name_en'])
        ritem['name_en'] = all_representations(ritem['name_en'])

        ritem['contained_states'] = ', '.join(
            map(strip_to_name, ritem['state_en']))
        ritem['map_ids'] = ', '.join(
            as_map_id(pref) for pref in ritem['state_en'])

        for pref in ritem['state_en']:
            population += db_states[pref]['stats_population_f']
            area += db_states[pref]['stats_area_f']

        regions[region]['stats_population'] = population
        regions[region]['stats_area'] = area

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

        del ritem['state_en']

    with open('us/json/regions.json', 'w') as outfile:
        json.dump(regions, outfile, ensure_ascii=False, indent=4)

    fieldnames = [
        'index', 'title', 'name_en',
        'contained_states', 'map_ids',
        'stats_population', 'stats_population_density', 'stats_population_rank',
        'stats_area', 'stats_area_rank',
        'url_wikipedia',
        'tags']

    # Write the Anki deck
    for _, fields in regions.items():
        STATE_DECK.add_note(
            genanki.Note(
                model=REG_MODEL,
                fields=[str(fields[fieldname]) for fieldname in fieldnames
                        if fieldname not in ('tags',)],
                tags=fields['tags'],
                guid=fields['index']))

    # Write the CSV file
    with open('us/csv/regions.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        regions = fix_urls(regions)

        writer.writeheader()
        writer.writerows(sorted(regions.values(), key=itemgetter('index')))

###############################################################################
def process_states(preprocess=False):
    '''
    Collect all information for the states in the US.
    '''

    with open('us/json/regions.json', 'r') as infile:
        db_regs = json.load(infile)

    query = Path('us/sparql/states.rq').read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    states = json_extract(sparql.query().convert())

    states_by_pop = sorted(states.values(),
                           key=itemgetter('stats_population'),
                           reverse=True)
    states_by_area = sorted(states.values(),
                            key=itemgetter('stats_area'),
                            reverse=True)

    for _, sitem in states.items():
        reg_index = db_regs[sitem['in_region']]['index']

        sitem['title'] = strip_to_name(sitem['name_en'])
        sitem['map_ids'] = as_map_id(sitem['name_en'])

        sitem['name_en'] = all_representations(sitem['name_en'])
        sitem['in_region'] = strip_to_name(sitem['in_region'])

        sitem['stats_population_f'] = sitem['stats_population']
        sitem['stats_population'] = '{:,d}'.format(int(sitem['stats_population']))

        sitem['stats_area_f'] = sitem['stats_area']
        sitem['stats_area'] = '{:,.2f}'.format(sitem['stats_area'])

        sitem['stats_population_density'] = '{:,.2f}'.format(
            sitem['stats_population_f']/ sitem['stats_area_f'])

        sitem['stats_population_rank'] = list(
            map(itemgetter('name_kanji'), states_by_pop)).index(
                as_map_id(sitem['name_kanji'])) + 1
        sitem['stats_area_rank'] = list(
            map(itemgetter('name_kanji'), states_by_area)).index(
                as_map_id(sitem['name_kanji'])) + 1

        sitem['index'] = reg_index + sitem['stats_population_rank'] * 2
        sitem['tags'] = ('Prefecture', as_map_id(sitem['in_region']))

    states['Hokkaidō Prefecture']['url_wikipedia'] = 'https://en.wikipedia.org/wiki/Hokkaido'

    with open('us/json/states.json', 'w') as outfile:
        json.dump(states, outfile, ensure_ascii=False, indent=4)

    if preprocess:
        # Do not write the output to the deck when gathering the stats only
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
    for sitem in states.values():
        del sitem['stats_population_f']
        del sitem['stats_area_f']

    # Write the Anki deck
    for _, fields in states.items():
        STATE_DECK.add_note(
            genanki.Note(
                model=STATE_MODEL,
                fields=[str(fields[fieldname]) for fieldname in fieldnames
                        if fieldname not in ('tags',)],
                tags=fields['tags'],
                guid=fields['index']))

    # Write the CSV file
    with open('us/csv/states.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        states = fix_urls(states)

        writer.writeheader()
        writer.writerows(sorted(states.values(), key=itemgetter('index')))

###############################################################################
# def process_capitals():
#     '''
#     Collect all information for the states in the US.
#     '''

#     query = Path('sparql/capitals.rq').read_text()

#     sparql = SPARQLWrapper(ENDPOINT_URL)
#     sparql.setQuery(query)
#     sparql.setReturnFormat(JSON)

#     capitals = json_extract(sparql.query().convert())

#     with open('us/json/states.json', 'r') as infile:
#         db_states = json.load(infile)

#     for _, citem in capitals.items():
#         pref_name = as_map_id(citem['in_prefecture'])

#         citem['title'] = strip_to_name(citem['name_en'])
#         citem['map_ids'] = ', '.join([pref_name, '{}-{}'.format(
#             pref_name, as_map_id(citem['name_en']))])

#         citem['name_en'] = all_representations(citem['name_en'])
#         citem['index'] = db_states[citem['in_prefecture']]['index'] + 1

#         citem['in_prefecture'] = strip_to_name(citem['in_prefecture'])
#         citem['stats_population'] = int(citem['stats_population'])

#         # Occasionally the area is in square meters instead ...
#         if citem['stats_area'] > 10**7:
#             citem['stats_area'] /= 10**6

#         citem['stats_population_density'] = '{:,.2f}'.format(
#             citem['stats_population']/ citem['stats_area'])
#         citem['stats_population'] = '{:,d}'.format(int(citem['stats_population']))
#         citem['stats_area'] = '{:,.2f}'.format(citem['stats_area'])

#         # Only keep the first image, it should have the highest priority in Wikidata
#         for key in ('url_official', 'img_impression'):
#             if isinstance(citem[key], list):
#                 citem[key] = citem[key][0]

#         citem['tags'] = ('Capital', as_map_id(citem['in_prefecture']))

#     with open('us/json/capitals.json', 'w') as outfile:
#         json.dump(capitals, outfile, ensure_ascii=False, indent=4)

#     fieldnames = [
#         'index', 'title',
#         'name_en', 'name_kanji', 'name_kana',
#         'in_prefecture', 'map_ids',
#         'stats_population', 'stats_population_date', 'stats_population_density',
#         'stats_area',
#         'url_official', 'url_wikipedia',
#         'img_flag', 'img_seal', 'img_impression',
#         'tags']

#     # TODOS: write the Anki file ...

#     # Write the CSV file
#     with open('us/csv/capitals.csv', 'w') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#         capitals = fix_urls(capitals)

#         writer.writeheader()
#         writer.writerows(sorted(capitals.values(), key=itemgetter('index')))

################################################################################
def main():
    '''Main function.'''

    parser = argparse.ArgumentParser()

    parser.add_argument('--regs', action='store_true')
    parser.add_argument('--states', action='store_true')
    # parser.add_argument('--caps', action='store_true')
    parser.add_argument('--all', action='store_true')

    args = parser.parse_args()

    if args.regs:
        process_regions()

    if args.states:
        process_states()

    # if args.caps:
    #     process_capitals()

    if args.all:
        process_states(preprocess=True)
        process_regions()
        process_states()
        # process_capitals()

    genanki.Package(STATE_DECK).write_to_file('states_us.apkg')

if __name__ == '__main__':
    main()

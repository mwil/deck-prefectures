#! /usr/bin/env python3

import argparse
import csv
import json
import regex

from collections import defaultdict
from operator import itemgetter
from pathlib import Path

from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT_URL = "https://query.wikidata.org/sparql"


###############################################################################
def json_extract(js):
    result = defaultdict(dict)

    keys = js["head"]["vars"]

    # TODO: use first hit instead of overwriting in dict

    for line in js["results"]["bindings"]:
        for key in keys:
            item = line["name_en"]["value"]

            try:
                value = line[key]["value"]
            except KeyError:
                result[item][key] = None
                continue

            if ("datatype" in line[key] and
                    line[key]["datatype"] == "http://www.w3.org/2001/XMLSchema#decimal"):
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
def as_map_id(name):
    patterns = [
        ("ū", "u"),
        ("Ō", "O"),
        ("ō", "o")
    ]

    result = regex.sub("\s+Prefecture|\s+\(?region\)?", "", name)

    for pattern in patterns:
        result = regex.sub(*pattern, result)

    return result
###############################################################################

###############################################################################
def process_regions():
    with open("json/prefectures.json", "r") as infile:
        db_prefs = json.load(infile)

    query = Path("sparql/regions.rq").read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    regions = json_extract(sparql.query().convert())

    # TODO: remove all special character for fields than can appear as answers
    #       tags are broken?
    #       use correct integer and float values
    #       round floats to two digits in csv strings

    # Hokkaido only has a single prefecture, fix to list
    regions["Hokkaidō (region)"]["prefecture_en"] = [regions["Hokkaidō (region)"]["prefecture_en"]]

    ###########################################################################
    # Get the information from the prefectures ...
    for region, ritem in regions.items():
        population = 0
        area = 0.0

        ritem["name_en"] = as_map_id(ritem["name_en"])

        ritem["contained_prefs"] = ", ".join(as_map_id(pref) for pref in ritem["prefecture_en"])
        ritem["map_ids"] = ", ".join(as_map_id(pref) for pref in ritem["prefecture_en"])

        for pref in ritem["prefecture_en"]:
            population += db_prefs[pref]["stats_population"]
            area += db_prefs[pref]["stats_area"]

        regions[region]["stats_population"] = int(population)
        regions[region]["stats_area"] = round(area, 2)
    ###########################################################################

    ###########################################################################
    regs_by_popu = sorted(regions.values(), key=itemgetter("stats_population"), reverse=True)
    regs_by_area = sorted(regions.values(), key=itemgetter("stats_area"), reverse=True)

    for reg, ritem in regions.items():
        ritem["stats_population_density"] = round(ritem["stats_population"]/ ritem["stats_area"], 2)
        ritem["stats_population_rank"] = list(map(itemgetter("name_en"), regs_by_popu)).index(as_map_id(reg)) + 1
        ritem["stats_area_rank"] = list(map(itemgetter("name_en"), regs_by_area)).index(as_map_id(reg)) + 1

        ritem["index"] = ritem["stats_population_rank"] * 100
        ritem["tags"] = "Region"

        del ritem["prefecture_en"]
    ###########################################################################

    ###########################################################################
    # Static fixes
    regions["Hokkaidō (region)"]["url_wikipedia"] = "https://en.wikipedia.org/wiki/Hokkaido"
    regions["Shikoku (region)"]["url_wikipedia"] = "https://en.wikipedia.org/wiki/Shikoku"
    regions["Kyūshū (region)"]["url_wikipedia"] = "https://en.wikipedia.org/wiki/Kyushu"
    ###########################################################################

    with open("json/regions.json", "w") as outfile:
        json.dump(regions, outfile, ensure_ascii=False, indent=4)

    fieldnames = ["index",
                  "name_en", "name_kanji", "name_kana",
                  "contained_prefs", "map_ids",
                  "stats_population", "stats_population_density", "stats_population_rank",
                  "stats_area", "stats_area_rank",
                  "url_wikipedia",
                  "tags"]

    with open("csv/regions.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(regions.values())
###############################################################################

###############################################################################
def process_prefectures():
    with open("json/regions.json", "r") as infile:
        db_regs = json.load(infile)

    query = Path("sparql/prefectures.rq").read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    prefectures = json_extract(sparql.query().convert())

    prefs_by_popu = sorted(prefectures.values(), key=itemgetter("stats_population"), reverse=True)
    prefs_by_area = sorted(prefectures.values(), key=itemgetter("stats_area"), reverse=True)

    for pref, pitem in prefectures.items():
        reg_index = db_regs[pitem["in_region"]]["index"]

        pitem["name_en"] = as_map_id(pitem["name_en"])
        pitem["in_region"] = as_map_id(pitem["in_region"])
        pitem["map_ids"] = pitem["name_en"]

        pitem["stats_population"] = int(pitem["stats_population"])

        pitem["stats_population_density"] = round(pitem["stats_population"]/ pitem["stats_area"], 2)

        pitem["stats_population_rank"] = list(map(itemgetter("name_en"), prefs_by_popu)).index(as_map_id(pref)) + 1
        pitem["stats_area_rank"] = list(map(itemgetter("name_en"), prefs_by_area)).index(as_map_id(pref)) + 1

        pitem["index"] = reg_index + pitem["stats_population_rank"] * 2
        pitem["tags"] = "Prefecture"

    # TODO:
    #       Download and convert images
    #       check for SVG first ...

    # svg2png(url=u, write_to="png/test.png")

    prefectures["Hokkaidō Prefecture"]["url_wikipedia"] = "https://en.wikipedia.org/wiki/Hokkaido"

    with open("json/prefectures.json", "w") as outfile:
        json.dump(prefectures, outfile, ensure_ascii=False, indent=4)

    fieldnames = ["index",
                  "name_en", "name_kanji", "name_kana",
                  "in_region", "capital", "map_ids",
                  "stats_population", "stats_population_date", "stats_population_density", "stats_population_rank",
                  "stats_area", "stats_area_rank",
                  "url_official", "url_wikipedia",
                  "img_flag", "img_symbol",
                  "tags"]

    with open("csv/prefectures.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(prefectures.values())
###############################################################################


###############################################################################
def process_capitals():
    query = Path("sparql/capitals.rq").read_text()

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    capitals = json_extract(sparql.query().convert())

    with open("json/prefectures.json", "r") as infile:
        db_prefs = json.load(infile)

    for cap, citem in capitals.items():
        pref_name = as_map_id(citem["in_prefecture"])

        citem["name_en"] = as_map_id(citem["name_en"])
        citem["index"] = db_prefs[citem["in_prefecture"]]["index"] + 1
        citem["map_ids"] = ", ".join([pref_name, "{}-{}".format(pref_name, citem["name_en"])])

        citem["in_prefecture"] = as_map_id(citem["in_prefecture"])
        citem["stats_population"] = int(citem["stats_population"])

        # Occasionally the area is in square meters instead ...
        if citem["stats_area"] > 10**7:
            citem["stats_area"] /= 10**6

        citem["stats_population_density"] = round(citem["stats_population"]/ citem["stats_area"], 2)

        for key in ("url_official", "img_impression"):
            if isinstance(citem[key], list):
                citem[key] = citem[key][0]

        citem["tags"] = "Capital"

    with open("json/capitals.json", "w") as outfile:
        json.dump(capitals, outfile, ensure_ascii=False, indent=4)

    fieldnames = ["index",
                  "name_en", "name_kanji", "name_kana",
                  "in_prefecture", "map_ids",
                  "stats_population", "stats_population_date", "stats_population_density",
                  "stats_area",
                  "url_official", "url_wikipedia",
                  "img_flag", "img_seal", "img_impression",
                  "tags"]

    with open("csv/capitals.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(capitals.values())
###############################################################################


################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--regs", action="store_true")
    parser.add_argument("--prefs", action="store_true")
    parser.add_argument("--caps", action="store_true")
    parser.add_argument("--all", action="store_true")

    args = parser.parse_args()

    if args.regs:
        process_regions()

    if args.prefs:
        process_prefectures()

    if args.caps:
        process_capitals()

    if args.all:
        process_prefectures()
        process_regions()
        process_prefectures()  # Fix the indices according to the regions
        process_capitals()

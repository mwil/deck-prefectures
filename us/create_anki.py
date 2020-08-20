"""
Create an Anki deck from Wikidata results.
"""

from pathlib import Path
from urllib.parse import urlparse

import genanki as anki
import numpy as np
import pandas as pd
import requests as rq

from wand.api import library as wandlib
import wand.color
import wand.image

from core.wikidata import WDQuery
from us.data import US_REGIONS
from us.models import STATE_DECK, STATE_MODEL, STATE_FIELDS, REG_MODEL


########################################################################################
def name_to_id(name):
    """Fix strings so that they can be used as IDs everywhere."""

    return name.replace(" ", "_")


########################################################################################
def prepare_images(wd_s, itype="flag"):
    """
    Get all SVG images referenced in Wikidata and convert them to PNGs.
    """

    ####################################################################################
    def convert_img(state, itype, url):
        if not url:
            return None

        svgpath = Path("us/img/svg") / Path(urlparse(url).path).name
        pngpath = Path("us/img/png") / f"{name_to_id(state)}_{itype}.png"

        if not svgpath.is_file():
            svgblob = rq.get(url).content

            with svgpath.open("wb") as outfile:
                outfile.write(svgblob)

        if pngpath.is_file():
            return pngpath

        with wand.image.Image() as image:
            with wand.color.Color("transparent") as background_color:
                wandlib.MagickSetBackgroundColor(image.wand, background_color.resource)

            image.read(blob=svgpath.read_bytes())
            image.transform(resize="x128")

            with pngpath.open("wb") as outfile:
                outfile.write(image.make_blob("png32"))

        return pngpath

    # The seal is what we want for the symbol/seal, if it is not present
    # we replace it with the content from svg_symbol.
    conv_type = "symbol" if itype == "seal" and not wd_s.svg_seal else itype

    pngpath = convert_img(wd_s.name_en, itype, wd_s[f"svg_{conv_type}"])
    imgtag = f'<img src="{pngpath.name}" height="128px">' if pngpath else None

    return pngpath, imgtag


########################################################################################
def prepare_anki(wd_df):
    """
    Take the pre-processed information and dump it to the Anki format.
    """

    media_files = []

    for name in ("flag", "seal"):
        media_files.extend(map(str, wd_df[f"pngpath_{name}"].dropna().tolist()))

    wd_df.stats_population = wd_df.stats_population.apply(lambda x: f"{x:,}")
    wd_df.stats_area = wd_df.stats_area.apply(lambda x: f"{x:,.0f}")

    wd_df.reg_stats_population = wd_df.reg_stats_population.apply(lambda x: f"{x:,}")
    wd_df.reg_stats_area = wd_df.reg_stats_area.apply(lambda x: f"{x:,.0f}")

    wd_df = wd_df.sort_values(by="idx")

    for _, reg_group in wd_df.groupby("reg_name_en", sort=False):
        reg_data = {
            "idx": str(100 * reg_group.iloc[0]["reg_stats_population_rank"]),
            "title": reg_group.iloc[0]["reg_name_en"],
            "name_en": ", ".join(reg_group.iloc[0]["aliases"]),
            "contained_states": ", ".join(reg_group.loc[:, "name_en"]),
            "map_ids": name_to_id(reg_group.iloc[0]["reg_name_en"]),
            "stats_population": str(reg_group.iloc[0]["reg_stats_population"]),
            "stats_population_density": f'{reg_group.iloc[0]["reg_stats_population_density"]:.2f}',
            "stats_population_rank": str(
                reg_group.iloc[0]["reg_stats_population_rank"]
            ),
            "stats_area": reg_group.iloc[0]["reg_stats_area"],
            "stats_area_rank": str(reg_group.iloc[0]["reg_stats_area_rank"]),
            "url_wikipedia": reg_group.iloc[0]["reg_url_wikipedia"],
        }
        print(reg_data.values())

        STATE_DECK.add_note(
            anki.Note(
                model=REG_MODEL,
                fields=list(reg_data.values()),
                sort_field="title",
                tags=["region"],
                guid=reg_data["idx"],
            )
        )

        for row_idx, row in reg_group.iterrows():
            print(row.loc[STATE_FIELDS].to_list())
            STATE_DECK.add_note(
                anki.Note(
                    model=STATE_MODEL,
                    fields=list(map(str, row.loc[STATE_FIELDS].to_list())),
                    sort_field="title",
                    tags=["state"],
                    guid=row_idx,
                )
            )

    pkg = anki.Package(STATE_DECK)
    pkg.media_files = media_files
    pkg.write_to_file("output_us.apkg")


########################################################################################
def prepare_states(wd_df):
    """
    Augment the DF with statistics.
    """

    wd_df = wd_df.assign(title=wd_df.name_en)
    wd_df = wd_df.assign(map_ids=wd_df.name_en.apply(name_to_id))

    wd_df = wd_df.astype({"stats_population": int, "stats_area": float})

    pop_dens = wd_df.stats_population / wd_df.stats_area

    wd_df = wd_df.assign(stats_population_density=pop_dens.apply(lambda x: f"{x:.2f}"))

    wd_df = wd_df.sort_values(by="stats_population", ascending=False, ignore_index=True)

    wd_df = wd_df.assign(stats_population_rank=wd_df.index + 1)

    area_index = wd_df.sort_values(by="stats_area", ascending=False).index
    wd_df.loc[area_index, "stats_area_rank"] = range(1, len(area_index) + 1)

    return wd_df


########################################################################################
def prepare_regions(wd_df):
    """
    Format the manual region information into expected format.
    """

    regions = pd.DataFrame(US_REGIONS)
    regions = regions.explode("reg_state_list")

    wd_df = wd_df.join(regions.set_index("reg_state_list"), on="name_en")

    wd_df = wd_df.assign(reg_stats_population=None, reg_stats_area=None)

    for reg_indices in wd_df.groupby("reg_name_en").groups.values():
        wd_df.loc[reg_indices, "reg_stats_population"] = wd_df.loc[
            reg_indices, "stats_population"
        ].sum()

        wd_df.loc[reg_indices, "reg_stats_area"] = wd_df.loc[
            reg_indices, "stats_area"
        ].sum()

        wd_df.loc[reg_indices, "reg_stats_population_density"] = (
            wd_df.loc[reg_indices, "reg_stats_population"]
            / wd_df.loc[reg_indices, "reg_stats_area"]
        )

    regions = wd_df.groupby("reg_name_en")

    pop_indices = (
        regions.sum().sort_values(by="stats_population", ascending=False).index
    )

    for rank, pop_index in enumerate(pop_indices, 1):
        reg_index = regions.indices[pop_index]

        wd_df.loc[reg_index, "reg_stats_population_rank"] = rank

        # Index the cards according to their region and population rank, keep
        # the even numbers for the capitals if necessary
        wd_df.loc[reg_index, "idx"] = 100 * rank + 2 * np.arange(len(reg_index)) + 1

    area_indices = regions.sum().sort_values(by="stats_area", ascending=False).index

    for rank, area_index in enumerate(area_indices, 1):
        wd_df.loc[regions.indices[area_index], "reg_stats_area_rank"] = rank

    wd_df = wd_df.astype(
        {"idx": int, "reg_stats_population_rank": int, "reg_stats_area_rank": int}
    )

    return wd_df


########################################################################################
def main():
    """Main."""

    df_pickle_path = Path("us/jar/wd_df.bz2")

    if not df_pickle_path.is_file():
        print("Pickled query does not exist, querying WikiData ...")

        states_rq = Path("us/sparql/states.rq").read_text()

        wdq = WDQuery(states_rq)
        wdq.get_df().to_pickle(df_pickle_path)

    wd_df = pd.read_pickle(df_pickle_path)
    wd_df = prepare_states(wd_df)

    for itype in ("flag", "seal"):
        wd_df[[f"pngpath_{itype}", f"img_{itype}"]] = wd_df.apply(
            prepare_images, axis=1, result_type="expand", args=(itype,)
        )

    wd_df = prepare_regions(wd_df)

    prepare_anki(wd_df)


########################################################################################
if __name__ == "__main__":
    main()

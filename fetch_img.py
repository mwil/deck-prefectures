import requests
import PIL

from io import BytesIO

from cairosvg import svg2png
from PIL import Image

PNG_BASEWIDTH = 640


################################################################################
def fetch_img():
    for img_type in ("img_flag", "img_seal", "img_impression"):
        if isinstance(citem[img_type], []):
            img_url = citem[img_type][0]
        else:
            img_url = citem[img_type]

        if ext == svg:
            svg2png(url=u, parent_width=500, write_to="tmp.png")

        response = requests.get(img_url)
        tmp_img = Image.open(BytesIO(response.content))
################################################################################

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
        pass

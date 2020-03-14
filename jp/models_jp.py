'''
A place for the models of the Anki deck.
'''

import json

from pathlib import Path

import genanki

JP_SVG = Path('svg/MapJapan_final.svg').read_text()
CSS = Path('layouts/common.css').read_text()


with Path('make_deck.json').open('r') as jsonfile:
    CONF = json.load(jsonfile)

################################################################################
PREF_DECK = genanki.Deck(CONF['Deck']['deck_id'], CONF['Deck']['deck_name'])


CARD_TEMPLATE = '''
    <div id="card_wrapper">
        <div id="map_wrapper" class="%(template)s">
            %(svg)s
        </div>
        <div id="input_wrapper">
            %(input)s
        </div>
        <div id="answer_wrapper">
            %(answer)s
        </div>
    </div>'''


################################################################################
################################################################################
REG_MARK_INPUT = '''
    {{addclass:map_ids}}
    {{type:name_en[Enter Region Name ...]}}
    '''

REG_CLICK_INPUT_FRONT = '''
    {{click:map_ids}}
    <div class="typeans tcenter">
        Click on a Prefecture in the {{first:name_en}} Region!
    </div>'''

REG_CLICK_INPUT_BACK = '''
    {{addclass:map_ids}}
    <div class="typeans tcenter">
        <div class="inreviews">Clicked on the {{enteredanswer}} Region!</div>
        <div class="inlessons">Click on the Highlighted Region in Reviews!</div>
    </div>'''

REG_ANSWER = '''
    <div id="answer_card" class="expand_content" data-content="1">
        <h1>
            {{first:name_en}} Region
            <div class="subtitle">（{{name_kanji}}・{{name_kana}}）</div>
        </h1>
        <p>The region consists of {{contained_prefs}}.</p>

        <table id="stats">
        <tbody>
            <tr>
                <td>Population: {{stats_population}}人</td>
                <td>Area: {{stats_area}} km²</td>
            </tr>
            <tr>
                <td>Population Rank: {{stats_population_rank}}/8</td>
                <td>Area Rank: {{stats_area_rank}}/8</td>
            </tr>
            <tr>
                <td>Population Density: {{stats_population_density}}/km²</td>
            </tr>
        </tbody>
        </table>
    </div>'''

################################################################################
REG_MODEL = genanki.Model(
    CONF['Region Model']['model_id'],
    CONF['Region Model']['model_name'],
    fields=CONF['Region Model']['model_fields'],
    templates=[
        {
            'name': 'Marked on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': REG_MARK_INPUT,
                'answer': '',
                'template': 'marked'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': REG_MARK_INPUT,
                'answer': REG_ANSWER,
                'template': 'marked'
            }
        },
        {
            'name': 'Click on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': REG_CLICK_INPUT_FRONT,
                'answer': '',
                'template': 'click'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': REG_CLICK_INPUT_BACK,
                'answer': REG_ANSWER,
                'template': 'click'
            }
        }],
        css=CSS)


################################################################################
################################################################################
PREF_MARK_INPUT = '''
    {{addclass:map_ids}}
    {{type:name_en[Enter Prefecture Name ...]}}'''

PREF_CLICK_INPUT_FRONT = '''
    {{click:map_ids}}
    <div class="typeans tcenter">
        Click on the {{first:name_en}} Prefecture!
    </div>'''

PREF_CLICK_INPUT_BACK = '''
    {{addclass:map_ids}}
    <div class="typeans tcenter">
        <div class="inlessons">Click on the Highlighted Prefecture in Reviews!</div>
        <div class="inreviews">Clicked on the {{enteredanswer}} Prefecture!</div>
    </div>'''

PREF_ANSWER = '''
    <div id="answer_card" class="expand_content" data-content="1">
        <h1>
            {{first:name_en}} Prefecture
            <div class="subtitle">（{{name_kanji}}・{{name_kana}}）</div>
        </h1>
        <table id="stats">
        <tbody>
            <tr>
                <td>Population: {{stats_population}}人</td>
                <td>Area: {{stats_area}} km²</td>
            </tr>
            <tr>
                <td>Population Rank: {{stats_population_rank}}/47</td>
                <td>Area Rank: {{stats_area_rank}}/47</td>
            </tr>
            <tr>
                <td>Population Density: {{stats_population_density}}/km²</td>
            </tr>
        </tbody>
        </table>
    </div>'''

################################################################################
PREF_MODEL = genanki.Model(
    CONF['Prefecture Model']['model_id'],
    CONF['Prefecture Model']['model_name'],
    fields=CONF['Prefecture Model']['model_fields'],
    templates=[
        {
            'name': 'Marked on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': PREF_MARK_INPUT,
                'answer': '',
                'template': 'marked'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': PREF_MARK_INPUT,
                'answer': PREF_ANSWER,
                'template': 'marked'
            }
        },
        {
            'name': 'Click on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': PREF_CLICK_INPUT_FRONT,
                'answer': '',
                'template': 'click'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': JP_SVG,
                'input': PREF_CLICK_INPUT_BACK,
                'answer': PREF_ANSWER,
                'template': 'click'
            }
        }],
    css=CSS)

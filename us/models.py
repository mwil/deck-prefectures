'''
A place for the models of the US Anki deck.
'''

import json

from pathlib import Path
from operator import itemgetter

import genanki as anki


################################################################################
SVG_STATES = Path('us/svg/MapUS1.svg').read_text()
SVG_REGS = Path('us/svg/MapUS1_reg.svg').read_text()
CSS = Path('us/templates/common.css').read_text()
CONF = json.loads(Path('us/make_deck_us.json').read_text())


################################################################################
STATE_DECK = anki.Deck(CONF['Deck']['deck_id'], CONF['Deck']['deck_name'])

STATE_FIELDS = list(map(itemgetter('name'), CONF['State Model']['model_fields']))
REG_FIELDS = list(map(itemgetter('name'), CONF['Region Model']['model_fields']))


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
        <div class="inreviews front">Click on a State in {{first:name_en}}!</div>
        <div class="inlessons front">Unlocked New Region: {{first:name_en}}!</div>
        <div class="inreviews back">Clicked on {{enteredanswer}}!</div>
        <div class="inlessons back">Click on the Highlighted Region in Reviews!</div>
    </div>
    '''

REG_CLICK_INPUT_BACK = '''
    {{addclass:map_ids}}
    {{FrontSide}}'''

REG_ANSWER = '''
    <div id="answer_card" class="expand_content" data-content="1">
        <h1>
            {{first:name_en}}
        </h1>
        <p>The region consists of {{contained_states}}.</p>

        <table id="stats">
        <tbody>
            <tr>
                <td>Population: {{stats_population}}</td>
                <td>Area: {{stats_area}} km²</td>
            </tr>
            <tr>
                <td>Population Rank: {{stats_population_rank}}/9</td>
                <td>Area Rank: {{stats_area_rank}}/9</td>
            </tr>
            <tr>
                <td>Population Density: {{stats_population_density}}/km²</td>
            </tr>
        </tbody>
        </table>
    </div>'''

################################################################################
REG_MODEL = anki.Model(
    CONF['Region Model']['model_id'],
    CONF['Region Model']['model_name'],
    fields=CONF['Region Model']['model_fields'],
    templates=[
        {
            'name': 'Marked on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': SVG_REGS,
                'input': REG_MARK_INPUT,
                'answer': '',
                'template': 'marked'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': SVG_REGS,
                'input': REG_MARK_INPUT,
                'answer': REG_ANSWER,
                'template': 'marked'
            }
        },
        {
            'name': 'Click on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': SVG_REGS,
                'input': REG_CLICK_INPUT_FRONT,
                'answer': '',
                'template': 'click'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': SVG_REGS,
                'input': REG_CLICK_INPUT_BACK,
                'answer': REG_ANSWER,
                'template': 'click'
            }
        }],
        css=CSS)


################################################################################
################################################################################
STATE_MARK_INPUT = '''
    {{addclass:map_ids}}
    {{type:name_en[Enter State Name ...]}}'''

STATE_CLICK_INPUT_FRONT = '''
    {{click:map_ids}}
    <div class="typeans tcenter">
        Click on {{first:name_en}}!
    </div>'''

STATE_CLICK_INPUT_BACK = '''
    {{addclass:map_ids}}
    <div class="typeans tcenter">
        <div class="inlessons">Click on the Highlighted State in Reviews!</div>
        <div class="inreviews">Clicked on {{enteredanswer}}!</div>
    </div>'''

STATE_ANSWER = '''
    <div id="answer_card" class="expand_content" data-content="1">
        <h1>
            {{first:name_en}}
        </h1>
        <p>Capital: {{capital}}</p>

        <table id="stats">
        <tbody>
            <tr>
                <td>Population: {{stats_population}}</td>
                <td>Area: {{stats_area}} km²</td>
            </tr>
            <tr>
                <td>Population Rank: {{stats_population_rank}}/50</td>
                <td>Area Rank: {{stats_area_rank}}/50</td>
            </tr>
            <tr>
                <td>Population Density: {{stats_population_density}}/km²</td>
            </tr>
        </tbody>
        </table>
    </div>'''

################################################################################
STATE_MODEL = anki.Model(
    CONF['State Model']['model_id'],
    CONF['State Model']['model_name'],
    fields=CONF['State Model']['model_fields'],
    templates=[
        {
            'name': 'Marked on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': SVG_STATES,
                'input': STATE_MARK_INPUT,
                'answer': '',
                'template': 'marked'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': SVG_STATES,
                'input': STATE_MARK_INPUT,
                'answer': STATE_ANSWER,
                'template': 'marked'
            }
        },
        {
            'name': 'Click on Map',
            'qfmt': CARD_TEMPLATE % {
                'svg': SVG_STATES,
                'input': STATE_CLICK_INPUT_FRONT,
                'answer': '',
                'template': 'click'
            },
            'afmt': CARD_TEMPLATE % {
                'svg': SVG_STATES,
                'input': STATE_CLICK_INPUT_BACK,
                'answer': STATE_ANSWER,
                'template': 'click'
            }
        }],
    css=CSS)

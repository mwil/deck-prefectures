'''
Static information that does not exist nicely in Wikidata.
'''

from collections import namedtuple

USRegion = namedtuple('USRegion',
                      'reg_name_en, aliases, reg_state_list, reg_url_wikipedia')

################################################################################
US_REGIONS = {
    # Region 1: Northeast
    USRegion('New England',
             ('New England', 'New England States'),
             ('Connecticut', 'Maine', 'Massachusetts', 'New Hampshire',
              'Rhode Island', 'Vermont'),
             'https://en.wikipedia.org/wiki/New_England'),
    USRegion('Mid-Atlantic States',
             ('Mid-Atlantic States', 'Mid-Atlantic',),
             ('New Jersey', 'New York', 'Pennsylvania'),
             'https://en.wikipedia.org/wiki/Mid-Atlantic_(United_States)'),

    # Region 2: Midwest
    USRegion('East North Central States',
             ('East North Central States', 'East North Central', 'EN Central'),
             ('Illinois', 'Indiana', 'Michigan', 'Ohio', 'Wisconsin'),
             'https://en.wikipedia.org/wiki/East_North_Central_states'),
    USRegion('West North Central States',
             ('West North Central States', 'West North Central', 'WN Central'),
             ('Iowa', 'Kansas', 'Minnesota', 'Missouri', 'Nebraska',
              'North Dakota', 'South Dakota'),
             'https://en.wikipedia.org/wiki/West_North_Central_states'),

    # Region 3: South
    USRegion('South Atlantic States',
             ('South Atlantic States', 'South Atlantic', 'S Atlantic'),
             ('Delaware', 'Florida', 'Georgia', 'Maryland', 'North Carolina',
              'South Carolina', 'Virginia', 'District of Columbia',
              'West Virginia'),
             'https://en.wikipedia.org/wiki/South_Atlantic_states'),
    USRegion('East South Central States',
             ('East South Central States', 'East South Central', 'ES Central'),
             ('Alabama', 'Kentucky', 'Mississippi', 'Tennessee'),
             'https://en.wikipedia.org/wiki/East_South_Central_states'),
    USRegion('West South Central States',
             ('West South Central States', 'West South Central', 'WS Central'),
             ('Arkansas', 'Louisiana', 'Oklahoma', 'Texas'),
             'https://en.wikipedia.org/wiki/West_South_Central_states'),

    # Region 4: West
    USRegion('Mountain States',
             ('Mountain States', 'Mountain'),
             ('Arizona', 'Colorado', 'Idaho', 'Montana', 'Nevada',
              'New Mexico', 'Utah', 'Wyoming'),
             'https://en.wikipedia.org/wiki/Mountain_states'),
    USRegion('Pacific States',
             ('Pacific States', 'Pacific'),
             ('Alaska', 'California', 'Hawaii', 'Oregon', 'Washington'),
             'https://en.wikipedia.org/wiki/Pacific_states'),
}

'''
Query WikiData for information and parse it into a DataFrame.
'''

import pandas as pd

from SPARQLWrapper import SPARQLWrapper, JSON

################################################################################
class WDQuery():  # pylint: disable=too-few-public-methods
    '''
    Create a pandas DataFrame with information queried from Wikidata.
    '''

    ENDPOINT_URL = 'https://query.wikidata.org/sparql'

    ############################################################################
    def __init__(self, query):
        self.query = query
        self.data = pd.DataFrame()

    ############################################################################
    def get_df(self):
        '''
        Get the result Wikidata.
        '''

        sparql = SPARQLWrapper(self.ENDPOINT_URL)
        sparql.setQuery(self.query)
        sparql.setReturnFormat(JSON)

        result = sparql.query().convert()

        wd_df = pd.DataFrame(result['results']['bindings'])

        # wd_dtypes = wd_df.applymap(
        #     lambda x: x.get('datatype', None) if isinstance(x, dict) else None)

        # float_cols = wd_dtypes.columns[
        #     (wd_dtypes == 'http://www.w3.org/2001/XMLSchema#decimal').all()]

        wd_df = wd_df.applymap(
            lambda x: (x['value'] if isinstance(x, dict) else None))

        # wd_df = wd_df.astype({colname: 'float' for colname in float_cols})

        return wd_df

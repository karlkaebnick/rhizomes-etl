#!/usr/bin/env python


import requests
import json

import solr

from setup import ETLEnv


etl_env = ETLEnv()
etl_env.start()
api_key = etl_env.get_api_key(name="calisphere")


# "https://solr.calisphere.org/solr/query/?q=fred"


SOLR_KEYS = [
    "title",
    "subject",
    "creator",
    "id",
    "date",
    "url_item",
    "description",
    "type",
    "repository_url",
    "reference_image_dimensions",
    'collection_data',
    'rights_holder',
    'campus_name',
    'facet_decade'
    'campus_data',
    'collection_url',
    'repository_name',
    'repository_data',
    'rights'
    'collection_name',
    'campus_url',
    'sort_collection_data',
    'timestamp',
    'score'
]

field_map = {
    "title":                 "Title",
    "creator":               "Author/Artist",
    "description":           "Description ",
    "date":                  "Date",
    "type":                  "Digital Format",
    "id":                    "Resource Identifier",
    "sort_collection_data":  "Source",
    "subject":               "Subjects (Topic/Keywords)",
}


def extract():

    # Get a connection to Calisphere's solr server.
    ss = solr.SolrConnection("https://solr.calisphere.org/solr", post_headers={ "X-Authentication-Token": api_key } )

    data = []

    # Do a search
    response = ss.query('title:chicano', rows=25)
    for hit in response.results:
        
        record = {}
        for key in SOLR_KEYS:

            if hit.get(key):

                record[key] = hit[key]

        data.append(record)

    return data


# REVIEW TODO come up with generic default versions of transform() and load()

def transform(data):

    for record in data:

        for name, description in field_map.items():

            if not description:

                continue

            value = record.get(name)
            if value:

                if record.get(description):

                    record[description] += value

                else:

                    record[description] = value

                del record[name]

def load(data):

    for record in data:

        print("")

        for name in field_map.values():

            value = record.get(name)
            if value and name:

                print(f"{name}: {value}")

if __name__ == "__main__":

    data = extract()
    transform(data=data)
    load(data=data)
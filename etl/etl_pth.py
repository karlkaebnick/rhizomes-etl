#!/usr/bin/env python

import os
import re
import requests
import shutil
import sys

from etl.etl_process import BaseETLProcess
from etl.setup import ETLEnv
from etl.tools import RhizomeField, get_oaipmh_record

from bs4 import BeautifulSoup


import pdb


protocol = "https://"
domain = "texashistory.unt.edu"

list_sets_path = "/oai/?verb=ListSets"
list_sets_url = protocol + domain + list_sets_path

RECORD_LIMIT = None
record_count = 0
num_calls = 0


records_path =       "/oai/?verb=ListRecords"
start_records_path = records_path + "&metadataPrefix=oai_dc"
start_records_url = protocol + domain + start_records_path
resume_records_url = protocol + domain + records_path


field_map = {
    "identifier":                             RhizomeField.ID,
    "title":                                  RhizomeField.TITLE,
    "creator":                                RhizomeField.AUTHOR_ARTIST,
    "contributor":                            RhizomeField.AUTHOR_ARTIST,
    "description":                            RhizomeField.DESCRIPTION,
    "date":                                   RhizomeField.DATE,
    "type":                                   RhizomeField.RESOURCE_TYPE,
    "format":                                 RhizomeField.DIGITAL_FORMAT,
    "dimensions":                             RhizomeField.DIMENSIONS,
    "url":                                    RhizomeField.URL,
    "source":                                 RhizomeField.SOURCE,
    "language":                               RhizomeField.LANGUAGE,
    "subjects_hist":                          RhizomeField.SUBJECTS_HISTORICAL_ERA,
    "subject":                                RhizomeField.SUBJECTS_TOPIC_KEYWORDS,
    "subjects_geo":                           RhizomeField.SUBJECTS_GEOGRAPHIC,
    "thumbnail":                              RhizomeField.IMAGES,
}


# REVIEW: See https://docs.google.com/document/d/1cD559D8JANAGrs5pwGZqaxa7oHTwid0mxQG0PmAKhLQ/edit for how to pull data.

DATA_PULL_LOGIC = {

    None: {
        "dummy": {
            "filters": {
                "subject": {
                    "type": "include",
                    "values": [ "Arts and Crafts" ]
                },
                "keywords": {
                    "type": "include",
                    "values": [
                        "chicano", "chicana", "chicanx",
                        "mexican-american", "mexican american",
                        "hispanic", "arte",
                    ]
                }
            },
            "results" : {
                "min": 230,
                "max": 240
            },
            "ignore": False
        }
    },

    "partner": {

        #  Austin Presbyterian Theological Seminary
        "ATPS": {
            "filters": {
                "subject": {
                    "type": "include",
                    "values": [ "Arts and Crafts", "People - Ethnic Groups - Hispanics" ]
                }
            },
            "results" : {
                "min": 230,
                "max": 240
            },
            "ignore": False
        },

        #  Dallas Museum of Art
        "DMA": {
            "filters": {
                "keywords": {
                    "type": "include",
                    "case-sensitive": False,
                    "exact-match": False,
                    "values": [
                        "texas panorama",
                        "american printmaking, 1913-1947",
                        "catalog list: the aldrich collection",
                        "modern american color prints",
                        "six latin american painters",
                        "visions of the west: american art from dallas collections",
                        "handbook of american painting and sculpture in the collection of the dallas museum of fine arts",
                        "concentrations 11: luis jimenez opens at the dallas museum of art",
                        "1930's expositions",
                        "handbook of collections, exhibitions and activities",
                        "texas painting and sculpture in the collection of the dallas museum of fine arts",
                        "twelfth annual dallas allied arts exhibition",
                        "christmas at the museum",
                        "the hand and the spirit: religious art in america",
                        "robert graham exhibition",
                        "poets of the cities: new york and san francisco",
                        "25th annual dallas county painting, sculpture and drawing",
                        "dallas museum of fine arts bulletin",
                        "dallas museum of art installation: museum of the americas, 1993",
                        "fifteenth exhibition of southwestern prints and drawings, january 27–february 17, 1965",
                        "twenty fourth annual texas painting and sculpture exhibition, 1962-1963",
                        "first annual exhibition by texas sculptors group",
                        "eighth texas general exhibition",
                        "26th annual dallas county exhibition: painting, drawing, sculpture",
                        "john hernandez",
                    ]
                },
            },
            "results" : {
                "expected_number": 3,
            },
            "ignore": False
        },

        #  Hispanic Heritage Center
        "HHCT": {
            "filters": {
                "type": {
                    "type": "include",
                    "values": [ "Photograph" ]
                }
            },
            "results" : {
                "expected_number": 119
            },
            "ignore": False
        },

        # Mexic-Arte Museum
        "MAMU": {
            "results": {
                "min": 290,
                "max": 310
            },
            "ignore": False
        },

         # Museum of South Texas History
        "MSTH": {
            "results": {
                "expected_number": 99,
            },
            "ignore": False
        },

        # Texas A&M University Kingsville
        "AMKV": {
            "filters": {
                "type": {
                    "type": "include",
                    "values": [ "Photograph" ]
                }
            },
            "results" : {
                "expected_number": 112
            },
            "ignore": False
        },

        # Pharr Memorial Library
        # Note: We unfortunately are getting zero results for Pharr Memorial Library via the current data pull.
        "PHRML": {
            "filters": {
                "keywords": {
                    "type": "include",
                    # "values": [ "chicano art", "lowriders club", "xochil art center" ]
                    "values": [ "chicana", "chicano", "lowrider", "xochil" ]
                }
            },
            "results" : {
                "expected_number": 112
            },
            "ignore": False
        },

        # UNT Libraries Government Documents Department
        "UNTGD": {
            "filters": {
                "keywords": {
                    "type": "include",
                    "values": [ "mexican american art", "chicano art" ]
                }
            },
            "ignore": False
        },
    },

    "collection" : {

        # Art Lies
        "ARTL": {
            "results" : {
                "expected_number": 64
            },
            "ignore": False
        },

        # Texas Borderlands Newspaper Collection
        "BORDE": {
            "filters": {
                "keywords": {
                    "type": "include",
                    "values": [ "obra de arte", "artista", "arte" ]
                }
            },
            "ignore": False
        },

        # Civil Rights in Black and Brown (part of TCU Mary Couts Burnett Library)
        "CRBB": {
            "filters": {
                "type": {
                    "type": "include"
                }
            },
            "ignore": False
        },

        # Diversity in the Desert (part of Marfa Public Library)
        "MDID": {
            "results" : {
                "min": 1740,
                "max": 1760,
            },
            "ignore": False
        },

        # The Mexican American Family and Photo Collection (part of Houston Metropolitan Research Center at Houston Public Library)
        "MAFP": {
            "filters": {
                "type": {
                    "type": "include",
                    "values": [ "Photograph" ]
                }
            },
            "results" : {
                "expected_number": 431
            },
            "ignore": False
        },

         # Texas Trends in Art Education (part of Texas Art Education Association)
        "TTAE" : {
            "results" : {
                "expected_number": 56
            },
            "ignore": False
        },
    },
}

# REVIEW TODO Get canonical list of PTH formats.
KNOWN_FORMATS = ('image', 'text')


def has_number(value):

    return re.search(r'\d', value)

def get_data(resumption_token=None):
    """
    Download PTH's metadata.
    """

    global num_calls

    if not resumption_token:

        # Rename current metadata directory first to indicate it is old.
        if os.path.exists("etl/data/pth"):

            if os.path.exists("etl/data/pth_old"):

                shutil.rmtree("etl/data/pth_old")

            os.rename("etl/data/pth", "etl/data/pth_old")

        os.mkdir("etl/data/pth")

        num_calls = 0

        url = start_records_url

    else:

        url = f"{resume_records_url}&resumptionToken={resumption_token}"

        if ETLEnv.instance().are_tests_running():

            return

    response = requests.get(url)
    if not response.ok:    # pragma: no cover (should never be True during testing)

        raise Exception(f"Error retrieving data from PTH, status code: {response.status_code}, reason: {response.reason}")

    xml_data = BeautifulSoup(markup=response.content, features="lxml-xml", from_encoding="utf-8")

    # Oheck for search errors.
    errors = xml_data.find_all("error")
    if errors:

        raise Exception(errors[0].text)

    with open(f"etl/data/pth/pth_{num_calls}.xml", "w") as output:

        output.write(response.text)

    resumption_tokens = xml_data.find_all("resumptionToken")

    # Loop through next set of data (if any).
    if resumption_tokens:

        num_calls += 1
        curr_record_count = num_calls * 1000

        print(f"{curr_record_count} PTH records retrieved ...", file=sys.stderr)

        # Make recursive call to extract all records.
        if not RECORD_LIMIT or curr_record_count < RECORD_LIMIT:

            get_data(resumption_token=resumption_tokens[0].text)

def add_filter_match(key_name, key, filter_name, filter_, match):
    "Increment the hit count for the given filter."

    global DATA_PULL_LOGIC

    if not DATA_PULL_LOGIC[key_name][key].get("results"):

        DATA_PULL_LOGIC[key_name][key]["results"] = {}

    DATA_PULL_LOGIC[key_name][key]["results"]["number"] = DATA_PULL_LOGIC[key_name][key]["results"].get("number", 0) + 1

    if not filter_.get("matches"):

        filter_["matches"] = {}

    filter_["matches"][match] = filter_.get(match, 0) + 1

def do_include_record(record):
    """
    Returns True if the record should be added, based on the filters.

    Possible effects of a given filter:

    - For a filter that tries to exclude records:
        - if matched, then add a False include vote.
        - if not matched, then add a True include vote.

    - For a filter that tries to include records:
        - if matched, then add a True include vote.
        - if not matched, then add a False include vote.

    If, after all filters have been applied, there are no include votes,
    or if there are any False include votes, then do not include the record.

    """

    class IncludeVote():

        def __init__(self, key_name, key, filter_name, filter_, match, filter_includes, include_vote_value):

            self.key_name = key_name
            self.key = key
            self.filter_name = filter_name
            self.filter_ = filter_
            self.match = match
            self.filter_includes = filter_includes
            self.include_vote_value = include_vote_value

    include_votes = []

    # Loops through all the filters and check each one.
    for key_name, keys in DATA_PULL_LOGIC.items():

        for key, config in keys.items():

            # Ignore this filter completely?
            if config.get("ignore") and False:

                continue

            # First verify the list set matches.
            if key_name:

                if key_name not in [ "collection", "partner" ]:


                    pdb.set_trace()


                elif key_name + ":" + key not in record["setSpec"]:

                    continue

            # Now apply any filters.
            filters = config.get("filters", {})
            for filter_name, filter_ in filters.items():

                match = None

                if filter_name == "keywords":

                    title = ''.join(record.get('title', [])).lower()
                    description = ''.join(record.get('description', [])).lower()

                    for keyword in filter_["values"]:

                        if keyword in title or keyword in description:

                            match = keyword
                            break

                else:

                    case_sensitive = filter_.get("case-sensitive", False)
                    exact_match = filter_.get("exact-match", False)
                    desired_values = filter_["values"]

                    values = record.get(filter_name, [])
                    if type(values) is not list:

                        values = [ values ]

                    if not case_sensitive:

                        for idx, value in enumerate(values):

                            # if type(value) is None:
                            if not value:


                                pdb.set_trace()


                            values[idx] = value.lower()

                    for desired_value in desired_values:

                        desired_value_copy = desired_value if case_sensitive else desired_value.lower()

                        if exact_match:

                            matched = desired_value_copy in values

                        else:

                            for value in values:

                                if desired_value_copy in value:

                                    match = desired_value
                                    break

                # - For a filter that tries to exclude records:
                #     - if matched, then add a False include vote.
                #     - if not matched, then add a True include vote.
                # 
                # - For a filter that tries to include records:
                #     - if matched, then add a True include vote.
                #     - if not matched, then add a False include vote.

                filter_includes = filter_["type"] == "include"
                include_vote_value = filter_includes if match else not filter_includes

                include_votes.append(IncludeVote(key_name=key_name, key=key, filter_name=filter_name, filter_=filter_, match=match, filter_includes=filter_includes, include_vote_value=include_vote_value))

    # If, after all filters have been applied, there are no include votes,
    # or if there are any False include votes, then do not include the record.
    # return False if not include_votes or False in include_votes else True

    if not include_votes:

        return False

    final_answer = True
    for vote in include_votes:

        if not vote.include_vote_value:

            final_answer = False
            break

    # Now record which filters caused the record to be included or excluded.
    category_set = set()
    for vote in include_votes:

        if (final_answer and vote.filter_includes) or (not final_answer and not vote.filter_includes):

            if vote.key_name not in category_set:

                category_set.add(vote.key_name)

                add_filter_match(key_name=vote.key_name, key=vote.key, filter_name=vote.filter_name, filter_=vote.filter_, match=vote.match)

    return final_answer

def check_filter_results(key_name, key, config):
    "Output error info if results for this filter are not what was expected."

    results_info = config.get("results", {})
    msg = None


    # REVIEW: Finish this.
    pdb.set_trace()


    expected_number = results_info.get("expected_number")
    num_results = DATA_PULL_LOGIC[key_name][key]["results"].get("number", 0)

    if expected_number and num_results != expected_number:

        msg = f"ERROR: {number} results were expected from PTH {key_name} {key}, {num_results} extracted"    # pragma: no cover (should not get here)

    min_ = results_info.get("min")
    if min_ and num_results < min_:

        msg = f"ERROR: at least {min_} results were expected from PTH {key_name} {key}, {num_results} extracted"    # pragma: no cover (should not get here)

    max_ = results_info.get("max")
    if max_ and num_results > max_:

        msg = f"ERROR: no more than {max_} results were expected from PTH {key_name} {key}, {num_results} extracted"    # pragma: no cover (should not get here)

    if msg:    # pragma: no cover (should not get here)

        if ETLEnv.instance().are_tests_running():

            raise Exception(msg)

        print(msg, file=sys.stderr)

    msgs = []

    # Now check how well the filters performed.
    for filter_name, filter_ in DATA_PULL_LOGIC[key_name][key]["filters"].items():

        matches = filter_.get("matches", {})
        if not matches:

            msgs.append(f"ERROR: the {filter_name} filter got no matches.")

        for value in filter_.get("values"):

            if not matches.get(value, 0):

                msgs.append(f"ERROR: the {filter_name} filter '{value}' got no matches.")

    for msg in msgs:    # pragma: no cover (should not get here)

        if ETLEnv.instance().are_tests_running():

            raise Exception(msg)

        print(msg, file=sys.stderr)

def check_results():
    "Output error info if results for any filters are not what was expected."

    for key_name, keys in DATA_PULL_LOGIC.items():

        for key, config in keys.items():

            if not config.get("ignore") or True:

                check_filter_results(key_name=key_name, key=key, config=config)

def read_file(file_num):
    "Returns the contents of the current file."

    file_path = f"etl/data/pth/pth_{file_num}.xml"

    if not os.path.exists(file_path):

        return None

    with open(file_path, "r") as input:

        data = input.read()

    # if testing, use test data?
    etl_env = ETLEnv.instance()
    if etl_env.are_tests_running():

        from etl.tests.test_tools import try_to_read_file

        data, format_ = try_to_read_file()

    return data

def extract_data(records=[], file_num=0):
    """
    Extract all relevant PTH records.
    """

    if file_num and  ETLEnv.instance().are_tests_running():

        return records

    # Read current file and parse the xml.
    data = read_file(file_num=file_num)
    if not data:

        return records

    xml_data = BeautifulSoup(markup=data, features="lxml-xml", from_encoding="utf-8")

    # Check for search errors.
    errors = xml_data.find_all("error")
    if errors:

        raise Exception(errors[0].text)

    # Get relevant records.
    for record in xml_data.find_all("record"):

        record = get_oaipmh_record(record=record)

        if do_include_record(record=record):

            records.append(record)

    # Keep going until we have gone through all of PTH's metadata.
    return extract_data(records=records, file_num=file_num+1)


class PTHETLProcess(BaseETLProcess):

    def init_testing(self):

        # Disable all data pulls except the one being tested.
        test_info = ETLEnv.instance().get_test_info()
        pos = test_info.tag.find('_')
        test_key_name = test_info.tag[ : pos]
        test_key = test_info.tag[pos + 1 : ].upper()

        for key_name, keys in DATA_PULL_LOGIC.items():

            for key, config in keys.items():

                ignore = not( key_name == test_key_name and key == test_key)
                config["ignore"] = ignore

        # Set record very low for testing.
        RECORD_LIMIT = 1

    def get_field_map(self):

        return field_map

    def extract(self):

        # Rebuild metadata cached?
        if not ETLEnv.instance().use_cache():

            get_data()

        records = extract_data()

        check_results()

        return records

    def transform(self, data):

        for record in data:

            # Split 'format' into digital format and dimensions.
            formats = record.get("format", [])
            if formats:

                new_formats = []
                new_dimensions = []

                for format in formats:

                    if format.lower() in KNOWN_FORMATS:

                        new_formats.append(format)

                    else:

                        new_dimensions.append(format)

                record["format"] = new_formats
                record["dimensions"] = new_dimensions

            # Add in a URL value.
            identifiers = record["identifier"]
            new_ids = []
            new_urls = []

            for identifier in identifiers:

                if identifier.startswith('http'):

                    new_urls.append(identifier)

                else:

                    new_ids.append(identifier)

            record["identifier"] = new_ids
            record["url"] = new_urls

            # Add in a link to the thumbnail image.
            if new_urls:

                url = new_urls[0]
                if not url.endswith('/'):
                    url += '/'

                record["thumbnail"] = url + "thumbnail"

            # Split 'coverage' into values dealing with geography and values dealing with history (dates).
            coverage_values = record.get("coverage", [])
            if coverage_values:

                hist_vals = []
                geo_vals = []

                for value in coverage_values:

                    if has_number(value=value):

                        hist_vals.append(value)

                    else:

                        geo_vals.append(value)

                record["subjects_hist"] = hist_vals
                record["subjects_geo"] = geo_vals

        # Let base class do rest of transform.
        super().transform(data=data)


if __name__ == "__main__":    # pragma: no cover

    from etl.run import run_cmd_line

    args_ = [ "pth" ]

    if len(sys.argv) > 1:

        args_ += sys.argv[1:]

    run_cmd_line(args=args_)
"""
Normalize and combine the released Iraq csv file and Afghanistan csv file into
the same "excel dialect" csv format, without header row.

Clean fields and deal with nulls appropriately.
"""
import re
import sys
import csv
import itertools

try:
    afg_infile = sys.argv[1]
    iraq_infile = sys.argv[2]
    outfile = sys.argv[3]
except IndexError:
    print "Usage: %s <afghanistan csv file> <iraq csv file> <outfile.csv>"
    sys.exit(1)

def clean_summary(text):
    # Fix ampersand mess
    if text.strip() == "<null value>":
        return text.strip()
    while text.find("&amp;") != -1:
        text = text.replace("&amp;", "&")
    text = re.sub('&(?!(#[a-z\d]+|\w+);)/gi', "&amp;", text)
    return text

def force_int(a):
    return int(a or 0)

def float_or_null(f):
    try:
        return float(f)
    except ValueError:
        return "<null value>"

def complex_attack(f):
    if f == "<null value>":
        return f
    else:
        return bool(f)

import_fields = [
    ("report_key",),       # 0
    ("date",),             # 1
    ("type",),             # 2
    ("category",),         # 3
    ("tracking_number",),  # 4
    ("title",),            # 5 
    ("summary", clean_summary),          # 6
    ("region",),           # 7 
    ("attack_on",),        # 8
    ("complex_attack", complex_attack),   # 9 
    ("reporting_unit",),   # 10
    ("unit_name",),        # 11
    ("type_of_unit",),     # 12 
    ("friendly_wia", force_int),     # 13
    ("friendly_kia", force_int),     # 14
    ("host_nation_wia", force_int),  # 15
    ("host_nation_kia", force_int),  # 16
    ("civilian_wia", force_int),     # 17
    ("civilian_kia", force_int),     # 18
    ("enemy_wia", force_int),        # 19
    ("enemy_kia", force_int),        # 20
    ("enemy_detained", force_int),   # 21
    ("mgrs",),             # 22
    ("latitude", float_or_null),         # 23
    ("longitude", float_or_null),        # 24
    ("originator_group",), # 25
    ("updated_by_group",), # 26
    ("ccir",),             # 27
    ("sigact",),           # 28
    ("affiliation",),      # 29
    ("dcolor",),           # 30
    ("classification",),   # 31
]
# Add "thru" default
import_fields = [field if len(field) == 2 else field + (lambda f: f,) for field in import_fields]

with open(outfile, 'w') as outfh:
    writer = csv.writer(outfh, dialect='excel')
    with open(afg_infile) as afgin:
        reader = csv.reader(afgin, delimiter=",", quotechar='"', doublequote=True)
        for row in reader:
            # Include the additional "Release" parameter.
            outrow = ['Afghanistan']
            for field, (name, cleaner) in zip(row, import_fields):
                outrow.append(cleaner(field))
            writer.writerow(outrow)

    with open(iraq_infile) as iraqin:
        reader = csv.reader(iraqin, delimiter=",", quotechar='"', escapechar='\\')
        for row in itertools.islice(reader, 1, None):
            if row:
                outrow = ['Iraq']
                # Skip the 'id' and 'url' fields
                for field, (name, cleaner) in zip(row[2:], import_fields):
                    outrow.append(cleaner(field))
                writer.writerow(outrow)

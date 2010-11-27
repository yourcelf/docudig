"""
This file contains lists of "FIELD" definitions, which are used to construct
both database models and search indexes.

A "field" consists of a dictionary that defines properties about the field:
{
   'name': the name of the field (must be a valid python var name)
   'display_name': Human readable string identifying the field.
   'type': A string that is one of:
          'char': A short (255 char or less) string
          'text': A long (arbitrary length) string
          'date': A date
          'int': An integer
          'float': A real
          'latitude': A real representing a latitude
          'longitude': A real representing a longitude
          'boolean': True or False
          'null_boolean': True, False, or Null
   'faceted': boolean; if true, field will be indexed for faceted search
   'index': boolean; if true, field will be included in the search index
   'primary_key': boolean; if true, the field will be considered a unique
                  identifier for this doc.  Only one field should be true.
   'document': boolean; if true, field will be indexed for full-text search.
               Only one field should be true.  
   'body': boolean; if true, field will be used to build excerpts for search
           results.
   'facet_limit': integer; the maximum number of facets to return for a 
                  given field.
}

Fields listed in "META_FIELDS" require one additional key:

   'build': A function that receives the document model as an argument, and
            returns the value for this field.  Useful for processing other
            document fields.

Each of the following are required for one and only one field:
   * 'primary_key=True' (may not be a META_FIELD)
   * 'body=True'        (may be a META_FIELD)
   * 'document=True'    (may be a META_FIELD)

"""

def field(name, display_name, type_, faceted=True, index=True, 
          primary_key=False, document=False, body=None, facet_limit=100,
          build=None):
    """ 
    Convenience function to construct a field dict with defaults 
    """
    return { 'name': name, 'display_name': display_name, 'type': type_,
        'faceted': faceted, 'index': index, 'primary_key': primary_key,
        'document': document, 'build': build, 'body': body, 
        'facet_limit': facet_limit}

# A list of regular model fields.  This should correspond to the column order
# of fields in the import CSV file.
FIELDS = [
        # field_name, Verbose Name, type
    field('release', 'Release', 'char'),
    field('report_key', 'Report Key', 'char', faceted=False, primary_key=True), 
    field('date', 'Date', 'date'),
    field('type', 'Type', 'char'),
    field('category', 'Category', 'char'),
    field('tracking_number', 'Tracking Number', 'char', faceted=False),
    field('title', 'Title', 'text', faceted=False),
    field('summary', 'Summary', 'text', body=True, faceted=False),
    field('region', 'Region', 'char'),
    field('attack_on', 'Attack on', 'char'),
    field('complex_attack', 'Complex Attack', 'boolean'),
    field('reporting_unit', 'Reporting Unit', 'char'),
    field('unit_name', 'Unit Name', 'char'),
    field('type_of_unit', 'Type of Unit', 'char'),
    field('friendly_wia', 'Friendly Wounded', 'int'),
    field('friendly_kia', 'Friendly killed', 'int'),
    field('host_nation_wia', 'Host Nation Wounded', 'int'),
    field('host_nation_kia', 'Host Nation Killed', 'int'),
    field('civilian_wia', 'Civilian Wounded', 'int', facet_limit=200),
    field('civilian_kia', 'Civilian Killed', 'int', facet_limit=200),
    field('enemy_wia', 'Enemy Wounded', 'int'),
    field('enemy_kia', 'Enemy killed', 'int'),
    field('enemy_detained', 'Enemy Detained', 'int'),
    field('mgrs', 'MGRS', 'char'),
    field('latitude', 'Latitude', 'latitude'),
    field('longitude', 'Longitude', 'longitude'),
    field('originator_group', 'Originator group', 'char'),
    field('updated_by_group', 'Updated by group', 'char'),
    field('ccir', 'CCIR', 'char'),
    field('sigact', 'SIGACT', 'char'),
    field('affiliation', 'Affiliation', 'char'),
    field('dcolor', 'DColor', 'char'),
    field('classification', 'Classification', 'char'),
]
# A list of fields which are functions of the other data in the model.
# Requires one additional "build" parameter, which is a function that builds
# the field given a model.
META_FIELDS = [
    field('total_casualties', 'Total Casualties', 'int', 
        facet_limit=200,
        build=lambda d: sum((d.friendly_wia, d.friendly_kia, 
                            d.host_nation_wia, d.host_nation_kia, 
                            d.civilian_wia, d.civilian_kia, 
                            d.enemy_wia, d.enemy_kia))),
    field('text', 'Text', 'text', 
        build=lambda doc: "\n".join((doc.title, doc.summary)),
        faceted=False, document=True),
]
# A list of fields which will be offered as searching/faceting choices in the
# search sidebar.
FACET_DISPLAY = ['text', 'date', 'type', 'category', 'region', 'total_casualties']

# Sort fields is a list of fields over which documents may be sorted.
SORT_FIELDS = ['date', 'total_casualties']

# Default sort is the initial sort field.  Add a "-" to default to descending.
DEFAULT_SORT = '-date'


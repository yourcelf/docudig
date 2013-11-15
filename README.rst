DocuDig_Dat
+++++++

<a href="https://github.com/yourcelf/docudig">DocuDig</a> is a Django application for rich faceted browsing and searching of
structured documents.  It began its life as a search application for the
WikiLeaks war log releases, but has evolved to a general purpose structured
document browsing and searching tool.

<a href="https://github.com/maxogden/dat">Dat</a> is a tool for sharing and versioning tabular data.
This DocuDig_Dat branch adds capability to upload documents to DocuDig using Dat.
Dat is an alternative to git which better supports:

* real time data (sensors, social media, geolocation)
* transforming data (tracking updates in several formats)
* data filtering/subsets

*Features*

* Faceted browsing, including date and numeric ranges
* Full text searching
* Expansion of acronyms
* Free, Libre, Open Source Software

*Use Cases* -- if your data...

* is *uniformly structured*: It could reasonably be expressed as a CSV file with
  a reasonable number of columns
* *doesn't change much*: the data set doesn't get updated very often
* is  *large*: thousands to small millions of rows
* contains *acronyms*: could benefit from client-side processing to add
  acronym definitions
* needs to be *self hosted*: you want to run it on your own server
* needs to handle *high load*: you need to be able to handle lots of traffic
* needs an *API*: you want to expose the search results and documents to other
  developers through JSON

... then DocuDig might be for you.

You should be comfortable with:

* Defining your data's structure in a configuration file.
* Correcting any inconsistencies in your documents' data and structure, and
  either formatting it into a standard CSV format (the Python `excel dialect
  <http://docs.python.org/library/csv.html#csv.excel>`_) and using the provided
  management commands, or using some other means to import your data into a
  Django database.
* Editing a javascript file to define acronyms.
* Deploying a Django application, and running Solr
* For high load, deploying a caching server/HTTP accelerator like varnish.

Installation
------------

As easy as 1, 2, 3:  Dependencies, Configuration, Data.

1. Dependencies
~~~~~~~~~~~~~~~

DocuDig is build with `Django <http://www.djangoproject.com>`_ and 
`Solr <http://lucene.apache.org/solr/>`_.  

python and Django
=================

It is recommended that you install using pip and virtualenv.  To install
dependencies:
    
    pip install -r requirements.txt -E /path/to/your/virtualenv

If you use postgresql (recommended), you will need to install
``egenix-mx-base``, which `cannot be installed using pip
<http://bitbucket.org/ianb/pip/issue/40/package-egenix-mx-base-cant-be-installed-with>`_.
To install it, first activate your virtualenv, and then:

    easy_install -i http://downloads.egenix.com/python/index/ucs4/ egenix-mx-base

Solr
====

`Install Solr <http://lucene.apache.org/solr/#getstarted>`_.  For the purposes
of testing and development, the `example server
<http://lucene.apache.org/solr/tutorial.html#Getting+Started>`_ should be
adequate, though you will need to add add the schema.xml file as described
below.

Stylesheets
===========

Style sheets are compiled using `Compass <http://compass-style.org/>`_.  If you
wish to modify the style sheets, you will need to install that as well.  After
compass is installed, stylesheets can be compiled as you modify the ``.sass``
files as follows:

    cd media/css/sass/
    compass watch

2. Configuration
~~~~~~~~~~~~~~~~

A. Django settings
==================

Copy the file `example.settings.py` to `settings.py`, add your database
settings, and set ``DEBUG`` mode as appropriate.  Any Django supported database
should work; postgresql is recommended over sqlite3 for importing larger data
sets unless you have a lot of memory.

Other notable settings which you may wish to override:

``CACHE_MIDDLEWARE_SECONDS``
    Default 600; the number of seconds ahead of ``now`` to set the ``Expires``
    header for all requests.
``HAYSTACK_SOLR_URL``
    Default ``http://127.0.0.1:8983/solr``; the path to the instance of Solr to use
    for this installation
``TEMPLATE_DIRS``
    Default ``(PROJECT_ROOT + "/templates",)``; a list of directories that
    store templates.  Can be a convenient way to override templates without
    having to edit the provided ones directly.

B. Field definitions
====================

Edit the file ``field_settings.py``.  This file contains definitions of the
fields that constitute your data set, which are used to construct both database
models and search indexes.  The file defines 5 variables:

``FIELDS``
    A list of primary fields that make up your model.  If you use the provided
    management command described below to import data, the fields here should
    be listed in the same order as columns in the import CSV file.
``META_FIELDS``
    A list of fields that are some function of other fields on your model.
    These fields require an extra ``build`` parameter which is the function
    used to construct the field's value.
``FACET_DISPLAY``
    A list of names of fields that will be included in the facet browsing sidebar.
``SORT_FIELDS``
    A list of names of fields over which documents may be sorted.
``DEFAULT_SORT``
    The name of the field over which to sort initially.  Prepend a ``-`` to
    defualt to descending order.

The field definitions in ``FIELDS`` and ``META_FIELDS`` are dictionaries with
the following parameters::

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
       'build': (Used only for META_FIELDs) A function that receives the document
                model as an argument, and returns the value for this field.
    }

For convenience, a function ``field(name, display_name, type, **kwargs)`` is
defined in the ``field_settings`` file which sets defaults values for a field.

Once fields are defined, the database must be initialized::

    python manage.py syncdb

C. Templates
============

To customize the display of your data, it will be necessary to modify at least
two templates:

``dig/_document_excerpt.html``
    This template stub shows a single search result excerpt, which is part of a
    list of search results.  Two context variables are provided:

    * ``doc``: The search index result for this document, which has attributes
      for all of the indexed fields.
    * ``excerpt``: A marked-up excerpt of the search result.
``dig/document_page.html``
    This template shows the full document page for a single result.  One context
    variable is provided:

    * ``doc``: The database model representing this document, which has
      attributes for all of the defined fields.

You will probably also want to edit:

``dig/_about.html``
    This is the template that sits in the main area of the front page.

``dig/_logo.html``
    The site logo (in the top left).

``dig/base.html``
    The base template for everything else in DocuDig.

All templates are available in the ``dig/templates/dig`` directory.  Rather
than modifying them directly, it's recommended to override them with
definitions stored in one of the ``TEMPLATE_DIRS`` directories; e.g.
``PROJECT_ROOT + /templates/dig/...html``.

D. Acronyms
===========

Acronyms are computed client-side.  They are defined in the file
``media/js/acronyms.js``.  The ``ACRONYM`` variable contains a list of pairs of
regular expressions that identify the acronyms and their replacements.

3. Importing Data
~~~~~~~~~~~~~~~~~

You can import data in any method that gets documents into the database
properly.  After all data is present, the Solr index must be rebuilt.  The
management command described here may be a convenient means for importing data.

A. Import using management command
==================================

Data should be in a single CSV file in python's `excel dialect
<http://docs.python.org/library/csv.html#csv.excel>`_ (comma delimited,
quotechar `"`, doublequote escaping).  Null values should be represented
as the string ``<null value>``.  Column order should be identical to the
order represented in ``field_settings.py`` described above, and the file
should contain no header row.

An example script which reformats WikiLeaks' Afghanistan and Iraq war log CSV
files into a single file in the correct format is provided in ``scripts/``.

Using the prepared CSV file, Run the management command::

    python manage.py import_documents <path/to/file.csv>

B. Rebuild Solr schema and index
================================

To generate the Solr schema, run the following management command::

    python manage.py build_solr_schema > schema.xml

Copy or link this file to the Solr conf directory (if you're using the example
Solr server, this will be ``apache-solor-1.4.1/example/solr/conf``), replacing
any ``schema.xml`` file that is already there, and then restart Solr.  After
restarting Solr, the following management command will rebuild the index::

    python manage.py rebuild_index

License
-------

This branch is made available under the GPLv3 license.

Original DocuDig is granted to the public domain.

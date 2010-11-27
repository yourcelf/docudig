from __future__ import print_function
import sys
import csv

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection, transaction

from dig.models import Document
from dig.utils import StatusPrinter, iso_to_datetime

def string_conv(t):
    return t if (t and t != "<null value>") else ""

def nullable_lambda(func):
    def nullable(val):
        return None if val == "<null value>" else func(val)
    return nullable

CONVERSIONS = {
    'string': string_conv,
    'text': string_conv,
    'int': nullable_lambda(int),
    'float': nullable_lambda(float),
    'latitude': nullable_lambda(float),
    'longitude': nullable_lambda(float),
    'boolean': lambda b: True if b else False,
    'null_boolean': lambda b: None if b == "<null value>" else False if b == False else True,
    'date': lambda d: str(iso_to_datetime(d)),
}

class Command(BaseCommand):
    args = '<csv file>'
    help = """Import a structured document set as rows in a CSV file."""

    @transaction.commit_manually
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            print("""Usage: 

    python manage.py import_documents <csv file>
            """)
            sys.exit(1)
            
        filename = args[0]
        field_names = [f['name'] for f in settings.FIELDS]
        field_conv = [CONVERSIONS[f['type']] for f in settings.FIELDS]
        cursor = connection.cursor()
        
        print("Loading", filename)

        sp = StatusPrinter()
        with open(filename) as fh:
            reader = csv.reader(fh, delimiter=",", quotechar='"')
            for c, row in enumerate(reader):
                if row:
                    sp.print()
                    sp.inc()
                    Document.objects.create(**dict(zip(field_names, 
                        [field_conv[i](f) for i,f in enumerate(row)])))
        sp.end()
        transaction.commit()

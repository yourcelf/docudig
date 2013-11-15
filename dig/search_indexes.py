from django.conf import settings

from haystack import indexes, fields

from dig.models import Document

index_fields = {}
for name, field in settings.ALL_FIELDS.items():
    if field['index'] == False:
        continue

    kwargs = {
        'document': field['document'],
        'faceted': field['faceted'],
        'model_attr': field['name'],
    }
    if field['type'] == 'date':
        index_field = indexes.DateField(null=True, **kwargs)
    elif field['type'] == 'int':
        index_field = indexes.IntegerField(null=True, **kwargs)
    elif field['type'] in ('float', 'latitude', 'longitude'):
        index_field = indexes.FloatField(null=True, **kwargs)
    elif field['type'] == 'boolean':
        index_field = indexes.BooleanField(**kwargs)
    elif field['type'] == 'null_boolean':
        index_field = indexes.BooleanField(null=True, **kwargs)
    elif field['type'] in ('char', 'text'):
        index_field = indexes.CharField(**kwargs)
    else:
        raise Exception("Unrecognized search index field type '%s'." % field['type'])
    index_fields[field['name']] = index_field


class DocumentMetaclass(indexes.DeclarativeMetaclass):
    def __new__(cls, name, bases, attrs):
        return super(DocumentMetaclass, cls).__new__(cls, name,
                bases, index_fields)

class DocumentIndex(indexes.SearchIndex):
    __metaclass__ = DocumentMetaclass

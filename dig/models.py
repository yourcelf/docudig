from django.db import models

from django.conf import settings

class Document(models.Model):
    pass
# Remove the automatically created 'id' field
Document._meta.local_fields.pop()

for field in settings.FIELDS:
    t = field['type']
    kwargs = {
        'primary_key': field['primary_key'],
        'verbose_name': field['display_name'],
    }
    if t == 'char':
        model_field = models.CharField(max_length=255, default="", **kwargs)
    elif t == 'text':
        model_field = models.TextField(default="", **kwargs)
    elif t == 'date':
        model_field = models.DateTimeField(null=True, **kwargs)
    elif t == 'int':
        model_field = models.IntegerField(null=True, **kwargs)
    elif t in ('float', 'latitude', 'longitude'):
        model_field = models.FloatField(null=True, **kwargs)
    elif t == 'boolean':
        model_field = models.BooleanField(**kwargs)
    elif t == 'null_boolean':
        model_field = models.NullBooleanField(**kwargs)
    else:
        raise Exception("Field type '%s' not recognized" % t)
    model_field.contribute_to_class(Document, field['name'])

    if field['primary_key']:
        Document._meta.pk = model_field

for field in settings.META_FIELDS:
    setattr(Document, field['name'], property(field['build']))

setattr(Document, 'to_dict', 
    lambda d: dict((n, unicode(getattr(d, n))) for n in settings.ALL_FIELDS.keys()))

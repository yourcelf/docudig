from django.conf.urls.defaults import *

urlpatterns = patterns('dig.views',
    url(r'^search/(?P<api>json)?$', 'search', name='dig.search'),
    url(r'^id/(?P<doc_pk>.*)/(?P<api>json)?$', 'show_document', name='dig.show_document'),
    url(r'^random$', 'random_document', name='dig.random_document'),
    url(r'^api$', 'api', name='dig.api'),
    url(r'^$', 'about', name='dig.about'),
)


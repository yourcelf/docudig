# Create your views here.
import re
import urllib
import datetime
from collections import defaultdict

from django.conf import settings
from django.core import paginator
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404

from haystack.query import SearchQuerySet
from haystack.utils import Highlighter

from dig.models import Document
from dig import utils

def show_document(request, doc_pk, template='dig/document_page.html', api=False):
    doc = get_object_or_404(Document, pk=doc_pk)
    if api:
        return utils.render_json(request, { 'document': doc.to_dict() })

    return utils.render_request(request, template, {
        'doc': doc
    })

def random_document(request):
    count = Document.objects.count()
    id_ = Document.objects.all()[random.randint(0, count)].pk
    return utils.redirect_to("dig.show_document", id_)

def search(request, template='dig/search_page.html', api=False):
    sqs, choices, constraints, querystr = _parse_facets(request.GET)
    sqs, sort_links, cur_sort = _apply_sorting(sqs, request.GET, querystr)

    # Pagination
    p = paginator.Paginator(sqs, 10)
    try:
        page = p.page(int(request.GET.get('p_', 1)))
    except (ValueError, paginator.InvalidPage, paginator.EmptyPage):
        page = p.page(min(1, p.num_pages))

    # Result summaries and highlighting
    documents = []
    for doc in page.object_list:
        if doc.highlighted:
            excerpt = mark_safe(u"... %s ..." % doc.highlighted['text'][0])
        else:
            excerpt = (getattr(doc, settings.BODY_FIELD['name']) or '')[0:200] + "..."
        documents.append((doc, excerpt))

    if api:
        dict_docs = []
        for d, excerpt in documents:
            doc = dict((n, unicode(getattr(d, n))) for n in settings.FACET_DISPLAY)
            doc['excerpt_'] = excerpt
            dict_docs.append(doc)
        for choice in choices:
            choice['field'] = {
                'name': choice['field']['name'],
                'display_name': choice['field']['display_name'],
            }
            if choice['type'] in ("min_max", "date"):
                print "REDO!!!!"
                choice['choices'] = zip(choice.pop('vals'), choice.pop('counts'))

        return utils.render_json(request, {
            'pagination': {
                'p_': page.number,
                'num_pages': page.paginator.num_pages,
                'num_results': page.paginator.count,
            },
            'documents': dict_docs,
            'choices': choices,
            'sorting': cur_sort,
            'constraints': constraints,
        })

    return utils.render_request(request, template, {
        'sqs': sqs,
        'choices': choices,
        'constraints': constraints,
        'querystr': querystr,
        'sort_links': sort_links,
        'cur_sort': cur_sort,
        'cur_sort_qstring': urllib.urlencode(cur_sort) if cur_sort else "",
        'documents': documents,
        'page': page,
        'total_count': Document.objects.all().count(),
    })

def about(request):
    sqs, choices, constraints, querystr = _parse_facets(request.GET)
    return utils.render_request(request, "dig/about_page.html", {
        'page': {'paginator': {'count': Document.objects.all().count() }},
        'sqs': sqs,
        'choices': choices,
        'constraints': constraints,
        'querystr': querystr,
    })

def api(request):
    return utils.render_request(request, "dig/api.html")

def _narrow_range(sqs, field, qd):
    """
    Given a SearchQuerySet, a field name, and a querydict (e.g. request.GET),
    apply range facet constraints from the querydict to the SearchQuerySet.

    Returns a triple of: 
    * the constrained SearchQuerySet
    * the starting value (or None)
    * the ending value (or None)
    """
    gte = field['name'] + '__gte'
    lte = field['name'] + '__lte'

    if field['type'] == 'date':
        clean_func = utils.partial_date
        str_value = lambda c: c.isoformat() + 'Z'
    elif field['type'] == 'int':
        clean_func = int
        str_value = str
    elif field['type'] in ('float', 'latitude', 'longitude'):
        clean_func = float
        str_value = str

    start = qd.get(gte, None)
    end = qd.get(lte, None)
    if start is not None:
        try:
            start = clean_func(start)
            sqs = sqs.narrow(u"{0}:[{1} TO *]".format(field['name'], str_value(start)))
        except ValueError:
            start = None
    if end is not None:
        try:
            end = clean_func(end)
            sqs = sqs.narrow(u"{0}:[* TO {1}]".format(field['name'], str_value(end)))
        except ValueError:
            end = None
    return sqs, start, end

def _parse_facets(qd):
    """
    Given a request, returns a quadruple of:
    * A SearchQuerySet constrained by the request.GET vars.
    * a dict of constraints that have been applied
    * a list of potential choices for new constraints
    * a querystring that produces these constraints (without pagination 
      or sorting)
    """
    sqs = SearchQuerySet()

    constraints = []
    # Process constraints, and execute facets
    for name, field in settings.ALL_FIELDS.iteritems():
        if field['document']:
            terms = qd.get(field['name'], qd.get('document_', None))
            if terms:
                sqs = sqs.auto_query(terms).highlight()
                constraints.append({
                    'value': terms,
                    'key': name,
                    'type': 'document',
                    'display': field['display_name'],
                })
        elif field['faceted']:
            sqs = sqs.raw_search("", **{
                'f.%s_exact.facet.limit' % field['name']: field['facet_limit']
             })
            if field['type'] == 'date':
                sqs, start, end = _narrow_range(sqs, field, qd)
                if start:
                    constraints.append({
                        'value': start.strftime("%Y-%m-%d"),
                        'key': name + '__gte',
                        'type': 'date',
                        'display': "%s - more than" % field['display_name'],
                    })
                if end:
                    constraints.append({
                        'value': end.strftime("%Y-%m-%d"),
                        'key': name + '__lte',
                        'type': 'date',
                        'display': "%s - less than" % field['display_name'],
                    })
                if start or end or name in settings.FACET_DISPLAY:
                    if not end:
                        end = utils.d_to_dt(getattr(SearchQuerySet().order_by("-" + name)[0], name))
                    if not start:
                        start = utils.d_to_dt(getattr(SearchQuerySet().order_by(name)[0], name))
                    span = max(1, (end - start).days)
                    gap = max(1, int(span / 100))
                    sqs = sqs.date_facet(name, start, end, 'day', gap)

            elif field['type'] in ('int', 'float', 'latitude', 'longitude'):
                sqs, start, end = _narrow_range(sqs, field, qd)
                if start:
                    constraints.append({
                        'value': start,
                        'key': name + '__gte',
                        'type': 'min_max',
                        'display': "%s - more than" % field['display_name'],
                    })
                if end:
                    constraints.append({
                        'value': end,
                        'key': name + '__lte',
                        'type': 'min_max',
                        'display': "%s - less than" % field['display_name'],
                    })
                if start or end or name in settings.FACET_DISPLAY:
                    sqs = sqs.facet(name)
#                    if not end:
#                        end = getattr(SearchQuerySet().order_by("-" + name)[0], name)
#                    if not start:
#                        start = getattr(SearchQuerySet().order_by(name)[0], name)
#                    span = max(1, (end - start))
#                    gap = max(1, int(span / 100))
#                    exact = "%s_exact" % name
#                    sqs = sqs.raw_params(**{
#                        "facet.range": exact,
#                        "f.%s.facet.range.start" % exact: start,
#                        "f.%s.facet.range.end" % exact: end,
#                        "f.%s.facet.range.gap" % exact: gap,
#                    })
            else:
                val = qd.get(name, None)
                if val is not None:
                    constraints.append({
                        'value': val,
                        'key': name,
                        'type': 'text',
                        'display': field['display_name'],
                    })
                    sqs = sqs.narrow('%s:"%s"' % (name + "_exact", val))
                if val is not None or name in settings.FACET_DISPLAY:
                    sqs = sqs.facet(name)

    # Constraint removal links
    queryargs = dict((p['key'], p['value']) for p in constraints)
    querystr = urllib.urlencode(queryargs)
    for param in constraints:
        # remove key
        value = queryargs.pop(param['key'])
        remainder = urllib.urlencode(queryargs)
        param.update({'remove_link': remainder})
        # restore key
        queryargs[param['key']] = value
    
    # Choices
    counts = sqs.facet_counts()
    choices = []
    for name in settings.FACET_DISPLAY:
        field = settings.ALL_FIELDS[name]
        choice = {'field': field}
        if field['document']:
            choice.update({
                'type': 'document',
                'value': queryargs.get(name, ''),
            })
        elif field['type'] in ('text', 'char'):
            facets = sorted((k, c) for k, c in counts['fields'][name] if c > 0)
            if facets:
                choice.update({
                    'choices': facets,
                    'type': 'text',
                    'value': queryargs.get(name, '')
                })
        elif field['type'] in ('int', 'float', 'latitude', 'longitude'):
            facets = sorted([(int(k), c) for k,c in counts['fields'][name] if c > 0])
            if facets:
                choice.update({
                    'type': 'min_max',
                    'counts': [c for k,c in facets],
                    'vals': [k for k,c in facets],
                    'min_value': facets[0][0],
                    'max_value': facets[-1][0],
                    'chosen_min': queryargs.get(name + '__gte', ''),
                    'chosen_max': queryargs.get(name + '__lte', ''),
                })
        elif field['type'] == 'date':
            facets = sorted(counts['dates'].get(name, {}).iteritems())
            if facets:
                val_counts = []
                vals = []
                last_dt = None
                for d,c in facets:
                    if c > 0:
                        try:
                            last_dt = utils.iso_to_datetime(d)
                            val_counts.append(c)
                            vals.append(last_dt.strftime('%Y-%m-%d'))
                        except (TypeError, ValueError):
                            pass
                if vals and last_dt:
                    max_value = min(
                        utils.iso_to_datetime(counts['dates'][name]['end']),
                        utils.d_to_dt(
                            getattr(SearchQuerySet().order_by('-' + name)[0], name)
                        ) + datetime.timedelta(days=1),
                        last_dt + datetime.timedelta(
                            days=int(re.sub('[^\d]', '', counts['dates'][name]['gap']))
                        ),
                    )
                    vals.append(max_value.strftime('%Y-%m-%d'))
                    val_counts.append(0)
                    choice.update({
                        'type': 'date',
                        'counts': val_counts,
                        'vals': vals,
                        'min_value': vals[0],
                        'max_value': vals[-1],
                        'chosen_min': queryargs.get(name + '__gte', ''),
                        'chosen_max': queryargs.get(name + '__lte', ''),
                    })
        choices.append(choice)
    return sqs, choices, constraints, querystr

def _apply_sorting(sqs, qd, base_querystr="", query_var="sort_"):
    """
    Given a SearchQuerySet, a querydict, and an optional definition of the
    query var for sorting, sort the SearchQuerySet by the sort definition
    present in the querydict, and return:
    * The SearchQuerySet ordered by the sorting params
    * a list of links for changing sorting
    * a dict representing current sort params
    """
    sort = qd.get(query_var, settings.DEFAULT_SORT)
    if not sort or sort.strip('-') not in settings.SORT_FIELDS:
        sort = settings.DEFAULT_SORT
    sqs = sqs.order_by(sort)

    # Get links to change sorting
    sort_links = []
    desc = sort[0] == '-'
    sort_by = sort.strip('-')
    for field in settings.SORT_FIELDS:
        if field == sort_by:
            direction = '' if desc else '-'
        else:
            direction = '-' if desc else ''
        new_sort = direction + field
        # Don't show the key in the queryarg if it's default.
        if new_sort == settings.DEFAULT_SORT:
            full_querystr = base_querystr
        else:
            querystr = urllib.urlencode({query_var: new_sort})
            if base_querystr:
                full_querystr = "&".join((base_querystr, querystr))
            else:
                full_querystr = querystr
        sort_links.append({
            'display': settings.ALL_FIELDS[field]['display_name'],
            'desc': desc,
            'querystr': full_querystr,
            'current': field == sort_by,
        })
    if sort == settings.DEFAULT_SORT:
        cur_sort = None
    else:
        cur_sort = { query_var: sort }
    return sqs, sort_links, cur_sort

from __future__ import print_function
import re
import json
import datetime
from collections import defaultdict

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

def render_json(request, obj):
    dumped = json.dumps(obj)
    callback = request.GET.get('callback', None)
    if callback:
        return HttpResponse("%s(%s);" % (callback, dumped),
                content_type="text/javascript")
    return HttpResponse(json.dumps(obj), content_type="application/json")

def render_request(request, template, context=None):
    return render_to_response(template, context or {},
            context_instance=RequestContext(request))

def redirect_to(name, *args, **kwargs):
    return HttpResponseRedirect(reverse(name, args=args, kwargs=kwargs))

def excerpt(text, needles=None):
    """
    Return an excerpt of 'text' which contains the most closely bunched
    instances of search terms in the list 'needles'
    """
    if not needles:
        i = 200
        while i < len(text) and text[i] != " ":
            i += 1
        return text[0:i] + "..."

    # clean text and needles
    text = re.sub("\s+", " ", text)
    needles = [re.sub("[^-A-Z0-9 ]", "", needle.upper()) for needle in needles]

    # Get locations of search terms in cleaned text
    locations = defaultdict(list)
    for term in needles:
        for match in re.finditer(term, text, re.I):
            locations[word].append(match.start())

    # Search for closest matches to choose excerpts
    winner = None
    min_dist = 100000000 # arbitrary high number
    for word1, locs1 in locations.iteritems():
        for loc1 in locs1:
            for word2, locs2 in locations.iteritems():
                if word2 == word1:
                    continue
                loc1_loc2_dist = 1000000000
                best_word2_loc = None
                for loc2 in locs2:
                    dist = abs(loc2 - loc1)
                    # avoid overlapping words
                    if loc2 > loc1 and loc1 + len(word1) > loc2:
                        continue
                    if loc2 < loc1 and loc2 + len(word2) > loc1:
                        continue
                    if dist < loc1_loc2_dist:
                        loc1_loc2_dist = dist
                        best_word2_loc = loc2
                    else:
                        break
                best_locs[best_word2_loc] = word2
            distance = sum(best_locs.keys())
            if distance < min_dist:
                best_locs[loc1] = word1
                winner = best_locs
                min_dist = distance

    # Snip text to build excerpt
    snipped = []
    if winner:
        snips = sorted(winner.items())
        n = 0
        for loc, word in snips:
            snipped.append((text[n:loc], 0))
            snipped.append((text[loc:loc+len(word)], 1))
            n = loc + len(word)
        snipped.append((text[n:], 0))
        out = []
        for i, (snip, bold) in enumerate(snipped):
            if bold:
                out.append("<em>")
                out.append(snip)
                out.append("</em>")
            else:
                if len(snip) > 100:
                    if i != 0:
                        out.append(snip[0:50])
                    out.append(" ... ")
                    if i != len(snipped) - 1:
                        out.append(snip[-50:])
                else:
                    out.append(snip)
        return mark_safe("".join(out))
    else:
        return text[0:200]
            
def iso_to_datetime(iso_date_str):
    return datetime.datetime(*map(int, re.split('[^\d]', iso_date_str)[:-1]))

def d_to_dt(date):
    """ Convert a date to a datetime """
    return datetime.datetime.combine(date, datetime.time(0, 0, 0))

def partial_date(date_str):
    if date_str is None:
        return None
    return datetime.datetime(*[int(a) for a in ((date_str + '-1-1').split('-')[0:3])])

class StatusPrinter(object):
    def __init__(self, c=0, n=0):
        self.c = c
        self.n = n
        self.previous = ""

    def inc(self):
        self.c += 1

    def print(self):
        print("\b" * len(self.previous), end="")
        self.previous = "{0} / {1}".format(self.c, self.n)
        print(self.previous, end="")

    def end(self):
        print()

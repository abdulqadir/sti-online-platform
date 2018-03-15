from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, Http404
from django.db.models import F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from sti.models import Store

def index(request):
    template = loader.get_template('sti/index.html')
    return HttpResponse(template.render({}, request))

def search(request):
    query = request.GET['query'].split(' ')
    search_query = SearchQuery(query[0])
    for i in range(1,len(query)):
        search_query = search_query & SearchQuery(query[i])
    results = Store.objects.all().filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')
    template = loader.get_template('sti/search.html')
    return HttpResponse(template.render({'results':results},request))

def all(request, datatype):
    if datatype == 'publications':
        results = Store.objects.filter(store_type__exact = 'Publication')
    elif datatype == 'technology-offers':
        results = Store.objects.filter(store_type__exact = 'Technology Offer')
    elif datatype == 'technology-requests':
        results = Store.objects.filter(store_type__exact = 'Technology Request')
    elif datatype == 'business-offers':
        results = Store.objects.filter(store_type__exact = 'Business Offer')
    elif datatype == 'business-requests':
        results = Store.objects.filter(store_type__exact = 'Business Request')
    else:
        raise Http404('No records found')
    template = loader.get_template('sti/search.html')
    return HttpResponse(template.render({'results':results},request))

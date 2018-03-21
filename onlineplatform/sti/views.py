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
    publications = Store.objects.filter(store_type = 'Publication').filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')[:3]
    technology = Store.objects.filter(store_type__contains = 'Technology').filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')[:3]
    business = Store.objects.filter(store_type__contains = 'Business').filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')[:3]
    results = Store.objects.filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')
    template = loader.get_template('sti/search.html')
    return HttpResponse(template.render({'publications':publications, 'technology':technology, 'business':business, 'results':results}, request))

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
    template = loader.get_template('sti/all.html')
    return HttpResponse(template.render({'results':results},request))

def source(request, source):
    if source == 'apctt':
        results = Store.objects.filter(partner = 'APCTT C')
    elif source == 'cittc':
        results = Store.objects.filter(partner = 'CITTC C')
    elif source == 'unido':
        results = Store.objects.filter(partner = 'UNIDO C')
    elif source == 'wipogreen':
        results = Store.objects.filter(partner = 'WIPO GREEN C')
    elif source == 'een':
        results = Store.objects.filter(partner = 'EEN C')
    elif source == 'unossc':
        results = Store.objects.filter(partner = 'UNOSSC C')
    elif source == 'openaire':
        results = Store.objects.filter(partner = 'OpenAire')
    else:
        raise Http404('No records found')
    template = loader.get_template('sti/all.html')
    return HttpResponse(template.render({'results':results},request))

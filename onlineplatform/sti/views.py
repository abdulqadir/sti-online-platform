from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, Http404
from django.db.models import F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from sti.models import Store
import json

def index(request):
    template = loader.get_template('sti/index.html')
    return HttpResponse(template.render({}, request))

def get_filters(request):
    filters = {'query': request.POST['query']}
    if request.POST['language'] != '':
        filters['language'] = request.POST['language']
    else:
        filters['language'] = 'any'
    if request.POST['partners'] != '':
        filters['partners'] = json.loads(request.POST['partners'])
        partners = filters['partners']
        actuals = []
        for partner in partners.keys():
            if partners[partner] == False:
                continue
            if partner == 'apctt':
                actuals.append('APCTT C')
            elif partner == 'cittc':
                actuals.append('CITTC C')
            elif partner == 'unido':
                actuals.append('UNIDO C')
            elif partner == 'wipogreen':
                actuals.append('WIPO GREEN C')
            elif partner == 'een':
                actuals.append('EEN C')
            elif partner == 'unossc':
                actuals.append('UNOSSC C')
            elif partner == 'openaire':
                actuals.append('OpenAire')
        filters['partnerlist'] = actuals
    else:
        filters['partners'] = 'all'
    print(filters)
    return filters

def search(request):
    if request.method == 'GET':
        query = request.GET['query'].split(' ')
        filters = {'language':'any', 'partners':'all'}
    else:
        query = request.POST['query'].split(' ')
        filters = get_filters(request)
    search_query = SearchQuery(query[0])
    for i in range(1,len(query)):
        search_query = search_query & SearchQuery(query[i])
    publications = Store.objects.filter(store_type = 'Publication').filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')
    technology = Store.objects.filter(store_type__contains = 'Technology').filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')
    business = Store.objects.filter(store_type__contains = 'Business').filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')
    results = Store.objects.filter(search_vector = search_query).annotate(rank=SearchRank(F('search_vector'), search_query)).order_by('-rank')
    if filters['language'] != 'any':
        publications = publications.filter(language = filters['language'])
        technology = technology.filter(language = filters['language'])
        business = business.filter(language = filters['language'])
        results = results.filter(language = filters['language'])
    if filters['partners'] != 'all':
        publications = publications.filter(partner__in = filters['partnerlist'])
        technology = technology.filter(partner__in = filters['partnerlist'])
        business = business.filter(partner__in = filters['partnerlist'])
        results = results.filter(partner__in = filters['partnerlist'])
    template = loader.get_template('sti/search.html')
    return HttpResponse(template.render({'publications':publications[:3], 'technology':technology[:3], 'business':business[:3], 'results':results, 'filters': filters}, request))

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

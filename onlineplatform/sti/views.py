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
    if request.method == 'GET':
        querydict = request.GET
    else:
        querydict = request.POST
    if 'query' in querydict:
        query = querydict['query'].split(' ')
        filters = {'query': querydict['query']}
    else:
        query = ['']
        filters = {'query':''}
    if 'language' in querydict and querydict['language'] != '':
        config = filters['language'] = querydict['language']
    else:
        filters['language'] = 'any'
        config = None
    if 'partners' in querydict and querydict['partners'] != '':
        filters['partners'] = json.loads(querydict['partners'])
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
    search_query = SearchQuery(query[0], config=config)
    for i in range(1,len(query)):
        search_query = search_query & SearchQuery(query[i], config=config)
    filters['search_query'] = search_query
    return filters

def recommend(request, filters=None, context=None):
    if filters == None:
        filters = get_filters(request)
    publications = Store.objects.filter(store_type = 'Publication').filter(search_vector = filters['search_query']).annotate(rank=SearchRank(F('search_vector'), filters['search_query'])).order_by('-rank')
    technology = Store.objects.filter(store_type__contains = 'Technology').filter(search_vector = filters['search_query']).annotate(rank=SearchRank(F('search_vector'), filters['search_query'])).order_by('-rank')
    business = Store.objects.filter(store_type__contains = 'Business').filter(search_vector = filters['search_query']).annotate(rank=SearchRank(F('search_vector'), filters['search_query'])).order_by('-rank')
    results = Store.objects.filter(search_vector = filters['search_query']).annotate(rank=SearchRank(F('search_vector'), filters['search_query'])).order_by('-rank')
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
    c = {'publications':publications[:3], 'technology':technology[:3], 'business':business[:3], 'results':results[:100], 'filters': filters}
    if context:
        c.update(context)
    return HttpResponse(template.render(c, request))

def search(request):
    return recommend(request)

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
    return HttpResponse(template.render({'results':results, 'hidepartners': True},request))

def sdg(request, sdg):
    if int(sdg) > 17:
        raise Http404('Not found')
    filters = get_filters(request)
    sdg = int(sdg) - 1
    synonyms = [
            'poverty poor',
            'hunger food starvation nutrition stunting malnutrition drought soil farm pastoralist fisher cultivate livestock',
            'health wellbeing well-being mortality death AIDS tuberculosis malaria hepatitis disease alcohol narcotic drug accident healthcare health-care medicine vaccine hazardous pollution contamination tobacco substance abuse injuries health-care',
            'education learning university skills literacy numeracy learners scholarships training teachers',
            'women discrimination marriage trafficking exploitation equal empowerment',
            'water sanitation drinking defecation pollution hygiene wastewater freshwater sanitation harvesting',
            'energy fuel',
            'work economic growth productivity job entrepreneurship enterprises production employment unemployment pay wage labour salary earnings slavery',
            'industry innovation infrastructure industrial enterprise markets technology research internet',
            'inequality income growth empower equal inequal discrimination discriminatory migration migrant',
            'city settlement slum urban municipal peri-urban metropolitan neighbourhood',
            'consumption production waste consumer producer recycling reuse procurement',
            'climate natural',
            'oceans seas marine coastal overfishing fishing fisheries fishery island',
            'terrestrial forest desertification desert land biodiversity conservation inland freshwater wetland mountain dryland deforestation reforestation soil drought floods habitat extinction poaching species flora fauna wildlife',
            'peace justice violence violent abuse exploitation trafficking torture law arms crime stolen corruption bribery legal freedom terrorism',
            'partnership assistance commitment ODA GNI coordinate cooperation dissemination diffusion universal duty-free quota-free'
            ]
    wordlist = synonyms[sdg].split(' ')
    query = SearchQuery(wordlist[0])
    for i in range(1, len(wordlist)):
        query = query | SearchQuery(wordlist[i])
    filters['search_query'] = query
    return recommend(request, filters, {'hidesearch': True})

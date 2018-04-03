from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, Http404
from django.db.models import F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.core.cache import cache
from sti.models import Store, Event
import json

def index(request):
    events = Event.objects.order_by('-date')[:5]
    template = loader.get_template('sti/index.html')
    return HttpResponse(template.render({'events':events}, request))

def get_filters(request):
    if request.method == 'GET':
        querydict = request.GET
    else:
        querydict = request.POST
    if 'query' in querydict:
        filters = {'query': querydict['query']}
    else:
        filters = {'query':''}
    if 'page' in querydict and querydict['page'] != '':
        filters['page'] = int(querydict['page'])
    else:
        filters['page'] = 1
    if 'language' in querydict and querydict['language'] != '':
        config = filters['language'] = querydict['language']
    else:
        filters['language'] = 'any'
        config = None
    if 'type' in querydict and querydict['type'] != '':
        # Strip trailing s
        filters['type'] = querydict['type'][:-1]
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
    search_query = SearchQuery(filters['query'], config=config)
    filters['search_query'] = search_query
    return filters

def filter_results(results, filters):
    if filters['query'] != '':
        results = results.filter(search_vector = filters['search_query']).annotate(rank=SearchRank(F('search_vector'), filters['search_query'])).filter(rank__gte=0.11).order_by('-rank')
    if filters['language'] != 'any':
        results = results.filter(language = filters['language'])
    if filters['partners'] != 'all':
        results = results.filter(partner__in = filters['partnerlist'])
    return results

def recommend(request, filters=None, context=None):
    if filters == None:
        filters = get_filters(request)
    if filters['query'] == '':
        results = Store.objects.none()
        return listresults(results, request, filters, context=context)
    cached = cache.get(str(filters))
    if cached:
        print('Cache hit')
        return cached
    print('Cache miss')
    if 'type' in filters:
        results = filter_results(Store.objects.filter(store_type = filters['type']), filters)
        response = listresults(results, request, filters, context=context)
        cache.set(str(filters), response)
        return response
    publications = filter_results(Store.objects.filter(store_type = 'Publication'), filters)[:3]
    technologyoffers = filter_results(Store.objects.filter(store_type = 'Technology Offer'), filters)[:3]
    businessoffers = filter_results(Store.objects.filter(store_type = 'Business Offer'), filters)[:3]
    technologyrequests = filter_results(Store.objects.filter(store_type = 'Technology Request'), filters)[:3]
    businessrequests = filter_results(Store.objects.filter(store_type = 'Business Request'), filters)[:3]
    available = list(filter(lambda t: len(t) > 0, [publications, technologyoffers, technologyrequests, businessoffers, businessrequests]))
    results = filter_results(Store.objects, filters)
    if filters['page'] == 1 and len(available) > 1 and results.count() > 10:
        paginator = Paginator(results, 10)
        page = paginator.page(filters['page'])
        template = loader.get_template('sti/search.html')
        c = {'recommendations':[{'type':'Publications', 'results':publications},{'type':'Technology Offers', 'results':technologyoffers}, {'type':'Technology Requests', 'results':technologyrequests}, {'type':'Business Offers', 'results':businessoffers}, {'type':'Business Requests', 'results': businessrequests}], 'results':page, 'filters': filters, 'hasprev':page.has_previous(), 'hasnext':page.has_next()}
        if context:
            c.update(context)
        response = HttpResponse(template.render(c, request))
    else:
        response = listresults(results, request, filters, context=context)
    cache.set(str(filters), response)
    return response

def listresults(results, request, filters, context=None):
    paginator = Paginator(results, 10)
    page = paginator.page(filters['page'])
    template = loader.get_template('sti/all.html')
    c = {'results': page, 'filters': filters, 'hasprev':page.has_previous(), 'hasnext':page.has_next()}
    if context:
        c.update(context)
    return HttpResponse(template.render(c, request))

def search(request):
    return recommend(request)

def all(request, datatype):
    if datatype == 'publications':
        results = Store.objects.filter(store_type = 'Publication')
    elif datatype == 'technology-offers':
        results = Store.objects.filter(store_type = 'Technology Offer')
    elif datatype == 'technology-requests':
        results = Store.objects.filter(store_type = 'Technology Request')
    elif datatype == 'business-offers':
        results = Store.objects.filter(store_type = 'Business Offer')
    elif datatype == 'business-requests':
        results = Store.objects.filter(store_type = 'Business Request')
    else:
        raise Http404('No records found')
    filters = get_filters(request)
    results = filter_results(results, filters).order_by('-last_updated')
    return listresults(results, request, filters)

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
    filters = get_filters(request)
    results = filter_results(results, filters).order_by('-last_updated')
    return listresults(results, request, filters, context={'hidepartners': True})

def sdg(request, sdg):
    if int(sdg) > 17:
        raise Http404('Not found')
    filters = get_filters(request)
    sdg = int(sdg) - 1
    queries = [
            SearchQuery('poverty'),
            SearchQuery('hunger') | SearchQuery('starvation') | SearchQuery('stunting') | SearchQuery('malnutrition'),
            (SearchQuery('health') | SearchQuery('mortality') | SearchQuery('death') | SearchQuery('disease')) & (SearchQuery('care') | SearchQuery('prevention') | SearchQuery('medicine') | SearchQuery('vaccine') | SearchQuery('reduction') | SearchQuery('abuse') | SearchQuery('improve')),
            SearchQuery('education') & (SearchQuery('learn') | SearchQuery('university') | SearchQuery('skills') | SearchQuery('literacy') | SearchQuery('numeracy') | SearchQuery('scholarship') | SearchQuery('training') | SearchQuery('teachers')),
            (SearchQuery('women') | SearchQuery('girl') | SearchQuery('woman') | SearchQuery('female')) & (SearchQuery('discrimination') | SearchQuery('trafficking') | SearchQuery('exploitation') | SearchQuery('equal') | SearchQuery('empowerment')),
            SearchQuery('water') & (SearchQuery('sanitation') | SearchQuery('drinking') | SearchQuery('defecation') | SearchQuery('pollution') | SearchQuery('hygiene') | SearchQuery('wastewater') | SearchQuery('freshwater') | SearchQuery('harvesting')),
            (SearchQuery('energy') | SearchQuery('fuel')) & (SearchQuery('green') | SearchQuery('clean') | SearchQuery('affordable') | SearchQuery('cheap')),
            (SearchQuery('work') | SearchQuery( 'economic') | SearchQuery('job') | SearchQuery('entrepreneurship')) & (SearchQuery('growth') | SearchQuery('productivity') | SearchQuery('enterprise') | SearchQuery('production') | SearchQuery('employment') | SearchQuery('unemployment') | SearchQuery('pay') | SearchQuery('wage') | SearchQuery('labour') | SearchQuery('salary') | SearchQuery('earning')),
            (SearchQuery('industry') | SearchQuery('innovation')) & (SearchQuery('infrastructure') | SearchQuery('enterprise') | SearchQuery('markets') | SearchQuery('technology') | SearchQuery('research') | SearchQuery('internet')),
            (SearchQuery('inequality') | SearchQuery('equality')) & (SearchQuery('income') | SearchQuery('growth') | SearchQuery('empower') | SearchQuery('discrimination') | SearchQuery('migrant') | SearchQuery('reduce')),
            (SearchQuery('city') | SearchQuery('urban')) & (SearchQuery('settlement') | SearchQuery('slum') | SearchQuery('municipal') | SearchQuery('peri-urban') | SearchQuery('metropolitan') | SearchQuery('neighbourhood')),
            (SearchQuery('consumption') | SearchQuery('production')) & (SearchQuery('waste') | SearchQuery('consumer') | SearchQuery('producer') | SearchQuery('recycling') | SearchQuery('reuse')),
            SearchQuery('climate') & SearchQuery('natural'),
            (SearchQuery('ocean') | SearchQuery('sea')) & (SearchQuery('marine') | SearchQuery('coastal') | SearchQuery('overfishing') | SearchQuery('fishing') | SearchQuery('fishery') | SearchQuery('island')),
            (SearchQuery('land') | SearchQuery('terrestrial') | SearchQuery('forest') | SearchQuery('desert')) & (SearchQuery('desertification') | SearchQuery('biodiversity') | SearchQuery('conservation') |SearchQuery('inland') | SearchQuery('freshwater') | SearchQuery('wetland') | SearchQuery('mountain') | SearchQuery('dryland') | SearchQuery('soil') | SearchQuery('drought') | SearchQuery('floods') | SearchQuery('habitat') | SearchQuery('extinction') | SearchQuery('poaching') | SearchQuery('species') | SearchQuery('flora') | SearchQuery('fauna') | SearchQuery('wildlife')),
            (SearchQuery('peace') | SearchQuery('justice')) & (SearchQuery('violence') | SearchQuery('abuse') | SearchQuery('exploitation') | SearchQuery('trafficking') | SearchQuery('torture') | SearchQuery('law') | SearchQuery('arms') | SearchQuery('crime') | SearchQuery('stolen') | SearchQuery('corruption') | SearchQuery('bribery') | SearchQuery('legal') | SearchQuery('freedom') | SearchQuery('terrorism')),
            (SearchQuery('partnership') | SearchQuery('assistance') | SearchQuery('cooperation') | SearchQuery('coordinate')) & (SearchQuery('commitment') | SearchQuery('ODA') | SearchQuery('GNI') | SearchQuery('dissemination') | SearchQuery('diffusion') | SearchQuery('universal') | SearchQuery('duty-free') | SearchQuery('quota-free'))
            ]
    filters['query'] = 'sdg' + str(sdg+1)
    filters['search_query'] = queries[sdg]
    return recommend(request, filters, {'hidesearch': True})

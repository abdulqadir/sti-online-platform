from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, Http404
from django.db import connection
from django.db.models import F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils import html
from sti.models import Store, Event
import json, re

def index(request):
    events = Event.objects.order_by('-date')[:5]
    template = loader.get_template('sti/index.html')
    return HttpResponse(template.render({'sdgs':range(1,18), 'events':events}, request))

def get_filters(request):
    querydict = request.GET
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
        filters['language'] = 'all'
        config = None
    if 'location' in querydict and querydict['location'] != '':
        filters['location'] = querydict['location']
    else:
        filters['location'] = 'all'
    if 'types' in querydict and querydict['types'] != '':
        filters['types'] = json.loads(querydict['types'])
        types = filters['types']
        actuals = []
        for t in types.keys():
            if types[t] == False:
                continue
            if t == 'publications':
                actuals.append('Publication')
            elif t == 'technologyoffers':
                actuals.append('Technology Offer')
            elif t == 'technologyrequests':
                actuals.append('Technology Request')
            elif t == 'businessoffers':
                actuals.append('Business Offer')
            elif t == 'businessrequests':
                actuals.append('Business Request')
        filters['typelist'] = actuals
    else:
        filters['types'] = 'all'
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
            elif partner == 'unfccc':
                actuals.append('UNFCCC C')
            elif partner == 'unossc':
                actuals.append('UNOSSC C')
            elif partner == 'openaire':
                actuals.append('OpenAire')
        filters['partnerlist'] = actuals
    else:
        filters['partners'] = 'all'
    search_query = SearchQuery(filters['query'], config=config)
    filters['search_query'] = search_query
    print(filters)
    return filters

def filter_results(results, filters):
    if filters['language'] != 'all':
        results = results.filter(language = filters['language'])
    if filters['location'] != 'all':
        results = results.filter(location = filters['location'])
    if filters['partners'] != 'all':
        results = results.filter(partner__in = filters['partnerlist'])
    if filters['types'] != 'all':
        results = results.filter(store_type__in = filters['typelist'])
    if filters['query'] != '':
        results = results.filter(search_vector = filters['search_query']).annotate(rank=SearchRank(F('search_vector'), filters['search_query'])).filter(rank__gte=0.11).order_by('-rank')
    else:
        results = results.order_by('-last_updated')
    return results

def paginate(request, page):
    q = request.GET.copy()
    resp = {'prev':False, 'next':False}
    if page.has_previous():
        q['page'] = page.previous_page_number()
        resp['prev'] = request.path + '?' + q.urlencode(safe="{}")
    if page.has_next():
        q['page'] = page.next_page_number()
        resp['next'] = request.path + '?' + q.urlencode(safe="{}")
    return resp

def highlight(page, query):
    cursor = connection.cursor()
    for result in page:
        if result.language in ['french','german','spanish','russian','danish','dutch','finnish','hungarian','italian','norwegian','portuguese','romanian','swedish','turkish']:
            config = result.language
        else:
            config = 'english'
        cursor.execute("Select ts_headline(%s, %s, plainto_tsquery(%s), 'MaxWords=100, MaxFragments=10')",[config, result.description, query])
        r = cursor.fetchone()
        if r[0]:
            result.description = r[0]
    return page

def search(request, filters=None, context=None):
    if filters == None:
        filters = get_filters(request)
    if filters['query'] == '' and filters['types'] == 'all' and filters['language'] == 'all' and filters['partners'] == 'all' and filters['location'] == 'all':
        results = Store.objects.none()
        return listresults(results, request, filters, context=context)
    cached = cache.get(str(filters))
    if cached:
        print('Cache hit')
        return cached
    print('Cache miss')
    publications = filter_results(Store.objects.filter(store_type = 'Publication'), filters)[:3]
    technologyoffers = filter_results(Store.objects.filter(store_type = 'Technology Offer'), filters)[:3]
    businessoffers = filter_results(Store.objects.filter(store_type = 'Business Offer'), filters)[:3]
    technologyrequests = filter_results(Store.objects.filter(store_type = 'Technology Request'), filters)[:3]
    businessrequests = filter_results(Store.objects.filter(store_type = 'Business Request'), filters)[:3]
    available = list(filter(lambda t: t.count() > 0, [publications, technologyoffers, technologyrequests, businessoffers, businessrequests]))
    results = filter_results(Store.objects, filters)
    if filters['page'] == 1 and len(available) > 1 and results.count() > 10:
        paginator = Paginator(results, 10)
        page = paginator.page(filters['page'])
        for result in page:
            result.description = html.escape(result.description)
        if filters['query']:
            page = highlight(page, filters['query'])
        for result in page:
            result.description = re.sub(r'&lt;\s*[bB][rR]\s*/?&gt;','<br/>',result.description)
        template = loader.get_template('sti/search.html')
        pages = paginate(request, page)
        c = {'recommendations':[{'type':'Publications', 'results':publications},{'type':'Technology Offers', 'results':technologyoffers}, {'type':'Technology Requests', 'results':technologyrequests}, {'type':'Business Offers', 'results':businessoffers}, {'type':'Business Requests', 'results': businessrequests}], 'results':page, 'filters': filters, 'prev':pages['prev'], 'next':pages['next']}
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
    for result in page:
        result.description = html.escape(result.description)
    if filters['query']:
        page = highlight(page, filters['query'])
    for result in page:
        result.description = re.sub(r'&lt;\s*[bB][rR]\s*/?&gt;','<br/>',result.description)
    pages = paginate(request, page)
    template = loader.get_template('sti/all.html')
    c = {'results': page, 'filters': filters, 'prev':pages['prev'], 'next':pages['next']}
    if context:
        c.update(context)
    return HttpResponse(template.render(c, request))

def sdg(request, sdg):
    if int(sdg) > 17:
        raise Http404('Not found')
    filters = get_filters(request)
    sdg = int(sdg) - 1
    queries = [
            SearchQuery('poverty'),
            SearchQuery('hunger') | SearchQuery('starvation') | SearchQuery('stunting') | SearchQuery('malnutrition'),
            (SearchQuery('health') | SearchQuery('disease')) & (SearchQuery('care') | SearchQuery('prevention') | SearchQuery('medicine') | SearchQuery('vaccine') | SearchQuery('reduction') | SearchQuery('abuse')),
            SearchQuery('education') & (SearchQuery('university') | SearchQuery('skills') | SearchQuery('literacy') | SearchQuery('numeracy') | SearchQuery('scholarship') | SearchQuery('training') | SearchQuery('teachers')),
            (SearchQuery('women') | SearchQuery('girl') | SearchQuery('female')) & (SearchQuery('discrimination') | SearchQuery('trafficking') | SearchQuery('exploitation') | SearchQuery('equal') | SearchQuery('empowerment')),
            SearchQuery('water') & (SearchQuery('sanitation') | SearchQuery('drinking') | SearchQuery('defecation') | SearchQuery('pollution') | SearchQuery('hygiene') | SearchQuery('wastewater') | SearchQuery('freshwater') | SearchQuery('harvesting')),
            (SearchQuery('energy') | SearchQuery('fuel')) & (SearchQuery('green') | SearchQuery('clean') | SearchQuery('affordable') | SearchQuery('cheap')),
            (SearchQuery('work') | SearchQuery( 'economic growth') | SearchQuery('job') | SearchQuery('entrepreneurship')) & (SearchQuery('productivity') | SearchQuery('enterprise') | SearchQuery('employment') | SearchQuery('unemployment') | SearchQuery('pay') | SearchQuery('wage') | SearchQuery('labour') | SearchQuery('salary') | SearchQuery('earning')),
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
    return search(request, filters, {'hidesearch': True})

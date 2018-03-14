from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from sti.models import Store

def index(request):
    template = loader.get_template('sti/index.html')
    return HttpResponse(template.render({}, request))

def search(request):
    query = SearchQuery(request.GET['query'])
    vector = SearchVector('title',weight='A') + SearchVector('description',weight='B')
    #results = Publication.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.53).order_by('-rank')
    results = Store.objects.filter(search_vector=query)
    template = loader.get_template('sti/search.html')
    return HttpResponse(template.render({'results':results},request))

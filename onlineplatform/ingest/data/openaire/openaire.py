# To fetch data
# pip install oaiharvest
# then
# oai-harvest -s <setname> http://api.openaire.eu/oai_pmh
import requests
import time
from xml.etree import ElementTree
import os, re
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'onlineplatform.settings'
import django
django.setup()
from sti.models import Store
from django.contrib.postgres.search import SearchVector

if (not os.access('.processed',os.F_OK)):
    os.mkdir('.processed')

for s in os.listdir('data'):
    if not os.access('.processed/' + s,os.F_OK):
        os.mkdir('.processed/' + s)
    for xml in os.listdir('data/'+s):
        try:
            store = Store.objects.get(client_id=xml)
        except Store.DoesNotExist:
            store = Store()
            store.client_id = xml
            store.store_type = 'Publication'
            store.partner = 'OpenAire'
        store.raw_data = open('data/' + s + '/' + xml,'r').read()
        oaidc = ElementTree.fromstring(store.raw_data)
        nsdc = '{http://purl.org/dc/elements/1.1/}'
        store.title = oaidc.find(nsdc + 'title').text
        if len(store.title) > 2048:
            store.title = store.title[:2048]
        store.description = '\n'.join(map(lambda d:d.text, filter(lambda d:d.text!=None,oaidc.findall(nsdc + 'description'))))
        config = 'english'
        language = oaidc.find(nsdc + 'language')
        if language != None:
            language = language.text
        if language != None and language not in ['und','mis','mul']:
            found = False
            if language[0] == "'" and language[-1] == "'":
                language = language[1:-1]
            # Language code lookup as per ISO 639-3
            lookup = {'eng':'english','por':'portuguese','deu/ger':'german','fra/fre':'french','spa':'spanish','esl/spa':'spanish','hun':'hungarian','jpn':'japanese','lit':'lithuanian','ita':'italian','gre/ell':'greek','ell/gre':'greek','dut/nld':'dutch','hrv':'croatian','srp':'serbian','cat':'catalan','sit':'sino-tibetan','nor':'norwegian','nob':'norwegian','nno':'norwegian','rus':'russian','dan':'danish','vie':'vietnamese','ces/cze':'czech','ukr':'ukrainian','tur':'turkish','lav':'latvian','swe':'swedish','slk/slo':'slovak','slv':'slovenian','ara':'arabic','nau':'nauru','ron/rum':'romanian','chi/zho':'chinese','bul':'bulgarian','enm':'middle english','srr':'serer','ang':'old english','cym/wel':'welsh','lat':'latin','fin':'finnish','pol':'polish','fas/per':'persian','bel':'belarusian','ind':'indonesian','ota':'ottoman turkish','baq/eus':'basque','heb':'hebrew','glg':'galician','afr':'afrikaans','lad':'ladino','grc':'ancient greek','est':'estonian','may/msa':'malay','kor':'korean','epo':'esperanto','sme':'northern sami','pan':'panjabi','tam':'tamil','non':'old norse'}
            if language in lookup.keys():
                language = lookup[language]
                found = True
            if language in ['danish', 'dutch', 'english', 'finnish', 'french', 'german', 'hungarian', 'italian', 'norwegian', 'portuguese', 'romanian', 'russian', 'spanish', 'swedish', 'turkish']:
                config = language
            elif not found:
                print('Unknown language:' + language)
                raise Exception(language)
            store.language = language
        store.keywords = ' '.join(map(lambda x:x.text,filter(lambda x:x.text!=None,oaidc.findall(nsdc + 'subject'))))
        try:
            store.url = oaidc.find(nsdc + 'identifier').text
        except:
            print('No URL found for ' + s + '/' + xml)
        store.save()
        store.search_vector = SearchVector('title', weight='A', config=config) + SearchVector('keywords', weight='D', config=config) + SearchVector('description', weight='C', config=config)
        store.save()
        os.rename('data/' + s + '/' + xml, '.processed/' + s + '/' + xml)

# To fetch data
# pip install oaiharvest
# then
# oai-harvest https://openknowledge.worldbank.org/oai/request
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

for xml in os.listdir('data'):
    try:
        store = Store.objects.get(client_id=xml)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = xml
        store.store_type = 'Publication'
        store.partner = 'World Bank'
    oaidc = ElementTree.fromstring(open('data/' + xml,'r').read())
    nsdc = '{http://purl.org/dc/elements/1.1/}'
    try:
        store.title = oaidc.find(nsdc + 'title').text
    except:
        print("No title found: "+xml)
        continue
    if len(store.title) > 2048:
        store.title = store.title[:2048]
    store.description = '\n'.join(map(lambda d:d.text, filter(lambda d:d.text!=None,oaidc.findall(nsdc + 'description'))))
    config = 'english'
    language = oaidc.find(nsdc + 'language')
    if language != None:
        language = language.text.lower()
        if language in ['cambodian,english','portuguese,english']:
            language = 'english'
        language = language.split(',')[0]
        if language in ['en_us', 'en']:
            language = 'english'
        if language in ['danish', 'dutch', 'english', 'finnish', 'french', 'german', 'hungarian', 'italian', 'norwegian', 'portuguese', 'romanian', 'russian', 'spanish', 'swedish', 'turkish']:
            config = language
        elif language not in ['cambodian','polish','arabic','chinese']:
            raise Exception(language)
        store.language = language
    store.keywords = ' '.join(map(lambda x:x.text,filter(lambda x:x.text!=None,oaidc.findall(nsdc + 'subject'))))
    store.location = ' '.join(map(lambda x:x.text,filter(lambda x:x.text!=None,oaidc.findall(nsdc + 'coverage'))))
    store.url = re.sub('https?://hdl.handle.net','https://openknowledge.worldbank.org/handle', oaidc.find(nsdc + 'identifier').text)
    print(store.title, store.description, store.language, store.keywords, store.url, store.location)
    store.save()
    store.search_vector = SearchVector('title', weight='A', config=config) + SearchVector('keywords', weight='D', config=config) + SearchVector('description', weight='C', config=config)
    store.save()
    os.rename('data/' + xml, '.processed/' + xml)

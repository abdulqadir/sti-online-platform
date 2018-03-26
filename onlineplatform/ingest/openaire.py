import requests
import time
from xml.etree import ElementTree
import os
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'onlineplatform.settings'
import django
django.setup()
from sti.models import Store
from ingest.models import Metadata
from datetime import date, timedelta
from django.contrib.postgres.search import SearchVector

def scrape():
    try:
        metadata = Metadata.objects.get(partner='openaire')
    except Metadata.DoesNotExist:
        metadata = Metadata()
        metadata.partner = 'openaire'
        metadata.keyval = {'nextDate':'2015-01-01'}
        metadata.save()
    while True:
        frm = list(map(lambda s:int(s), metadata.keyval['nextDate'].split('-')))
        nxt = date(frm[0], frm[1], frm[2]) + timedelta(days=1)
        if nxt > date(2018,1,1):
            return;
        toDate = nxt.strftime('%Y-%m-%d')
        for page in range(1,1001):
            url = 'http://api.openaire.eu/search/publications?fromDateAccepted='+ metadata.keyval['nextDate'] + '&toDateAccepted='+ toDate +'&page='+str(page)
            r = requests.get(url)
            if r.status_code == 200:
                print(url)
                root = ElementTree.fromstring(r.text)
                results = root.findall('results/result')
                if len(results) == 0:
                    break
                for result in results:
                    client_id = result.find('header/{http://www.driver-repository.eu/namespace/dri}objIdentifier').text
                    try:
                        publication = Store.objects.get(client_id = client_id)
                    except Store.DoesNotExist:
                        publication = Store()
                        publication.client_id = client_id
                    publication.partner = 'OpenAire'
                    publication.store_type = 'Publication'
                    print(publication.client_id)
                    publication.raw_data = ElementTree.tostring(result)
                    publication.save()
        metadata.keyval = {'nextDate': toDate}
        metadata.save()

def parse():
    while True:
        update = Store.objects.all().filter(title='')[:100]
        if len(update) == 0:
            return
        for publication in update:
            result = ElementTree.fromstring(publication.raw_data)
            publication.title = result.find('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/title').text
            if len(publication.title) > 2048:
                publication.title = publication.title[:2048]
            publication.description = '\n'.join(map(lambda d:d.text, filter(lambda d:d.text != None, result.findall('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/description'))))
            language = result.find('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/language')
            config = 'simple'
            language = language.get('classname').lower().split(';')[0]
            if language in ['danish', 'dutch', 'english', 'finnish', 'french', 'german', 'hungarian', 'italian', 'norwegian', 'portuguese', 'romanian', 'russian', 'spanish', 'swedish', 'turkish']:
                config = language
            publication.language = language
            try:
                publication.url = result.findall('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/children/instance/webresource/url')[0].text
            except Exception:
                print('No URL found for ' + publication.client_id)
                publication.url = ''
            print(publication.language, publication.url, publication.title)
            publication.save()
            publication.search_vector = SearchVector('title', weight='A', config=config) + SearchVector('keywords', weight='D', config=config) + SearchVector('description', weight='C', config=config)
            publication.save()

parse()

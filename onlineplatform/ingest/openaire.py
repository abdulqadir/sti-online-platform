import requests
import time
from xml.etree import ElementTree
import os
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'onlineplatform.settings'
import django
django.setup()
from sti.models import Publication
from ingest.models import Metadata

def scrape():
    try:
        metadata = Metadata.objects.get(partner='openaire')
    except Metadata.DoesNotExist:
        metadata = Metadata()
        metadata.partner = 'openaire'
        metadata.keyval = {'nextDate':'2015-01-01'}
        metadata.save()
    fromDate = metadata.keyval['nextDate'].split('-')
    for page in range(1,1001):
        r = requests.get('http://api.openaire.eu/search/publications?fromDateAccepted=2015-01-01&toDateAccepted=2017-12-31&page='+str(page))
        if r.status_code == 200:
            root = ElementTree.fromstring(r.text)
            for result in root.findall('results/result'):
                publication = Publication()
                publication.client_id = result.find('header/{http://www.driver-repository.eu/namespace/dri}objIdentifier').text
                publication.title = result.find('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/title').text
                publication.description = '\n'.join(map(lambda d:d.text, filter(lambda d:d.text != None, result.findall('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/description'))))
                print(publication.client_id, publication.title, publication.description)
                publication.raw_data = ElementTree.tostring(result)
                publication.save()

def language():
    update = Publication.objects.all().filter(language='')
    for publication in update:
        result = ElementTree.fromstring(publication.raw_data)
        language = result.find('metadata/{http://namespace.openaire.eu/oaf}entity/{http://namespace.openaire.eu/oaf}result/language')
        if language != None:
            language = language.get('classname').lower().split(';')[0]
            if language in ['danish', 'dutch', 'english', 'finnish', 'french', 'german', 'hungarian', 'italian', 'norwegian', 'portuguese', 'romanian', 'russian', 'spanish', 'swedish', 'turkish']:
                publication.language = language
                print(publication.language)
                publication.save()
                continue
        publication.language = ''
        publication.save()


language()

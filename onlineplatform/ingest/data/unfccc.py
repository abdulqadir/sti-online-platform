import json
import os
import sys
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'onlineplatform.settings'
    sys.path.append('/'.join(os.getcwd().split('/')[:-2]))
import django
django.setup()
from django.contrib.postgres.search import SearchVector
from sti.models import Store

people = json.loads(open('unfccc/country-data.json','r').read())
for record in people['rows']:
    rec = 1
    for person in record['Focal points']:
        client_id = 'unfccc_people_'  + record['Country'] + str(rec)
        try:
            store = Store.objects.get(client_id=client_id)
        except Store.DoesNotExist:
            store = Store()
            store.client_id = client_id
            store.store_type = 'People'
            store.partner = 'UNFCCC C'
            store.language = 'english'
        store.title = person['Name']
        store.description = person['Position'] + '\n' + record['Name'] + ' ' + record['Acronym'] + '\n' + record['Physical address'] + '\n' + record['Website']
        store.url = 'http://unfccc.int/ttclear/support/national-designated-entity.html'
        store.raw_data = json.dumps(record)
        store.location = record['Country']
        store.save()
        rec += 1
        store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
        store.save()
        print(store.client_id, store.title)

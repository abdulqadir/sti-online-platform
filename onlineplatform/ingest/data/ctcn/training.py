import requests
import datetime
import os, re, json
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'onlineplatform.settings'
import django
django.setup()
from sti.models import Store
from django.contrib.postgres.search import SearchVector

url = 'https://www.ctc-n.org/api/webinarrecordings'
r = requests.get(url)
if r.status_code == 200:
    results = json.loads(r.text)
    for result in results:
        client_id = 'CTCN-' + result['Nid']
        try:
            event = Store.objects.get(client_id = client_id)
        except Store.DoesNotExist:
            event = Store()
            event.client_id = client_id
            event.store_type = 'Training'
            event.partner = 'CTCN'
        event.title = result['Title']
        event.description = result['Body']
        event.language = 'english'
        event.keywords = ' '.join(result['CTCN Keyword Matches'])
        event.raw_data = json.dumps(result)
        event.url = result['url']
        if 'value' in result['Date and time'] and 'value2' in result['Date and time']:
            event.meta_data = {'from': result['Date and time']['value'], 'to': result['Date and time']['value2']}
        event.save()
        event.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
        event.save()
        print(event.client_id, event.title)

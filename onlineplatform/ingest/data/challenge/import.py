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
import csv

csvreader = csv.DictReader(open('data/unfccc/unfccc_data_with_summaries.csv','r'))
rec = 1
for record in csvreader:
    client_id = 'unfccc_c_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Project'
        store.partner = 'UNFCCC C'
        store.language = 'english'
    store.title = record['title']
    store.description = record['summary']
    store.url = record['document_url']
    store.raw_data = str(record)
    store.keywords = record['keywords']
    store.location = record['country']
    store.save()
    rec += 1
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    print(store.client_id, store.title)

records = json.loads(open('data/apctt/offers.json','r').read())
rec = 1
for record in records:
    client_id = 'apctt_c_offer_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Technology Offer'
        store.partner = 'APCTT C'
        store.language = 'english'
    store.title = record['title']
    store.description = record['description']
    store.url = record['url']
    store.raw_data = json.dumps(record)
    store.keywords = record['keywords'] + ' ' + record['sector']
    store.location = record['country']
    store.save()
    rec += 1
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    print(store.client_id, store.title)

records = json.loads(open('data/apctt/requests.json','r').read())
rec = 1
for record in records:
    client_id = 'apctt_c_request_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Technology Request'
        store.partner = 'APCTT C'
        store.language = 'english'
    store.title = record['title']
    store.description = record['description']
    store.url = record['url']
    store.raw_data = json.dumps(record)
    store.keywords = record['keywords'] + ' ' + record['sector']
    store.location = record['country']
    store.save()
    rec += 1
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    print(store.client_id, store.title)

records = json.loads(open('data/cittc/cittc_offers.json','r').read())
rec = 1
for record in records:
    client_id = 'cittc_c_offer_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Technology Offer'
        store.partner = 'CITTC C'
        store.language = 'english'
    store.title = record['title']
    store.description = record['description']
    store.raw_data = json.dumps(record)
    if record['keywords']:
        store.keywords = record['keywords']
    else:
        store.keywords = ''
    if record['sector']:
        store.keywords = store.keywords + ' ' + record['sector']
    if record['secondary_field']:
        store.keywords = store.keywords + ' ' + record['secondary_field']
    if record['country']:
        store.location = record['country']
    store.save()
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    rec += 1
    print(store.client_id, store.title)

records = json.loads(open('data/cittc/cittc_requests.json','r').read())
rec = 1
for record in records:
    client_id = 'cittc_c_request_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Technology Request'
        store.partner = 'CITTC C'
        store.language = 'english'
    store.title = record['title']
    store.description = record['description']
    store.url = record['meta_base_url']
    store.raw_data = json.dumps(record)
    if record['keywords']:
        store.keywords = record['keywords']
    else:
        store.keywords = ''
    if record['sector']:
        store.keywords = store.keywords + ' ' + record['sector']
    if record['secondary_field']:
        store.keywords = store.keywords + ' ' + record['secondary_field']
    if record['country']:
        store.location = record['country']
    store.save()
    rec += 1
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    print(store.client_id, store.title)

records = json.loads(open('data/unido/clean_article_content.json','r').read())
rec = 1
for record in records:
    client_id = 'unido_c_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Technology Offer'
        store.partner = 'UNIDO C'
        store.language = 'english'
    if record['meta_category'] != store.store_type:
        print(record['meta_category'])
        raise Exception()
    store.title = record['title']
    store.description = record['description']
    store.location = 'Japan'
    store.url = record['meta_base_url']
    store.raw_data = json.dumps(record)
    if record['applications']:
        store.keywords = record['applications']
    else:
        store.keywords = ''
    store.save()
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    rec += 1
    print(store.client_id, store.title)

records = json.loads(open('data/wipo_green/wipo_green.json','r').read())
rec = 1
for record in records:
    client_id = 'wipo_green_c_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.partner = 'WIPO GREEN C'
        store.language = 'english'
    if record['meta_category'] == 'need':
        store.store_type = 'Technology Request'
    elif record['meta_category'] == 'offer':
        store.store_type = 'Technology Offer'
    else:
        raise Exception()
    store.title = record['title']
    if 'project_summary' in record and record['project_summary']:
        store.description = record['project_summary']
    else:
        store.description = ''
    if record['benefits']:
        store.description = store.description + ' ' + record['benefits']
    store.raw_data = json.dumps(record)
    if record['sector']:
        store.keywords = record['sector']
    else:
        store.keywords = ''
    if record['technical_fields']:
        store.keywords = store.keywords + ' ' + record['technical_fields']
    store.save()
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    rec += 1
    print(store.client_id, store.title)

records = json.loads(open('data/een/een.json','r').read())
rec = 1
for record in records:
    client_id = 'een_c_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.partner = 'EEN C'
        store.language = 'english'
    if record['type'] == 'Bus. Offer':
        store.store_type = 'Business Offer'
    elif record['type'] == 'Bus. Request':
        store.store_type = 'Business Request'
    elif record['type'] == 'Tech. Offer' or record['type'] == 'R&D Request':
        store.store_type = 'Technology Offer'
    elif record['type'] == 'Tech. Request':
        store.store_type = 'Technology Request'
    else:
        print(record['type'])
        raise Exception()
    store.title = record['title']
    store.description = record['description']
    store.url = record['meta_base_url']
    store.raw_data = json.dumps(record)
    if record['market_keywords']:
        store.keywords = record['market_keywords']
    else:
        store.keywords = ''
    if record['nace_keywords']:
        store.keywords = store.keywords + ' ' + record['nace_keywords']
    if record['country']:
        store.location = record['country']
    store.save()
    rec += 1
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    print(store.client_id, store.title)

records = json.loads(open('data/south_south/unossc_data.json','r').read())
rec = 1
for record in records:
    client_id = 'unossc_c_' + str(rec)
    try:
        store = Store.objects.get(client_id=client_id)
    except Store.DoesNotExist:
        store = Store()
        store.client_id = client_id
        store.store_type = 'Publication'
        store.partner = 'UNOSSC C'
        store.language = 'english'
    store.title = record['chapter_title']
    store.description = record['abstract']
    store.url = record['document_url']
    store.raw_data = json.dumps(record)
    if record['mdg']:
        store.keywords = record['mdg']
    else:
        store.keywords = ''
    if record['thematic_area']:
        store.keywords = store.keywords + ' ' + record['thematic_area']
    if record['chapter_title']:
        store.keywords = store.keywords + ' ' + record['chapter_title']
    if record['country']:
        store.location = record['country']
    store.save()
    rec += 1
    store.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
    store.save()
    print(store.client_id, store.title)

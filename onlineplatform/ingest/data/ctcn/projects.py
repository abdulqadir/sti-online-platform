import requests
import datetime
import os, re, json
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'onlineplatform.settings'
import django
django.setup()
from sti.models import Store
from django.contrib.postgres.search import SearchVector

url = 'https://www.ctc-n.org/api/projects'
r = requests.get(url)
if r.status_code == 200:
    results = json.loads(r.text)
    for result in results:
        client_id = 'CTCN-' + result['nid']
        try:
            event = Store.objects.get(client_id = client_id)
        except Store.DoesNotExist:
            event = Store()
            event.client_id = client_id
            event.store_type = 'Project'
            event.partner = 'CTCN'
        event.title = result['Title']
        event.description = result['Description']
        event.language = 'english'
        event.keywords = ' '.join(result['CTCN Keyword Matches']) + ' '  + ' '.join(result['Sustainable Development Goals']) + ' '  + ' '.join(result['Relevant technologies'])
        event.raw_data = json.dumps(result)
        event.url = result['URL']
        # Lookup country code based on ISO 3166
        # https://www.iso.org/obp/ui/#search
        country_lookup = {'SB':'Solomon Islands', 'AR':'Argentina', 'AF':'Afghanistan', 'CO':'Colombia', 'AZ':'Azerbaijan', 'ZM':'Zambia', 'CL':'Chile', 'NP':'Nepal', 'ZW':'Zimbabwe', 'TO':'Tonga', 'TG':'Togo', 'BZ':'Belize', 'SN':'Senegal', 'NG':'Nigeria', 'KE':'Kenya', 'NE':'Niger', 'MM':'Myanmar', 'AG':'Antigua and Barbuda', 'MG':'Madagascar', 'BT':'Bhutan', 'HN':'Honduras', 'CG':'Congo', 'UG':'Uganda', 'MW':'Malawi', 'ET':'Ethiopia', 'BA':'Bosnia and Herzegovina', 'GE':'Georgia', 'GT':'Guatemala', 'GH':'Ghana', 'BF':'Burkina Faso', 'SC':'Seychelles', 'PS':'Palestine, State of', 'KI':'Kiribati', 'UY':'Uruguay', 'TH':'Thailand', 'ZA':'South Africa', 'AM':'Armenia', 'PE':'Peru', 'DO':'Dominican Republic', 'GN':'Guinea', 'CR':'Costa Rica', 'EC':'Ecuador', 'CI':'Côte d\'Ivoire', 'GM':'Gambia', 'MU':'Mauritius', 'BD':'Bangladesh', 'ML':'Mali', 'SL':'Sierra Leone', 'MH':'Marshall Islands', 'CF':'Central African Republic', 'BR':'Brazil', 'IR':'Iran (Islamic Republic of)', 'LR':'Liberia', 'BW':'Botswana', 'GD':'Grenada', 'BJ':'Benin', 'PK':'Pakistan', 'PG':'Papua New Guinea', 'RS':'Serbia', 'SZ':'Swaziland', 'VN':'Vietnam', 'PY':'Paraguay', 'MZ':'Mozambique', 'TN':'Tunisia', 'NA':'Namibia', 'BS':'Bahamas', 'PA':'Panama', 'ID':'Indonesia', 'TZ':'Tanzania, United Republic of', 'JO':'Jordan', 'AL':'Albania', 'DZ':'Algeria', 'LA':'Lao People\'s Democratic Republic', 'LS':'Lesotho', 'PW':'Palau'}
        event.location = ' '.join(map(lambda c:country_lookup[c], result['Countries']))
        event.save()
        event.search_vector = SearchVector('title', weight='A', config='english') + SearchVector('keywords', weight='D', config='english') + SearchVector('description', weight='C', config='english')
        event.save()
        print(event.client_id, event.title)

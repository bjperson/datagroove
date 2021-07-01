#! /usr/bin/env python3
# -*- coding: utf8 -*-
#
#  DataGroove : RSS feed generator for Open Data
#  Copyright (C) 2021 Brice Person
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys, os, sqlite3, urllib.parse, html, json, markdown, bleach, re
from collections import OrderedDict
from datetime import datetime, date, timedelta
from requests.utils import requote_uri

day_names = {
  "0": "dimanche",
  "1": "lundi",
  "2": "mardi",
  "3": "mercredi",
  "4": "jeudi",
  "5": "vendredi",
  "6": "samedi"
}

month_names = {
  "01": "janvier",
  "02": "février",
  "03": "mars",
  "04": "avril",
  "05": "mai",
  "06": "juin",
  "07": "juillet",
  "08": "août",
  "09": "septembre",
  "10": "octobre",
  "11": "novembre",
  "12": "décembre"
}

frequency = {
  "annual": "Annuelle",
  "biennial": "Biennale",
  "bimonthly": "Bimestrielle",
  "biweekly": "Toutes les deux semaines",
  "continuous": "Temps réel",
  "daily": "Quotidienne",
  "fourTimesADay": "Quatre fois par jour",
  "fourTimesAWeek": "Quatre fois par semaine",
  "hourly": "Toutes les heures",
  "irregular": "Sans régularité ",
  "monthly": "Mensuelle",
  "punctual": "Ponctuelle",
  "quarterly": "Trimestrielle",
  "quinquennial": "Quinquennale",
  "semiannual": "Semestrielle",
  "semidaily": "Deux fois par jour",
  "semimonthly": "Deux fois par mois",
  "semiweekly": "Deux fois par semaine",
  "threeTimesADay": "Trois fois par jour",
  "threeTimesAWeek": "Trois fois par semaine",
  "threeTimesAMonth": "Trois fois par mois",
  "threeTimesAYear": "Trois fois par an",
  "triennial": "Triennale",
  "unknown": "Inconnue",
  "weekly": "Hebdomadaire"
}

spatial_granularity = {
  "country": "Pays",
  "country-group": "Groupement de pays",
  "country-subset": "Sous-ensemble de pays",
  "fr:arrondissement": "Arrondissement français",
  "fr:canton": "Canton français",
  "fr:collectivite": "Collectivités d'outre-mer françaises",
  "fr:commune": "Commune française",
  "fr:departement": "Département français",
  "fr:epci": "Intercommunalité française (EPCI)",
  "fr:iris": "Iris (quartiers INSEE)",
  "fr:region": "Région française",
  "other": "Autre",
  "poi": "Point d'Intérêt"
}

reuse_type = {
  "api": "API",
  "application": "Application",
  "hardware": "Objet connecté",
  "idea": "Idée",
  "news_article": "Article de presse",
  "paper": "Papier",
  "post": "Article de blog",
  "visualization": "Visualisation"
}

def cleanUrl(url):
  url = requote_uri(url.replace('&', '&amp;'))
  u = url.split('#')
  if len(u) == 1:
    url = url+'#datagroove'
  return url

def cleanText(txt):
  return html.escape(txt, quote=True)

def format_date(day):
  d = date.fromisoformat(day)
  d = d.strftime("%w-%d-%m-%Y").split('-')
  return day_names[d[0]]+' '+d[1]+' '+month_names[d[2]]+' '+d[3]

def date_synthese(day):
  d = date.fromisoformat(day)
  d1 = d.strftime("%w-%d-%m-%Y").split('-')
  d2 = (d + timedelta(days=1)).strftime("%w-%d-%m-%Y").split('-')
  return 'Du '+day_names[d1[0]]+' '+d1[1]+' '+month_names[d1[2]]+' '+d1[3]+' à 07:45 au '+day_names[d2[0]]+' '+d2[1]+' '+month_names[d2[2]]+' '+d2[3]+' à 07:44'

def saveTheDay(day, content, data):
  path = './pages/d/'+'/'.join(day.split('-'))
  if not os.path.exists(path):
    os.makedirs(path)
  with open(path+'/index.html', 'w') as outfile:
    outfile.write(content+"\n")
  with open(path+'/data.json', 'w') as outfile:
    json.dump(data, outfile, sort_keys=False, indent=2)

def createPathIndexes():
  dir_paths = []
  full_path = []

  for dpath, dnames, fnames in os.walk('./pages/d'):
    full_path.append(dpath)
    p = '/'.join(dpath.split('/')[:-1])
    if p not in dir_paths:
      dir_paths.append(p)

  indexes = {}

  for dpath in dir_paths[::-1]:
    if dpath not in indexes:
      indexes[dpath] = []

    for path in full_path:
      if path.startswith(dpath):
        remain = path.replace(dpath, '')
        if "/" not in remain[1:]:
          if remain[1:]:
            indexes[dpath].append(remain[1:])

  for dpath in indexes:
    with open(dpath+'/index.json', 'w') as outfile:
      json.dump(sorted(indexes[dpath]), outfile, sort_keys=False, indent=2)


con = sqlite3.connect('./bin/datagroove.db')
cur = con.cursor()

# Popular

for row in cur.execute("SELECT id, title, url, organization, description, frequency, license, `temporal_coverage.start`, `temporal_coverage.end`, `spatial.granularity`, `spatial.zones`, featured, last_modified, tags, `metric.discussions`, `metric.issues`, `metric.reuses`, `metric.followers`, `metric.views`, created_at, last_modified, (`metric.discussions` + `metric.reuses` + `metric.followers`) as popularity FROM dataset WHERE private is false AND updated_at_ts >= strftime('%s', 'now', '-26 hour') AND popularity >= 5 order by updated_at_ts desc limit 100"):

  description = bleach.clean(markdown.markdown(row[4]).replace('&nbsp;', ' '), ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
  tags = ''
  for tag in cleanText(row[13]).split(','):
    tags += '<a target="_blank" class="tag" rel="noreferrer" href="https://www.data.gouv.fr/fr/search/?tag='+tag+'&amp;sort=-last_modified#datagroove">'+tag+'</a> '

  item = {
    "id": row[0],
    "title": cleanText(row[1]),
    "url": cleanUrl(row[2]),
    "organization": '<h4>Organisation : '+cleanText(row[3])+'</h4>' if row[3] != '' else '',
    "description": description,
    "frequency": frequency[row[5]] if row[5] in frequency else 'Inconnue',
    "license": row[6],
    "temporal_coverage_start": format_date(row[7]) if row[7] else '',
    "temporal_coverage_end": format_date(row[8]) if row[8] else '',
    "spatial_granularity": spatial_granularity[row[9]] if row[9] in spatial_granularity else 'Inconnue',
    "spatial_zones": cleanText(row[10]),
    "featured": "oui" if row[11] == True else 'non',
    "last_modified": row[12].split('.')[0],
    "tags": '<p>Tags : '+tags[:-1]+'</p>' if row[13] != '' else '',
    "metric_discussions": row[14],
    "metric_issues": row[15],
    "metric_reuses": row[16],
    "metric_followers": row[17],
    "metric_views": row[18],
    "created_at": format_date(row[19].split('T')[0]),
    "updated_at": datetime.fromisoformat(row[20]).strftime("%d/%m/%Y %H:%M"),
    "popularity": row[21]
  }

  html_entry = '''<div class="dataset">
          <h3><span class="date_maj" title="Mise à jour" style="float:right;font-size:0.9em;">{updated_at}</span> <a target="_blank" rel="noreferrer" href="{url}">{title}</a></h3>
          <div class="dataset_desc">
            {organization}
          {description}
          <p>
            <table style="width:100%;">
              <tr>
                <th>Mis en avant</th>
                <td>{featured}</td>
              </tr>
              <tr>
                <th>Fréquence MàJ</th>
                <td>{frequency}</td>
              </tr>
              <tr>
                <th>Licence</th>
                <td>{license}</td>
              </tr>
              <tr>
                <th>Début couverture temporelle</th>
                <td>{temporal_coverage_start}</td>
              </tr>
              <tr>
                <th>Fin couverture temporelle</th>
                <td>{temporal_coverage_end}</td>
              </tr>
              <tr>
                <th>Granularité</th>
                <td>{spatial_granularity}</td>
              </tr>
              <tr>
                <th>Zone géographique</th>
                <td>{spatial_zones}</td>
              </tr>
              <tr>
                <th>Nombre de discussions</th>
                <td>{metric_discussions}</td>
              </tr>
              <tr>
                <th>Anomalies</th>
                <td>{metric_issues}</td>
              </tr>
              <tr>
                <th>Réutilisations</th>
                <td>{metric_reuses}</td>
              </tr>
              <tr>
                <th>Abonnés</th>
                <td>{metric_followers}</td>
              </tr>
              <tr>
                <th>Nombre de vues</th>
                <td>{metric_views}</td>
              </tr>
              <tr>
                <th>Date de création</th>
                <td>{created_at}</td>
              </tr>
            </table>
          </p>
          {tags}
          </div>
        </div>'''.format(
          organization = item['organization'],
          updated_at = item['updated_at'],
          url = item['url'],
          title = item['title'],
          description = item['description'],
          featured = item['featured'],
          frequency = item['frequency'],
          license = item['license'],
          temporal_coverage_start = item['temporal_coverage_start'],
          temporal_coverage_end = item['temporal_coverage_end'],
          spatial_granularity = item['spatial_granularity'],
          spatial_zones = item['spatial_zones'],
          metric_discussions = item['metric_discussions'],
          metric_issues = item['metric_issues'],
          metric_reuses = item['metric_reuses'],
          metric_followers = item['metric_followers'],
          metric_views = item['metric_views'],
          created_at = item['created_at'],
          tags = item['tags']
        )

  entry = '''
    <entry>
      <title>{title}</title>
      <link rel="related" href="{url}"/>
      <id>{id}-{last_modified}</id>
      <updated>{last_modified}</updated>
      <summary>{organization} - {title}</summary>
      <content type="xhtml">
        <div xmlns="http://www.w3.org/1999/xhtml">
          {h}
        </div>
      </content>
    </entry>\
  '''.format(
    title = item['title'],
    url = item['url'],
    id = item['id'],
    last_modified = item['last_modified'],
    organization = item['organization'],
    h = html_entry
  )

  data = {"html_entry": html_entry, "entry": entry}

  fname = item['last_modified']+'_'+item['id']+'.json'

  path = './pages/p'
  if not os.path.exists(path):
    os.makedirs(path)
  with open(path+'/'+fname, 'w') as outfile:
    json.dump(data, outfile, sort_keys=False, indent=2)


min_date = datetime.now() - timedelta(days=31)
entries = []

for dpath, dnames, fnames in os.walk('./pages/p'):
  for fname in fnames:
    if fname.endswith('json'):
      item_date = datetime.fromisoformat(fname.split('_')[0])

      if item_date < min_date:
        os.remove(dpath+'/'+fname)
      else:
        with open(dpath+'/'+fname, 'r') as jsonfile:
          item = json.loads(jsonfile.read())

        item["date"] = int(item_date.strftime("%s"))

        entries.append(item)

entries.sort(key=lambda d: d["date"], reverse=True)

last_update = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")

xml = '''\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>data.gouv.fr - Populaires</title>
  <link href="https://bjperson.github.io/datagroove"/>
  <link rel="self" href="https://bjperson.github.io/datagroove/flux/datagouv-popular.xml" />
  <author>
    <name>DataGroove</name>
  </author>
  <updated>{last}</updated>
  <id>datagouv-popular</id>'''.format(last=last_update)

html_entries = '<h2>Jeux de données populaires - data.gouv.fr <span title="Mise à jour" style="float:right;font-size:0.7em;line-height:1.7em;">dernière mise à jour : {maj}</span></h2>'.format(maj = (datetime.utcnow() + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M"))

for entry in entries:
  xml += entry["entry"]
  html_entries += entry["html_entry"]

xml += "\n</feed>"

with open('./flux/datagouv-popular.xml', 'w') as outfile:
  outfile.write(xml+"\n")

with open('./pages/p/index.html', 'w') as outfile:
  outfile.write(html_entries+"\n")


timings = {}
# Reuses
last_update = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")

timings["reuse"] = []

for row in cur.execute("SELECT id, title, slug, url, type, description, remote_url, organization, organization_id, image, featured, created_at, last_modified, tags, datasets, `metric.discussions`, `metric.issues`, `metric.datasets`, `metric.followers`, `metric.views`, created_at_ts, updated_at_ts FROM reuse WHERE created_at_ts >= strftime('%s', 'now', '-26 hour') order by created_at_ts desc limit 100"):

  description = bleach.clean(markdown.markdown(row[5]).replace('&nbsp;', ' '), ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])

  tags = ''
  for tag in cleanText(row[13]).split(','):
    tags += '<a target="_blank" class="tag" rel="noreferrer" href="https://www.data.gouv.fr/fr/reuses/?tag='+tag+'&amp;sort=-created#datagroove">'+tag+'</a> '

  item = {
    "id": row[0],
    "title": cleanText(row[1]),
    "slug": row[2],
    "url": cleanUrl(row[3]),
    "type": reuse_type[row[4]] if row[4] in reuse_type else 'Non précisé',
    "description": description,
    "remote_url": cleanUrl(row[6]),
    "organization": '<h4>Organisation : '+cleanText(row[7])+'</h4>' if row[7] != '' else '',
    "organization_id": row[8],
    "image": row[9],
    "featured": "oui" if row[10] == True else 'non',
    "created_at": row[11].split('.')[0],
    "last_modified": row[12].split('.')[0]+'+02:00',
    "tags": '<p>Tags : '+tags[:-1]+'</p>' if row[13] != '' else '',
    "datasets": row[14],
    "metric_discussions": row[15],
    "metric_issues": row[16],
    "metric_datasets": row[17],
    "metric_followers": row[18],
    "metric_views": row[19],
    "created_at_ts": row[20],
    "updated_at_ts": row[21]
  }

  html_entry = '''<div class="dataset">
            <h3><span class="date_maj" title="Création" style="float:right;font-size:0.9em;">{created_at_h}</span> <a target="_blank" rel="noreferrer" href="{url}">{title}</a></h3>
            <div class="dataset_desc">
              {organization}
              {description}
              <p>
                <table style="width:100%;">
                  <tr>
                    <th>Mis en avant</th>
                    <td>{featured}</td>
                  </tr>
                  <tr>
                    <th>Lien direct</th>
                    <td><a target="_blank" rel="noreferrer" href="{remote_url}">Visiter</a></td>
                  </tr>
                  <tr>
                    <th>Nombre de discussions</th>
                    <td>{metric_discussions}</td>
                  </tr>
                  <tr>
                    <th>Anomalies</th>
                    <td>{metric_issues}</td>
                  </tr>
                  <tr>
                    <th>Nombre de jeux de données utilisés</th>
                    <td>{metric_datasets}</td>
                  </tr>
                  <tr>
                    <th>Abonnés</th>
                    <td>{metric_followers}</td>
                  </tr>
                  <tr>
                    <th>Nombre de vues</th>
                    <td>{metric_views}</td>
                  </tr>
                </table>
              </p>
              {tags}
            </div>
          </div>'''.format(
            organization = item['organization'],
            url = item['url'],
            title = item['title'],
            description = item['description'],
            featured = item['featured'],
            remote_url = item['remote_url'],
            datasets = item['datasets'],
            metric_discussions = item['metric_discussions'],
            metric_issues = item['metric_issues'],
            metric_datasets = item['metric_datasets'],
            metric_followers = item['metric_followers'],
            metric_views = item['metric_views'],
            created_at = item['created_at'],
            created_at_h = (datetime.fromisoformat(item['created_at']) + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M"),
            tags = item['tags']
          )

  entry = '''
    <entry>
      <title>{title}</title>
      <link rel="related" href="{url}"/>
      <id>{id}-{last_modified}</id>
      <updated>{created_at}</updated>
      <summary>{organization} - {title}</summary>
      <content type="xhtml">
        <div xmlns="http://www.w3.org/1999/xhtml">
          {h}
        </div>
      </content>
    </entry>\
  '''.format(
    title = item['title'],
    url = item['url'],
    id = item['id'],
    created_at = item['created_at'],
    last_modified = item['last_modified'],
    organization = item['organization'],
    h = html_entry
  )

  data = {"html_entry": html_entry, "entry": entry}

  fname = item['created_at']+'_'+item['id']+'.json'

  path = './pages/r'
  if not os.path.exists(path):
    os.makedirs(path)
  with open(path+'/'+fname, 'w') as outfile:
    json.dump(data, outfile, sort_keys=False, indent=2)


min_date = datetime.now() - timedelta(days=31)
entries = []

for dpath, dnames, fnames in os.walk('./pages/r'):
  for fname in fnames:
    if fname.endswith('json'):
      item_date = datetime.fromisoformat(fname.split('_')[0])

      if item_date < min_date:
        os.remove(dpath+'/'+fname)
      else:
        with open(dpath+'/'+fname, 'r') as jsonfile:
          item = json.loads(jsonfile.read())

        item["date"] = int(item_date.strftime("%s"))

        entries.append(item)


entries.sort(key=lambda d: d["date"], reverse=True)

last_update = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")

xml = '''\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>data.gouv.fr - Réutilisations</title>
  <link href="https://bjperson.github.io/datagroove"/>
  <link rel="self" href="https://bjperson.github.io/datagroove/flux/datagouv-reuses.xml" />
  <author>
    <name>DataGroove</name>
  </author>
  <updated>{last}</updated>
  <id>datagouv-reuses</id>\
'''.format(last=last_update)

html_entries = '<h2>Réutilisations - data.gouv.fr <span title="Mise à jour" style="float:right;font-size:0.7em;line-height:1.7em;">dernière mise à jour : {maj}</span></h2>'.format(maj = (datetime.utcnow() + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M"))

for entry in entries:
  xml += entry["entry"]
  html_entries += entry["html_entry"]

xml += "\n</feed>"

with open('./flux/datagouv-reuses.xml', 'w') as outfile:
  outfile.write(xml+"\n")

with open('./pages/r/index.html', 'w') as outfile:
  outfile.write(html_entries+"\n")


# Day
resources = []
timings["datasets"] = []

if len(sys.argv) > 1:
  day = sys.argv[1]

  if not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", day):
    sys.exit("first arg is not an iso date (2021-06-28)")

  to_day = (datetime.fromisoformat(day) + timedelta(days=1)).strftime('%Y-%m-%d')+'T07:45:00'
else:
  day = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

  to_day = datetime.now().strftime('%Y-%m-%d')+'T07:45:00'

from_day = day+"T07:45:00"

print(from_day)
print(to_day)

for row in cur.execute("SELECT `dataset.id`, `dataset.title`, `dataset.url`, `dataset.organization`, `dataset.organization_id`, url, title, format,  created_at_ts, updated_at_ts FROM resource WHERE `dataset.private` is false AND (created_at_ts >= strftime('%s', :from_day) OR updated_at_ts >= strftime('%s', :from_day)) AND (created_at_ts < strftime('%s', :to_day) OR updated_at_ts < strftime('%s', :to_day)) order by updated_at_ts desc", {"from_day": from_day, "to_day": to_day}):
  latest_date = row[8] if row[8] > row[9] else row[9]
  latest_date = datetime.utcfromtimestamp(latest_date)
  # some are in the futur...
  if latest_date < datetime.utcnow():
    timings["datasets"].append(int(latest_date.strftime('%s')))
    latest_date = latest_date.strftime('%Y-%m-%d')
    item = {
      "dataset_id": row[0],
      "dataset_title": cleanText(row[1]),
      "dataset_url": cleanUrl(row[2]),
      "dataset_organization": cleanText(row[3]),
      "dataset_organization_id": row[4],
      "url": cleanUrl(row[5]),
      "title": cleanText(row[6]),
      "format": row[7],
      "date": latest_date
    }
    resources.append(item)

# dataset
datasets = []

for row in cur.execute("SELECT id, title, url, organization, organization_id, created_at_ts, updated_at_ts, `metric.discussions`, `metric.reuses`, `metric.followers` FROM dataset WHERE private is false AND (created_at_ts >= strftime('%s', :from_day) OR updated_at_ts >= strftime('%s', :from_day)) AND (created_at_ts < strftime('%s', :to_day) OR updated_at_ts < strftime('%s', :to_day)) order by updated_at_ts desc", {"from_day": from_day, "to_day": to_day}):
  latest_date = row[5] if row[5] > row[6] else row[6]
  latest_date = datetime.utcfromtimestamp(latest_date)
  if latest_date < datetime.utcnow():
    timings["datasets"].append(int(latest_date.strftime('%s')))
    latest_date = latest_date.strftime('%Y-%m-%d')
    popularity = int(row[7]) + int(row[7]) + int(row[7])
    item = {
      "dataset_id": row[0],
      "dataset_title": cleanText(row[1]),
      "dataset_url": cleanUrl(row[2]),
      "dataset_organization": cleanText(row[3]),
      "dataset_organization_id": row[4],
      "date": latest_date,
      "popularity": popularity
    }
    datasets.append(item)

# reuse
reuses = []

for row in cur.execute("SELECT title, url, type, organization, created_at_ts FROM reuse WHERE created_at_ts >= strftime('%s', :from_day) order by created_at_ts desc", {"from_day": from_day}):
  latest_date = datetime.utcfromtimestamp(row[4]).strftime('%Y-%m-%d')
  item = {
    "title": cleanText(row[0]),
    "url": cleanUrl(row[1]),
    "type": row[2],
    "organization": cleanText(row[3]),
    "date": latest_date
  }
  reuses.append(item)

  timings["reuse"].append(int(row[4]))

# organization
orga_infos = {}

for row in cur.execute("SELECT id, name, slug, badges, competence FROM organization order by id desc"):
  item = {
    "name": cleanText(row[1]),
    "slug": row[2],
    "badges": cleanText(row[3]),
    "competence": row[4]
  }
  orga_infos[row[0]] = item

con.close()

rss = OrderedDict()

for item in resources:
  if "orgas" not in rss:
    rss["orgas"] = {}

  if item["dataset_organization_id"] not in rss["orgas"]:
    rss["orgas"][item["dataset_organization_id"]] = {}
    rss["orgas"][item["dataset_organization_id"]]["dataset_organization"] = item["dataset_organization"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"] = {}

  if item["dataset_id"] not in rss["orgas"][item["dataset_organization_id"]]["datasets"]:
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]] = {}
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["dataset_title"] = item["dataset_title"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["dataset_url"] = item["dataset_url"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["dataset_organization"] = item["dataset_organization"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["resources"] = []

  _item = {"url": item["url"], "title": item["title"], "format": item["format"]}

  rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["resources"].append(_item)

for item in datasets:
  if "orgas" not in rss:
    rss["orgas"] = {}

  if item["dataset_organization_id"] not in rss["orgas"]:
    rss["orgas"][item["dataset_organization_id"]] = {}
    rss["orgas"][item["dataset_organization_id"]]["dataset_organization"] = item["dataset_organization"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"] = {}

  if item["dataset_id"] not in rss["orgas"][item["dataset_organization_id"]]["datasets"]:
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]] = {}
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["dataset_title"] = item["dataset_title"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["dataset_url"] = item["dataset_url"]
    rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["dataset_organization"] = item["dataset_organization"]

  rss["orgas"][item["dataset_organization_id"]]["datasets"][item["dataset_id"]]["popularity"] = item["popularity"]

for item in reuses:
  if "reuses" not in rss:
    rss["reuses"] = []

  rss["reuses"].append(item)


#print(json.dumps(rss, sort_keys=False, indent=2))
#sys.exit(1)


parts = {}
summary = {}
metrics = {}
formats = {}
formats["general"] = {}

if "orgas" in rss:

  nb_datasets = 0
  nb_resources = 0
  nb_orgas = len(rss["orgas"])

  for orga_id in rss["orgas"]:

    if orga_id in orga_infos:
      competence = orga_infos[orga_id]["competence"] if orga_infos[orga_id]["competence"] else 'autre'
    else:
      competence = 'autre'

    if competence not in parts:
      parts[competence] = {}
      metrics[competence] = {"nb_orgas": 0, "nb_datasets": 0, "nb_resources": 0}
      formats[competence] = {}

    metrics[competence]["nb_orgas"] += 1

    details = ''

    for dataset_id in rss["orgas"][orga_id]["datasets"]:

      dataset = rss["orgas"][orga_id]["datasets"][dataset_id]

      nb = ' ('+str(len(dataset["resources"]))+')' if "resources" in dataset else ' (MàJ page)'

      details += '''<ul><li><h5><a target="_blank" rel="noreferrer" href="{u}">{t}</a>{n}</h5>\
      '''.format(
        u=dataset["dataset_url"],
        t=dataset["dataset_title"],
        n=nb
      )

      if "resources" in dataset:

        details += '<ul>'

        for resource in dataset["resources"]:

          nb_resources += 1

          metrics[competence]["nb_resources"] += 1

          resource_format = ' ('+resource["format"]+')' if resource["format"] else ''

          if resource["format"]:

            if "." in resource["format"]:
              resource["format"] = resource["format"].split('.')[-1]

            resource_format = ' ('+resource["format"]+')'

            if resource["format"] not in formats[competence]:
              formats[competence][resource["format"]] = 0

            if resource["format"] not in formats["general"]:
              formats["general"][resource["format"]] = 0

            formats[competence][resource["format"]] += 1
            formats["general"][resource["format"]] += 1

          else:

            resource_format = ''

            if "nc" not in formats[competence]:
              formats[competence]["nc"] = 0

            if "nc" not in formats["general"]:
              formats["general"]["nc"] = 0

            formats[competence]["nc"] += 1
            formats["general"]["nc"] += 1

          details += '''<li><a target="_blank" rel="noreferrer" href="{u}">{t}</a>{f}</li>
          '''.format(
            u=resource["url"],
            t=resource["title"],
            f=resource_format
          )

        details += '</ul>'

      details += '</li></ul>'

      nb_datasets += 1

      metrics[competence]["nb_datasets"] += 1

    parts[competence][orga_id] = details


  metrics["general"] = {"nb_orgas": nb_orgas, "nb_datasets": nb_datasets, "nb_resources": nb_resources}

  p_no = 's ont' if nb_orgas > 1 else ' a'
  p_nds = 's' if nb_datasets > 1 else ''
  p_ndx = 'x' if nb_datasets > 1 else ''
  p_nr = 's' if nb_resources > 1 else ''

  summary["general"] = '''{no} organisation{p_no} mis à jour {nd} page{p_nds} de jeu{p_ndx} de données et publié {nr} ressource{p_nr} sur <a target="_blank" rel="noreferrer" href="https://www.data.gouv.fr">data.gouv.fr</a>.\
  '''.format(
    no = nb_orgas,
    p_no = p_no,
    nd = nb_datasets,
    p_nds = p_nds,
    p_ndx = p_ndx,
    nr = nb_resources,
    p_nr = p_nr
  )

if "reuses" in rss:

  details = ''

  nb = len(rss["reuses"])

  plur = 's' if nb > 1 else ''

  details += '''
          <h3 id="{d}_reuses">Réutilisation{s} ({n})</h3>
          <ul>
          '''.format(
            d = day,
            s = plur,
            n = nb
          )

  for reuse in rss["reuses"]:

    orga = 'par '+reuse["organization"]+' ' if reuse["organization"] else ''

    details += '''<li><a target="_blank" rel="noreferrer" href="{u}">{t}</a> {o}({f})</li>
          '''.format(
            u = reuse["url"],
            t = reuse["title"],
            f = reuse["type"],
            o = orga
          )

  parts["reuses"] = details+'</ul>'

  metrics["reuses"] = nb

  summary["reuses"] = '''Il y a eu {n} réutilisation{s}.'''.format(s=plur, n=nb)


# RSS day
competences = ['nationale', 'régionale', 'départementale', 'EPCI', 'rectorat', 'communale', 'autre']
nb_entries = 10

toc_competences = []
content = ''
whole_summary = ''

if "general" in summary:
  whole_summary = summary["general"]

for competence in competences:

  if competence in parts:

    toc_competences.append(competence)

    if competence == 'autre':
      content += '<div class="competences"><h3 name="'+day+'_'+competence+'" id="'+day+'_'+competence+'">Compétence non déterminée</h3>'

    else:
      content += '<div class="competences"><h3 name="'+day+'_'+competence+'" id="'+day+'_'+competence+'">Compétence '+competence+'</h3>'

    for orga_id in parts[competence]:

      if orga_id in orga_infos:
        content += '<ul><li><h4 name="'+day+'_'+orga_infos[orga_id]["slug"]+'" id="'+day+'_'+orga_infos[orga_id]["slug"]+'">'+orga_infos[orga_id]["name"]+'</h4>'

      else:
        content += '<ul><li><h4 name="'+day+'_users" id="'+day+'_users">Utilisateurs individuels</h4>'

      content += parts[competence][orga_id]+'</li></ul>'

    if competence == 'autre':
      content += '<p>Seules les organisations certifiées "Service public" et une petite sélection sont catégorisées par compétences territoriales.</p>'

    content += '</div>'

toc = ''

if len(toc_competences) > 0:

  toc += '<table style="width:100%;margin-top:2em;">'

  toc += '<tr><th>Compétence</th><th>Organisations</th><th>Pages MàJ</th><th>Ressources ajoutées / MàJ</th></tr>'

  for competence in toc_competences:

    toc += '''
            <tr><td><a href="#{d}_{c}" rel="noreferrer" target="_self">{cc}</a></td><td>{nbo}</td><td>{nbd}</td><td>{nbr}</td></tr>
            '''.format(d=day, c=competence, cc=competence.capitalize(), nbo=str(metrics[competence]["nb_orgas"]), nbd=str(metrics[competence]["nb_datasets"]), nbr=str(metrics[competence]["nb_resources"]))

  toc += '</table>'

  if "reuses" in parts:

    toc += '<p><table style="width:100%;"><tr><th><a href="#'+day+'_reuses" rel="noreferrer" target="_self">Réutilisations</a></th><td style="background-color:#0D1117;">'+str(metrics["reuses"])+'</td></tr></table></p>';

  content = toc+content

if "general" in summary:
  content = '<p style="text-align:center;">'+summary["general"]+'</p>'+content

if "reuses" in parts:
  content += '<div class="competences">'+parts["reuses"]+'</div><p style="text-align:center;">...</p>'

dh = date_synthese(day)

content = '<h2 id="'+day+'" style="text-align:center;">Synthèse 24H</h2><h3 style="text-align:center;font-size:0.9em">'+dh+'</h3>'+content

data = {"metrics": metrics, "formats": formats, "timings": timings}

saveTheDay(day, content, data)

createPathIndexes()

xml = '''\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>data.gouv.fr - Synthèse 24H</title>
  <link href="https://bjperson.github.io/datagroove/"/>
  <link rel="self" href="https://bjperson.github.io/datagroove/flux/datagouv-day.xml" />
  <author>
    <name>DataGroove</name>
  </author>
  <updated>{last}:06:00:00+02:00</updated>
  <id>datagouv-day</id>\
'''.format(last=day)

nb_done = 0

for dpath, dnames, fnames in os.walk('./pages/d'):
  dnames.sort(reverse = True)
  if "index.html" in fnames:

    if nb_done < nb_entries:
      day = "-".join(dpath.replace('./pages/d/', '').split('/'))

      with open(dpath+'/index.html', 'r') as oldfile:
        content = oldfile.read()

      entry = '''
        <entry>
          <title>Synthèse</title>
          <link rel="related" href="https://www.data.gouv.fr/"/>
          <link rel="self" href="https://bjperson.github.io/datagroove/#{d}"/>
          <id>https://bjperson.github.io/datagroove/#{d}</id>
          <updated>{d}T06:00:00+02:00</updated>
          <summary>{dh}</summary>
          <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
              {h}
            </div>
          </content>
        </entry>\
      '''.format(dh=dh, d=day, h=content)

      xml += entry;
    else:
      break

xml += "\n</feed>"

with open('./flux/datagouv-day.xml', 'w') as outfile:
  outfile.write(xml+"\n")

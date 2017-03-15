#!/usr/bin/python
# -:- coding: utf8 -:-

#
# (C) Strainu 2016-2017
#
# Distributed under the terms of the MIT license.
#

import codecs
import sys
import csv
import requests
import json
import time
import os

sys.path.append("wikiro/robots/python/pywikipedia")
import csvUtils

def filterName(oldName):
    name = oldName.upper()
    name = name.replace("\""," ")
    name = name.replace("\'"," ")
    name = name.replace(",","")
    name = name.replace("."," ")
    name = name.replace("+"," ")
    name = name.replace("-"," ")
    name = name.replace(u"Ă", u"A")
    name = name.replace(u"Â", u"A")
    name = name.replace(u"Á", u"A")
    name = name.replace(u"Î", u"A")
    name = name.replace(u"Ș", u"S")
    name = name.replace(u"Ț", u"T")
    name = name.replace(u"Ş", u"S")
    name = name.replace(u"Ţ", u"T")
    name = name.replace(u"’", u" ")
    name = name.replace(u"„", u" ")
    name = name.replace(u"”", u" ")
    name = name.replace(u"GIMNAZIALA", u"GENERALA")
    name = name.replace(u"GPN", u"GRADINITA CU PROGRAM NORMAL")
    name = name.replace(u"GPP", u"GRADINITA CU PROGRAM PRELUNGIT")
    name = name.replace(u" PP ", u" PROGRAM PRELUNGIT ")
    name = name.replace(u"GRAD CU", u"GRADINITA CU")
    name = name.replace(u"GRADINITA CU PR", u"GRADINITA CU PROGRAM")
    name = name.replace(u"GRADINITA PROG", u"GRADINITA CU PROGRAM")
    name = name.replace(u"GRADINITA PR", u"GRADINITA CU PROGRAM")
    name = name.replace(u"PROGRAM N ", u"PROGRAM NORMAL ")
    name = name.replace(u"LIC TEH", u"LICEUL TEHNOLOGIC")
    while name != oldName:
        oldName = name
        name = oldName.replace("  "," ")
    return name.strip()

def filterNameAndCity(oldName, city, county=None):
    name = filterName(oldName)
    city = filterName(city)
    name = name.replace(u"COMUNA " + city, u"")
    name = name.replace(u"SAT " + city, u"")
    name = name.replace(u"ORASUL " + city, u"")
    name = name.replace(u"ORAS " + city, u"")
    name = name.replace(u"MUNICIPIUL " + city, u"")
    name = name.replace(u"MUN " + city, u"")
    name = name.replace(u"LOCALITATEA " + city, u"")
    name = name.replace(city, u"")
    if county:
        county = filterName(county)
        name = name.replace(u"JUDETUL " + county, u"")
        name = name.replace(u"JUDET " + county, u"")
        name = name.replace(county, u"")
    while name != oldName:
        oldName = name
        name = oldName.replace("  "," ")
    return name.strip()

def fixKey(code):
    return u"%010d" % int(code)

def wikidataAndNominatim():
    out = {}
    headers = {
        'User-Agent': 'School scripts by Strainu<osm@strainu.ro>',
    }
    retea = csvUtils.csvToJson("wikiro/data/schools/retea20152016.csv", delimiter="\t")
    wikidata = csvUtils.csvToJson("wikiro/data/schools/scoli_wikidata.csv", field='item')
    #cod curat
    coduri = csvUtils.csvToJson("wikiro/data/schools/coduri_scoli.csv", field='COD SIIIR')
    url = u"https://nominatim.openstreetmap.org/search?format=json&street={0}+{1}&city={2}&county={3}&country=ROM%C3%82NIA&dedupe=1"
    for key in retea:
        name = filterNameAndCity(retea[key]['Denumire'], retea[key]['Localitate'].strip())
        newkey = fixKey(key)
        out[newkey] = {}
        out[newkey]['cod'] = newkey
        out[newkey]['nume'] = retea[key]['Denumire']
        out[newkey]['nume_ascii'] = name
        out[newkey]['str'] = retea[key][u'Stradă'].strip()
        out[newkey]['nr'] = retea[key][u'Număr'].strip()
        out[newkey]['oras'] = retea[key]['Localitate'].strip()
        out[newkey]['judet'] = retea[key][u'Județ']
        out[newkey]['lat'] = u""
        out[newkey]['lon'] = u""
        out[newkey]['wikidata'] = u""
        if newkey in coduri:
            out[newkey].update(coduri[newkey])
        for wdkey in wikidata:
            label = filterName(wikidata[wdkey]['itemLabel'])
            if name.find(label) > -1 or label.find(name)> -1:
                print name
                print label
                out[newkey]['wikidata'] = wikidata[wdkey]['item']
                out[newkey]['lat'] = wikidata[wdkey].get('lat')  or u""
                out[newkey]['lon'] = wikidata[wdkey].get('lon')  or u""
                break

        if not out[newkey]['lat']:
            if out[newkey]['str'].strip() == u"" or out[newkey]['nr'].strip() == u"":
                continue
            cache = "wikiro/data/schools/{0}.json".format(newkey)
            if os.path.exists(cache):
                print u"Using Nominatim cache for {0}".format(newkey)
                with open(cache, "r") as c:
                    js = json.load(c)
            else:
                city = out[newkey]['oras']
                county = out[newkey]['judet']
                if city.find(u"BUCURE") > -1:
                    city = u"București"
                    county = u"București"
                print url.format(out[newkey]['nr'], out[newkey]['str'], city, county)
                try:
                    time.sleep(1)
                    r = requests.get(url.format(out[newkey]['nr'], out[newkey]['str'], city, county))
                    js = json.loads(r.text)
                    with open(cache, "w") as c:
                        json.dump(js, c)
                except Exception as e:
                    print e
                    continue
            # print js
            if len(js):
                    for resp in js:
                        if resp['class'] in ['highway', 'leisure', 'natural']:
                            continue
                        out[newkey]['lat'] = resp['lat']
                        out[newkey]['lon'] = resp['lon']
                        out[newkey]['osm'] = resp['osm_id']
                        print resp['class']
                        lastkey = key
                        break

    with open( "wikiro/data/schools/scoli_geocoded.json", 'w' ) as jsonFile:
        jsonFile.write( json.dumps( out, indent=2) )
    keys = out[lastkey].keys()
    keys.sort()
    with open( "wikiro/data/schools/scoli_geocoded.csv", 'w' ) as csvFile:
        dw = csv.DictWriter(csvFile, fieldnames=keys)
        dw.writeheader()
        for entry in out:
            dw.writerow({k:v.encode('utf8') for k,v in out[entry].items()})
        

def osmNodes():
    osm = csvUtils.csvToJson("wikiro/data/schools/scoli_osm_node.csv", field=u'id')
    scoli = {}
    with open( "wikiro/data/schools/scoli_geocoded.json", 'r' ) as jsonFile:
        scoli = json.load( jsonFile )
    print len(scoli)
    for key in scoli:
        #if key == "4061206655":
        #    import pdb
        #    pdb.set_trace()
        if 'osm' not in scoli[key]:
            scoli[key]['osm'] = ''
        if scoli[key]['lat']:
            continue
        for id in osm:
            if scoli[key]['SIRUTA LOCALITATE'] != osm[id][u'siruta']:
                continue
            name = scoli[key][u'nume_ascii']
            label = osm[id][u'name']
            if name and label and (name.find(label) > -1 or label.find(name)> -1):
                print('our', name)
                print('osm', label)
                print('before', scoli[key])
                scoli[key]['lat'] = osm[id]['latitude']
                scoli[key]['lon'] = osm[id]['longitude']
                scoli[key]['osm'] = id
                lastkey = key
                print('after', scoli[key])
                print u"----------------------------------------------------------------------"

    with open( "wikiro/data/schools/scoli_geocoded_osm.json", 'w' ) as jsonFile:
        jsonFile.write( json.dumps( scoli, indent=2) )
    keys = scoli[lastkey].keys()
    keys.sort()
    with open( "wikiro/data/schools/scoli_geocoded_osm.csv", 'w' ) as csvFile:
        dw = csv.DictWriter(csvFile, fieldnames=keys)
        dw.writeheader()
        for entry in scoli:
            dw.writerow({k:v.encode('utf8') for k,v in scoli[entry].items()})

def roaepSchools():
    roaep = csvUtils.csvToJson("wikiro/data/schools/scoli_roaep.csv", field=u'SEDIU_SECT')
    scoli = {}
    with open( "wikiro/data/schools/scoli_geocoded_osm.json", 'r' ) as jsonFile:
        scoli = json.load( jsonFile )
    print len(scoli)
    for key in scoli:
        if scoli[key]['lat']:
            continue
        for id in roaep:
            if scoli[key][u'SIRUTA LOC SUP'] != roaep[id][u'SIRUTA_UAT']:
                continue
            name = scoli[key][u'nume_ascii']
            label = filterName(roaep[id][u'SEDIU_SECT'])
            if name and label and (name.find(label) > -1 or label.find(name)> -1):
                # print('our', name)
                # print('roaep', label)
                # print('before', scoli[key])
                scoli[key]['lat'] = roaep[id]['lat']
                scoli[key]['lon'] = roaep[id]['lon']
                lastkey = key
                # print('after', scoli[key])
                # print u"----------------------------------------------------------------------"
                break
        else:
            pass # print('not found', scoli[key])

    with open( "wikiro/data/schools/scoli_geocoded_full.json", 'w' ) as jsonFile:
        jsonFile.write( json.dumps( scoli, indent=2) )
    keys = scoli[lastkey].keys()
    keys.sort()
    with open( "wikiro/data/schools/scoli_geocoded_full.csv", 'w' ) as csvFile:
        dw = csv.DictWriter(csvFile, fieldnames=keys)
        dw.writeheader()
        for entry in scoli:
            dw.writerow({k:v.encode('utf8') for k,v in scoli[entry].items()})

def main():
    wikidataAndNominatim()
    osmNodes()
    roaepSchools()

if __name__ == "__main__":
    main()
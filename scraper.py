import scraperwiki, urllib2
import lxml 
import re
import requests

def get_lang(s):
    lang = 'en'
    cnt = 0
    for c in s:
        if u'\u4e00' <= c <= u'\u9fff':
            lang = 'zh'  
            break
    return lang

def find_district(districts, page, top):
    k = 0
    for i in range(0, len(districts)):
        d = districts[i]
        if (d['page'] < page) or (page == d['page'] and d['y'] <= (top + 10)): 
            k = i
    return districts[k]

def fetch_rows(url, x_threshold):
    points_rows = []
    districts_rows = []
    print url
    f = requests.get(url)
    pdf = scraperwiki.pdftoxml(f.content)
    root = lxml.etree.fromstring(pdf)
    pages = root.xpath("//page")
    for page in pages:
        page_number = int(page.xpath("./@number")[0])
        texts = page.xpath("./text")
        tag = 0
        for text in texts:
            x = int(text.xpath("./@left")[0])
            y = int(text.xpath("./@top")[0])
            if text.text is not None:
                
                s = re.sub(r'\d+\.', '', text.text).strip()
                m = re.match(r'\d+\.', text.text)
                if m is not None:
                    tag = int(m.group(0).strip()[0:-1])
                if len(s) == 0:
                    continue
                d = {'text': s, 'y': y, 'x': x, 'page': page_number, 'tag': tag}
                if x >= x_threshold:
                    points_rows.append(d)                   
                else:
                    districts_rows.append(d)
    return  (points_rows, districts_rows)

def convert_point_rows(points_rows):
    k = 0
    total = len(points_rows)
    points = []
    while k < total:
        chi_names = []
        eng_names = []
        x = points_rows[k]['x']
        y = points_rows[k]['y']
        page = points_rows[k]['page']
        lang = get_lang(points_rows[k]['text']) 
        tag = points_rows[k]['tag']
        while k < total and get_lang(points_rows[k]['text']) == lang and points_rows[k]['tag'] == tag:
            chi_names.append(points_rows[k]['text'])
            k = k + 1
     
        tag = points_rows[k]['tag']
        lang = get_lang(points_rows[k]['text']) 
        while k < total and get_lang(points_rows[k]['text']) == lang  and points_rows[k]['tag'] == tag:
            eng_names.append(points_rows[k]['text'])
            k = k + 1
        eng_name = " ".join(eng_names)
        chi_name = " ".join(chi_names)
        if get_lang(eng_name) == "zh":
            eng_name, chi_name = chi_name, eng_name
        points.append({"eng": eng_name, "chi": chi_name, "x": x, 'y': y, 'page': page})
    return points

def convert_districts_rows(districts_rows):
    districts = []
    for i in range(0, len(districts_rows) / 2):
        d = {'eng': districts_rows[2 * i + 1]['text'], 'chi': districts_rows[2 * i]['text'], 'x' : districts_rows[2 * i]['x'], 'y': districts_rows[2 * i]['y'], 'page':districts_rows[2 * i]['page']}
        districts.append(d)
    return districts

scraperwiki.sqlite.execute("DROP table IF EXISTS data")
configs = [('http://www.fehd.gov.hk/english/pleasant_environment/cleansing/list_of_recyclable_collection_points_nt.pdf', 301), ('http://www.fehd.gov.hk/english/pleasant_environment/cleansing/list_of_recyclable_collection_points_kln.pdf', 330), ('http://www.fehd.gov.hk/english/pleasant_environment/cleansing/list_of_recyclable_collection_points_hk.pdf', 330)]
for url, x_threshold in configs:
    points_rows, districts_rows = fetch_rows(url, x_threshold)
    points = convert_point_rows(points_rows)
    districts = convert_districts_rows(districts_rows)
    for p in points:
        district = find_district(districts, p['page'], p['y'])
        if  p['eng'] not in ["Location", "No."]:
            scraperwiki.sqlite.save(unique_keys=[], data={"d_eng": district['eng'], "d_chi": district['chi'], "addr_eng": p['eng'], "addr_chi":p['chi'] })


        

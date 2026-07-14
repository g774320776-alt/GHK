import re,json,requests
from urllib.parse import quote,unquote
from base.spider import Spider

class Spider(Spider):
    def init(self,extend=""):
        self.host='http://www.ddys001.com'
        self.ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
        self.headers={'User-Agent':self.ua,'Referer':self.host+'/'}

    def getName(self):
        return '低端影视'

    def isVideoFormat(self,url):
        return True

    def manualVideoCheck(self):
        return False

    def destroy(self):
        return 'ok'

    def fetch(self,url):
        r=requests.get(url,headers=self.headers,timeout=15)
        r.encoding='utf-8'
        return r.text

    def clean(self,s):
        return re.sub(r'\s+',' ',re.sub(r'<.*?>','',s or '')).strip()

    def abs(self,u):
        return u if u.startswith('http') else self.host+u

    def parse_list(self,html):
        vod=[]
        for m in re.finditer(r'<li[^>]*data-item[^>]*>.*?</li>',html,re.S):
            it=m.group(0)
            a=re.search(r'<a[^>]+href="([^"]*?/vod-[^"]+)"[^>]*title="([^"]+)"',it,re.S)
            if not a: continue
            pic=re.search(r'data-original="([^"]+)"',it) or re.search(r'data-src="([^"]+)"',it) or re.search(r'src="([^"]+)"',it)
            tag=re.search(r'<span[^>]*pic-label[^>]*>(.*?)</span>',it,re.S)
            vod.append({'vod_id':a.group(1),'vod_name':self.clean(a.group(2)),'vod_pic':pic.group(1) if pic else '','vod_remarks':self.clean(tag.group(1)) if tag else ''})
        return vod

    def homeContent(self,filter):
        return {'class':[{'type_id':'1','type_name':'电影'},{'type_id':'2','type_name':'连续剧'},{'type_id':'3','type_name':'综艺'},{'type_id':'4','type_name':'动漫'},{'type_id':'27','type_name':'短剧'},{'type_id':'20','type_name':'理论片'}]}

    def homeVideoContent(self):
        html=self.fetch(self.host+'/list-1/')
        return {'list':self.parse_list(html)[:12]}

    def categoryContent(self,tid,pg,filter,extend):
        pg=str(pg or 1)
        url=self.host+('/list-%s/'%tid if pg=='1' else '/list-%s-%s/'%(tid,pg))
        html=self.fetch(url)
        lst=self.parse_list(html)
        return {'page':int(pg),'pagecount':999,'limit':len(lst) or 36,'total':999*36,'list':lst}

    def detailContent(self,ids):
        url=self.abs(ids[0])
        html=self.fetch(url)
        name=re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*>(.*?)</a>',html,re.S) or re.search(r'<title>(.*?)</title>',html,re.S)
        pic=re.search(r'data-original="([^"]+)"',html) or re.search(r'data-src="([^"]+)"',html) or re.search(r'src="([^"]+)"',html)
        content=re.search(r'<h2[^>]*>\s*剧情介绍\s*</h2>.*?<div[^>]*section-content[^>]*>(.*?)</div>',html,re.S)
        vod={'vod_id':ids[0],'vod_name':self.clean(name.group(1)).replace('-低端影视','') if name else '','vod_pic':pic.group(1) if pic else '','type_name':'','vod_year':'','vod_area':'','vod_remarks':'','vod_actor':'','vod_director':'','vod_content':self.clean(content.group(1)) if content else ''}
        play_from=[];play_url=[]
        for sec in re.finditer(r'<section[^>]*vod-play-list-box[^>]*>.*?</section>',html,re.S):
            s=sec.group(0)
            h=re.search(r'<h2[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h2>',s,re.S)
            eps=[]
            seen=[]
            for a in re.finditer(r'<a[^>]+href="([^"]*?/play-[^"]+)"[^>]*>(.*?)</a>',s,re.S):
                href=a.group(1)
                if href in seen: continue
                seen.append(href)
                t=self.clean(a.group(2)) or '播放'
                eps.append(t+'$'+href)
            if h and eps:
                play_from.append(self.clean(h.group(1)))
                play_url.append('#'.join(eps))
        vod['vod_play_from']='$$$'.join(play_from)
        vod['vod_play_url']='$$$'.join(play_url)
        return {'list':[vod]}

    def searchContent(self,key,quick,pg='1'):
        html=self.fetch(self.host+'/search--------------/?wd='+quote(key))
        return {'list':self.parse_list(html)}

    def playerContent(self,flag,id,vipFlags):
        play_url=self.abs(id)
        html=self.fetch(play_url)
        m=re.search(r'player_aaaa\s*=\s*(\{.*?\})</script>',html,re.S)
        if m:
            data=json.loads(m.group(1))
            u=unquote(data.get('url',''))
            if u and re.search(r'\.m3u8|\.mp4',u,re.I):
                return {'parse':0,'url':u,'header':{'User-Agent':self.ua,'Referer':play_url,'Origin':self.host}}
        return {'parse':1,'url':play_url,'header':self.headers}
# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,sys,string,time,base64,datetime,gzip
from urlparse import urlparse
import aes
import bs4
import requests
try:
    import hashlib
except ImportError:
    import md5

from parseutils import *
from stats import *
import xbmcplugin,xbmcgui,xbmcaddon
__baseurl__ = 'http://tv.idnes.cz/'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
addon = xbmcaddon.Addon('plugin.video.idnestv')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
__settings__ = xbmcaddon.Addon(id='plugin.video.idnestv')
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
nexticon = xbmc.translatePath( os.path.join( home, 'nextpage.png' ) )
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )
defaultprotocol = 'http:'


#Nacteni informaci o doplnku
__addon__      = xbmcaddon.Addon()
__addonname__  = __addon__.getAddonInfo('name')
__addonid__    = __addon__.getAddonInfo('id')
__cwd__        = __addon__.getAddonInfo('path').decode("utf-8")
__language__   = __addon__.getLocalizedString


def log(msg):
    xbmc.log(("### [%s] - %s" % (__addonname__.decode('utf-8'), msg.decode('utf-8'))).encode('utf-8'), level=xbmc.LOGDEBUG)

def load(url):
    r = requests.get(url)
    return r.text

def normalize_url(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        if url.startswith('//'):
            return defaultprotocol + url
        else:
            return defaultprotocol + '//' + url
    return url
    
def settings(setting, value = None):
    if value:
        __settings__.setSetting(setting, value)
    else:
        return __settings__.getSetting(setting)

def OBSAH():

    html = load(__baseurl__).encode('utf-8')
    doc = bs4.BeautifulSoup(html)
    
    ## Parsuje hlavní nabídku stránky
    MENU(doc)
    
    ## Nejnovější videa ze stránky se řadí pod hlavní nabídku
    MAIN(doc)

def MENU(doc):

    url = ""
    menu = doc.find("menu", id = "menu")
    
    menuitems = menu.findAll("li", recursive=False)

    for item in menuitems:
            vysk = item.findAll("li")
            if len(vysk) > 0:
                typ = 1
                for subnew in vysk:
                    url = url + subnew.find("a")['href'].encode('windows-1250','replace').strip() + "*" + subnew.find("a").getText().encode('windows-1250','replace').strip() + ";"
            else:
                typ = 2
                url = __baseurl__ + item.find("a")['href']
            if "zive.aspx" in url or "#" in url:
                # PREHRAVANI ZIVE a HLEDANI SE MUSI JESTE DODELAT #
                typ = 3
                continue
            title = "[B]" + item.find("a").getText().encode('windows-1250','replace').strip() + "[/B]"
            desc = title
            addDir(title,url,typ,icon,1,desc)

def MAIN(doc):

    items = doc.findAll("a", "art-link")
    
    for item in items:
        try:
            url = item['href']
            title = item.find("h3").getText().encode('windows-1250','replace').strip()
            # predpoklad je videolink
            try:
                desc = title + "[CR][CR]Vydáno: " + item.find("span","time").getText().encode('windows-1250','replace').strip() + "[CR]Délka: " + item.find("span","length").getText().encode('windows-1250','replace').strip()
                typ = 4
            except:
            # ale kdyz neni popis a delka, jedna se pravdepodobne o porad
                if __baseurl__ not in url:
                    url = __baseurl__ + "porady.aspx" + url
                desc = "Pořad: " + title
                typ = 2
            thumb = item.find("div","art-img")['style']
            thumb = normalize_url(re.findall(r"//\S+.\w", thumb)[0])
            addDir(title,url,typ,thumb,1,desc)
        except:
            pass


def LIVE(url,page):
    # MUSI SE DODELAT #
    html = load(url).encode('utf-8')
    doc = bs4.BeautifulSoup(html)
    
    items = doc.findAll("a", "art-link")

    for item in items:
        try:
            url = item['href']
            title = item.find("h3").getText().encode('windows-1250','replace').strip()
            desc = "živě"
            thumb = item.find("div","art-img")['style']
            thumb = normalize_url(re.findall(r"//\S+.\w", thumb)[0])
            addDir(title,url,4,thumb,1,desc)
        except:
            pass

def NEWS(url,page):

    subnews = url.split(';')

    for item in subnews:
        try:
            data = item.split("*")
            url = __baseurl__ + data[0]
            title = data[1]
            desc = title
            addDir(title,url,2,icon,1,desc)
        except:
           pass


def CATEGORIES(url,page):

    html = load(url).encode('utf-8')
    doc = bs4.BeautifulSoup(html)
    topics = doc.find("div", "topics").ul
    items = topics.findAll("li")

    for item in items:
            urlel = item.find("a")
            url = urlel['href']
            desc = urlel.getText().encode('windows-1250','replace')
            title = desc
            video_name = title
            thumb = ""
            addDir(title,url,2,thumb,1,desc)

def INDEX(url,page):

    html = load(url).encode('utf-8')
    doc = bs4.BeautifulSoup(html)

    MAIN(doc)
    
    try:

	    item = doc.find("div", "next-art")
	    
	    urlnext = item.find("a")['href']
	    if __baseurl__ not in urlnext:
	        urlnext = url + urlnext
	    title = "[COLOR blue]Další strana >>>[/COLOR]"
	    thumb = nexticon
	    desc = "Přejít na další stránku"
	    addDir(title,urlnext,2,thumb,1,desc)
	    
    except:
      	    pass

def VIDEOLINK(url,name):

    html = load(url).encode('utf-8')
    doc = bs4.BeautifulSoup(html)
    video = doc.findAll("meta", property="og:url")
    video_name = name

    for item in video:
		if "idvideo=" in item['content']:
	    		xmlurl = "http://servix.idnes.cz/media/video.aspx?" + re.findall(r"idvideo=\S+", item['content'])[0]
			configxml = load(xmlurl).encode('utf-8')
    			configxml = bs4.BeautifulSoup(configxml)
			thumb = normalize_url(configxml.find("imageprev").getText())
			desc = configxml.find("title").getText()
			linkvideo = configxml.find("linkvideo")
			server = linkvideo.find("server").getText()
			for video in linkvideo.findAll("file"):
				name = "Kvalita: " + video['quality']
				url = normalize_url(server + "/" + video.getText())
				addLink(name,video_name, url,normalize_url(thumb),desc)

            

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param



def addLink(name,video_name, url,iconimage,popis):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": video_name, "Plot": popis} )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage,page,popis):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": popis } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
    
params=get_params()
url=None
name=None
thumb=None
mode=None
page=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        page=int(params["page"])
except:
        pass

if mode==None or url==None or len(url)<1:
        print ""
        STATS("OBSAH", "Function")
        OBSAH()

elif mode==5:
        print ""+url
        print ""+str(page)      
        STATS("CATEGORIES", "Function") 
        CATEGORIES(url,page)
        
elif mode==1:     
        STATS("NEWS", "Function") 
        NEWS(url,page)

elif mode==2:
        print ""+url
        print ""+str(page) 
        STATS("INDEX", "Function")       
        INDEX(url,page)

elif mode==4:
        print ""+url
        STATS("VIDEOLINK", "Item")
        VIDEOLINK(url, name)
     
elif mode==3:
        STATS("LIVE", "Function") 
        LIVE(url,page)
 
xbmcplugin.endOfDirectory(int(sys.argv[1]))

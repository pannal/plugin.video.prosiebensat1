#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import xbmcvfs
import requests
import base64
import urllib
from inputstreamhelper import Helper
from hashlib import sha1

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
defaultFanart = os.path.join(addonPath, 'resources/fanart.png')
icon = os.path.join(addonPath, 'resources/icon.png')
baseURL = "https://www."
pluginBaseUrl = "plugin://" + addon.getAddonInfo('id')
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'


def listShows(entry):
    content = getContentFull(entry.get('domain'), entry.get('path'))
    if content and len(content) > 0:
        shows = getListItems(content.get('data', None), 'show')
        for show in shows:
            infoLabels = show.get('infoLabels', {})
            art = show.get('art')
            url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': '{0}{1}'.format(show.get('url'), '/video'), 'cmsId': show.get('cmsId'), 'type': 'season', 'art': art, 'infoLabels': infoLabels}})
            addDir(infoLabels.get('title'), url, art=art, infoLabels=infoLabels)

    xbmcplugin.setContent(addon_handle, 'tvshows')
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def listShowcontent(entry):
    content = getContentFull(entry.get('domain'), entry.get('path'))
    if content and len(content) > 0:
        items = getListItems(content.get('data', None), entry.get('type'), entry.get('domain'), entry.get('path'), entry.get('cmsId'))
        seasons = sorted(list(dict.fromkeys(['{0}'.format(item.get('infoLabels', {}).get('season')) for item in items if item.get('infoLabels', {}).get('season')])))
        if entry.get('type') == 'season' and len(seasons) > 1:
            for season in seasons:
                url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': entry.get('path'), 'cmsId': entry.get('cmsId'), 'seasonno': season}})
                addDir('Staffel {0}'.format(season), url, art=entry.get('art'), infoLabels=entry.get('infoLabels'))
                xbmcplugin.setContent(addon_handle, 'tvshows')
        else:
            for item in items:
                infoLabels = item.get('infoLabels', {})
                if item.get('type') == 'season':
                    url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': item.get('url'), 'cmsId': entry.get('cmsId')}})
                    addDir(infoLabels.get('title'), url, art=item.get('art'), infoLabels=infoLabels)
                    xbmcplugin.setContent(addon_handle, 'tvshows')
                else:
                    if entry.get('seasonno') and infoLabels.get('season') != int(entry.get('seasonno')):
                        continue
                    url = build_url({'action': 'play', 'entry': {'domain': entry.get('domain'), 'path': item.get('url')}})
                    addFile(infoLabels.get('title'), url, art=item.get('art', {}), infoLabels=infoLabels)
                    xbmcplugin.setContent(addon_handle, 'episodes')
                    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_EPISODE)

    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def getContentFull(domain, path):
    base = 'https://magellan-api.p7s1.io/content-full/{0}{1}/graphql'.format(domain, path)
    parameters = {'query': ' query FullContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { content(type: FULL, contentType: $contentType) { ...fContent } somtag(contentType: $contentType) { ...fSomtag } tracking(contentType: $contentType) { ...fTracking } } } } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } fragment fSomtag on Somtag { configs } fragment fTracking on Tracking { context }'}
    parameters.update({'variables': '{{"authentication":null,"contentType":"frontpage","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    url = '{0}?{1}'.format(base, urllib.urlencode(parameters).replace('+', '%20'))

    result = requests.get(url).json()
    if result and path.endswith('/video') and result.get('data', None) and result.get('data').get('site', None) and result.get('data').get('site').get('path', None) and not result.get('data').get('site').get('path').get('somtag'):
        result = getContentFull(domain, '{0}s'.format(path))
    return result

def getContentPreview(domain, path):
    base = 'https://magellan-api.p7s1.io/content-preview/{0}{1}/graphql'.format(domain, path)
    parameters = {'query': ' query PreviewContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { route { ...fRoute } page { ...fPage ...fVideoPage } content(type: PREVIEW, contentType: $contentType) { ...fContent } mainNav: navigation(type: MAIN) { items { ...fNavigationItem } } metaNav: navigation(type: META) { items { ...fNavigationItem } } channelNav: navigation(type: CHANNEL) { items { ...fNavigationItem } } showsNav: navigation(type: SHOWS) { items { ...fNavigationItem } } footerNav: navigation(type: FOOTER) { items { ...fNavigationItem } } networkNav: navigation(type: NETWORK) { items { ...fNavigationItem } } } } } fragment fRoute on Route { url exists authentication comment contentType name cmsId startDate status endDate } fragment fPage on Page { cmsId contentType pagination { ...fPagination } title shortTitle subheadline proMamsId additionalProMamsIds route source regWall { ...fRegWall } links { ...fLink } metadata { ...fMetadata } breadcrumbs { id href title text } channel { ...fChannel } seo { ...fSeo } modified published flags mainClassNames } fragment fPagination on Pagination { kind limit parent contentType } fragment fRegWall on RegWall { isActive start end } fragment fLink on Link { id classes language href relation title text outbound } fragment fMetadata on Metadata { property name content } fragment fChannel on Channel { name title shortName licenceTerms cssId cmsId proMamsId additionalProMamsIds route image hasLogo liftHeadings, logo sponsors { ...fSponsor } } fragment fSponsor on Sponsor { name url image } fragment fSeo on Seo { title keywords description canonical robots } fragment fVideoPage on VideoPage { ... on VideoPage { copyright description longDescription duration season episode airdate videoType contentResource image webUrl livestreamStartDate livestreamEndDate recommendation { results { headline subheadline duration url image videoType contentType recoVariation recoSource channel { ...fChannelInfo } } } } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } '}
    parameters.update({'variables': '{{"authentication":null,"contentType":"video","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    url = '{0}{1}?{2}'.format(base, path, urllib.urlencode(parameters).replace('+', '%20'))

    result = requests.get(url).json()
    if result and path.endswith('/video') and result.get('data', None) and result.get('data').get('site', None) and result.get('data').get('site').get('path', None) and result.get('data').get('site').get('path').get('somtag', None) and result.get('data').get('site').get('path').get('route').get('status').lower() == 'not_found':
        result = getContentFull(domain, '{0}s'.format(path))
    return result

def getListItems(data, type, domain=None, path=None, cmsId=None):
    items = []
    if type == 'season':
        content = getContentPreview(domain, path)
        links = getShownav(content.get('data', None))
        if len(links) > 0:
            for link in links:
                items.append(getContentInfos(link, 'season'))

    if len(items) == 0 and data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('content', None) and data.get('site').get('path').get('content').get('areas', None):
        areas = data.get('site').get('path').get('content', None).get('areas')
        if len(areas) > 0:
            containers = areas[0].get('containers')
            for container in containers:
                elements = container.get('elements', None)
                if elements and len(elements) > 0:
                    element = elements[0]
                    groups = element.get('groups', None)
                    if groups and len(groups) > 0:
                        groupitems = groups[0].get('items', None)
                        if groupitems:
                            for groupitem in groupitems:
                                if type == 'show':
                                    items.append(getContentInfos(groupitem, 'show'))
                                elif cmsId and groupitem.get('channel').get('cmsId') == cmsId:
                                    if not groupitem.get('videoType') and groupitem.get('headline').lower().startswith('staffel') or groupitem.get('headline').lower().startswith('season'):
                                        items.append(getContentInfos(groupitem, 'season'))
                                    elif groupitem.get('videoType') and groupitem.get('videoType').lower() == 'full':
                                        items.append(getContentInfos(groupitem, 'episode'))

    return items   

def getShownav(data):
    items = []
    if data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('channelNav', None) and data.get('site').get('path').get('channelNav').get('items', None):
        channelitems = data.get('site').get('path').get('channelNav').get('items')
        for channelitem in channelitems:
            if channelitem.get('title').lower() == 'video':
                for channelsubitem in channelitem.get('items'):
                    if channelsubitem.get('title').lower().startswith('staffel'):
                        items.append(channelsubitem)

    return items
                
def getContentInfos(data, type):
    infos = {'url': data.get('url') if data.get('url') else data.get('href'), 'type': type}

    if type == 'episode':
        title = data.get('headline')
        if title.find('Originalversion') > 1:
            title = title.replace('Originalversion', 'OV')
        if title.find(':') > -1 and title.find('Episode') > -1 or title.find('Folge') > -1:
            title = title.split(':')[1]
        infoLabels = {'title': title}
        infoLabels.update({'tvShowTitle': data.get('channel').get('title')})
        season = data.get('epg').get('season').get('number')
        if season.startswith('s'):
            season = season.split('s', 1)[1]
        infoLabels.update({'season': int(season)})
        episode = data.get('epg').get('episode').get('number')
        if episode.startswith('e'):
            episode = episode.split('e', 1)[1]
        infoLabels.update({'episode': int(episode)})
        infoLabels.update({'duration': data.get('epg').get('duration')})
        infoLabels.update({'mediatype': 'episode'})
    elif type == 'season':
        infoLabels = {'title': data.get('headline').split(':')[0] if data.get('headline') else data.get('title').split(':')[0]}
    elif type == 'show':
        infoLabels = {'title': data.get('channel').get('shortName') if data.get('channel').get('shortName') else data.get('headline')}
        infos.update({'cmsId': data.get('id')})

    infoLabels.update({'plot': data.get('info').encode('utf-8') if data.get('info', None) else None})    
    infos.update({'infoLabels' : infoLabels})

    if data.get('picture'):
        art = {'thumb': '{0}{1}'.format(data.get('picture').get('url'), '/profile:mag-648x366')}
        infos.update({'art' : art})

    return infos

def getVideoId(data):
    videoid = None
    if data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('page', None):
        page = data.get('site').get('path').get('page')
        videoid = page.get('contentResource')[0].get('id')

    return videoid
    
def playVideo(entry):
    video_id = None
    content = getContentPreview(entry.get('domain'), entry.get('path'))
    if content:
        video_id = getVideoId(content.get('data'))

    # Inputstream and DRM
    helper = Helper(protocol='mpd', drm='widevine')
    isInputstream = helper.check_inputstream()

    if not isInputstream:
        access_token = 'h''b''b''t''v'
        salt = '0''1''r''e''e''6''e''L''e''i''w''i''u''m''i''e''7''i''e''V''8''p''a''h''g''e''i''T''u''i''3''B'
        client_name = 'h''b''b''t''v'
    else:
        access_token = 'seventv-web'
        salt = '01!8d8F_)r9]4s[qeuXfP%'
        client_name = ''

    source_id = 0
    json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s?access_token=%s&client_location=%s&client_name=%s' % (video_id, access_token, entry.get('path'), client_name)
    json_data = requests.get(json_url).json()

    if isInputstream:
        for stream in json_data['sources']:
            if stream['mimetype'] == 'application/dash+xml':
                if int(source_id) < int(stream['id']):
                    source_id = stream['id']
    else:
        if json_data["is_protected"] == True:
            xbmc.executebuiltin('Notification("Inputstream", "DRM geschützte Folgen gehen nur mit Inputstream")')
            return
        else:
            for stream in json_data['sources']:
                if stream['mimetype'] == 'video/mp4':
                    if int(source_id) < int(stream['id']):
                        source_id = stream['id']

    client_id_1 = salt[:2] + sha1(''.join([str(video_id), salt, access_token, entry.get('path'), salt, client_name]).encode('utf-8')).hexdigest()

    json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources?access_token=%s&client_location=%s&client_name=%s&client_id=%s' % (video_id, access_token, entry.get('path'), client_name, client_id_1)
    json_data = requests.get(json_url).json()
    server_id = json_data['server_id']

    # client_name = 'kolibri-1.2.5'
    client_id = salt[:2] + sha1(''.join([salt, video_id, access_token, server_id, entry.get('path'), str(source_id), salt, client_name]).encode('utf-8')).hexdigest()
    url_api_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources/url?%s' % (video_id, urllib.urlencode({
        'access_token': access_token,
        'client_id': client_id,
        'client_location': entry.get('path'),
        'client_name': client_name,
        'server_id': server_id,
        'source_ids': str(source_id),
    }))

    json_data = requests.get(url_api_url).json()
    max_id = 0
    for stream in json_data["sources"]:
        ul = stream["url"]
        try:
            sid = re.compile('-tp([0-9]+).mp4', re.DOTALL).findall(ul)[0]
            id = int(sid)
            if max_id < id:
                max_id = id
                data = ul
        except:
          data = ul

    li = xbmcgui.ListItem(path='%s|%s' % (data, userAgent))
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')

    try:
        lic = json_data['drm']['licenseAcquisitionUrl']
        token = json_data['drm']['token']
        li.setProperty('inputstream.adaptive.license_key', '%s?token=%s|%s|R{SSM}|' % (lic, token, userAgent))
    except:
        pass

    if entry.get('infoLabels') and len(entry.get('infoLabels')) > 0:
        li.setInfo('video', entry.get('infoLabels'))

    xbmcplugin.setResolvedUrl(addon_handle, True, li)

def index():
    entries = [
                  {'title': 'ProSieben', 'domain': 'prosieben.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/prosieben.png')}},
                  {'title': 'Sat.1', 'domain': 'sat1.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sat1.png')}},
                  {'title': 'ProSieben MAXX', 'domain': 'prosiebenmaxx.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/prosiebenmaxx.png')}},
                  {'title': 'Kabel Eins', 'domain': 'kabeleins.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/kabeleins.png')}},
                  {'title': 'kabel eins Doku', 'domain': 'kabeleinsdoku.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/kabeleinsdoku.png')}},
                  {'title': 'Sixx', 'domain': 'sixx.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sixx.png')}},
                  {'title': 'Sat.1 Gold', 'domain': 'sat1gold.de', 'path': '/tv', 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sat1gold.png')}}
              ]
    for entry in entries:
        parameter = {'action': 'shows', 'entry': entry}
        addDir(entry.get('title'), build_url(parameter), art=entry.get('art'))

    #xbmcplugin.setContent(addon_handle, 'tvshows')
    xbmcplugin.endOfDirectory(addon_handle)

def addDir(label, url, art={}, infoLabels={}):
    addFile(label, url, art, infoLabels, True)

def addFile(label, url, art={}, infoLabels={}, isFolder=False):
    li = xbmcgui.ListItem(label)
    li.setInfo('video', infoLabels)
    li.setArt(art)
    li.setProperty('IsPlayable', str(isFolder))

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=isFolder)

def build_url(query):
    return pluginBaseUrl + '?' + base64.urlsafe_b64encode(json.dumps(query))

params = urllib.unquote(sys.argv[2][1:])
if len(params) > 0:
    if len(params) % 4 != 0:
        params += '=' * (4 - len(params) % 4)

    params = dict(json.loads(base64.urlsafe_b64decode(params)))
xbmc.log('params = {0}'.format(params))
if 'action' in params:
    action = params.get('action')
    if(action == 'shows'):
        listShows(params.get('entry'))
    elif(action == 'showcontent'):
        listShowcontent(params.get('entry'))
    elif(action == 'play'):
        playVideo(params.get('entry'))
else:
    index()
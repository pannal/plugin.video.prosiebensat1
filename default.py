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
import calendar
from datetime import datetime, timedelta
import time

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
defaultFanart = os.path.join(addonPath, 'resources/fanart.png')
icon = os.path.join(addonPath, 'resources/icon.png')
baseURL = "https://www."
pluginBaseUrl = "plugin://" + addon.getAddonInfo('id')
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'

channels = [
               {
                  'id': '1'
                , 'label': 'ProSieben'
                , 'domain': 'prosieben.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/prosieben.png')}
                , 'property_name': 'prosieben-de-24x7'
                , 'client_location': 'https://www.prosieben.de/livestream'
                , 'access_token': 'prosieben'
                , 'client_token':  '01b353c155a9006e80ae7c5ed3eb1c09c0a6995556'
                , 'epg_name': 'prosieben'
              }
            , {
                  'id': '2'
                , 'label': 'SAT.1'
                , 'domain': 'sat1.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sat1.png')}
                , 'property_name': 'sat1-de-24x7'
                , 'client_location': 'https://www.sat1.de/livestream'
                , 'access_token': 'sat1'
                , 'client_token':  '01e491d866b37341734d691a8acb48af37a77bf26f'
                , 'epg_name': 'sat1'
              }
            , {
                  'id': '3'
                , 'label': 'kabel eins'
                , 'domain': 'kabeleins.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/kabeleins.png')}
                , 'property_name': 'kabeleins-de-24x7'
                , 'client_location': 'https://www.kabeleins.de/livestream'
                , 'access_token': 'kabeleins'
                , 'client_token':  '014c87bfe2ce4aebf6219ed699602a1f152194e4cd'
                , 'epg_name': 'k1'
              }
            , {
                  'id': '4'
                , 'label': 'Sixx'
                , 'domain': 'sixx.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sixx.png')}
                , 'property_name': 'sixx-de-24x7'
                , 'client_location': 'https://www.sixx.de/livestream'
                , 'access_token': 'sixx'
                , 'client_token':  '017705703133050842d3ca11fc20a6fc205b8b4025'
                , 'epg_name': 'sixx'
              }
            , {
                  'id': '5'
                , 'label': 'ProSiebenMaxx'
                , 'domain': 'prosiebenmaxx.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/prosiebenmaxx.png')}
                , 'property_name' : 'prosiebenmaxx-de-24x7'
                , 'client_location': 'https://www.prosiebenmaxx.de/livestream'
                , 'access_token' : 'prosiebenmaxx'
                , 'client_token':  '01963623e9b364805dbe12f113dba1c4914c24d189'
                , 'epg_name': 'prosiebenmaxx'
              }
            , {
                  'id': '6'
                , 'label': 'SAT.1 Gold'
                , 'domain': 'sat1gold.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/sat1gold.png')}
                , 'property_name' : 'sat1gold-de-24x7'
                , 'client_location': 'https://www.sat1gold.de/livestream'
                , 'access_token' : 'sat1gold'
                , 'client_token': '01107e433196365e4d54d0f90bdf1070cd2df5e190'
                , 'epg_name': 'sat1gold'
              }
            , {
                  'id': '7'
                , 'label': 'kabel eins Doku'
                , 'domain': 'kabeleinsdoku.de'
                , 'path': '/tv'
                , 'art': {'icon': os.path.join(addonPath, 'resources/media/channels/kabeleinsdoku.png')}
                , 'property_name' : 'kabeleinsdoku-de-24x7'
                , 'client_location': 'https://www.kabeleinsdoku.de/livestream'
                , 'access_token' : 'kabeleinsdoku'
                , 'client_token': '01ea6d32ff5de5d50d0290dbdf819f9b856bcfd44a'
                , 'epg_name': 'k1doku'
              }
           ]

rootDirs = [
              {'label': 'Live', 'action': 'livechannels'}
            , {'channels': channels}
           ]

def listShows(entry):
    content = getContentFull(entry.get('domain'), entry.get('path'))
    if content and len(content) > 0:
        shows = getListItems(content.get('data', None), 'show').get('items')
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
        detail = getListItems(content.get('data', None), entry.get('type'), entry.get('domain'), entry.get('path'), entry.get('cmsId'))
        items = detail.get('items')
        seasons = sorted(list(dict.fromkeys(['{0}'.format(item.get('infoLabels', {}).get('season')) for item in items if item.get('infoLabels', {}).get('season')])))
        if detail.get('type') == 'season' and len(seasons) > 1:
            for season in seasons:
                url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': entry.get('path'), 'cmsId': entry.get('cmsId'), 'seasonno': season}})
                addDir('Staffel {0}'.format(season), url, art=entry.get('art'), infoLabels=entry.get('infoLabels'))
                xbmcplugin.setContent(addon_handle, 'tvshows')

            noseasons = [item for item in items if not item.get('infoLabels', {}).get('season')]
            if len(noseasons) > 0:
                url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': entry.get('path'), 'cmsId': entry.get('cmsId'), 'seasonno': None}})
                addDir('Videos ohne Staffelzuordnung', url, art=entry.get('art'), infoLabels=entry.get('infoLabels'))
                xbmcplugin.setContent(addon_handle, 'tvshows')
        else:
            for item in items:
                infoLabels = item.get('infoLabels', {})
                if detail.get('type') == 'season':
                    url = build_url({'action': 'showcontent', 'entry': {'domain': entry.get('domain'), 'path': item.get('url'), 'cmsId': entry.get('cmsId')}})
                    addDir(infoLabels.get('title'), url, art=item.get('art'), infoLabels=infoLabels)
                    xbmcplugin.setContent(addon_handle, 'tvshows')
                else:
                    if detail.get('type') != 'episode' and entry.get('seasonno') and infoLabels.get('season') != int(entry.get('seasonno')):
                        continue
                    elif detail.get('type') != 'episode' and not entry.get('seasonno') and infoLabels.get('season'):
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
    xbmc.log('url = {0}'.format(url))
    result = requests.get(url).json()
    if result and path.endswith('/video') and result.get('data', None) and result.get('data').get('site', None) and result.get('data').get('site').get('path', None) and not result.get('data').get('site').get('path').get('somtag'):
        result = getContentFull(domain, '{0}s'.format(path))
    return result

def getContentPreview(domain, path):
    base = 'https://magellan-api.p7s1.io/content-preview/{0}{1}/graphql'.format(domain, path)
    if path == '/livestream':
        parameters = {'query': 'query PreviewContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { route { ...fRoute } page { ...fPage ...fLivestream24Page } content(type: PREVIEW, contentType: $contentType) { ...fContent } mainNav: navigation(type: MAIN) { items { ...fNavigationItem } } metaNav: navigation(type: META) { items { ...fNavigationItem } } channelNav: navigation(type: CHANNEL) { items { ...fNavigationItem } } showsNav: navigation(type: SHOWS) { items { ...fNavigationItem } } footerNav: navigation(type: FOOTER) { items { ...fNavigationItem } } networkNav: navigation(type: NETWORK) { items { ...fNavigationItem } } } } } fragment fRoute on Route { url exists authentication comment contentType name cmsId startDate status endDate } fragment fPage on Page { cmsId contentType pagination { ...fPagination } title shortTitle subheadline proMamsId additionalProMamsIds route source regWall { ...fRegWall } links { ...fLink } metadata { ...fMetadata } breadcrumbs { id href title text } channel { ...fChannel } seo { ...fSeo } modified published flags mainClassNames } fragment fPagination on Pagination { kind limit parent contentType } fragment fRegWall on RegWall { isActive start end } fragment fLink on Link { id classes language href relation title text outbound } fragment fMetadata on Metadata { property name content } fragment fChannel on Channel { name title shortName licenceTerms cssId cmsId proMamsId additionalProMamsIds route image hasLogo liftHeadings, logo sponsors { ...fSponsor } } fragment fSponsor on Sponsor { name url image } fragment fSeo on Seo { title keywords description canonical robots } fragment fLivestream24Page on Livestream24Page { ... on Livestream24Page { livestreamId contentResources epg { name items { ...fEpgItem tvShowTeaser { ...fTeaserItem } } } } } fragment fEpgItem on EpgItem { id title description startTime endTime episode { number } season { number } tvShow { title } images { url title copyright } links { href contentType title } } fragment fTeaserItem on TeaserItem { id url info headline contentType channel { ...fChannelInfo } branding { ...fBrand } site picture { url } videoType orientation date flags valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } '}
        parameters.update({'variables': '{{"authentication":null,"contentType":"video","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    else:
        parameters = {'query': ' query PreviewContentQuery($domain: String!, $url: String!, $date: DateTime, $contentType: String, $debug: Boolean!, $authentication: AuthenticationInput) { site(domain: $domain, date: $date, authentication: $authentication) { domain path(url: $url) { route { ...fRoute } page { ...fPage ...fVideoPage } content(type: PREVIEW, contentType: $contentType) { ...fContent } mainNav: navigation(type: MAIN) { items { ...fNavigationItem } } metaNav: navigation(type: META) { items { ...fNavigationItem } } channelNav: navigation(type: CHANNEL) { items { ...fNavigationItem } } showsNav: navigation(type: SHOWS) { items { ...fNavigationItem } } footerNav: navigation(type: FOOTER) { items { ...fNavigationItem } } networkNav: navigation(type: NETWORK) { items { ...fNavigationItem } } } } } fragment fRoute on Route { url exists authentication comment contentType name cmsId startDate status endDate } fragment fPage on Page { cmsId contentType pagination { ...fPagination } title shortTitle subheadline proMamsId additionalProMamsIds route source regWall { ...fRegWall } links { ...fLink } metadata { ...fMetadata } breadcrumbs { id href title text } channel { ...fChannel } seo { ...fSeo } modified published flags mainClassNames } fragment fPagination on Pagination { kind limit parent contentType } fragment fRegWall on RegWall { isActive start end } fragment fLink on Link { id classes language href relation title text outbound } fragment fMetadata on Metadata { property name content } fragment fChannel on Channel { name title shortName licenceTerms cssId cmsId proMamsId additionalProMamsIds route image hasLogo liftHeadings, logo sponsors { ...fSponsor } } fragment fSponsor on Sponsor { name url image } fragment fSeo on Seo { title keywords description canonical robots } fragment fVideoPage on VideoPage { ... on VideoPage { copyright description longDescription duration season episode airdate videoType contentResource image webUrl livestreamStartDate livestreamEndDate recommendation { results { headline subheadline duration url image videoType contentType recoVariation recoSource channel { ...fChannelInfo } } } } } fragment fChannelInfo on ChannelInfo { title shortName cssId cmsId } fragment fContent on Content { areas { ...fContentArea } } fragment fContentArea on ContentArea { id containers { ...fContentContainer } filters { ...fFilterOptions } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fContentContainer on ContentContainer { id style elements { ...fContentElement } } fragment fContentElement on ContentElement { id authentication title description component config style highlight navigation { ...fNavigationItem } regwall filters { ...fFilterOptions } update styleModifiers groups { id title total cursor itemSource { type id } items { ...fContentElementItem } debug @include(if: $debug) { ...fContentDebugInfo } } groupLayout debug @include(if: $debug) { ...fContentDebugInfo } } fragment fNavigationItem on NavigationItem { selected href channel { ...fChannelInfo } contentType title items { selected href channel { ...fChannelInfo } contentType title } } fragment fFilterOptions on FilterOptions { type remote categories { name title options { title id channelId } } } fragment fContentElementItem on ContentElementItem { id url info branding { ...fBrand } body config headline contentType channel { ...fChannelInfo } site picture { url } videoType orientation date duration flags genres valid { from to } epg { episode { ...fEpisode } season { ...fSeason } duration nextEpgInfo { ...fEpgInfo } } debug @include(if: $debug) { ...fContentDebugInfo } } fragment fBrand on Brand { id, name } fragment fEpisode on Episode { number } fragment fSeason on Season { number } fragment fEpgInfo on EpgInfo { time endTime primetime } fragment fContentDebugInfo on ContentDebugInfo { source transformations { description } } '}
        parameters.update({'variables': '{{"authentication":null,"contentType":"livestream24","debug":false,"domain":"{0}","isMobile":false,"url":"{1}"}}'.format(domain, path)})
    url = '{0}{1}?{2}'.format(base, path, urllib.urlencode(parameters).replace('+', '%20'))
    xbmc.log('url = {0}'.format(url))
    result = requests.get(url).json()
    if result and path.endswith('/video') and result.get('data', None) and result.get('data').get('site', None) and result.get('data').get('site').get('path', None) and result.get('data').get('site').get('path').get('route').get('status').lower() == 'not_found':
        result = getContentPreview(domain, '{0}s'.format(path))
    return result

def getListItems(data, type, domain=None, path=None, cmsId=None, content=None):
    if not content:
        content = {'items': []}

    if type == 'season':
        subcontent = getContentPreview(domain, path)
        content = getShownav(subcontent.get('data', None), content, domain, cmsId)

    if (len(content.get('items')) == 0 or content.get('type') == 'episode') and data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('content', None) and data.get('site').get('path').get('content').get('areas', None):
        areas = data.get('site').get('path').get('content').get('areas')
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
                                citems = content.get('items')
                                if type == 'show':
                                    item = getContentInfos(groupitem, 'show')
                                    if checkItemUrlExists(citems, item) == False:
                                        citems.append(item)
                                        content.update({'items': citems})
                                elif cmsId and groupitem.get('channel').get('cmsId') == cmsId:
                                    if not groupitem.get('videoType') and groupitem.get('headline') and (groupitem.get('headline').lower().startswith('staffel') or groupitem.get('headline').lower().startswith('season')):
                                        content.update({'type': 'season'})
                                        item = getContentInfos(groupitem, 'season')
                                        if checkItemUrlExists(citems, item) == False:
                                            citems.append(item)
                                            content.update({'items': citems})
                                    elif groupitem.get('videoType') and groupitem.get('videoType').lower() == 'full':
                                        content.update({'type': 'episode'})
                                        item = getContentInfos(groupitem, 'episode')
                                        if checkItemUrlExists(citems, item) == False:
                                            citems.append(item)
                                            content.update({'items': citems})

    if not content.get('type'):
        content.update({'type': type})

    return content   

def getShownav(data, content, domain, cmsId):
    if data.get('site', None) and data.get('site').get('path', None) and data.get('site').get('path').get('channelNav', None) and data.get('site').get('path').get('channelNav').get('items', None):
        channelitems = data.get('site').get('path').get('channelNav').get('items')
        for channelitem in channelitems:
            if channelitem.get('title').lower() == 'video' or channelitem.get('title').lower() == 'videos':
                for channelsubitem in channelitem.get('items'):
                    if channelsubitem.get('title').lower().startswith('staffel') or channelsubitem.get('title').lower().startswith('season'):
                        content.update({'type': 'show'})
                        citems = content.get('items')
                        citems.append(channelsubitem)
                        content.update({'items': citems})
                    elif channelsubitem.get('title').lower().startswith('episode') or channelsubitem.get('title').lower().startswith('folge'):
                        subcontent = getContentFull(domain, channelsubitem.get('href'))
                        content = getListItems(subcontent.get('data'), 'episode', domain, channelsubitem.get('href'), cmsId, content)
                        content.update({'type': 'episode'})

    return content
                
def getContentInfos(data, type):
    infos = {}
    if type == 'live':
        now_item = None
        next_item = None
        for index, item in enumerate(data.get('items')):
            now = datetime.utcnow()

            start_time = datetime.fromtimestamp(time.mktime(time.strptime(item.get('startTime'), '%Y-%m-%dT%H:%M:%S.%fZ')))
            end_time = datetime.fromtimestamp(time.mktime(time.strptime(item.get('endTime'), '%Y-%m-%dT%H:%M:%S.%fZ')))

            infos.update({'stime': start_time})
            infos.update({'etime': end_time})
            if (now >= start_time) and (now <= end_time):
                now_item = item
                next_item = data.get('items')[index + 1]
                break
        
        if now_item:
            infoLabels = {'title': now_item.get('title')}
            if now_item.get('tvShow'):
                if not infoLabels.get('title'):
                    infoLabels.update({'title': now_item.get('tvShow').get('title')})
                infoLabels.update({'tvShowTitle': now_item.get('tvShow').get('title')})
                infoLabels.update({'mediatype': 'episode'})
                
            infoLabels.update({'season': now_item.get('season').get('number')})
            infoLabels.update({'episode': now_item.get('episode').get('number')})
            
            local_start_time = utc_to_local(infos.get('stime'))
            local_end_time = utc_to_local(infos.get('etime'))
            plot = '{0} - {1}'.format(local_start_time.strftime('%H:%M'), local_end_time.strftime('%H:%M'))
            if next_item:
                next_title = next_item.get('title').encode('utf-8') if next_item.get('title') else None
                next_show = next_item.get('tvShow').get('title').encode('utf-8') if next_item.get('tvShow') else ''
                
                plot += '\nDanach: [COLOR blue]{0}[/COLOR] {1}'.format(next_show, next_title) if next_title and next_show != '' and next_title != next_show else '\nDanach: {0}'.format(next_title if next_title else next_show)

            plot += '\n\n'
            plot += now_item.get('description').encode('utf-8') if now_item.get('description') else ''
            infoLabels.update({'plot': plot})
            
            if now_item.get('images') and len(now_item.get('images')) > 0:
                art = {'thumb': '{0}{1}'.format(now_item.get('images')[0].get('url'), '/profile:mag-648x366')}
                infos.update({'art' : art})

            infos.update({'infoLabels' : infoLabels})    
    else:
        infos.update({'url': data.get('url') if data.get('url') else data.get('href'), 'type': type})
    
        if type == 'episode':
            title = data.get('headline')
            if title.find('Originalversion') > 1:
                title = title.replace('Originalversion', 'OV')
            if title.find(':') > -1 and (title.find('Episode') > -1 or title.find('Folge') > -1):
                title = title.split(':')[1]
            infoLabels = {'title': title}
            infoLabels.update({'tvShowTitle': data.get('channel').get('title')})
            season = data.get('epg').get('season').get('number')
            if season and season.startswith('s'):
                season = season.split('s', 1)[1]
            if season:
                infoLabels.update({'season': int(season)})
            episode = data.get('epg').get('episode').get('number')
            if episode and episode.startswith('e'):
                episode = episode.split('e', 1)[1]
            if episode:
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

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

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
    
def playLive(entry):
    # Inputstream and DRM
    helper = Helper(protocol='mpd', drm='widevine')
    if helper.check_inputstream() == False:
        return

    url = 'https://vas-live-mdp.glomex.com/live/1.0/getprotocols?%s' % (urllib.urlencode({
        'access_token': entry.get('access_token'),
        'client_location':  entry.get('client_location'),
        'property_name':  entry.get('property_name'),
        'client_token':  entry.get('client_token'),
        'secure_delivery': 'true'
    }))

    data = requests.get(url).json()

    server_token = data.get('server_token')
    salt = '01!8d8F_)r9]4s[qeuXfP%'
    client_token = salt[:2] + sha1(''.join([ entry.get('property_name'), salt,  entry.get('access_token'), server_token,  entry.get('client_location'), 'dash:widevine']).encode('utf-8')).hexdigest()

    url = 'https://vas-live-mdp.glomex.com/live/1.0/geturls?%s' % (urllib.urlencode({
        'access_token':  entry.get('access_token'),
        'client_location':  entry.get('client_location'),
        'property_name':  entry.get('property_name'),
        'protocols': 'dash:widevine',
        'server_token': server_token,
        'client_token': client_token,
        'secure_delivery': 'true'
    }))

    data = requests.get(url).json()['urls']['dash']['widevine']

    li = xbmcgui.ListItem(path=data['url'] + "|" + userAgent)
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')

    try:
        lic = data['drm']['licenseAcquisitionUrl']
        token = data['drm']['token']
        li.setProperty('inputstream.adaptive.license_key', '%s?token=%s|%s|R{SSM}|' % (lic, token, userAgent))
    except:
        pass

    xbmcplugin.setResolvedUrl(addon_handle, True, li)
    
def rootDir():
    for dir in rootDirs:
        if not dir.get('channels'):
            url = build_url({'action': dir.get('action')})
            addDir(dir.get('label'), url)
        else:
            channels = dir.get('channels')
            for channel in channels:
                parameter = {'action': 'shows', 'entry': channel}
                addDir(channel.get('label'), build_url(parameter), art=channel.get('art'))

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def listLiveChannels():
    content = getContentPreview(channels[0].get('domain'), '/livestream')
    epg_data = None
    if content.get('data') and content.get('data').get('site') and content.get('data').get('site').get('path') and content.get('data').get('site').get('path').get('page') and content.get('data').get('site').get('path').get('page').get('epg'):
        epg_data = content.get('data').get('site').get('path').get('page').get('epg')

    addDir('Aktualisieren', 'xbmc.executebuiltin("Container.Refresh")', infoLabels={'plot': 'Aktualisieren'})
    for channel in channels:
        thumbnailImage = None
        if channel.get('property_name', None) and epg_data:
            infoLabels = None
            art = None
            for epg in epg_data:
                if epg.get('name').lower() == channel.get('epg_name').lower():
                    infos = getContentInfos(epg, 'live')
                    infoLabels = infos.get('infoLabels')
                    art = infos.get('art')

            channel.update({'infoLabels': infoLabels, 'art': art})
            url = build_url({'action': 'playlive', 'entry': channel})
            title = infoLabels.get('title') if infoLabels.get('tvShowTitle', None) is None or infoLabels.get('tvShowTitle') == infoLabels.get('title') else '[COLOR blue]' + infoLabels.get('tvShowTitle') + '[/COLOR] ' + infoLabels.get('title')
            title = '[COLOR orange][%s][/COLOR] %s' % (channel.get('label'), title)
            addFile(title, url, art=art, infoLabels=infoLabels)

    xbmcplugin.setContent(addon_handle, 'files')
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

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

def checkItemUrlExists(items, compItem):
    for item in items:
        if item.get('url') == compItem.get('url'):
            return True

    return False

params = urllib.unquote(sys.argv[2][1:])
if len(params) > 0:
    if len(params) % 4 != 0:
        params += '=' * (4 - len(params) % 4)

    params = dict(json.loads(base64.urlsafe_b64decode(params)))
xbmc.log('params = {0}'.format(params))
if 'action' in params:
    action = params.get('action')
    if action == 'livechannels':
        listLiveChannels()
    elif action == 'shows':
        listShows(params.get('entry'))
    elif action == 'showcontent':
        listShowcontent(params.get('entry'))
    elif action == 'play':
        playVideo(params.get('entry'))
    elif action == 'playlive':
        playLive(params.get('entry'))
else:
    rootDir()
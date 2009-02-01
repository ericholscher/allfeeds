import urllib2
import simplejson as json
import re, os
import datetime
import BeautifulSoup as bs
from djangopeople.models import Member, ServiceEntry, Service, Subdomain
from django.template.defaultfilters import slugify

def _update_python(soup):
        for links in soup.find('div', {'class': 'sidebar'}).find('ul').findAll('li'):
            try:
                yield (links.findAll('a')[1]['href'], links(text=True)[2], links.a['href'])
            except Exception, e:
                print "Someone has no website: %s" % e
                continue

def _update_django(soup):
    for links in soup.find('div', id='content-related').findAll('ul')[-1].findAll('li'):
        yield (links.a['href'], links.a(text=True)[0], links.findAll('a')[1]['href'])

SUBDOMAIN_DISPATCH = {
    'django': _update_django,
    'python': _update_python,
}

def _recently_updated(subdomain_obj):
    last_checked = subdomain_obj.last_user_check
    now = datetime.datetime.now()
    if last_checked:
        diff = now - last_checked
        if not diff.days > 0:
            print "NOT UPDATING BECAUSE RECENTLY UPDATED"
            return True
    subdomain_obj.last_user_check = now
    subdomain_obj.save()
    return False


def _update_user_list(subdomain_obj):
    from_url = subdomain_obj.source_url
    resp = urllib2.urlopen(from_url)
    soup = bs.BeautifulSoup(resp.read())

    parser_func = SUBDOMAIN_DISPATCH[subdomain_obj.slug]
    for url, name, feed in parser_func(soup):
        matched = _create_user(url, name, feed, subdomain_obj, from_url=from_url)


def _create_user(url, name, feed, subdomain_obj='', from_url='', requery=False):
        member, created = Member.objects.get_or_create(name=name)
        if created:
            try:
                member.site_url = url
                member.save()
                print "Created user %s" % name
            except Exception:
                print "Name fail"

        s, created2 = ServiceEntry.objects.get_or_create(feed_url=feed, profile_url=feed, service=Service.objects.get(slug='service-blog'))
        if created2:
            member.service_entries.add(s)
            if subdomain_obj:
                subdomain_obj.members.add(member)

def _update_socialgraph(member, url='', loose=False):
    if not url:
        url = member.site_url
    try:
        resp = urllib2.urlopen("http://socialgraph.apis.google.com/lookup?q=%s&fme=1&edi=1&edo=1" % url)
        json_decoder = json.JSONDecoder()
        json_obj = json_decoder.decode(resp.read())
        url_dict = {'toplevel_nodes' : json_obj['nodes'].keys()}
        for subnode in json_obj['nodes'].values():
            #For each toplevel site object
            for key in subnode.keys():
                for site in subnode[key]:
                    if key in url_dict.keys():
                        url_dict[key].append(site)
                    else:
                        url_dict[key] = [site]
        urls_to_check = url_dict['toplevel_nodes']
        urls_to_check.extend(url_dict.get('claimed_nodes', []))
        if loose:
            urls_to_check.extend(url_dict.get('unverified_claiming_nodes', []))
        return _update_services_from_urls(member, urls_to_check)
    except:
        #http error.
        return ''

def _update_services_from_urls(member, urls, trusted=False):
    """Recives an iterable of urls to update a user for"""
    if not urls:
        return ''
    services = Service.objects.all()
    matched_urls = []
    for service in services:
        if service.user_template:
            myre = re.compile(service.user_template % '(\w+)')
            for site in urls:
                match_claimed = re.search(myre, site)
                if match_claimed and site not in matched_urls:
                    matched_urls.append(site)
                    profileurl = match_claimed.group(0)
                    username = match_claimed.group(1)
                    feedurl = ''
                    if service.userfeed_template:
                        feedurl = service.userfeed_template % username
                    try:
                        s, created = ServiceEntry.objects.get_or_create(profile_url=profileurl, username=username, service=service, feed_url=feedurl)
                        if created:
                            member.service_entries.add(s)
                    except Exception, e:
                        print "DB ERROR: %s" % e
                    #Only 1 per service
                    break
    if matched_urls:
        member.save()
        print "%s (SG) owns: %s" % (member.slug, ' '.join(matched_urls))
        return matched_urls

#This updates from Django people
def _update_django_people(mems = []):
    if not mems:
        mems = Member.objects.exclude(people='')
    for user in mems:
        try:
            matched_urls = []
            resp = urllib2.urlopen('http://djangopeople.net/%s/' % user.people)
            soup = bs.BeautifulSoup(resp.read())
            for li in soup.find('div', {'class':'finding'}).ul.findAll('li'):
                href = li.a['href']
                for site_re in PROVIDER_REGEX.keys():
                    myre = re.compile(site_re % '(\w+)')
                    match = re.search(myre, href)
                    if match:
                        setattr(user, PROVIDER_REGEX[site_re], match.group(2))
                        matched_urls.append(match.group(0))
            if matched_urls:
                user.save()
                try:
                    print "%s (DP) owns: %s" % (user.name, ' '.join(matched_urls))
                except Exception, e:
                    print e
        except:
            pass

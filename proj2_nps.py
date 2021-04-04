#################################
##### Name: Sasha Kenkre    #####
##### Uniqname: skenkre     #####
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key


CACHE_FILENAME = "nps_cache.json"
CACHE_DICT = {}

BASEURL = "https://www.nps.gov"

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def make_request_with_cache(baseurl):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    CACHE_DICT = open_cache()

    if baseurl in CACHE_DICT.keys():
        print("Using cache")
        return CACHE_DICT[baseurl]

    else:
        print("Fetching")
        CACHE_DICT[baseurl] = requests.get(baseurl).text
        save_cache(CACHE_DICT)
        return CACHE_DICT[baseurl]

def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs

    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''

    response = requests.get(baseurl, params=params)
    return response.json()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_dict = {}
    extension = "/index.htm"

    html = make_request_with_cache(BASEURL+extension)
    soup = BeautifulSoup(html, 'html.parser')
    search_ul = soup.find('ul', class_ ="dropdown-menu SearchBar-keywordSearch")
    links_list = search_ul.find_all('a')
    for link in links_list:
        state_url = link.get('href')
        url = BASEURL+state_url
        state = link.string.lower()
        state_dict[state] = url
    return state_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    html = make_request_with_cache(site_url)
    soup = BeautifulSoup(html, 'html.parser')

    header = soup.find(class_='Hero-titleContainer clearfix')
    footer = soup.find(class_='vcard')

    #category
    try:
        category = header.find(class_='Hero-designation').text.strip()
    except:
        category = "No category"
    
    name = header.find(class_='Hero-title').text.strip()
    address = footer.find(itemprop='addressLocality').text + ', ' + footer.find(itemprop='addressRegion').text
    zipcode = footer.find(class_='postal-code').text.strip()
    phone = footer.find(class_='tel').text.strip()

    return NationalSite(category=category, name=name, address=address, zipcode=zipcode, phone=phone)


#PART 3
def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    national_site_list = []

    response = make_request_with_cache(state_url)
    soup = BeautifulSoup(response, 'html.parser')

    parks = soup.find(id="list_parks").find_all('h3')
    # print(parks)

    for park in parks:
        park_a = park.find('a')
        park_href = park_a.get('href')
        park_url = BASEURL+park_href+'index.htm'
        # print(park_url)
        national_site_list.append(get_site_instance(park_url))

    return national_site_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    url = 'http://www.mapquestapi.com/search/v2/radius'
    params = {
        'key': secrets.API_KEY,
        'origin': site_object.zipcode,
        'radius': 10,
        'maxMatches': 10,
        'ambiguities': 'ignore',
        'outFormat': 'json',
    }

    unique_key = site_object.zipcode
    if unique_key in CACHE_DICT.keys():
        print("Using Cache")
        return CACHE_DICT[unique_key]

    else:
        print("Fetching")
        CACHE_DICT[unique_key] = make_request(url, params=params)
        save_cache(CACHE_DICT)
        return CACHE_DICT[unique_key]



if __name__ == "__main__":
    state_dict = build_state_url_dict()

    while True:
        state = input(f'\nEnter a U.S. state name (e.g. Michigan, michigan) or "exit": ')
        if state.lower() == 'exit':
            break
        elif state.lower() not in state_dict.keys():
            print(f"\n[ERROR] Enter a proper U.S. state name.")
            continue
        else:
            url = state_dict[state.lower()]
            sites_dict = get_sites_for_state(url)
            header = f"List of National Sites in {state.capitalize()}"
            print('-' * len(header))
            print(header)
            print('-' * len(header))
            for i,site in enumerate(sites_dict):
                print(f'[{i+1}] {site.info()}')

            while True:
                num = input('\nChoose a number from the list for a more detailed search, or enter "exit" to exit, or enter "back" to search another state: ')
                if num.lower() == 'exit':
                    quit()
                elif num.lower() == 'back':
                    break
                elif num.isnumeric() and int(num) >= 1 and int(num) <= len(sites_dict):
                    place = sites_dict[int(num)-1]
                    result = get_nearby_places(place)['searchResults']
                    header = f"Places near {place.name}"
                    print('-' * len(header))
                    print(header)
                    print('-' * len(header))

                    for info in result:
                        name = info['name']
                        field = info['fields']
                        if field['group_sic_code_name'] != '':
                            category = field['group_sic_code_name']
                        else:
                            category = 'no category'
                        if field['address'] != '':
                            address = field['address']
                        else:
                            address = 'no address'
                        if field['city'] != '':
                            city = field['city']
                        else:
                            city = 'no city'

                        print(f"- {name} ({category}): {address}, {city}")
                else:
                    print(f"\n[ERROR] Invalid input. Please enter a valid integer. ")
    save_cache(CACHE_DICT)
import csv
import urllib.request
from bs4 import BeautifulSoup
import amazon_entry


def yn_entry_scrape(dict, url):
    yn_html = urllib.request.urlopen(url)
    yn_soup = BeautifulSoup(yn_html, 'html.parser')

    # to view elements
    # import sys
    # sys.stdout = open('log.txt', 'w')
    # print yn_soup.prettify()
    return dict


def yn_entry_obtain_amzn(url):
    yn_html = urllib.request.urlopen(url)
    yn_soup = BeautifulSoup(yn_html, 'html.parser')

    # basic format entails that the first button is amazon?
    available_seller = ''
    amzn_url = None
    url_cluster = yn_soup.find('div', class_='syoseki-page3')
    if url_cluster:
        first_url = url_cluster.find('a')
        if first_url:
            amzn_url = first_url.get('href')
    return amzn_url


# Test Bench
if __name__ == '__main__':
    yn_entry_url = 'https://yurinavi.com/2023/05/09/koekano-11/' # example url
    # for no amzn link: http://yurinavi.com/2023/08/29/succubus-yuri-1/
    # odd specifications: http://yurinavi.com/2023/08/17/futagoshimaichanno-1/

    # initialize csv file
    csv_filename = 'yurinavientry.csv'

    # fieldname specifications (changes copy and pastable)
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['title', 'error', 'authors', 'volume',
                  'released', 'publisher', 'label', 'serialization',
                  'length', 'link', 'iskindle', 'ranking', 'rating',
                  'reviews', 'description']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    # initialize relevant variables:
    title = None
    error = None
    authors = None
    volume = None
    released = None
    publisher = None
    label = None
    serialization = None
    link = None
    length = None
    iskindle = None
    ranking = None
    rating = None
    reviews = None
    description = None

    # dictionary keys that are being written
    entry_dict = {
        'title': title,
        'error': error,
        'authors': authors,
        'volume': volume,
        'released': released,
        'publisher': publisher,
        'label': label,
        'serialization': serialization,
        'link': link,
        'length': length,
        'iskindle': iskindle,
        'ranking': ranking,
        'rating': rating,
        'reviews': reviews,
        'description': description
    }

    # insert entry into dictionary: switch tests whether to scrape entry on yn page or amazon
    switch_amazontest = True
    if switch_amazontest:
        amazon_url = yn_entry_obtain_amzn(yn_entry_url)
        entry_dict = amazon_entry.scrape(entry_dict, amazon_url)
    else:
        entry_dict = yn_entry_scrape(entry_dict, yn_entry_url)
    csv_writer.writerow(entry_dict)
    print(f'{entry_dict}\n')

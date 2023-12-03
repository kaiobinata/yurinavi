import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv
import re


def category_scrape(base_url, csv_filename):
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['title', 'link']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    url_next_page = base_url
    while url_next_page is not None:
        url_curr = url_next_page

        # # parses the current page:
        # html_curr = urllib.request.urlopen(url_curr)
        # soup_curr = BeautifulSoup(html_curr, 'html.parser')
        soup_curr = simple_soup(url_curr)

        # initialize a dictionary that defaults to listing entries as errors
        entry_dict = {'title': 'error', 'link': 'error'}

        # a more complex system that also obtains links
        iter_products = soup_curr.find_all('li', class_="product")  # "type-product" may also work
        for elem_product in iter_products:
            anchor = elem_product.find('a', class_='woocommerce-LoopProduct-link')  # OR woocommerce-loop-product__link
            if anchor:
                url_product = anchor.get('href')
                entry_dict['link'] = url_product
            elem_title = elem_product.find('h2', class_='woocommerce-loop-product__title')
            if elem_title:
                entry_dict['title'] = elem_title.string
            csv_writer.writerow(entry_dict)
            print(f'{entry_dict}\n')

        url_next_page = next_page(soup_curr)


def simple_soup(url):
    custom_headers = {
        'authority': 'fls-fe.amazon.co.jp',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/search/',
        'accept': '*/*',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'en-US,en;q=0.9',
    }
    response = requests.get(url, headers=custom_headers)
    if response.status_code == 503:
        print("simple_soup() | error likely anti-bot blocking (?)")
        return None
    elif response.status_code != 200:
        print("simple_soup() | url invalid; return None (!soup)")
        return None
    else:
        html_response = response.text
        soup_response = BeautifulSoup(html_response, 'html.parser')
        return soup_response


def next_page(soup):
    pages = soup.find('ul', class_='page-numbers')
    assert pages # a page without page_numbers is strange!
    el_next_page = pages.find('a', class_='next')
    if el_next_page:
        url_next = el_next_page.get('href')
        return url_next
    else:
        return None


def volume_clean(csv_filename):
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['title', 'volume', 'link']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    org_data = pd.read_csv('okazu_eng.csv')
    df = org_data.copy()
    df.set_index('title')

    for index, row in df.iterrows():
        title = row['title']    # or = index
        link = row['link']

        dict_eng = eng_parse_volume(title)
        dict_eng['link'] = link
        print(dict_eng)
        csv_writer.writerow(dict_eng)


def eng_parse_volume(string):
    match1 = re.match(r'(?P<title>.+), Volume (?P<vol>\d+)', string)
    match2 = re.match(r'(?P<title>.+), Vol. (?P<vol>\d+)', string)
    match1a = re.match(r'(?P<title>.+) Volume (?P<vol>\d+)', string)
    match2a = re.match(r'(?P<title>.+) Vol. (?P<vol>\d+)', string)
    match3 = re.search(r'(?P<vol>\d+)', string)
    if match1:
        return {'title': match1.group('title'), 'volume': match1.group('vol')}
    elif match2:
        return {'title': match2.group('title'), 'volume': match2.group('vol')}
    elif match1a:
        return {'title': match1a.group('title'), 'volume': match1a.group('vol')}
    elif match2a:
        return {'title': match2a.group('title'), 'volume': match2a.group('vol')}
    elif match3:
        return {'title': string, 'volume': match3.group('vol')}
    else:
        return {'title': string, 'volume': None}


def jpn_split_volume(csv_filename):
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['romanized title', 'japanese title', 'volume', 'link']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    org_data = pd.read_csv('okazu_jpn.csv')
    df = org_data.copy()
    df.set_index('title')

    for index, row in df.iterrows():
        title_string = row['title']    # or = index
        link = row['link']

        ser_titles = re.split(' / ', title_string)
        if len(ser_titles) == 2:
            rom_title = ser_titles[0]
            jpn_title = ser_titles[1]
        else:
            ser_titles = re.split('/ ', title_string)
            if len(ser_titles) == 2:
                rom_title = ser_titles[0]
                jpn_title = ser_titles[1]
            else:
                ser_titles = re.split(' /', title_string)
                if len(ser_titles) == 2:
                    rom_title = ser_titles[0]
                    jpn_title = ser_titles[1]
                else:
                    rom_title = title_string
                    jpn_title = None

        dict_parsed = eng_parse_volume(rom_title)

        dict_new = {
            'romanized title': dict_parsed.get('title'),
            'japanese title': jpn_title,
            'volume': dict_parsed.get('volume'),
            'link': link
        }

        print(dict_new)
        csv_writer.writerow(dict_new)


# main function
if __name__ == '__main__':
    # a program for obtaining the csv by webscraping the given okazu website
    # # okazu_url = 'https://www.yuricon.com/product-category/jpn-manga/'
    # okazu_url = 'https://www.yuricon.com/product-category/english-manga/'
    # # okazu_url = 'https://www.yuricon.com/product-category/novels/'
    # category_scrape(okazu_url, 'okazu.csv')

    # # a program for cleaning the obtained csv into individual titles and volumes
    # volume_clean('okazu_eng_cleaned.csv')

    # a program for cleaning the obtained jpn csv into Japanese and Romanized titles:
    jpn_split_volume('okazu_jpn_cleaned.csv')
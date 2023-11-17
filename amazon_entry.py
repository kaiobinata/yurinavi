import time
import sys
import logging
import csv
import re
import urllib.request
import requests
from bs4 import BeautifulSoup
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
# replaced per seleniumwire: from selenium import webdriver
from seleniumwire import webdriver  # seleniumwire allows selenium requests w/ headers
from selenium.webdriver.chrome.options import Options
import yurinavi_monthly


def scrape(dic, url):
    # switch between packages (creatively bypass automated access to Amazon)
    request_type = 'requests'   # 'urllib.request' or 'requests'
    amzn_soup = simple_soup(request_type, url)
    if amzn_soup is None:
        dic.update(error='URL invalid')
        return dic

    print(f'***** Current Entry ***** \nURL: {url}')

    # parse status of the current page: [is the page a Kindle/Physical entry?] else [is URL valid?]
    tmm_swatches = amzn_soup.find(id="tmmSwatches")  # looks for format information
    if tmm_swatches:
        selected = tmm_swatches.find('li', class_="selected")
        if selected:
            selected_string = selected.get_text()
            # if 'selected' is in the 'Kindle版' format
            if re.search('Kindle', selected_string):
                print(f'isKindle: {True}')
                dic.update(iskindle='Kindle版')
            # if 'selected' is not a 'Kindle版' format
            else:
                unselected = tmm_swatches.find('li', class_="unselected")
                if unselected:
                    unselected_string = unselected.get_text()
                    # if there exists an 'unselected' format, and it is 'Kindle版'
                    if re.search('Kindle', unselected_string):
                        kindle_button = unselected.find('a', class_="a-button-text")
                        kindle_url = 'https://www.amazon.co.jp' + kindle_button.get('href')
                        url = kindle_url
                        print(f'redirected: {url}')
                        dic.update(iskindle='Kindle版 (Convert)')
                    # if there exists an 'unselected' format, but it is not 'Kindle版'
                    else:
                        format_cluster = selected.get_text()
                        format_curr = re.match(r'\s*(?P<format_curr>\S+)\s+', format_cluster)
                        if format_curr:
                            format_curr = format_curr.group('format_curr')
                        print(f'format_curr: {format_curr}')
                        dic.update(iskindle=format_curr)    # if there is no match, format is None
                # if there does not exist an 'unselected' format
                else:
                    format_cluster = selected.get_text()
                    format_curr = re.match(r'\s*(?P<format_curr>\S+)\s+', format_cluster)
                    if format_curr:
                        format_curr = format_curr.group('format_curr')
                    print(f'format_curr: {format_curr}')
                    dic.update(iskindle=format_curr)  # if there is no match, format is None
    else:
        page_not_found = amzn_soup.find('a', href="/ref=cs_404_link")
        age_verification = amzn_soup.find('p', id="black-curtain-verification")
        if page_not_found:
            dic.update(error="404 Page not Found")
            return dic
        elif age_verification:
            dic.update(error="Age verification")
            # # assumes if age_verification element exists, so does verification button
            # verification_button = age_verification.find(id='black-curtain-yes-button')
            # verification_href = verification_button.find('a').get('href')
            # verified_url = url + verification_href
            # dic = scrape(dic, verified_url)
            return dic
        else:
            dic.update(error="Unknown URL Error")
            return dic

    # initialize finalized dictionary
    final_dict = dic

    switch_soup = 'selenium'
    if switch_soup == 'selenium':
        amzn_soup = selenium_soup(url)
        final_dict = amazon_selenium_scrape(dic, amzn_soup)
    elif switch_soup == 'simple':
        amzn_soup = simple_soup(request_type, url)
        final_dict = amazon_simple_scrape(dic, amzn_soup)

    # to view entire soup:
    # import sys
    # org_stdout = sys.stdout
    # file = open('log.txt', 'w')
    # sys.stdout = file
    # print amzn_soup.prettify()
    # sys.stdout = org_stdout
    # file.close()
    # print "Now this prints to the screen again!"

    return final_dict


def selenium_soup(url):
    switch_head = 'headless'
    if switch_head == 'headless':
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument("--disable-extensions")
        driver = webdriver.Chrome(options=options)
    elif switch_head == 'head visible':
        # edited version of: https://stackoverflow.com/questions/15645093/setting-request-headers-in-selenium
        # All requests will use 'some_referer' for the referer

        # Create a new instance of the Chrome driver (or Firefox)
        driver = webdriver.Chrome()

        # Create a request interceptor
        def interceptor(request):
            del request.headers['Referer']  # Delete the header first
            request.headers['Referer'] = 'https://yurinavi.com/'

        # Set the interceptor on the driver
        driver.request_interceptor = interceptor
    driver.get(url)
    page = driver.page_source

    # Prevent anti-bot blocking from amazon, clicks mouse:
    # https://www.selenium.dev/documentation/webdriver/actions_api/mouse/
    try:
        sample = driver.find_element(By.ID, "ebooksReadSampleButton-announce")
        ActionChains(driver) \
            .click(sample) \
            .perform()
    except NoSuchElementException:
        pass

    driver.quit()
    sel_soup = BeautifulSoup(page, 'html.parser')
    return sel_soup
# obtains a more robust html given a dynamic data-loading page (i.e. amazon)


def simple_soup(req_type, url):
    if req_type == 'requests':
        custom_headers = {
            'authority': 'fls-fe.amazon.co.jp',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'referer': 'https://yurinavi.com/',
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
            amzn_html = response.text
            amzn_soup = BeautifulSoup(amzn_html, 'html.parser')
            return amzn_soup
    elif req_type == 'urllib.request':
        amzn_html = urllib.request.urlopen(url)
        amzn_soup = BeautifulSoup(amzn_html, 'html.parser')
        return amzn_soup
    else:
        print("simple_soup() | req_type invalid; return None (!soup)")
        return None
# obtains a simpler html that assumes a page is static (i.e. yurinavi)


def amazon_selenium_scrape(diction, soup):
    # elements pertaining to carousel
    carousel = soup.find(id="rich_product_information")
    if carousel is None:    # assert that page has a carousel
        diction.update(error="selenium_scrape() | no carousel")
        return diction

    # title and volume
    series_check = carousel.find('div', id="rpi-attribute-book_details-series")
    if series_check:
        title_check = series_check.find('div', class_="rpi-attribute-value")
        volume_check = series_check.find('div', class_="rpi-attribute-label")
        if title_check:
            # tit_string_method = str(title_check.find('span').string).lstrip()
            tit = str(title_check.get_text()).lstrip()
            diction.update(title=tit)
            print(f"tit: {tit}")
        if volume_check:
            vol = str(volume_check.get_text()).lstrip()
            diction.update(volume=vol)
            print(f"vol: {vol}")
    else:
        tit_last_resort = soup.find('h1', id="title")
        tit_last_resort = tit_last_resort.find('span', id="productTitle")
        tit = str(tit_last_resort.string)
        diction.update(title=tit)
        print(f"tit_last_resort: {tit}")
        vol_last_resort = yurinavi_monthly.parse_volume(tit)
        vol = vol_last_resort
        diction.update(volume=vol)
        print(f"vol_last_resort: {vol}")

    # publisher
    pub_check = carousel.find('div', id="rpi-attribute-book_details-publisher")
    if pub_check:
        attr_label = pub_check.find('div', class_="rpi-attribute-label")
        attr_pub = pub_check.find('div', class_="rpi-attribute-value")
        if re.search("(出版社)|(Publisher)", str(attr_label.get_text())):
            pub = str(attr_pub.get_text()).lstrip()
            print(f"pub: {pub}")
            diction.update(publisher=pub)
        else:
            diction.update(publisher="ERROR")

    # release date
    rel_check = carousel.find('div', id="rpi-attribute-book_details-publication_date")
    if rel_check:
        attr_label = rel_check.find('div', class_="rpi-attribute-label")
        attr_rel = rel_check.find('div', class_="rpi-attribute-value")
        if attr_label and attr_rel:
            if re.search("(発売日)|(Publication date)", str(attr_label.get_text())):
                rel = str(attr_rel.get_text())
                # reformat from yyyy/m/d into yyyy-mm-dd
                # match may work ONLY if (white)space at front of rel is removed
                rel = reformat_date(rel)
                rel_comparison = (rel == diction['released'])
                print(f"rel: {rel}")
                print(f"rel_comparison: {rel_comparison}")
                diction.update(released=rel)
            else:
                diction.update(released="ERROR")

    # page length
    len_check = carousel.find('div', id="rpi-attribute-book_details-ebook_pages")
    if len_check:
        attr_label = len_check.find('div', class_="rpi-attribute-label")
        attr_len = len_check.find('div', class_="rpi-attribute-value")
        if re.search("(本の長さ)|(Print length)", str(attr_label.get_text())):
            leng = str(attr_len.get_text()).lstrip()
            print(f"leng: {leng}")
            diction.update(length=leng)
        else:
            diction.update(length="ERROR")

    # author element
    div_authorlist = soup.find('div', id="bylineInfo_feature_div")
    if div_authorlist:
        author_list = div_authorlist.find_all('span', class_="author")
        if author_list:
            # switch between a list or a concatenated single string (&&)
            switch_list_type = 'list'
            if switch_list_type == 'list':
                # List Comprehensions implemented
                aut = [author.find('a').string for author in author_list]
                print(f"aut: {aut}")
                diction.update(authors=aut)
            elif switch_list_type == 'concat':
                aut = ''
                for author in author_list:
                    author_link = author.find('a')
                    aut = str(aut) + " && " + str(author_link.string)
                aut = re.sub(' && ', '', aut, 1)
                print(f"aut: {aut}")
                diction.update(authors=aut)
        else:
            diction.update(authors="ERROR")

    # ratings
    div_ratings = soup.find('div', id="detailBullets_averageCustomerReviews")
    if div_ratings:
        ratings_average = div_ratings.find('span', id="acrPopover")
        ratings_submissions = div_ratings.find('span', id="acrCustomerReviewText")
        if ratings_average and ratings_submissions:
            ratings_average = str(ratings_average['title'])
            ratings_average = re.sub('(5つ星のうち)|( out of 5 stars)', '', ratings_average)
            ratings_submissions = str(ratings_submissions.string)
            ratings_submissions = re.sub('(個の評価)|( ratings)', '', ratings_submissions)
            ratings_submissions = re.sub(',', '', ratings_submissions)  # removes commas from values
            rat = [ratings_average, ratings_submissions]
            print(f"rat: {rat}")
            diction.update(rating=rat)

    # description element
    div_description = soup.find('div', id="bookDescription_feature_div")
    if div_description:
        des = str(div_description.get_text()).lstrip()
        # consider errors that may arise from when a description contains a comma
        des = re.sub(',', '、', des)
        des = re.sub(r'(  続きを読む)|(Read more)', '', des)
        print(f"des: {des}")
        diction.update(description=des)
    else:
        diction.update(description="ERROR")

    # returns updated dictionary
    return diction


def amazon_simple_scrape(diction, soup):
    diction.update(error='simple_scrape() | work in progress')
    return diction


def reformat_date(date_string):
    jpn = re.search(r"(?P<year>\d+)/(?P<month>\d+)/(?P<date>\d+)", date_string)
    eng = re.search(r"(?P<month>\w+) (?P<date>\d+), (?P<year>\d+)", date_string)
    if jpn:
        ymd = jpn
        yyyy_mm_dd = f"{ymd.group('year')}-{ymd.group('month').zfill(2)}-{ymd.group('date').zfill(2)}"
        return yyyy_mm_dd
    elif eng:
        month = eng.group('month')
        match month:
            case 'January':
                month = '1'
            case 'February':
                month = '2'
            case 'March':
                month = '3'
            case 'April':
                month = '4'
            case 'May':
                month = '5'
            case 'June':
                month = '6'
            case 'July':
                month = '7'
            case 'August':
                month = '8'
            case 'September':
                month = '9'
            case 'October':
                month = '10'
            case 'November':
                month = '11'
            case 'December':
                month = '12'
            case _:
                month = '0'
        yyyy_mm_dd = f"{eng.group('year')}-{month.zfill(2)}-{eng.group('date').zfill(2)}"
        return yyyy_mm_dd
    else:
        return 'reformat_date() | unrecognizable date format'


# Test Bench
if __name__ == '__main__':
    # # Set up logging
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    # # Debugging example
    # logging.debug(f"Dividing {a} by {b}")
    # result = a / b
    # logging.debug(f"Result: {result}")

    amazon_url = 'https://www.amazon.co.jp/マザーグール-1-(-リュウコミックス-菅原キク/dp/B01N4WXWDK/'
    # https://www.amazon.co.jp/マザーグール-1-(-リュウコミックス-菅原キク/dp/B01N4WXWDK/
    # for no kindle: https://www.amazon.co.jp/gp/product/B00MNM36PY
    # for not kindle2 (old): https://www.amazon.co.jp/gp/product/B000J8PYR2/
    # for long description: https://www.amazon.co.jp/コミック百合姫2023年12月号-百合姫編集部/dp/B0CHBCWPTK/
    # for multiple authors:
    # https://www.amazon.co.jp/シロップ-PURE-おねロリ百合アンソロジー-アクションコミックス-月刊アクション)/dp/B08B5SGBNY/
    # for english:
    # https://www.amazon.co.jp/シロップ-PURE-おねロリ百合アンソロジー-アクションコミックス-月刊アクション)/dp/4575854816/
    # for 18+ content:
    # https://amzn.to/45EFaeS

    # initialize csv file
    csv_filename = 'amazon.csv'
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['title', 'error', 'authors', 'volume',
                  'released', 'publisher', 'label', 'serialization',
                  'length', 'link', 'iskindle', 'ranking', 'rating',
                  'reviews', 'description']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    # initialize relevant variables to blank
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

    # initialize blank dictionary
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

    entry_dict = scrape(entry_dict, amazon_url)
    csv_writer.writerow(entry_dict)
    print(f'{entry_dict}\n')

    # # temp: troubleshooting
    # t0 = time.time()
    # # temp: troubleshooting
    # t1 = time.time()
    # print(f'time elapsed: {t1 - t0}')
    # print(supersoup.prettify())
    # breakpoint()

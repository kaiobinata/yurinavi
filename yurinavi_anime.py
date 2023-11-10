from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
# import openpyxl as xl
import csv


def title_author_test(driver):
    elem_json = driver.find_element(By.ID, 'post-50785')
    print(f'elem_json.id: {elem_json.id}')
    print(f'elem_json.text: {elem_json.text}')

    # obtains list of title n\ author pair
    elem_json = driver.find_elements(By.CLASS_NAME, 'entry-header')
    for entry in elem_json:
        print(f'{entry.id}: \n {entry.text}')
        # link = entry.find_element(By.PARTIAL_LINK_TEXT)
        # print(f'link: {link}')


def csv_basic(driver, writer):
    elem_json = driver.find_elements(By.CLASS_NAME, 'hentry')
    for entry in elem_json:
        entry_list = entry.text.split('\n', 3)

        title = entry_list[0]
        author_list = entry_list[1]
        category_list = entry_list[2]
        authors = entry_list[1].split(' / ')
        categories = entry_list[2].split(' / ')

        print(f'title: {title}')
        print(f'authors: {authors}')
        print(f'categories: {categories}')

        entry_dict = {
            "title": title,
            "authors": author_list,
            "categories": category_list
        }
        print(entry_dict)
        # print(entry_dict.keys())
        writer.writerow(entry_dict)


def navi_singularentry(driver, writer):
    xyz = 'placeholder'
    return xyz


def csv_secondary(driver, writer):
    json_list = driver.find_elements(By.CLASS_NAME, 'type-post')
    for entry in json_list:
        entry_text = entry.text.split('\n', 3)

        title = entry_text[0]
        author_list = entry_text[1]
        category_list = entry_text[2]
        authors = entry_text[1].split(' / ')
        categories = entry_text[2].split(' / ')

        print(f'title: {title}')
        print(f'authors: {authors}')
        print(f'categories: {categories}')

        # does not work because reloading page changes elements (ID?)
        # navi_link = entry.find_element(By.PARTIAL_LINK_TEXT, '')
        # navi_link.click()
        # current_url = driver.current_url
        # print(f'link: {current_url}')
        # driver.back()

        navi_link = entry.find_element(By.PARTIAL_LINK_TEXT, '')
        dive_url = navi_link.get_attribute('href')  # obtains url

        # Open a new window (prevents disturbing elements cache (?))
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(dive_url)
        print(f'link: {driver.current_url}')

        author_volumes_raw = driver.find_element(By.CLASS_NAME, 'syoseki-page1')
        author_volumes_raw = author_volumes_raw.text
        isfinished = None  # Default Error Value
        if author_volumes_raw.count('完結') == 1:
            isfinished = True
        else:
            if author_volumes_raw.count('連載中') == 1:
                isfinished = False
            if author_volumes_raw.count('刊行中') == 1:
                isfinished = '刊行中'
            if author_volumes_raw.count('既刊') == 1:
                isfinished = '既刊'
            if author_volumes_raw.count('休載中') == 1:
                isfinished = '休載中'
        print(f'isfinished: {isfinished}')
        # strip away all but: 全8巻(完結)
        volumes_raw = author_volumes_raw.split(' ')
        volumes = volumes_raw[-1]
        # safety code because yagakimi entry is screwed up (has some invisible text)
        if volumes.count('\u3000') > 0:
            volumes = volumes.split('\u3000')[-1]
        volumes = (volumes.split('巻'))[0]
        volumes = volumes.replace('全', '')
        volumes = volumes.replace('既刊', '')
        if not volumes.isdigit():
            volumes = None

        # assert volumes[volumes].isdigit()
        print(f'volumes: {volumes}')
        # lorem_ipsum = author_volumes_raw.get_attribute('style')

        tags_description_raw = driver.find_element(By.CLASS_NAME, 'syoseki-page2')
        tags_description = tags_description_raw.text
        print(f'tags_description: {tags_description}')
        # works: = driver.find_element(By.CSS_SELECTOR, 'div[class="syoseki-page2"]')
        description = None
        try:
            description = tags_description_raw.find_element(By.CSS_SELECTOR, 'p[style="line-height: 1.2em;"]')
        except NoSuchElementException:
            print('inconsistent font style (not 1.2em) for description: check specific example')
        try:
            description = tags_description_raw.find_element(By.CSS_SELECTOR, 'p[style="line-height: 1.1em;"]')
        except NoSuchElementException:
            print('inconsistent font style (not 1.1em) for description: check specific example')
        description = description.text
        print(f'description: {description}')

        # initialize variables:
        publisher = None
        label = None
        serialized = None
        released = None

        full_content = driver.find_element(By.CLASS_NAME, 'entry-content')
        date_publisher_label_raw = full_content.find_elements(By.CSS_SELECTOR, 'p[style="line-height: 1.2em;"]')
        aggregate = date_publisher_label_raw[-1].text
        aggregate = aggregate.splitlines()  # or split via "<br />"
        print(f'aggregate: {aggregate}')
        for info_line in aggregate:
            if info_line.count('発売日') == 1:
                released = info_line.split('：')[-1]
            if info_line.count('出版社') == 1:
                publisher = info_line.split('出版社：')[-1]
            if info_line.count('発表') == 1:
                serialized = info_line.split('発表：')[-1]
            if info_line.count('掲載誌') == 1:
                serialized = info_line.split('掲載誌：')[-1]
            if info_line.count('レーベル') == 1:
                label = info_line.split('レーベル：')[-1]

        # Closing new_url tab and switching to old tab
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        entry_dict = {
            'title': title,
            'authors': author_list,
            'categories': category_list,
            'publisher': publisher,
            'label': label,
            'serialized': serialized,
            'released': released,
            'volumes': volumes,
            'concluded': isfinished,
            'description': description
        }

        print(f'{entry_dict}\n')
        writer.writerow(entry_dict)


def next_page(driver):
    elem_json = driver.find_elements(By.CLASS_NAME, 'previous')
    for entry in elem_json:
        entry.click()
        linktest1 = driver.current_url
        print(f'linktest1: {linktest1}')
        # driver.back()

        # # alternative method:
        # linktest2 = entry.find_element(By.PARTIAL_LINK_TEXT, 'Next')
        # linktest2.click()
        # print(f'linktest2: {driver.current_url}')


url = 'https://yurinavi.com/?f1&f2&f6&f7&f9%5B0%5D=1&wpcfs=preset-4'
# urlpath = url.split('/')

webdriver = webdriver.Chrome()
webdriver.get(url)
assert 'yurinavi.com' in webdriver.current_url

# title_author_test(webdriver)
csv_filename = 'animeadaptedyurimanga.csv'

csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
fieldnames = ['title', 'authors', 'categories',
              'publisher', 'label', 'serialized', 'released',
              'volumes', 'concluded', 'description']
# fieldnames = ['作品', '著', 'ジャンル',
#               '出版社', 'レーベル', '発表', '発売日'
#               '内容紹介']
# ASIN ‏ : ‎ B08VDBNJXT
# Amazon 売れ筋ランキング: - 8,724位青年マンガ - 40,712位コミック
# カスタマーレビュー: 4.4 5つ星のうち4.4    98個の評価
csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
csv_writer.writeheader()

# csv_basic(webdriver, csv_writer)
# next_page(webdriver)
# csv_basic(webdriver, csv_writer)
# next_page(webdriver)
# csv_basic(webdriver, csv_writer)
# next_page(webdriver)
# csv_basic(webdriver, csv_writer)

csv_secondary(webdriver, csv_writer)
next_page(webdriver)
csv_secondary(webdriver, csv_writer)
next_page(webdriver)
csv_secondary(webdriver, csv_writer)
next_page(webdriver)
csv_secondary(webdriver, csv_writer)

# driver.back()
# driver.forward()

webdriver.quit()

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
import csv
import re


def ynavimonthlypagescrape(driver, writer, elements_list):
    for element in elements_list:
        if element.text.count('年』') > 0:  # edge case upon reaching month links
            break
        elif element.text.count('作品/作者') > 0:  # edge case for fieldnames
            continue
        elif element.text.count('月発売の百合漫画') > 0:  # edge case for fieldnames
            continue
        element = element.find_element(By.CLASS_NAME, 'column-3')
        entry_link = element.find_element(By.PARTIAL_LINK_TEXT, '')
        entry_url = entry_link.get_attribute('href')
        ynavientryscrape(driver, writer, entry_url)


def yurihime_author(author_list, fullstring):
    author_match = re.findall(
        r"(^|／|漫画：|原作：|キャラクターデザイン原案：|作画：|漫画:)([^：／［\u3000]+)(\u3000|［)", fullstring)
    if author_match is not None:
        for author in author_match:
            author_list += ' / ' + author[1]
    return author_list


def ynavientryscrape(driver, writer, url):
    # Open a new window (prevents disturbing elements cache (?))
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[2])
    driver.get(url)
    print(f'current_url: {driver.current_url}')

    # note if you check 2018 entries, they are just links to amazon
    if driver.current_url.find('www.amazon.co.jp') > 0:
        print('THIS IS IT!')

    # initialize relevant variables:
    category_list = ''
    publisher = None
    label = None
    serialized = None
    released = None
    volume = None
    notif = None
    kounin = False

    title_element = driver.find_element(By.CLASS_NAME, 'entry-title')
    title = title_element.text

    # all authors of an entry
    author_list_el = driver.find_element(By.CLASS_NAME, 'syoseki-page1')
    # standard volumes:
    try:
        author_list_el = author_list_el.find_element(By.CLASS_NAME, 'futo')
        author_list = author_list_el.text.replace('著・', '')
    except NoSuchElementException:
        # most plausible reason: magazine volumes
        author_list = '雑誌'
        if re.match('コミック百合姫', title) is not None:
            author_list = ''
    if author_list == 'アンソロジー':
        notif = 'CHECK_ANTHOLOGY'

    # number of volumes
    volume_match = re.match(r"\((?P<volume_integer>\d+)\)", title)
    if volume_match is not None:
        volume = volume_match.group('volume_integer')
    elif re.match('【小説】', title) is not None:
        volume = 1
        notif = 'CHECK_NOVEL'
    # edge case for YuriHime: X年X月号
    volume_match = re.match(r"(\d+年\d+月号)", title)
    if volume_match is not None:
        volume = volume_match.group(0)
    # edge case for Gallete No.XX
    volume_match = re.match(r"No\.(\d+)\Z", title)  # \Z matches at the end of a string
    if volume_match is not None:
        volume = volume_match.group(0)

    genre_list = driver.find_elements(By.CLASS_NAME, 'genre')
    for genre in genre_list:
        category_list += ' / ' + genre.text
    category_list = re.sub(' / ', '', category_list, 1)  # remove the first divisor

    tags_desc_el = driver.find_element(By.CLASS_NAME, 'syoseki-page2')
    print(f'tags_desc_el: {tags_desc_el.text}')
    description = tags_desc_el.text
    # removes all genre.text
    for genre in genre_list:
        description = description.replace(genre.text, '', 1)
    # special case for this identifier (not genre)
    if description.find('百合公認') != -1:
        description = description.replace('百合公認', '', 1)
        kounin = True
    description = description.lstrip()

    full_content = driver.find_element(By.CLASS_NAME, 'entry-content')
    date_publisher_label_raw = full_content.find_elements(By.CSS_SELECTOR, 'p[style="line-height: 1.2em;"]')
    aggregate = date_publisher_label_raw[-1].text
    aggregate = aggregate.splitlines()  # or split via "<br />"
    print(f'aggregate: {aggregate}')
    for info_line in aggregate:
        string_type = info_line.split('：', 1)  # 1 max split prevents splitting entries with ':'
        # special case for yurihime:
        # TEST: one should remove duplicate names (see case '●巻頭カラー':)
        if title.startswith('コミック百合姫'):
            match string_type[0]:
                case '発売日':
                    released = string_type[1]
                case '出版社':
                    publisher = string_type[1]
                case '●表紙':
                    author_list += string_type[1]
                case '●巻頭カラー':
                    # if author_list.search(string_type[1]) is None:
                    author_list = yurihime_author(author_list, string_type[1])
                case '●センターカラー':
                    author_list = yurihime_author(author_list, string_type[1])
                case '●連載作品':
                    author_list = yurihime_author(author_list, string_type[1])
                case '●読切':
                    author_list = yurihime_author(author_list, string_type[1])
                case '●読切作品':
                    author_list = yurihime_author(author_list, string_type[1])
                case '●出張掲載':
                    author_list = yurihime_author(author_list, string_type[1])
                case '●特集':
                    author_match = re.findall(r"「(.+)」", string_type[1])
                    if author_match is not None:
                        for author in author_match:
                            author_list += ' / ' + author
                case '●巻末コラム':
                    author_match = re.findall(r"「(.+)」", string_type[1])
                    if author_match is not None:
                        for author in author_match:
                            author_list += ' / ' + author
                case ' ':
                    pass
                case _:
                    notif = 'CHECK_FOR_ERROR'
        else:
            # standard case (not yurihime)
            match string_type[0]:
                case '発売日':
                    released = string_type[1]
                case '出版社':
                    publisher = string_type[1]
                case '発表':
                    serialized = string_type[1]
                case '掲載誌':
                    serialized = string_type[1]
                case '掲載':
                    serialized = string_type[1]
                case 'レーベル':
                    label = string_type[1]
                case _:
                    notif = 'CHECK_FOR_ERROR'

    # placeholder
    amazon_element = driver.find_element(By.CLASS_NAME, 'syoseki-page3')
    amazon_link = amazon_element.find_element(By.CSS_SELECTOR, 'a[target="_blank"]')
    amazon_url = amazon_link.get_attribute('href')
    print(f'amazon_url: {amazon_url}')

    # amazon_entryscrape call
    amazon_entryscrape(driver, writer, amazon_url)

    # dictionary keys that are being written
    entry_dict = {
        'title': title,
        'authors': author_list,
        'categories': category_list,
        'publisher': publisher,
        'label': label,
        'serialized': serialized,
        'released': released,
        'volume': volume,
        'notification': notif,
        '百合公認': kounin,
        'description': description
    }

    # Closing new_url tab and switching to old tab
    webdriver.close()
    webdriver.switch_to.window(webdriver.window_handles[1])

    print(f'{entry_dict}\n')
    writer.writerow(entry_dict)


def amazon_entryscrape(driver, writer, url):
    # Open a new window (prevents disturbing elements in cache)
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[3])
    driver.get(url)
    print(f'current_url: {driver.current_url}')

    title_element = driver.find_element(By.CLASS_NAME, 'LOREM IPSUM')
    title = title_element.text

    # all authors of an entry
    author_list_el = driver.find_element(By.CLASS_NAME, 'LOREM IMPSUM')
    # standard volumes:
    try:
        author_list_el = author_list_el.find_element(By.CLASS_NAME, 'futo')
        author_list = author_list_el.text.replace('著・', '')
    except NoSuchElementException:
        # most plausible reason: magazine volumes
        author_list = '雑誌'
        if re.match('コミック百合姫', title) is not None:
            author_list = ''
    if author_list == 'アンソロジー':
        notif = 'CHECK_ANTHOLOGY'

    # Closing new_url tab and switching to old tab
    webdriver.close()
    webdriver.switch_to.window(webdriver.window_handles[2])


base_url = 'https://yurinavi.com/yuri-calendar/'
webdriver = webdriver.Chrome()
webdriver.get(base_url)
assert 'yurinavi.com' in webdriver.current_url

csv_filename = 'yurimanga.csv'
csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
fieldnames = ['title', 'authors', 'categories',
              'publisher', 'label', 'serialized', 'released',
              'volume', 'notification', '百合公認', 'description']
csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
csv_writer.writeheader()

# # current test for yurinavi yurihime pages
# webdriver.execute_script("window.open('');")  # making sure the window is at index 2
#
# yurinavi_url = 'http://yurinavi.com/2023/06/14/yurihime-202308/'
# print(yurinavi_url)
# ynavientryscrape(webdriver, csv_writer, yurinavi_url)

# obtain data from all previous months:
month_list = webdriver.find_elements(By.CLASS_NAME, 'kuro-haikei')
for month_box in month_list:
    dive_url = month_box.get_attribute('href')  # obtains url

    # Open a new window (prevents disturbing elements cache (?))
    webdriver.execute_script("window.open('');")
    webdriver.switch_to.window(webdriver.window_handles[1])
    webdriver.get(dive_url)

    # discover all entries on the yurivani monthly page
    elements_list1 = webdriver.find_elements(By.CLASS_NAME, 'odd')
    elements_list2 = webdriver.find_elements(By.CLASS_NAME, 'even')

    # scrape data from the monthly + entry pages
    ynavimonthlypagescrape(webdriver, csv_writer, elements_list1)
    ynavimonthlypagescrape(webdriver, csv_writer, elements_list2)

    # Closing new_url tab and switching to old tab
    webdriver.close()
    webdriver.switch_to.window(webdriver.window_handles[0])

# next obtain recent sales content:
elements_list3 = webdriver.find_elements(By.CLASS_NAME, 'odd')
elements_list4 = webdriver.find_elements(By.CLASS_NAME, 'even')
ynavimonthlypagescrape(webdriver, csv_writer, elements_list3)
ynavimonthlypagescrape(webdriver, csv_writer, elements_list4)

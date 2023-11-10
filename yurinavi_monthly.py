
from bs4 import BeautifulSoup
import urllib.request
import csv
import re


# parse and reformat date string (from the yurinavi monthly calendar)
def reformat_date(ym_string, md_string):
    md = re.match(r"(?P<month>\d+)/(?P<date>\d+)", md_string)
    # month = md.group('month')
    try:
        date = md.group('date')
        ymd_format = ym_string + '-' + date.zfill(2)  # formats into yyyy_mm_dd
        return ymd_format
    except AttributeError:
        # note: 2017-11 entry サタノファニ(3) is the only ERROR entry (“6” instead of “11/6”)
        return "ERROR"


# parse volume number from title string
def parse_volume(title_string):
    # Known or Obvious exceptions: title includes (上) or (中) | note (下) could be 2 or 3
    if re.search(r"\(上\)", title_string):
        return 1
    elif re.search(r"\(中\)", title_string):
        return 2
    elif re.search(r"\(下\)", title_string):
        # return 'parse_volume() | contains (下)'
        return None

    # parses for numbers in the parenthesis format of "(XX)"
    volume_format = re.search(r"\((?P<volume>\d+)\)", title_string)
    # parses for ANY numbers in the title: can give error-ridden volume numbers iff title itself has numbers
    if volume_format is None:
        volume_format = re.search(r"(?P<volume>\d+)", title_string)

    if volume_format:
        vol = volume_format.group('volume')
        # Known or Obvious exceptions: title includes years such as 20XX
        if re.match(r"20\d\d", vol):
            # return 'parse_volume() | contains year'
            vol = None
        # Known or Obvious exceptions: if there are more than 100 volumes (arbitrary maximum)
        elif int(vol) > 100:
            # return 'parse_volume() | parsed number is above 100'
            vol = None
        return vol
    else:
        # return 'parse_volume() | volume unknown'
        return None


# main function
if __name__ == '__main__':
    # base yuri navi calendar url
    base_url = 'https://yurinavi.com/yuri-calendar/'

    # initialize csv file
    csv_filename = 'yurinavimonthly.csv'
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['title', 'authors', 'released',
                  'publisher', 'label', 'serialization',
                  'volume', 'vol error', 'entry link', 'img src']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    # obtain urls of all previous months:
    base_html = urllib.request.urlopen(base_url)
    base_soup = BeautifulSoup(base_html, 'html.parser')
    month_table = base_soup.find(id="tablepress-152-no-2")
    month_anchors = month_table.find_all('a')

    for month in month_anchors:
        month_url = month.get('href')
        monthly_html = urllib.request.urlopen(month_url)
        monthly_soup = BeautifulSoup(monthly_html, 'html.parser')
        table = monthly_soup.find('tbody')
        entry_table = table.find_all('tr')

        # note: date format for CSV is yyyy-mm-dd
        release_counter = ""
        date_match = re.search(r"/yuricale-(\d+)", month_url)
        yearmonth = date_match.group(1)     # (1) returns the first parenthesized subgroup
        yyyy_mm = yearmonth[:4] + '-' + yearmonth[4:]
        yearmonth = int(yearmonth)

        for entry in entry_table:
            # initialize relevant variables:
            title = None
            author_list = None
            released = None
            publisher = None
            label = None
            serialized = None
            volume = None
            vol_err = None
            entry_link = None
            img_src = None

            # column 1 is date in ALL formats
            column1 = entry.find('td', class_="column-1")
            month_date = None
            # due to inconsistencies in table design (see post-2017年7月)
            if yearmonth >= 201706:
                month_date = column1.find('span')
                if month_date:
                    month_date = str((column1.find('span')).string)
                    # due to inconsistencies in table heading (see 2023年3月, 2022年02月, 2017年12月, etc.)
                    if re.search("発売の百合漫画", month_date):  # Match objects have boolean value of True
                        continue
            # due to inconsistencies in table design (see pre-2017年6月)
            elif yearmonth < 201706:
                month_date = str(column1.string)
            if month_date is not None:
                release_counter = reformat_date(yyyy_mm, month_date)
            released = release_counter

            # due to inconsistencies in table design (2017年3月-Present)
            if yearmonth >= 201703:
                # in post-2017年3月 format, column2 is the designated image source:
                column2 = entry.find('td', class_="column-2")
                try:
                    img_anchor = column2.find('a')
                    img_src = img_anchor.get('href')
                except AttributeError:  # entries sometimes don't have an image (see おへその下が、あついんだ 2019年5月)
                    img_src = "ERROR"

                # in post-2017年3月 format, column 3 has both title, entry_link, and author:
                column3 = entry.find('td', class_="column-3")
                # due to inconsistencies in table entry etiquette (see 2017年6月); dates where there were 0 entries
                if column3.string == '予定なし':
                    continue
                # parsing title and link
                entry_anchor = column3.find('a')
                entry_link = entry_anchor.get('href')
                title = str(entry_anchor.string)  # str() converts NavigableString to unicode
                title = re.sub(r'\u3000', ' ', title, 10)  # cleans whitespaces; 10 is arbitrary
                # alternative method for title (unreliable) is {c3_list[0]}
                # parsing volume
                volume_parsed = parse_volume(title)
                volume = volume_parsed[0]
                vol_err = volume_parsed[1]
                # parsing author list
                column3_list = list(column3.stripped_strings)  # converts generator (Iterator) object to list
                if len(column3_list) >= 2:
                    author_list = column3_list[1]
                    author_list = re.sub(r'\u3000', ' ', author_list, 10)  # cleans whitespaces; 10 is arbitrary
                else:
                    author_list = ''

                # in post-2017年3月 format, column 4 has publication info (publisher and label):
                column4 = entry.find('td', class_="column-4")
                pubinfo = list(column4.stripped_strings)  # converts generator (Iterator) object to list
                try:
                    publisher = pubinfo[0]
                except IndexError:  # due to inconsistencies in table design (see 2023年3月)
                    publisher = "ERROR"
                if len(pubinfo) >= 2:
                    label = pubinfo[1]
                # a precise command for parsing for ALL publishers would go here

            # due to inconsistencies in table design (2016年9月-2017年2月)
            elif yearmonth <= 201702:
                # in pre-2017年2月 format, there is no column for image source:
                img_src = None

                # in pre-2017年2月 format, column 2 has only title and entry_link:
                column2 = entry.find('td', class_="column-2")
                entry_anchor = column2.find('a')
                entry_link = entry_anchor.get('href')
                title = str(entry_anchor.string)
                volume_parsed = parse_volume(title)
                volume = volume_parsed[0]
                vol_err = volume_parsed[1]

                # in pre-2017年2月 format, column 3 has author:
                column3 = entry.find('td', class_="column-3")
                author_list = str(column3.string)
                author_list = re.sub(r'\u3000', ' ', author_list, 10)  # cleans whitespaces; 10 is arbitrary

                # in pre-2017年2月 format, publisher and label had their own columns (4 and 5 respectively):
                if yearmonth == 201701:
                    publisher = None
                    label = None
                else:
                    column4 = entry.find('td', class_="column-4")
                    publisher = str(column4.string)

                    column5 = entry.find('td', class_="column-5")
                    label = str(column5.string)

            # dictionary keys that are being written
            entry_dict = {
                'title': title,
                'authors': author_list,
                'released': released,
                'publisher': publisher,
                'label': label,
                'serialization': serialized,
                'volume': volume,
                'vol error': vol_err,
                'entry link': entry_link,
                'img src': img_src
            }

            print(f'{entry_dict}\n')
            csv_writer.writerow(entry_dict)

    # yurivanimonthly_ori = pd.read_csv('yurivanimonthly.csv')
    # ynm_csv = yurivanimonthly_ori.copy()
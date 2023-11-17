from bs4 import BeautifulSoup
import urllib.request
import csv
import re
import pandas as pd
import amazon_entry
import yurinavi_entry


def isamazon(link):
    return re.search('https://www.amazon.co.jp/', link) or re.search('https://amzn.to/', link)


# Test Bench
if __name__ == '__main__':
    yurinavi_monthly = pd.read_csv('yurinavimonthly_uncleaned.csv')
    df = yurinavi_monthly.copy()

    # initialize csv file
    csv_filename = 'yn_full.csv'
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['title', 'error', 'authors', 'volume',
                  'released', 'publisher', 'label', 'serialization',
                  'length', 'link', 'iskindle', 'ranking', 'rating',
                  'reviews', 'description']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    df = df.get(['title', 'released', 'entry link'])
    # basic functions for visualizing dataframes
    # print(f'head: \n{df.head(3)}')
    # print(f'tail: \n{df.tail(3)}')
    # print(f'desc: \n{df.describe()}')

    # iterates the rows of the df
    i = 0
    df_length = len(df.index)
    while i < df_length:
        initial_title = df.iloc[i, 0]
        initial_date = df.iloc[i, 1]
        entry_link = df.iloc[i, 2]
        i = i + 1

        # initialize relevant variables:
        title = initial_title
        error = None
        authors = None
        volume = None
        released = initial_date
        publisher = None
        label = None
        serialization = None
        link = entry_link
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

        is_amazon = isamazon(entry_link)
        is_yurinavi = re.search('http://yurinavi.com/', entry_link)
        if is_amazon:
            entry_dict = amazon_entry.scrape(entry_dict, entry_link)
        elif is_yurinavi:
            amazon_url = yurinavi_entry.yn_entry_obtain_amzn(entry_link)
            if amazon_url is not None:
                if isamazon(amazon_url):
                    entry_dict = amazon_entry.scrape(entry_dict, amazon_url)
            else:
                entry_dict = yurinavi_entry.yn_entry_scrape(entry_dict, entry_link)
        csv_writer.writerow(entry_dict)
        print(f'{entry_dict}\n')

    # After learning from experienced Python developers, I now prioritize performance optimization.
    # I leverage techniques like vectorization, caching, and algorithmic improvements to enhance
    # the speed and efficiency of my code.
    # For example, when working with Pandas DataFrames, I make use of vectorized operations instead
    # of iterating over rows or columns, which can be significantly slower.
    # # Example of vectorized operation using Pandas (df in this case)
    # data['new_column'] = data['existing_column'] * 2
    # # Applying a function to each row
    # df['new_column'] = df['existing_column'].apply(lambda x: x * 2)

# chrome workspace:
# https://yurinavi.com/
# https://www.mangaupdates.com/search.html?search=%E3%82%84%E3%81%8C%E3%81%A6%E5%90%9B%E3%81%AB%E3%81%AA%E3%82%8B%283%29
# https://chat.openai.com/auth/login?next=%2F%3Fmodel%3Dtext-davinci-002-render-sha

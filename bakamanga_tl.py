import pandas as pd
import csv
import re
import json
import requests
from openai import OpenAI
import amazon_entry



def baka(diction, url):

    if url is not None:
        # create a proper flowchart!

        r = requests.get(url)
        json_d = json.loads(r.text)

        print(json_d)

        romanized_title = json_d.get('title')
        associated_titles = json_d.get('associated')
        associated_titles = [titles.get('title') for titles in associated_titles]

        associated_authors = json_d.get('authors')
        associated_authors = [author.get('name') for author in associated_authors]
        # removes dupes i.e. in the situation that author and artist are the same
        associated_authors = set(associated_authors)
        diction.update(ENG_Authors=associated_authors)

        prompt_eng = "return just the first English string from the following list, \
                    without quotation marks nor explanatory context: " + str(associated_titles)
        prompt_jpn = "return just the first Japanese (日本語) string from the following list, \
                    without quotation marks nor explanatory context: " + str(associated_titles)

        client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key="",
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a database manager",
                },
                {
                    "role": "user",
                    "content": prompt_eng,
                }
            ],
            model="gpt-3.5-turbo",
        )

        english_title = response.choices[0].message.content.strip()
        print(f"ChatGPT eng_title: {english_title}")

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a database manager",
                },
                {
                    "role": "user",
                    "content": prompt_jpn,
                }
            ],
            model="gpt-3.5-turbo",
        )

        japanese_title = response.choices[0].message.content.strip()
        print(f"ChatGPT jpn_title: {japanese_title}")

        # for title in associated_titles:
        #     english_title = None

        diction.update(ENG_Title=english_title)
        diction.update(ROM_Title=romanized_title)
        diction.update(JPN_Title=japanese_title)

    return diction


def baka_search(switch, title):
    # if I am finding the entry url (api) through url manipulation
    if switch == 'api':
        search_url = 'https://www.mangaupdates.com/search.html?search=' + title
        print(f'search_url: {search_url}')
        soup = amazon_entry.simple_soup('requests', search_url)
        first_result = soup.find('div', class_="py-md-0")
        if first_result:
            link = first_result.find('a')
            if link:
                found_title = link.string

                compare_title = re.search(found_title, title)
                print(f'title resemblance: {compare_title}')
                if compare_title is None:
                    return None

                search_result_link = link.get("href")
                print(f'link obtained: {search_result_link}')

                match_id = re.match(r'https://www.mangaupdates.com/series/(?P<id>\S+)/.+', search_result_link)
                entry_id = match_id.group('id')
                print(f'entry_id obtained: {entry_id}')

                converted_id = int(entry_id, 36)  # converts base 36 to base 10
                print(f'converted_id: {converted_id}')

                api_url = 'https://api.mangaupdates.com/v1/series/' + str(converted_id)
                return api_url
    elif switch == 'form':
        base_url = 'https://api.mangaupdates.com/v1/series/'
        # placeholder: use base_url to search for title, and return url of search result
        new_url = base_url + title
        return new_url
    else:
        print(f'invalid switch_baka: {switch_baka}')
    return None


# Test Bench
if __name__ == '__main__':
    # initialize csv file
    csv_filename = 'title_converter.csv'
    csv_file = open(csv_filename, 'w', newline='', encoding='utf_8_sig')
    fieldnames = ['JPN_Title', 'ENG_Title', 'ROM_Title', 'JPN_Authors', 'ENG_Authors']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    # initialize relevant variables to blank
    jpn_title = None
    rom_title = None
    eng_title = None
    jpn_authors = None
    eng_authors = None

    # initialize blank dictionary
    entry_dict = {
        'JPN_Title': jpn_title,
        'ROM_Title': rom_title,
        'ENG_Title': eng_title,
        'JPN_Authors': jpn_authors,
        'ENG_Authors': eng_authors,
    }

    # switch between testing a single entry or the full yurinavi title list
    test_bench = 'single'
    if test_bench == 'single':
        test_title = 'SHIBUYA ギャル百合アンソロジー'
        # csv_example: 同居人が不安定でして%281巻%29
        # existing title: ぜんぶ壊して地獄で愛して      # example api_url: id = 'k7k4tye' -> 43992727718
        # existing title2: セントールの悩み
        # existing title3: やがて君になる
        # light novel & no english title: 祈りの国のリリエール３(GAノベル)
        # might not exist: ラストサマー・バケーション
        # doesn't exist: あーしとわたし。　ギャル×百合アンソロジー (カドカワデジタルコミックス)
        # anthology: SHIBUYA ギャル百合アンソロジー
        # fanbook: 転生王女と天才令嬢の魔法革命　ANIMATION　公式ファンブック(富士見ファンタジア文庫)

        # switch between url editing and in-site searching
        switch_baka = 'api'
        entry_url = baka_search(switch_baka, test_title)
        entry_dict = baka(entry_dict, entry_url)

        print(f'{entry_dict}\n')

        # during test run, confirm the soundness of the new Japanese title.
        title_comparison = re.search(entry_dict.get('JPN_Title'), test_title)
        if title_comparison is None:
            entry_dict.update(JPN_Title='ERROR')

        csv_writer.writerow(entry_dict)
        print(f'{entry_dict}\n')

    elif test_bench == 'list':
        org_data = pd.read_csv('yurinavimonthly_uncleaned.csv')
        df = org_data.copy()
        # troubleshooting: confirm code correctness!
        print(f'base df: \n{df}')
        print(f'head: \n{df.head(3)}')
        print(f'desc: \n{df.describe()}')

        title_column = df.get('title')
        print(f'title df: \n{title_column}')
        print(f'head: \n{title_column.head(3)}')
        print(f'desc: \n{title_column.describe()}')

        # # iterator
        # jpn_title = [uncleaned_title for uncleaned_title in initial_title]

        for initial_title in title_column:

            # switch between url editing and in-site searching
            switch_baka = 'api'
            entry_url = baka_search(switch_baka, initial_title)
            entry_dict = baka(entry_dict, entry_url)

            csv_writer.writerow(entry_dict)
            print(f'{entry_dict}\n')

    # elif test_bench == 'superbaka':
    #     test_title = 'ぜんぶ壊して地獄で愛して'
    #     entry_dict = superbaka(entry_dict, test_title)
    #     csv_writer.writerow(entry_dict)
    #     print(f'{entry_dict}\n')
    else:
        print(f'invalid test bench: {test_bench}')

# -*- coding: utf-8 -*- #
import argparse
import json
import re
import requests
from bs4 import BeautifulSoup
from sys import stderr
from time import sleep

ID_FILE = "data/archived-id.txt"
DATA_FILE = "data/data.json"
PSJP_URL = 'https://puzsq.jp/main/index.php'
PSJP_PROBLEM_URL = 'https://puzsq.jp/main/puzzle_play.php?pid={}'

def load_id():
    with open(ID_FILE) as f:
        data = f.read()
        if int(data) is None:
            return 1
        return int(data)


def write_id(max_id: int):
    with open(ID_FILE, 'w') as f:
        f.write("{}".format(max_id))


def get_psjp():
    try:
        r = requests.get(PSJP_URL, timeout=30)
    except Exception as e:
        print(e, file=stderr)
        print("error page: {}".format(PSJP_URL), file=stderr)
        return None

    return r.text


def get_latest_problem_id():
    psjp_page = get_psjp()
    psjp_soup = BeautifulSoup(psjp_page, 'html.parser')
    problem_href = psjp_soup.body.find('div', id='puz_table').find('a', class_='puz_card_index').get('href')
    matched = re.search(r'[0-9]+', problem_href)
    if matched is None:
        return None
    return int(matched.group(0))


def get_psjp_page(problem_id: int):
    url = PSJP_PROBLEM_URL.format(problem_id)

    try:
        r = requests.get(url, timeout=30)
    except Exception as e:
        print(e, file=stderr)
        print("error problem: {}".format(problem_id), file=stderr)
        return None

    return r.text


def is_error_page(soup):
    if soup is None:
        return True
    if soup.find('span', class_='error') is not None:
        return True
    return False


def get_link(soup):
    link_element = soup.find('div', id='ext_links')
    if link_element is None:
        image_path = soup.find('div', id='puz_main').find('img').get('src')
        return image_path.replace('../', "https://puzsq.jp/")
    return link_element.find('a').get('href')


def get_author(soup):
    author = soup.find('span', id='author')
    author_name = author.find('span', class_='user_name').get_text()
    author_url = author.find('a').get('href')
    author_id = re.search('[0-9]+$', author_url).group()
    return author_id, author_name


def get_puzzle(soup):
    puzzle = soup.find('div', id='puzzle_title').find('a')
    puzzle_name = puzzle.get_text()
    puzzle_id = re.search('[0-9]+$', puzzle.get('href')).group()
    return puzzle_id, puzzle_name


def get_variant(soup):
    variant = soup.find('span', id='variant')
    return 0 if variant is None else 1


def get_created_at(soup):
    return soup.find('span', id='registered').get_text()


def get_author_comment(soup):
    return soup.find('span', id='toukome').get_text()


def get_difficulty(soup):
    difficulty_str = soup.find('span', id='difficulty').get_text()
    difficulty = re.search(r'[0-9]', difficulty_str).group(0)
    return int(difficulty)


def get_problem_data_by_id(problem_id: int):
    psjp_page = get_psjp_page(problem_id)
    soup = BeautifulSoup(psjp_page, 'html.parser')

    if is_error_page(soup):
        return None

    problem_link = get_link(soup)
    author_id, author_name = get_author(soup)
    puzzle_id, puzzle_name = get_puzzle(soup)
    variant = get_variant(soup)
    created_at = get_created_at(soup)
    author_comment = get_author_comment(soup)
    difficulty = get_difficulty(soup)

    problem = {
        "id": problem_id, \
        "problem_link": problem_link, \
        "author_id": author_id, \
        "author_name": author_name, \
        "puzzle_id": puzzle_id, \
        "puzzle_name": puzzle_name, \
        "variant": variant, \
        "created_at": created_at, \
        "author_comment": author_comment, \
        "difficulty": difficulty
    }
    if None in problem.values():
        return None
    return problem


def loop(min: int, max: int):
    for problem_id in range(min, max):
        data = get_problem_data_by_id(problem_id)
        if data is None:
            print("error: invalid page (problem_id: {})".format(problem_id), file=stderr)
            continue

        with open(DATA_FILE, 'a', encoding="utf8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        sleep(1)


def main():
    min_id = load_id()
    max_id = get_latest_problem_id() + 1

    loop(min_id, max_id)
    write_id(max_id)


if __name__ == '__main__':
    main()

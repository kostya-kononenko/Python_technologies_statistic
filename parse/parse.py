import csv
import logging
import sys
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL_FOR_LINK = "https://djinni.co/jobs/?primary_keyword=Python"
BASE_URL = "https://djinni.co/"

VACANCIES_OUTPUT_CSV_PATH = "vacancies.csv"


@dataclass
class PythonVacancies:
    title: str
    company: str
    technologies: list


VACANCIES_FIELDS = [field.name for field in fields(PythonVacancies)]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ],
)


def parse_single_vacancies(vacancies):
    response = requests.get(vacancies)
    soup = BeautifulSoup(response.text, 'html.parser')
    return (PythonVacancies(
        title=soup.select_one("h1").text.strip().replace("\n", "").replace("$", ""),
        company=soup.select_one(".job-details--title").text.strip(),
        technologies=soup.select(".job-additional-info--item-text")
        [1].text.strip().replace("\n", "").replace(" ", "").split(","),
    ))


def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination_with_numbers")

    if pagination is None:
        return 1

    return int(pagination.select("a.page-link")[-2].text)


def get_single_page_vacancies(page_soup: BeautifulSoup) -> [PythonVacancies]:
    vacancies_link = page_soup.select(".job-list-item__link")
    return [parse_single_vacancies(urljoin(BASE_URL, link.get('href'))) for link in vacancies_link]


def get_all_python_vacancies_link():
    page = requests.get(BASE_URL_FOR_LINK).content
    first_page_soup = BeautifulSoup(page, "html.parser")
    num_pages = get_num_pages(first_page_soup)
    all_vacancies = get_single_page_vacancies(first_page_soup)
    for page_num in range(2, num_pages+1):
        logging.info(f"Start parsing page number: {page_num}")
        page = requests.get(BASE_URL_FOR_LINK, {"page": page_num}).content
        soup = BeautifulSoup(page, "html.parser")
        all_vacancies.extend(get_single_page_vacancies(soup))
    return all_vacancies


def write_vacancies_to_csv(vacancies: [PythonVacancies]) -> None:
    with open(VACANCIES_OUTPUT_CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(VACANCIES_FIELDS)
        writer.writerows([astuple(vacancy) for vacancy in vacancies])


def main():
    vacancies = get_all_python_vacancies_link()
    write_vacancies_to_csv(vacancies)


if __name__ == "__main__":
    main()

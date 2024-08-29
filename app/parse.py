import csv
from dataclasses import dataclass, astuple
from typing import Generator, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


def parse_quote_details(quote: Tag) -> Quote:
    """
    Parse and return the details of a book.
    Args:
        quote (Tag): A BeautifulSoup Tag object representing a book.
    Returns:
        Book: An instance of the Book dataclass containing book details.
    """
    return Quote(
        text=quote.select_one(".text").text[1:-1],
        author=quote.select_one(".author").text,
        tags=[tag_soup.text for tag_soup in quote.select(".tag")]
    )

def fetch_page_content(url: str) -> bytes | None:
    """
    Fetch the content of a webpage.
    Args:
        url (str): The URL of the webpage to fetch.
    Returns:
        Optional[str]: The content of the page, or None if an error occurs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching page content: {e}")


def page_generator(url: str) -> Generator[BeautifulSoup, None, None]:
    """
    Generate a BeautifulSoup object from the content of a webpage.
    Args:
        url (str): The URL of the webpage.
    Yields:
        BeautifulSoup: A BeautifulSoup object representing the parsed HTML content.
    """
    page_counter = 1
    while True:
        page_url = urljoin(url, f"/page/{page_counter}/")
        page_content = fetch_page_content(page_url)
        page_soup = BeautifulSoup(page_content, "html.parser")

        yield page_soup

        if not page_soup.select_one(".next"):
            break

        page_counter += 1


def write_quotes_to_csv(quotes: list[Quote], output_csv_path: str) -> None:
    with open(output_csv_path, "w", encoding="utf-8") as file:
        write = csv.writer(file)
        write.writerows([astuple(quote) for quote in quotes])


def extract_books(soup: BeautifulSoup) -> List[Quote]:
    """
    Extract the list of books from the parsed HTML content.
    Args:
        soup (BeautifulSoup): A BeautifulSoup object of the webpage.
    Returns:
        List[Book]: A list of Book dataclass instances with book details.
    """
    quotes = soup.select(".quote")
    return [parse_quote_details(quote) for quote in quotes]


def scrape_quotes() -> List[Quote]:
    """
    Scrape the books listing page for individual book details.
    """
    quotes = []
    for page in tqdm(page_generator(BASE_URL)):
        quotes.extend(extract_books(page))
    return quotes


def main(output_csv_path: str) -> None:
    quotes = scrape_quotes()
    write_quotes_to_csv(quotes, output_csv_path)


if __name__ == "__main__":
    main("quotes.csv")

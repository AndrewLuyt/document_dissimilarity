import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
from bs4 import BeautifulSoup
from collections import defaultdict, Counter
from pathlib import Path
import pickle
import numpy as np
import time
from functools import lru_cache


# https://matix.io/extract-text-from-webpage-using-beautifulsoup-and-python/
# importantly, skipping text from non-text elements
@lru_cache
def scrapeWikiArticle(url, verbose=False):
    """Returns a tuple containing
    [0] all the text content of the page,
    [1] the title of the page
    [2] a random URL inside the page, meant to be used by scrapeRandomArticles()"""

    # https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url-in-requests
    session = requests.Session()
    retry = Retry(connect=3, read=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    response = session.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the links. Search only in the content, not the navigation.
    # Examining html, id=bodyContent captures the entire content area.
    all_links = soup.find(id="bodyContent").find_all("a")
    if len(all_links) < 1:
        raise Exception("No links found here! Exiting...")
    random.shuffle(all_links)

    # find one random link to scrape
    if verbose:
        print("starting", url)
    for link in all_links:
        if verbose:
            print("Trying: ", link)
        # stay inside wikipedia: skip all outside links. All internal links are like <a href="/wiki/SOMETHING">
        # also skip special links like /wiki/Template, wiki/Special:
        if (
            # some <a></a> links have no href tags at all. NB: link is a bs4.element.Tag object
            "href" not in link.attrs
            or link["href"].find("/wiki/") == -1
            or link["href"].find(":") >= 0
            or link["href"].find("/wiki/Template") >= 0
            # or link["href"].find("wiki/Special:") >= 0
            # or link["href"].find("/wiki/Help:") >= 0
            # or link["href"].find("/wiki/Category:") >= 0
            # or link["href"].find("/wiki/File:") >= 0
            # or link["href"].find("/wiki/User:") >= 0
            # or link["href"].find("/wiki/Wikipedia:") >= 0
        ):
            continue
        next_link = link["href"]
        break

    next_url = "https://en.wikipedia.org" + next_link
    title = soup.find(id="firstHeading").string

    all_text = ""
    raw_text = soup.find_all(string=True)
    blacklist = [
        "[document]",
        "header",
        "html",
        "meta",
        "head",
        "input",
        "script",
        "style",
    ]
    for t in raw_text:
        if t.parent.name not in blacklist:
            all_text += f"{t} "
    all_text = all_text.replace("\n", "")
    all_text = all_text.replace("^ ", "")

    if verbose:
        print("Finishing: ", title, ": next: ", next_url)
    return (all_text, title, next_url)


def scrapeRandomArticles(firstURL, n_articles=10, sleepTime=0.2):
    """Returns a list of at most n_articles Wikipedia articles, each
    entry containing the text of the article, minus some arbitrary
    blacklisted text that is inside some html elements like
    [document], meta, noscript, etc.
    it's a list of tuples (TEXT, URL, TITLE)
    sleepTime: number of seconds to wait between grabbing wikipedia articles"""
    first = scrapeWikiArticle(firstURL)
    title = first[1]
    next_url = first[2]
    articles = [(first[0], title)]
    for i in range(n_articles - 1):
        if next_url:
            article = scrapeWikiArticle(next_url)
            articles.append((article[0], article[1]))
            next_url = article[2]
        else:
            raise FileNotFoundError("A valid link was not found: " + next_url[1])
        time.sleep(sleepTime)
    return articles


def createDictionary(
    articles, max=1000, file="dictionary.obj", minWordLength=2, overwrite=False
):
    """Create a set of the max most common words (all lowercase) in the article corpus."""
    if Path(file).exists() and overwrite is False:
        raise FileExistsError(
            file, "already exists. Set overwrite=True to overwrite it."
        )

    # keep stopwords minimal. Even v. common words like "she" could distinguish
    # some articles.
    stopWords = {"the", "to", "of", "in", "and", "or", "is", "that", "as"}
    d = defaultdict(int)
    for article in articles:
        for w in article[0].split():
            word = w.lower()
            if word not in stopWords and len(word) >= minWordLength:
                d[word] += 1

    c = Counter(d)
    sorted_wordlist = sorted([word for word, _ in c.most_common(max)])
    with open(file, "wb") as f:
        pickle.dump(sorted_wordlist, f, pickle.HIGHEST_PROTOCOL)


def loadDictionary(file="dictionary.obj"):
    with open(file, "rb") as f:
        return pickle.load(f)


def mostCommonWords(n, wordCounts, dictionary):
    c = Counter(wordCounts)
    return c.most_common(n)


def wordCounts(article, dictionary):
    word_counts = dict()
    # Python 3.7: "Dictionary order is guaranteed to be insertion order."
    # We can rely on .keys() and .values() to keep their order.
    for word in sorted(dictionary):
        word_counts[word] = 0
    article = article.lower()
    for word in article.split():
        if word in dictionary:
            word_counts[word] += 1
    return word_counts


def wordVector(article, dictionary):
    counts = wordCounts(article, dictionary)
    return np.array(list(counts.values()))


def standardizeVector(v):
    """Assumes v is a numpy array"""
    v = v - min(v)
    return v / max(v)


def documentDissimilarity(article1, article2, dictionary):
    wordvec1 = wordVector(article1, dictionary)
    wordvec2 = wordVector(article2, dictionary)

    # standardize to [0,1] so short vs long documents aren't treated as different.
    wordvec1 = standardizeVector(wordvec1)
    wordvec2 = standardizeVector(wordvec2)

    return np.sqrt(np.sum((wordvec1 - wordvec2) ** 2))


# print(scrapeWikiArticle("https://en.wikipedia.org/wiki/web_scraping"))
# print(createDictionary(scrapeWikiArticle("https://en.wikipedia.org/wiki/web_scraping")))

# make a standard dictionary so we don't have to do this every time, so the words
# are in the same order, etc etc...
# dictionary = createDictionary(
#     scrapeArticles("https://en.wikipedia.org/wiki/Aaron_Halfaker", n_articles=4)
# )
# print(
#     wordVector(
#         scrapeWikiArticle("https://en.wikipedia.org/wiki/web_scraping"), dictionary
#     ),
# )

# print(scrapeArticles("https://en.wikipedia.org/wiki/WDQ_(identifier)"))
# print(scrapeWikiArticle("https://en.wikipedia.org/wiki/Aaron_Halfaker"))

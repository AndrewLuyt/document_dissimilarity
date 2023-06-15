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
        # stay inside wikipedia: All internal links are like <a href="/wiki/SOMETHING">
        # also skip special links like /wiki/Template, wiki/Special:
        if (
            # some <a></a> links have no href tags. NB: link is a bs4.element.Tag object
            "href" not in link.attrs
            or link["href"].find("/wiki/") == -1
            or link["href"].find(":") >= 0
            or link["href"].find("/wiki/Template") >= 0
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
    """Returns a list of Wikipedia articles, each entry containing the text of the
    article, minus some arbitrary blacklisted text.

    firstURL: a string with the Wikipedia URL to start with.
    n_articles: integer,
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


def scrapeArticles(urlList):
    """Returns a list of articles, as per scrapeWikiArticle.

    urlList: list of strings. Each string is a URL of a Wikipedia article."""
    articles = []
    for url in urlList:
        article = scrapeWikiArticle(urlList)
        articles.append((article[0], article[1]))
    return articles


def createDictionary(
    articles, maxWords=1000, file="dictionary.obj", minWordLength=2, overwrite=False
):
    """Create a set of the max most common words (all lowercase) in the article
    corpus. Intended to be used on the output of scrapeRandomArticles.

    articles: output of scrapeRandomArticles
    maxWords: int, return the [maxWords] most common words in the article corpus
    file: string, name of the dictionary file. Just leave as dictionary.obj
    minWordLength: remove all words shorter than this many letters
    overwrite: if <file> exists, should it be overwritten?"""
    if Path(file).exists() and overwrite is False:
        raise FileExistsError(
            file, "already exists. Set overwrite=True to overwrite it."
        )

    stopWords = {"the", "to", "of", "in", "and", "or", "is", "that", "as"}
    d = defaultdict(int)
    for article in articles:
        for w in article[0].split():
            word = w.lower()
            if word not in stopWords and len(word) >= minWordLength:
                d[word] += 1

    c = Counter(d)
    sorted_wordlist = tuple(sorted([word for word, _ in c.most_common(maxWords)]))
    with open(file, "wb") as f:
        pickle.dump(sorted_wordlist, f, pickle.HIGHEST_PROTOCOL)


def loadDictionary(file="dictionary.obj"):
    """Returns a tuple containing all dictionary words. A 'dictionary' in this
    sense is the list of words which will be counted in a document to create
    its feature vector. Any word not in the dictionary isn't considered.

    file: string name of the dictionary file"""
    with open(file, "rb") as f:
        return tuple(pickle.load(f))  # old versions were unhashable lists


def _wordCounts(article, dictionary):
    """Return the count of all words in article, for those words in dictionary

    article: output of scrapeWikiArticle or similar
    dictionary: tuple of strings, the output of loadDictionary"""
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
    """Return the feature vector for article.

    article: output of scrapeWikiArticle or similar
    dictionary: tuple of strings, the output of loadDictionary"""
    counts = _wordCounts(article, dictionary)
    return np.array(list(counts.values()))


def standardizeVector(v):
    """Transforms values in v to [0,1]

    v: a numpy ndarray"""
    v = v - min(v)
    return v / max(v)


def documentDissimilarity(article1, article2, dictionary):
    """Return a dissimilarity score between articles. Higher is more dissimilar.
    Lowest value possible is 0, for documents with identical feature vectors.

    article1, article2: a string, the full text of the article.
    dictionary: tuple of strings, output of loadDictionary"""

    # ensure arguments are in the same order if we compare the
    # same two documents. This lets us hit the lru_cache.
    if article1 < article2:
        return _documentDissimilarity(article1, article2, dictionary)
    else:
        return _documentDissimilarity(article2, article1, dictionary)


@lru_cache
def _documentDissimilarity(article1, article2, dictionary):
    wordvec1 = wordVector(article1, dictionary)
    wordvec2 = wordVector(article2, dictionary)

    # standardize to [0,1] so short vs long documents aren't treated as different.
    wordvec1 = standardizeVector(wordvec1)
    wordvec2 = standardizeVector(wordvec2)

    return np.sqrt(np.sum((wordvec1 - wordvec2) ** 2))

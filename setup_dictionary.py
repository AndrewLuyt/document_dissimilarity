import random
import scraper

# Give the scraper an initial web page, a max number of articles to scan,
# and it will start at the first page, randomly choose a link from that
# page as its next page, and continue on thusly, accumulating word counts
# over a random (other than the 1st page) set of web pages.

random.seed(42)
dict_corpus = scraper.scrapeRandomArticles(
    "https://en.wikipedia.org/wiki/Human",
    n_articles=1000,
    sleepTime=0.6,
)

for _, title in dict_corpus:
    print(title, end=", ")
print()

# Create a dictionary of the 'max' most common words and save
# it to dictionary.obj
scraper.createDictionary(dict_corpus, maxWords=4000, minWordLength=4)

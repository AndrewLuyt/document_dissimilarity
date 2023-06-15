import scraper
import numpy as np
import pandas as pd
import seaborn as sns  # fmt: skip
import matplotlib.pyplot as plt

dictionary = scraper.loadDictionary()

urls = [
    "https://en.wikipedia.org/wiki/James_T._Kirk",
    "https://en.wikipedia.org/wiki/Spock",
    "https://en.wikipedia.org/wiki/web_scraping",
    "https://en.wikipedia.org/wiki/Data_scraping",
    "https://en.wikipedia.org/wiki/Star_Trek",
    "https://en.wikipedia.org/wiki/Christmas",
    "https://en.wikipedia.org/wiki/Vector_space",
    "https://en.wikipedia.org/wiki/Electric_guitar",
    "https://en.wikipedia.org/wiki/Vector_field",
    "https://en.wikipedia.org/wiki/Winter_solstice",
    "https://en.wikipedia.org/wiki/Guitar",
]
url_names = [url.split("/")[-1] for url in urls]

dissimilarityMatrix = pd.DataFrame(np.nan, columns=url_names, index=url_names)
for i in range(len(urls)):
    # for j in range(i + 1, len(urls)):  # upper triangle, no diagonal
    for j in range(len(urls)):
        if i == j:
            continue  # don't compare an article with itself
        dissimilarityMatrix.iloc[i, j] = scraper.documentDissimilarity(
            scraper.scrapeWikiArticle(urls[i])[0],
            scraper.scrapeWikiArticle(urls[j])[0],
            dictionary,
        )

print(dissimilarityMatrix)
# dissimilarityMatrix = dissimilarityMatrix.T.iloc[1:, :]  # flip & trim matrix
print(scraper.scrapeWikiArticle.cache_info())
print(scraper._documentDissimilarity.cache_info())
sns.heatmap(
    dissimilarityMatrix,
    annot=True,
    cmap=plt.get_cmap("coolwarm").reversed(),
    linewidths=0.1,
    linecolor="black",
)
plt.title("Measuring dissimilarity between Wikipedia Articles")

plt.tight_layout()
plt.show()

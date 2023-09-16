# Given a list of wikipedia article URLS (currently hardcoded), compute
# a dissimilarity matrix between articles. By editing the value of
# `dissimilarity_metric` to "cosine" or "distance", one can use cosine
# similarity or the l2 norm of the vector difference as a dissimilarity metric.

import scraper
import numpy as np
import pandas as pd

# import seaborn as sns  # fmt: skip
import matplotlib.pyplot as plt
from heatmap import heatmap, annotate_heatmap


dictionary = scraper.loadDictionary()

dissimilarity_metric = "distance"  # "cosine" or "distance"

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
            dissimilarity_metric,
        )

print(dissimilarityMatrix)
# dissimilarityMatrix = dissimilarityMatrix.T.iloc[1:, :]  # flip & trim matrix
print(scraper.scrapeWikiArticle.cache_info())
print(scraper._documentDissimilarity.cache_info())
# sns.heatmap(
#     dissimilarityMatrix,
#     annot=True,
#     cmap=plt.get_cmap("coolwarm").reversed(),
#     linewidths=0.1,
#     linecolor="black",
# )

fig, ax = plt.subplots()
labels = dissimilarityMatrix.index.values
im, cbar = heatmap(
    dissimilarityMatrix.to_numpy(),
    labels,
    labels,
    ax,
    cmap=plt.get_cmap("coolwarm").reversed(),
    cbarlabel="Similarity [lower is better]",
)
texts = annotate_heatmap(im, valfmt="{x:.1f}")

plt.title("Measuring dissimilarity between Wikipedia Articles")

plt.tight_layout()
plt.show()

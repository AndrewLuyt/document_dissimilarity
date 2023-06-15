import scraper

dictionary = scraper.loadDictionary()
# print(dictionary[1200])
# exit()

# a1 = "https://en.wikipedia.org/wiki/Elim_Garak"
a1 = "https://en.wikipedia.org/wiki/Benjamin_Sisko"
a2 = "https://en.wikipedia.org/wiki/Star_Trek"
a1 = "https://en.wikipedia.org/wiki/web_scraping"
# a2 = "https://en.wikipedia.org/wiki/web_scraping"
# a2 = "https://en.wikipedia.org/wiki/Data_scraping"
# a1 = "https://en.wikipedia.org/wiki/Vector_space"
# a2 = "https://en.wikipedia.org/wiki/Vector_field"
# a1 = "https://en.wikipedia.org/wiki/Archtop_guitar"
# a1 = "https://en.wikipedia.org/wiki/Guitar"
# a1 = "https://en.wikipedia.org/wiki/Electric_guitar"
# a1 = "https://en.wikipedia.org/wiki/Steel-string_acoustic_guitar"
# a2 = "https://en.wikipedia.org/wiki/Classical_guitar"
a2 = "https://en.wikipedia.org/wiki/Musical_instrument"
article1 = scraper.scrapeWikiArticle(a1, verbose=False)  # nb: article is in [0]
article2 = scraper.scrapeWikiArticle(a2, verbose=False)

# wc = scraper.wordCounts(article[0], dictionary)
# print(wc.values())
# print(scraper.mostCommonWords(30, wc, dictionary))
# print(list(wc.items())[1000:1010])
# print(scraper.wordVector(article[0], dictionary))
# print(type(scraper.wordVector(article1[0], dictionary)))
print(scraper.documentDissimilarity(article1[0], article2[0], dictionary))

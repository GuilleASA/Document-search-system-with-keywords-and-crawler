-SAR_Crawler.py. Main program for crawling Wikipedia articles.
articles. It creates an object of the SAR_Crawler class to download articles from the
Wikipedia and store them in a local directory in json format.
-SAR_Indexer.py. Main program for indexing articles. Creates an object
object of the SAR_Project class to extract the articles from a collection hosted in a local directory, indexes them and saves them in a json format.
directory, indexes them, and saves the object instance to disk.
-SAR_Searcher.py. Main program for retrieving articles. Loads from
an instance of the SAR_Project class to respond to queries made to it.
queries.
-SAR_Crawler_lib.py. Library for the definition of the SAR_Crawler class. The crawling
functionality is achieved by modifying some methods of that class.
-SAR_lib.py. Library for the definition of the SAR_Project class. The indexing and retrieval
indexing and retrieval functionality is achieved by a reduced number of
methods of that class.

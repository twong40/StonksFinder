from getAccessToken import getToken
from databaseOperations import createClient, insertOne, findItem
from credentials import stockApiKey, userAgent
from datetime import datetime
from pprint import pprint
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import requests
import itertools
import time
import re

def main():
    while(True):
        choice = input("Choose an option to run:\n[1] Collect reddit data\n[2] Display Data\n[3] Exit\nInput: ")
        db = createClient()
        if choice == "1":
            stockSymbols = searchReddit()
            jsonData = searchStockInfo(stockSymbols)
            pprint("Phase 3: Saving to MongoDb")
            insertOne(db, jsonData)
        elif choice == "2":
            pprint("Displaing Data")
            # Data for plotting
            t = np.arange(0.0, 2.0, 0.01)
            s = 1 + np.sin(2 * np.pi * t)

            fig, ax = plt.subplots()
            ax.plot(t, s)

            ax.set(xlabel='time (s)', ylabel='voltage (mV)',
                title='About as simple as it gets, folks')
            ax.grid()

            fig.savefig("test.png")
            plt.show()
            labels = ['G1', 'G2', 'G3', 'G4', 'G5']
            men_means = [20, 35, 30, 35, 27]
            women_means = [25, 32, 34, 20, 25]
            men_std = [2, 3, 4, 1, 2]
            women_std = [3, 5, 2, 3, 3]
            width = 0.35       # the width of the bars: can also be len(x) sequence

            fig, ax = plt.subplots()

            ax.bar(labels, men_means, width, yerr=men_std, label='Men')
            ax.bar(labels, women_means, width, yerr=women_std, bottom=men_means,
                label='Women')

            ax.set_ylabel('Scores')
            ax.set_title('Scores by group and gender')
            ax.legend()

            plt.show()
        elif choice == "3":
            pprint("Exiting")
            break
        else:
            pprint("Not a valid option!")

def isValidSymbol(symbolToCheck):
    regex = re.compile('[0-9@_!#%^&*()<>?/\|}{~:]')
    if len(symbolToCheck) > 0 and len(symbolToCheck) <= 5 and regex.search(symbolToCheck) == None:
        return True
    return False

def searchReddit():
    pprint("Phase 1: Scanning subreddits")
    seenTitles = set()
    stockSymbols = dict()
    newToken = getToken()
    headers = {"Authorization": "bearer " + newToken, "User-Agent": userAgent}
    payload = {'limit': 100}
    redditEndpoint = "https://oauth.reddit.com/r/<SUBREDDIT>/<FILTER>"
    stockSubreddits = ['stocks', 'investing', 'wallstreetbets']
    stockFilters = ['rising', 'new', 'top', 'best']
    # Iterate through the possible subreddits and filters
    for subreddit, filterKey in itertools.product(stockSubreddits, stockFilters):
        # Iterate through at most 4 papges
        for i in range(5):
            response = requests.get(redditEndpoint.replace("<SUBREDDIT>", subreddit).replace("<FILTER>", filterKey), headers=headers, params=payload)
            for i in range(len(response.json()['data']['children'])):
                responseData = response.json()['data']['children'][i]['data']
                title = responseData['title']
                # If this is a new title, search for the ticker and add it to the map with the amount seen
                if title not in seenTitles:
                    seenTitles.add(title)
                    splitTitle = title.split()
                    for word in splitTitle:
                        index = word.find("$")
                        if index != -1 and isValidSymbol(word):
                            ticker = word[index + 1:].upper()
                            value = stockSymbols.get(ticker)
                            if value is None:
                                redditStockData = dict()
                                redditStockData["symbol"] = ticker
                                redditStockData["numberOfMentions"] = 1
                                redditStockData["ups"] = [responseData["ups"]]
                                redditStockData["upvote_ratio"] = [responseData["upvote_ratio"]]
                                redditStockData["total_awards_received"] = [responseData["total_awards_received"]]
                                redditStockData["gilded"] = [responseData["gilded"]]
                                redditStockData["num_comments"] = [responseData["num_comments"]]
                                stockSymbols[ticker] = redditStockData
                            else:
                                value["numberOfMentions"] = value["numberOfMentions"] + 1
                                value["ups"].append(responseData["ups"])
                                value["upvote_ratio"].append(responseData["upvote_ratio"])
                                value["total_awards_received"].append(responseData["total_awards_received"])
                                value["gilded"].append(responseData["gilded"])
                                value["num_comments"].append(responseData["num_comments"])
                                stockSymbols[ticker] = value
            # No Page afterwards
            payload['after'] = response.json()['data']['after']
            if payload['after'] is None:
                break
    return stockSymbols

def searchStockInfo(stockSymbols):
    pprint("Phase 2: Searching for stock info")
    stockQuoteEndpoint = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=<SYMBOL>&apikey=" + stockApiKey
    counter = 0
    jsonData = {"timeStamp" : datetime.now()}
    totalData = []
    for ticker in stockSymbols:
        # Api only allows 5 calls per minute, 500 calls per day
        if counter % 5 == 0:
            counter = 0
            time.sleep(60)
        stockResponse = requests.get(stockQuoteEndpoint.replace("<SYMBOL>", ticker))
        if "Global Quote" in stockResponse.json() and len(stockResponse.json()["Global Quote"]) != 0:
            extraStockData = dict()
            # Clean up json response data
            for key in stockResponse.json()["Global Quote"]:
                extraStockData[key[4:]] = stockResponse.json()["Global Quote"][key]
            totalData.append({**stockSymbols[ticker], **extraStockData})
        counter+= 1
    jsonData["data"] = totalData
    return jsonData

if __name__ == "__main__":
    main()
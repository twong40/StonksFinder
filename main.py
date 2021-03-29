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
import random
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
            showData(db)

        elif choice == "3":
            pprint("Exiting")
            break
        else:
            pprint("Not a valid option!")

def showData(db):
    pprint("Displaying Data")
    # Data for plotting
    fig, (ax1, ax2) = plt.subplots(2,1,figsize=(14,8))
    dataPoints = createLineData(findItem(db, None))
    maxLabel = createMaxLabels(dataPoints)
    for key in dataPoints:
        if key in maxLabel.keys():
            ax1.plot(dataPoints[key]["xValues"], dataPoints[key]["yValues"], marker='o', linewidth=3, label=key, color=maxLabel[key][1])
        else:
            ax1.plot(dataPoints[key]["xValues"], dataPoints[key]["yValues"], linestyle="--")
    ax1.set(xlabel='Timestamp', ylabel='Reddit Score',
        title='Reddit Score Per Ticker')
    ax1.grid()
    ax1.legend(bbox_to_anchor=(1.03, 1), loc='upper left', borderaxespad=0.)
    # fig.savefig("graphs/NumberOfMentionsVsTimestamp_" + str(datetime.today()).replace(" ","") + ".png")
    stocksDataPoints = createStockLineData(maxLabel.keys(), findItem(db, None))
    for key in stocksDataPoints:
        ax2.plot(stocksDataPoints[key]["xValues"], stocksDataPoints[key]["yValues"], marker='o', linewidth=3, label=key, color=maxLabel[key][1])
    ax2.set(xlabel='Timestamp', ylabel='High of the day',
        title='Popular Reddit Stock Vs Stock High')
    ax2.grid()
    # fig.savefig("graphs/NumberOfMentionsVsTimestamp_" + str(datetime.today()).replace(" ","") + ".png")
    plt.subplots_adjust(left=None, bottom=0.06, right=None, top=None, wspace=None, hspace=0.28)
    plt.show()

def createMaxLabels(dataPoints):
    valueList = dict()
    for symbol in dataPoints:
        averageValue = average(dataPoints[symbol]["yValues"])
        color = [random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)]
        if len(valueList) < 5:
            valueList[symbol] = (averageValue, color)
        else:
            minTuple = min(valueList.items(), key=lambda x: x[1])
            if minTuple[1][0] < averageValue:
                valueList.pop(minTuple[0], None)
                valueList[symbol] = (averageValue, color)
    return valueList

def average(lst):
    return sum(lst) / len(lst)

def computeReditScore(mongoData):
    return (mongoData["numberOfMentions"] * 25) + sum(mongoData["ups"]) + (average(mongoData["upvote_ratio"]) * 20 ) + (sum(mongoData["total_awards_received"]) * 10) + (sum(mongoData["gilded"]) * 10) + sum(mongoData["num_comments"])

def createLineData(postData):
    dataPoints = dict()
    for post in postData:
        for entry in post["data"]:
            currentDataSet = dataPoints.get(entry["symbol"])
            if currentDataSet is None:
                dataSet = dict()
                dataSet["xValues"] = [post["timeStamp"]]
                dataSet["yValues"] = [computeReditScore(entry)]
                dataPoints[entry["symbol"]] = dataSet
            else:
                currentDataSet["xValues"].append(post["timeStamp"])
                currentDataSet["yValues"].append(computeReditScore(entry))
                dataPoints[entry["symbol"]] = currentDataSet
    return dataPoints

def createStockLineData(symbols, postData):
    dataPoints = dict()
    for post in postData:
        for symbol in symbols:
            storedData = next((item for item in post["data"] if item["symbol"] == symbol), None)
            currentDataSet = dataPoints.get(symbol)
            if storedData is not None:
                if currentDataSet is None:
                    dataSet = dict()
                    dataSet["xValues"] = [post["timeStamp"]]
                    dataSet["yValues"] = [float(storedData["high"])]
                    dataPoints[symbol] = dataSet
                else:
                    currentDataSet["xValues"].append(post["timeStamp"])
                    currentDataSet["yValues"].append(float(storedData["high"]))
                    dataPoints[symbol] = currentDataSet
    return dataPoints

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
from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse
from django.urls import reverse
import yfinance as yf
import os
import json
import pandas as pd
import numpy as np
import requests
import datetime
from datetime import timezone
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import praw
from django.http import JsonResponse
from dotenv import load_dotenv
from dateutil import parser



load_dotenv()
nltk.download('vader_lexicon')

def index(request):
    return render(request, 'app/landing.html')


def stock(request,pk):
    stock = yf.Ticker(pk)
    close = "{:.2f}".format(stock.history(period='1d').Close.values.tolist()[0])
    today = datetime.date.today().strftime('%m-%d-%Y')
    week_ago = (datetime.date.today() - datetime.timedelta(days=21)).strftime('%m-%d-%Y')
    print(week_ago)
    context = { 'ticker': pk,'today': today, 'week_ago': week_ago, 'stock':stock.info, 'close':close}
    return render(request,'app/stocks.html',context)

def search(request):  # new
    query = request.GET.get("query")
    print(query)
    return redirect(reverse("stock",kwargs={'pk':str(query)}))

def loadtweets(request):
# request should be ajax and method should be GET.
  if request.is_ajax and request.method == "GET":
    pk = request.GET.get("ticker", None)
    start = datetime.datetime.strptime(request.GET.get("start", None), '%m-%d-%Y')
    finish = datetime.datetime.strptime(request.GET.get("finish", None), '%m-%d-%Y')   
    pk = request.GET.get("ticker", None)
    tweets = getTweets(pk,start,finish)
    scores = getScores(list(zip(*tweets))[0])
    meanT = float("{:.3f}".format(scores.mean()))
    sentimentsT = getSentiments(scores)
    return JsonResponse({"sentimentsT":sentimentsT,"meanT":meanT,"tweets":tweets,"scores":list(scores)}, status = 200)
  return JsonResponse({}, status = 400)

def loadstock(request):
# request should be ajax and method should be GET.
  if request.is_ajax and request.method == "GET":
    pk = request.GET.get("ticker", None)
    start = datetime.datetime.strptime(request.GET.get("start", None), '%m-%d-%Y').strftime('%Y-%m-%d')
    finish = datetime.datetime.strptime(request.GET.get("finish", None), '%m-%d-%Y').strftime('%Y-%m-%d') 
    stock = yf.Ticker(pk)
    data = stock.history(start = start, end = finish)
    index = list(data.index.strftime('%Y-%m-%d %H'))
    print(index)
    close = data.Close.values.tolist()
    print(close)
    open = data.Open.values.tolist()
    high = data.High.values.tolist()
    low = data.Low.values.tolist()
    return JsonResponse( {'index': index, 'close': close, 'open': open,'high': high, 'low': low}, status = 200)
  return JsonResponse({}, status = 400)


def loadnews(request):
# request should be ajax and method should be GET.
  if request.is_ajax and request.method == "GET":   
    pk = request.GET.get("ticker", None)
    start = datetime.datetime.strptime(request.GET.get("start", None), '%m-%d-%Y').strftime('%Y%m%d')
    finish = datetime.datetime.strptime(request.GET.get("finish", None), '%m-%d-%Y').strftime('%Y%m%d')
    news = getNews(pk,start,finish)
    scores = getScores(list(zip(*news))[0])
    meanN = float("{:.3f}".format(scores.mean()))
    sentimentsN = getSentiments(scores)
    return JsonResponse({"sentimentsN":sentimentsN,"meanN":meanN, "news": news,"scores":list(scores)}, status = 200)
  return JsonResponse({}, status = 400)

def loadreddit(request):
# request should be ajax and method should be GET.
  if request.is_ajax and request.method == "GET":   
    pk = request.GET.get("ticker", None)
    stock = yf.Ticker(pk)
    reddit = getReddit(stock)
    scores = getScores(list(zip(*reddit))[0])
    meanR = float("{:.3f}".format(scores.mean()))
    sentimentsR = getSentiments(scores)
    return JsonResponse({"sentimentsR":sentimentsR,"meanR":meanR, "reddit" : reddit}, status = 200)
  return JsonResponse({}, status = 400)

    

def getNews(ticker,start,finish):
  start = start + 'T0130'
  finish = finish + 'T0130'
  url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={}&apikey=52F5JTIMVKJ0BMJM&limit=200&sort=RELEVANCE&time_from={}&time_to={}'.format(ticker,start,finish)
  print(url)
  r = requests.get(url)
  data = r.json()
  news =[]
  for n in data['feed']:
    news.append((n['summary'],n['title'],datetime.datetime.strptime(n['time_published'].split("T")[0],'%Y%m%d').strftime('%m-%d-%Y'),n['url']))
  return(news)


def getReddit(stock):
  reddit = praw.Reddit(client_id=os.getenv('CLIENT_ID'), client_secret=os.getenv('CLIENT_SECRET'), user_agent='stocks')
  posts = []
  subs = ['StockMarket','Investing','WallStreetBets']
  names = [stock.info['shortName'].split()[0].replace(',',''),stock.info['symbol']]
  for sub in subs:
    for name in names:
        hot_posts = reddit.subreddit(sub).search(name,limit=100,time_filter ='week')
        for post in hot_posts:
            title=post.title
            link=post.permalink
            date = post.created_utc
            print(type(post))
            posts.append([title,date,link])
  return posts


def getTweets(stock,start,finish):
  start_time = start.strftime('%Y-%m-%dT%H:%M:%SZ')
  print(start_time)
  end_time = finish.strftime('%Y-%m-%dT%H:%M:%SZ')

  if ( start < (datetime.datetime.today() - datetime.timedelta(days=7)) ):
    start_time = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
  if ( finish.date() >= datetime.date.today() ):
    end_time = (datetime.datetime.today() - datetime.timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
  tweets = []
  def auth():
      return os.getenv('TOKEN')
  def create_headers(bearer_token):
      headers = {"Authorization": "Bearer {}".format(bearer_token)}
      return headers
  def create_url(keyword, max_results):
      
      search_url = "https://api.twitter.com/2/tweets/search/recent" #Change to the endpoint you want to collect data from
      
      #change params based on the endpoint you are using
      query_params = {'query': keyword,
                      'max_results': max_results,
                      'start_time' : start_time,
                      'end_time' : end_time,
                      'expansions': '',
                      'tweet.fields': 'text,created_at,entities',
                      'user.fields': '',
                      'place.fields': '',
                      'sort_order' : 'relevancy',
                      'next_token': {}}
      return (search_url, query_params)

  def connect_to_endpoint(url, headers, params, next_token = None):
      params['next_token'] = next_token   #params object received from create_url function
      response = requests.request("GET", url, headers = headers, params = params)
      print("Endpoint Response Code: " + str(response.status_code))
      if response.status_code != 200:
          raise Exception(response.status_code, response.text)
      return response.json()
  bearer_token = auth()
  print(bearer_token)
  headers = create_headers(bearer_token)
  keyword = "{} lang:en".format(stock)
  max_results = 100
  url = create_url(keyword, max_results)
  json_response = connect_to_endpoint(url[0], headers, url[1])
  result_count = json_response['meta']['result_count']
  for i in range(0,result_count):
    try:
      tweets.append((json_response['data'][i]['text'],json_response['data'][i]['created_at'].strptime('%Y-%m-%dT%H:%M:%S.%fZ').strftime('%m-%d-%Y %H:%M'),json_response['data'][i]['entities']['urls'][0]['url']))
    except:
      tweets.append((json_response['data'][i]['text'],datetime.datetime.strptime(json_response['data'][i]['created_at'],'%Y-%m-%dT%H:%M:%S.%fZ').strftime('%m-%d-%Y %H:%M')))
  return tweets


def getScores(tweets):

  analyser = SentimentIntensityAnalyzer()

  compval1 = [ ]  #empty list to hold our computed 'compound' VADER scores


  for item in tweets:

    k = analyser.polarity_scores(item)
    compval1.append(k['compound'])
    
    
  return np.array(compval1)

def getSentiments(vals):
    positive = 0
    neutral = 0
    negative = 0
    for val in vals:
        if val >= 0.05 :
            positive += 1
 
        elif val <= - 0.05 :
            negative += 1
 
        else :
            neutral += 1
    return(positive,neutral,negative)


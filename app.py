import os
import time
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import pymongo
import csv

application = Flask(__name__)
app = application

@app.route('/', methods=['GET'])
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            driver = webdriver.Chrome()
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            driver.get(flipkart_url)
            page_text = driver.page_source
            flipkart_html = bs(page_text, 'html.parser')
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "http://www.flipkart.com" + box.div.div.div.a['href']
            driver.get(productLink)
            prodRes = driver.page_source
            driver.quit()
            prod_html = bs(prodRes, "html.parser")
            commentboxes = prod_html.findAll('div', {'class': "_16PBlm"})
            filename = searchString + ".csv"

            reviews = []
            for commentbox in commentboxes:
                try:
                    price_element = flipkart_html.select('div._25b18c ._30jeq3')[0]
                    price = price_element.text
                except Exception as e:
                    price = 'Price not found: ' + str(e)

                try:
                    name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                except Exception as e:
                    name = 'Name not found: ' + str(e)

                try:
                    rating = commentbox.div.div.div.div.text
                except Exception as e:
                    rating = 'Rating not found: ' + str(e)

                try:
                    commentHead = commentbox.div.div.div.p.text
                except Exception as e:
                    commentHead = 'Comment Head not found: ' + str(e)

                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except Exception as e:
                    custComment = 'Comment not found: ' + str(e)

                mydict = {"Price": price, "Product": searchString, "Customer Name": name,
                          "Rating": rating, "Heading": commentHead, "Comment": custComment}
                reviews.append(mydict)

            # Write to CSV file
            with open(filename, "w", newline='', encoding='utf-8') as fw:
                headers = ["Price", "Product", "Customer Name", "Rating", "Heading", "Comment"]
                writer = csv.DictWriter(fw, fieldnames=headers)
                writer.writeheader()
                writer.writerows(reviews)

            # MongoDB connection and insertion
            client = pymongo.MongoClient("mongodb+srv://webscrape:webscrape@cluster0.yq5xnzx.mongodb.net/?retryWrites=true&w=majority")
            db = client['flipkart_scrape']
            review_col = db['review_scrape_data']
            review_col.insert_many(reviews)

            # Close MongoDB connection
            client.close()

            return render_template('results.html', reviews=reviews[0:len(reviews) - 1])

        except Exception as e:
            print("The exception Message is ", e)
            return "Something went wrong"
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False)

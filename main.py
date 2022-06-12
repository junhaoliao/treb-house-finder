import os
import smtplib

import requests
import time
from datetime import datetime
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

url = 'https://onlistings.trreb.ca/listings'

parameters = {
    "orderby": "price",
    "latitude": [">=43.827248", "<=43.858194"],
    "longitude": [">=-79.403235", "<=-79.326409"],
    "gid": "treb",
    "class": ["FREE", "CONDO"],
    "availability": "A",
    "bedrooms": ["2", "3", "4", ">=5"],
    "bathrooms": ["2", "3", "4", ">=5"],
    "totalParkingSpaces": ["1", "2", "3", "4", ">=5"],
    "saleOrRent": ["RENT", "SUB-RENT"]
}

headers = {
    "Accept": "application/json"
}

OLD_LIST = []
NEW_LIST = []

LAST_FRESH_TIME = datetime.now()


def get_new_house(parking=1):
    global OLD_LIST, NEW_LIST
    OLD_LIST += NEW_LIST
    NEW_LIST = []

    parameters['totalParkingSpaces'] = ["2", "3", "4", ">=5"]
    if parking == 1:
        parameters['totalParkingSpaces'] = ["1"]

    resp = requests.get(url=url, params=parameters, headers=headers)
    data = resp.json()

    for s in data:
        if s not in OLD_LIST:
            NEW_LIST.append(s)

    return NEW_LIST


def get_new_house_text(parking=1):
    t = f'New Listings with {parking} Parkings ' + f"(since {LAST_FRESH_TIME})"
    b = '<h2>' + t + '</h2><br>'

    new_houses = get_new_house(parking)

    for s in new_houses:
        b += '🏘️\t' + '<b><a href="https://onlistings.trreb.ca/listings/' + s['_id'] + '">' + s['_id'] + '</a></b><br>'

        b += '<ul>'
        b += '<li>💰 $' + str(s['price']) + '</li>'

        map_url = f"https://maps.google.com?q={urllib.parse.quote_plus(s['streetAddress'])}"
        b += '<li>📍 ' + f'<a href="{map_url}">' + s['streetAddress'] + ', ' + s['city'] + '</a></li>'

        b += '<li>📐 ' + str(s['squareFeet']) + ' ft' + '\t🛏 ' + str(s['bedrooms']) + '\t🧱 ' + str(s['style']) + ' ' + \
             s['typeName'] + '</li>'

        b += '</ul>'

        # if len(s["images"]) > 0:
        #     b += f'<img src="https://onlistings.trreb.ca{s["images"][0]}" width="200"/>'

        b += '<br>'

    return len(new_houses), t, b


def send_email(to_email, subject, body):
    sender_server = os.environ['SENDER_SERVER']
    sender_port = int(os.environ['SENDER_PORT'])
    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWD']

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email
    html = MIMEText(body, 'html')
    msg.attach(html)

    server_ssl = smtplib.SMTP_SSL(sender_server, sender_port)
    server_ssl.ehlo()
    server_ssl.login(sender_email, sender_password)

    server_ssl.sendmail(sender_email, to_email, msg.as_string())
    server_ssl.close()


while True:
    # TODO: read from a list to check given numbers of parking spaces
    count1, _, body1 = get_new_house_text(1)
    count2, _, body2 = get_new_house_text(2)

    title = f'New Listings ' + f"(since {LAST_FRESH_TIME})"

    count = count1 + count2
    if count == 0:
        print('script still alive', datetime.now())
    else:
        send_email('example@example.com', title, body1 + '<br>' + body2)
        # print(body1 + body2)
        LAST_FRESH_TIME = datetime.now()

    time.sleep(10 * 60)

import time
import boto3
from flask import current_app
import datetime
import arrow
import bleach

#this would take ms time
def human_date_ms(ts):
    return datetime.datetime.fromtimestamp(ts / 1000.00)

def human_date(ts):
    return datetime.datetime.fromtimestamp(ts)

def utc_now_ts():
    return int(time.time())

def utc_now_ts_ms():
    return lambda: int(round(time.time() * 1000))

def ms_stamp_humanize(ts):
    ts = datetime.datetime.fromtimestamp(ts / 1000.0)
    return arrow.get(ts).humanize()

def linkify(text):
    text = bleach.clean(text, tags=[], attributes={}, styles=[], strip=True)
    return bleach.linkify(text)

def email(to_email,subject, body_html, body_text):
    if current_app.config.get('TESTING') or not current_app.config.get('AWS_SEND_MAIL'):
        return False
    client = boto3.client('ses')
    return client.send_email(
        Source='jaza008@msn.com',
        Destination = {'ToAddresses':[to_email,]},
        Message={
            'Subject':{
                'Data': subject,
                'Charset': 'UTF-8'
                },
            'Body':{
                'Text':{
                    'Data': body_text,
                    'Charset': 'UTF-8'
                    },
                'Html':{
                    'Data': body_html,
                    'Charset': 'UTF-8'
                    },
                }
            })

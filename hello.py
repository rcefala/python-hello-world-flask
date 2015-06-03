"""Cloud Foundry test"""
from flask import Flask
from random import randint
import os
import re
import json
import psycopg2
from boto.s3.connection import S3Connection
from boto.s3.key import Key

app = Flask(__name__)

# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))

con = None

uri_regex = "postgres:\/\/(?P<username>.*):(?P<password>.*)@(?P<hostname>.*):(?P<port>.*)\/(?P<database>.*)"
services = json.loads(os.getenv('VCAP_SERVICES', None))
uri = services['PostgreSQL'][0]['credentials']['uri']
match = re.match(uri_regex, uri)


print 'trying to connect to db...'
con = psycopg2.connect(database=match.group('database'),
                       host=match.group('hostname'),
                       user=match.group('username'),
                       password=match.group('password'))

print 'going to fetch version'
cur = con.cursor()
cur.execute('SELECT version()')
ver = cur.fetchone()
print 'pg version is: %s' % ver

print 'creating table if not present'
cur.execute("CREATE TABLE IF NOT EXISTS test (id serial PRIMARY KEY, num integer);")

s3_access_key = services['amazon-s3'][0]['credentials']['access_key_id']
s3_bucket = services['amazon-s3'][0]['credentials']['bucket']
s3_secret_key = services['amazon-s3'][0]['credentials']['secret_access_key']
s3_username = services['amazon-s3'][0]['credentials']['username']

print 'trying to connect to S3...'
s3_con = S3Connection(s3_access_key, s3_secret_key)


@app.route('/')
def hello_world():
    cur = con.cursor()
    cur.execute("SELECT * FROM test;")
    pg_data = "\n".join([str(x) for x in cur.fetchall()])
    cur.close()

    bucket = s3_con.get_bucket(s3_bucket)
    s3_data = "\n".join([x.key for x in bucket.list()])

    return 'PG:\n' + pg_data + '\nS3:\n' + s3_data


@app.route('/add')
def add():
    r = randint(1, 100)
    cur = con.cursor()
    cur.execute("INSERT INTO test (num) VALUES (%s)" % r)
    cur.close()

    bucket = s3_con.get_bucket(s3_bucket)
    k = Key(bucket)
    k.key = str(r)
    k.set_contents_from_string('S3 Broker test %d' % r)

    return 'Added %d.' % r

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
    if con:
        con.close()

"""Cloud Foundry test"""
from flask import Flask
from random import randint
import os
import re
import json
import psycopg2

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


@app.route('/')
def hello_world():
    cur = con.cursor()
    cur.execute("SELECT * FROM test;")
    data = "\n".join([str(x) for x in cur.fetchall()])
    cur.close()
    return data


@app.route('/add')
def add():
    cur = con.cursor()
    cur.execute("INSERT INTO test (num) VALUES (%s)" % randint(1, 100))
    cur.close()
    return 'Added.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
    if con:
        con.close()

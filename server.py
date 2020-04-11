from flask import Flask, redirect, request
from uuid import uuid1 as uuid
app = Flask(__name__)
import psycopg2
import random
import string

short_base = 'http://127.0.0.1:5000/r/'
personal_short_base = 'http://127.0.0.1:5000/pr/'

conn = psycopg2.connect("dbname='akbarshort' user='akbar30bill' host='localhost' password='pass'")
print("to connect to the database")

def get_timestamp_query(t):
    if t == 0:
        return ' and u.create_timestamp::date == now()::date '
    elif t == 1:
        return ' and u.create_timestamp::date between (now() - interval \'1 day\')::date and (now() - interval \'2 day\')::date'
    elif t == 2:
        return ' and u.create_timestamp::date between (now() - interval \'1 day\')::date and (now() - interval \'8 day\')::date'
    elif t == 3:
        return ' and u.create_timestamp > now() - interval \'1 month\''
    return ""


def get_rand():
    rt = ''
    for i in range(random.randint(6, 10)):
        rt += string.ascii_uppercase[random.randint(0, len(string.ascii_uppercase)-1)]
    return rt
def adduser(username, password, email, conn):
    cur = conn.cursor()
    cur.execute("insert into users (user_uuid, username, password, email) values (%s, %s, %s, %s)", [str(uuid()), username, password, email])
    conn.commit()
def addurl(username, password, url, conn):
    if not url.startswith('http'): url = 'https://' + url
    cur = conn.cursor()
    cur.execute("select * from users where username=%s and password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    cur = conn.cursor()
    shorted_url = get_rand()
    cur.execute("insert into short_url (short_url_uuid, url, shorted_url, creator_uuid) values (%s, %s, %s, %s)", (str(uuid()), url, shorted_url, user[0]))
    conn.commit()
    return shorted_url
def addprefshorturl(username, password, url, pref_short, conn):
    if not url.startswith('http'): url = 'https://' + url
    cur = conn.cursor()
    cur.execute("select * from users where username=%s and password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    cur = conn.cursor()
    shorted_url = pref_short
    cur.execute("insert into short_url (short_url_uuid, url, shorted_url, creator_uuid, is_pref_short) values (%s, %s, %s, %s, true)", (str(uuid()), url, shorted_url, user[0]))
    conn.commit()
    return shorted_url
def addqueryrecord(short_url_uuid, query_user, user_agent ,conn):
    cur = conn.cursor()
    cur.execute('select * from users where username=%s', (query_user, ))
    user = cur.fetchone()
    cur = conn.cursor()
    cur.execute('insert into url_query (user_uuid, short_url_uuid, user_agent) values (%s, %s, %s)', [user[0], short_url_uuid, user_agent])
    conn.commit()
    cur.close()
def getanalytics(username, password, timestamp, conn):
    cur = conn.cursor()
    cur.execute("select * from users where username=%s and password=%s", (username, password))
    user = cur.fetchone()
    print(user)
    cur.execute(f"select count(*), u.user_uuid, u.short_url_uuid from url_query u left join short_url s on s.short_url_uuid = u.short_url_uuid where s.creator_uuid = %s {get_timestamp_query(timestamp)} group by u.user_uuid, u.short_url_uuid", (user[0],))
    res = cur.fetchall()
    print(res)
    return str(res);



@app.route("/r/<string:url>")
def unshort_url(url):
    cur = conn.cursor()
    print(url)
    cur.execute("select * from short_url where shorted_url=%s and is_pref_short=false", (url, ))
    res = cur.fetchone()
    username = request.headers['username'] if request.headers['username'] else "unknown"
    useragent = request.headers['User-Agent'] if request.headers['User-Agent'] else "unknown"
    addqueryrecord(res[0], username, useragent, conn)
    res = res[1]
    cur.close()
    return redirect(res, code='302')

@app.route("/pr/<string:url>")
def unshort_personal_url(url):
    cur = conn.cursor()
    username = request.headers['username']
    password = request.headers['password']
    cur.execute("select * from users where username = %s and password = %s", (username, password))
    user = cur.fetchone()
    cur.close()

    cur = conn.cursor()
    cur.execute("select * from short_url where shorted_url=%s and is_pref_short=true and creator_uuid=%s", (url, user[0]))
    res = cur.fetchone()
    useragent = request.headers['User-Agent'] if request.headers['User-Agent'] else "unknown"
    addqueryrecord(res[0], username, useragent, conn)
    res = res[1]
    cur.close()
    return redirect(res, code='302')

@app.route("/", methods=['POST'])
def short_url():
    url = request.form['url']
    username = request.headers['username']
    password = request.headers['password']
    return short_base + addurl(username, password, url, conn)

@app.route("/personal", methods=['POST'])
def personal_short_url():
    data = request
    url = request.form['url']
    pref_short = request.form['pref_short']
    username = request.headers['username']
    password = request.headers['password']
    return personal_short_base + addprefshorturl(username, password, url, pref_short, conn)

@app.route("/signup", methods=['POST'])
def signup():
    username = request.headers['username']
    password = request.headers['password']
    email    = request.form['email']
    adduser(username, password, email, conn)
    return "ok"

@app.route("/analytics/<int:timestamp>")
def analytics(timestamp):
    username = request.headers['username']
    password = request.headers['password']
    return getanalytics(username, password, timestamp, conn)


if __name__ == "__main__":
    app.run()

from flask import Flask
import pymysql
import os

application = Flask(__name__)
DB_NAME = ""
TABLE_NAME = "redditVisitInformation"
connection = pymysql.connect(host=os.getenv("RDS_HOSTNAME", "localhost"),
                             user=os.getenv("RDS_USERNAME", "root"),
                             password=os.getenv("RDS_PASSWORD", ""),
                             db=os.getenv("RDS_DB_NAME", "reddit"),
                             port=os.getenv("RDS_DB_NAME", 3306),
                             charset="utf8mb4",
                             cursorclass=pymysql.cursors.DictCursor)
cur = connection.cursor()

# EB looks for an 'application' callable by default.


@application.route("/")
def mainFunction():
    cur.execute("Select COUNT(*) as count from " + TABLE_NAME)
    rowCount = cur.fetchone()['count']
    print(rowCount)
    return "Hello! The current row count is: {0} rows".format(rowCount)


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()

import pymysql
import os
import praw

TABLE_NAME = "redditVisitInformation"
# Connect to the database
connection = pymysql.connect(host=os.getenv("RDS_HOSTNAME", "localhost"),
                             user=os.getenv("RDS_USERNAME", "root"),
                             password=os.getenv("RDS_PASSWORD", ""),
                             db="reddit",
                             port=int(os.getenv("RDS_PORT", 3306)),
                             charset="utf8mb4",
                             cursorclass=pymysql.cursors.DictCursor)
# get the cursor
cur = connection.cursor()

# Connect to the reddit API
reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID", ""),
                     client_secret=os.getenv("CLIENT_SECRET", "localhost"),
                     user_agent='scraper by /u/ThatGuyWhoSucksAtLOL')

# The last person data was scraped for
cur.execute("SELECT username from redditUser ORDER BY id DESC LIMIT 1;")
INITIAL_USERNAME = cur.fetchone()["username"]


# Aggregate a list of dictionaries
def aggregate_values(lod):
    toReturn = {}
    for item in lod:
        key = item.subreddit.display_name
        if key in toReturn:
            toReturn[key] = toReturn[key] + 1
        else:
            toReturn[key] = 1
    return toReturn


# Insert the user into the database
# Insert the user's aggregate data in the database
def sendAggregateDataToDatabase(aggregate, username):
    cur.execute("INSERT INTO redditUser (`username`) VALUES (%s)", username)
    prev_id = cur.lastrowid
    for key, value in enumerate(aggregate):
        cur.execute(
            "INSERT INTO redditVisitInformation (`redditUser_id`, `subreddit`, `amount`) VALUES (%s, %s, %s)", (prev_id, value, aggregate[value]))
    connection.commit()


# Get the total aggregates (comments and posts) for a user
# Return the sum of the two dictionaries
def getTotalAggregates(username):
    comments = reddit.redditor(username).comments.new(limit=None)
    submissions = reddit.redditor(username).submissions.top('all')
    aggregateComments = {}
    aggregateSubmissions = {}
    try:
        aggregateComments = aggregate_values(comments)
    except Exception as e:
        print(e)
    try:
        aggregateSubmissions = aggregate_values(submissions)
    except Exception as e:
        print(e)
    return({k: aggregateComments.get(k, 0) + aggregateSubmissions.get(k, 0) for k in set(aggregateComments) | set(aggregateSubmissions)})


# Check if a user exists in the database
def existsInDB(username):
    cur.execute(
        "SELECT IF(COUNT(*) >0, TRUE,FALSE) as response FROM redditUser WHERE username='{0}';".format(username))
    return bool(cur.fetchone()["response"])


# Get the top people who have posted in a given subreddit for the past month
def getTopPosters(subreddit):
    topPostsForMonth = reddit.subreddit(subreddit).top("month")
    topPostersForMonth = []
    for post in topPostsForMonth:
        if post.author is None:
            continue
        topPostersForMonth.append(post.author.name)
    return set(topPostersForMonth)


# Run the process for a user
# The process is as follows:
#   Get the aggregate info for a user
#   If the user exists in the database don't send the data
#   If the user doesn't exist in the database
#   Go through the list of their subreddits
#       and get the top posters for that subreddit
#   For each person in the top posters list, run the process
def runProcess(user):
    print("Get aggregate for: {0}".format(user))
    agg = getTotalAggregates(user)
    if not existsInDB(user):
        sendAggregateDataToDatabase(agg, user)
        print("Send aggregate to database")
    for key, value in enumerate(agg):
        if value > 10:
            print("Get top posters for: {0}".format(value))
            tops = getTopPosters(value)
            counter = 0
            for person in tops:
                if person == user or existsInDB(person):
                    continue
                if counter > 10:
                    print("10 LIMIT REACHED MOVE ON!")
                    break
                else:
                    print("kickoff new process")
                    counter += 1
                    runProcess(person)

# Kickoff the process
runProcess(INITIAL_USERNAME)

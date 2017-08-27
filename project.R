library("recommenderlab")
library(RMySQL)


# Connect to the database
con <- dbConnect(MySQL(),
    user = Sys.getenv("RDS_USERNAME"),
    password = Sys.getenv("RDS_PASSWORD"),
    host = Sys.getenv("RDS_HOSTNAME"),
    dbname=Sys.getenv("RDS_DB_NAME"),
    port=as.numeric(Sys.getenv("RDS_PORT"))) # Connect to database

# Query to get all info from database
initialQuery <- "select * from redditUser rU JOIN redditVisitInformation rvi on rvi.redditUser_id=rU.id;"

# Get the user to run the recommendation algorithm for
args <- commandArgs(trailingOnly = TRUE)
usernameToRecommend = ifelse(is.na(args[1]), "ThatGuyWhoSucksAtLOL", args[1])

# Get the data as a data frame
redditDataFrame = data.frame(dbGetQuery(con, initialQuery))

# The maximum amount of posts and comments for any user
maxAmount = max(redditDataFrame$amount)

# Get the rating matrix from a data frame
getRatingMatrix <- function(df) {
	df$subreddit.rating <- sapply(df$amount, function(x){
		return(x/maxAmount)

	})
	cols.dont.want = c("id.1", "redditUser_id", "id", "amount")
	return(as(df[, ! names(df) %in% cols.dont.want, drop = F], "realRatingMatrix"))
}

# Get a training data set for the rating matrix
# It gets the data for every person except the person to be recommended for
getTrainingData <- function(ratingMatrix, indexToRemove) {
	rowCount <- dim(ratingMatrix)[1]
	goodSeq <- which(1:rowCount != indexToRemove)
	return(ratingMatrix[goodSeq])
}

# Get the index in the rating matrix given a username
getIndexOfUsername <- function(username, ratingMatrix) {
	return(which(dimnames(ratingMatrix)[[1]]==username, arr.ind = T))
}

# Get the prediction for a user given data and training data
# Recommend using user based collaborative filtering
getRecommendation <- function(trainingData, data, indexOfUser) {
	rec <- Recommender(trainingData, method = "UBCF")
	pre <- predict(rec, data[indexOfUser], n = 30)
	return(pre)
}

redditRatingMatrix <- getRatingMatrix(redditDataFrame)
indexOfUser <- getIndexOfUsername("ThatGuyWhoSucksAtLOL", redditRatingMatrix)
trainingData <- getTrainingData(redditRatingMatrix, indexOfUser)
recommendation <- getRecommendation(trainingData, redditRatingMatrix, indexOfUser)

# Make a list version of the data
list.version <- as(recommendation, "list")

# Get the ratings for the recommendation
ratings <- getRatings(recommendation)
df = data.frame(subreddit=character(), likelyAmountOfCommentsAndPosts=numeric(0))
# For the thirty recommendations, normalize the data
for(i in 1:30) {
	df = rbind(df, data.frame(subreddit = list.version[[1]][i], likelyAmountOfCommentsAndPosts=maxAmount*ratings[[1]][i]))
}

# Print the recommendations
print(df)

# print(methods(class=class(recommendation)))


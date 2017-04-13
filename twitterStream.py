from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import operator
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def main():
    conf = SparkConf().setMaster("local[2]").setAppName("Streamer")
    sc = SparkContext(conf=conf)
    ssc = StreamingContext(sc, 10)   # Create a streaming context with batch interval of 10 sec
    ssc.checkpoint("checkpoint")

    pwords = load_wordlist("positive.txt") #reading the words from the files and converting to a list
    nwords = load_wordlist("negative.txt")

    
   
    counts = stream(ssc, pwords, nwords, 100)
    make_plot(counts)
    


def make_plot(counts):
    """
    Plot the counts for the positive and negative words for each timestep.
    Use plt.show() so that the plot will popup.
    """
    # YOUR CODE HERE
    print counts
    p_list =[]
    n_list = []
    for i in counts:
        if len(i)!=0:
                p_list.append(i[0][1])
                n_list.append(i[1][1])

    x=[]
    for i in range(0,len(p_list)):
        x.append(i)
    #print p_list
    #print n_list
    #print x
    plt.xlabel("time step")
    plt.ylabel("word count")
    
    #blue_patch = mpatches.Patch(color='blue', label='positive')
    #plt.legend(handles=[blue_patch])

    #green_patch = mpatches.Patch(color='green', label='negative')
    #plt.legend(handles=[green_patch])


    plt.plot(x,p_list,'b',marker='o',label="positive")
    plt.plot(x,n_list,'g',marker='o',label="negative")

    plt.legend(loc="upper left")
    plt.show()
    plt.savefig("twitter.png");




def load_wordlist(filename):
	
    """ 
    This function should return a list or set of words from the given filename.
    """
    # YOUR CODE HERE
    with open(filename) as f:
    	lines = f.read().splitlines() #splitting the data according line by line
    return lines

def detect(word,pwords,nwords):
    if word in pwords:
        return ("positive",1)
    elif word in nwords:
        return ("negative",1)
    else:
        return ("neutral",1)

def updateFunction(newValues, runningCount):
    if runningCount is None:
        runningCount = 0
    return sum(newValues, runningCount)

def separate_neutral(x):
    if(x[0]=="neutral"):
        return False
    else:
        return True

def stream(ssc, pwords, nwords, duration):
    kstream = KafkaUtils.createDirectStream(
        ssc, topics = ['twitterstream'], kafkaParams = {"metadata.broker.list": 'localhost:9092'})
    tweets = kstream.map(lambda x: x[1].encode("ascii","ignore"))
    words = tweets.flatMap(lambda line:line.split(" ")) #splitting the input stream into words to compare with positive and negative lists
    pairs = words.map(lambda word : detect(word,pwords,nwords)) #counting the number of positive negative and neutral words
    #pairs.pprint()
    new_pairs = pairs.filter(separate_neutral) #filtering out the neutral words
    #new_pairs.pprint()

    wordcounts = new_pairs.reduceByKey(lambda x,y: x+y) #aggregating the sum of positive and negative words


    #runningCounts = pairs.reduceByKey(lambda x,y: x+y)
    #wordcounts.pprint()
    #runningCounts.pprint()
    # Each element of tweets will be the text of a tweet.
    # You need to find the count of all the positive and negative words in these tweets.
    # Keep track of a running total counts and print this at every time step (use the pprint function).
    # YOUR CODE HERE
    runningCounts = new_pairs.updateStateByKey(updateFunction) #updating the running counts with respect to incoming data
    
    runningCounts.pprint() #printing the running count of positive and negative numbers
    
    # Let the counts variable hold the word counts for all time steps
    # You will need to use the foreachRDD function.
    # For our implementation, counts looked like:
    #   [[("positive", 100), ("negative", 50)], [("positive", 80), ("negative", 60)], ...]
    counts = []
    
    wordcounts.foreachRDD(lambda t,rdd: counts.append(rdd.collect()))
    
    ssc.start()                         # Start the computation
    ssc.awaitTerminationOrTimeout(duration)
    ssc.stop(stopGraceFully=True)

    return counts


if __name__=="__main__":
    main()

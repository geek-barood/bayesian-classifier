import tweepy
import unicodedata
from nltk import stem
import keys
import math

consumer_key = keys.my_consumer_key
consumer_secret = keys.my_consumer_secret
access_token = keys.my_access_token
access_token_secret = keys.my_access_token_secret

stopwords = set()

# stores the number of tweets for a particular category in the training data
categories = {'Politics':0, 'Sports':0}

# stores the frequency of words found in the entire training data and put them
# in their respective category bucket so word_in_category['Politics']['alien'] = 4 and
# word_in_category['Sports']['alien'] = 1 means there are four 'alien' words which
# are categorized as 'Politics' and one 'alien' word which is categorized as 'Sports'
# in the entire training data-set.
word_in_category = {'Politics':{}, 'Sports':{}}

# lmtzr = WordNetLemmatizer() # turns out that the performance is worse than a stemmer
stemmer = stem.snowball.EnglishStemmer()


def slugify(word):
    word = unicode(word)
    word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode('ascii')
    return word.strip().lower()


def train(category, input_path):
    cnt = 0
    print 'Starting training...'
    with open(input_path, 'r') as f:
        for line in f.readlines():
            _train(category, line.split())
            cnt += 1

    print 'Finished training! {0} tweets processed for training.'.format(cnt)


def test_train():
    _train('Politics', 'This is a political crime'.split())
    _train('Politics', 'The party says they won\'t vote for him'.split())
    _train('Politics', 'The governer said to the president'.split())
    _train('Politics', 'The president resigns from the parliament'.split())
    _train('Politics', 'That political party is corrupt'.split())
    _train('Politics', 'vote for the nationalist party'.split())

    _train('Sports', 'That sport person is an artist'.split())
    _train('Sports', 'He\'s an excellent player'.split())
    _train('Sports', 'The team\'s score has been quite dismal'.split())
    _train('Sports', 'The coach asked their team to regroup'.split())
    _train('Sports', 'The team lost by 4 goals'.split())
    _train('Sports', 'Aniruddha is the best soccer player'.split())


def _train(category, list_words):
    global categories, word_in_category
    for word in list_words:
        word = stemmer.stem(word.lower().strip())
        if word in word_in_category[category].keys():
            word_in_category[category][word] += 1
        else:
            word_in_category[category][word] = 1

    categories[category] += 1

def each_word(line, stopwords=set()):
    """
    :param line: a string
    :param stopwords: a set of words which are to be ignored
    :return: a list of stemmed words which are not in stopwords and which are present in the line string
    """
    word_list = [slugify(word) for word in line.split() if len(slugify(word)) > 0]
    return [stemmer.stem(word) for word in word_list if word not in stopwords]


def classify(tweet):
    """
    Takes a tweet object or a string and classifies it as one of the categories
    :param tweet: a tweet object or a string object
    :return: string which the tweet is classified as
    """
    if not isinstance(tweet, str):
        text = tweet.text
    else:
        text = tweet

    # initially we don't have a max score
    max_score = None

    # initially we do not classify this tweet
    res_cat = None

    # extract the words from the tweet
    words_in_tweet = set(each_word(text, stopwords))

    for cat in categories.keys():
        score = 0.0 # ln(1.0) = 0

        for word in words_in_tweet:
            if word in word_in_category[cat].keys():
                # this translates to score *= (word_in_category[cat][word]+1)/categories[cat]
                score += math.log(word_in_category[cat][word]+1.0) - math.log(categories[cat])
            else:
                # this translates to score *= 1/categories[cat] in log form
                score -= math.log(categories[cat])

        # this translates to number of tweets in the training data divided by total number of tweets in the training data
        score += math.log(categories[cat]) - math.log(categories['Sports']+categories['Politics'])

        #print 'Prob that the current tweet is in \'{0}\' category: {1}'.format(cat, curr_prob)
        if score > max_score or max_score is None:
            max_score = score
            res_cat = cat

    print '[{0}]'.format(res_cat), text

    return res_cat


def generate_training_data(api, path_politics, path_sports):
    print 'Generating training data from the web...'
    with open(path_politics, 'w+') as f:
        # for politics related tweets
        for tweet in api.user_timeline('@BBCPolitics', count=200):
            print 'Trying to add - ', repr(tweet.text)
            filtered_words = each_word(tweet.text)
            if len(filtered_words) > 0:
                f.write(' '.join(filtered_words) + '\n')

    with open(path_sports, 'w+') as f:
        # for sports related tweets
        for tweet in api.user_timeline('@TwitterSports', count=200):
            print 'Trying to add - ', repr(tweet.text)
            filtered_words = each_word(tweet.text)
            if len(filtered_words) > 0:
                f.write(' '.join(filtered_words) + '\n')

    print 'Finished generating training data!'


def classify_local_tweets():
    test_data = []
    with open('/home/aniruddha/coding/twitminer-contest/code/politics_validated.txt', 'r') as f:
        test_data = f.read().split('\n')

    total_sports = 0
    total_politics = 0
    for data in test_data:
        if (len(data)>10):
            if classify(data) == 'Politics':
                total_politics += 1
            else:
                total_sports += 1

    print 'Sports:', total_sports, 'Politics:', total_politics, 'Total:', total_sports+total_politics


def test_online_sports_tweets(api):
    # classifying SkySports to be fair
    total_sports = 0
    total_politics = 0
    for tweet in api.user_timeline('@SkySports', count=200):
        if classify(tweet) == 'Politics':
            total_politics += 1
        else:
            total_sports += 1

    print 'Sports:', total_sports, 'Politics:', total_politics, 'Total:', total_sports+total_politics


def test_online_politics_tweets(api):
    # classifying @HuffPostPol to be fair
    total_sports = 0
    total_politics = 0
    for tweet in api.user_timeline('@HuffPostPol', count=200):
        if classify(tweet) == 'Politics':
            total_politics += 1
        else:
            total_sports += 1

    print 'Sports:', total_sports, 'Politics:', total_politics, 'Total:', total_sports+total_politics


def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    words = []
    with open('resources/stopwords.txt') as f:
        for line in f.readlines():
            words.extend([slugify(w) for w in line.split() if len(w)>0])

    global stopwords
    stopwords = set(words)

    generate_training_data(api, 'data/politics.txt', 'data/sports.txt')


    train('Politics', 'data/politics.txt')
    train('Sports', 'data/sports.txt')

    print '[Classification starts for politics]'
    test_online_politics_tweets(api)
    print '[Classification ends for politics]'
    print '-' * 80
    print '[Classification starts for sports]'
    test_online_sports_tweets(api)
    print '[Classification ends for sports]'


def test_main():
    test_train()
    print word_in_category['Politics'].keys()
    print word_in_category['Sports'].keys()
    print classify('which excellent game or sport should you play?')
    print classify('I will vote for AAP if BJP resigns')
    print classify('The football team joins politics')
    print classify('They say they will join some other party')
    print classify('Aniruddha is retiring!')

if __name__ == '__main__':
    main()
    #test_main()
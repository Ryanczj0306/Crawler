import re
from urllib.parse import urlparse,urldefrag,urljoin
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import nltk
import urllib.robotparser


from collections import defaultdict

stopwords_en = set(stopwords.words('english')) # To avoid stop words when tokenize, we first create a set of stopwords
stopwords_punctuation = stopwords_en.union(set(string.punctuation)) # merge set together  

longest_page = None
longest_url = None


urlSet = set()  # set of unique pages

word_freq = defaultdict(int)   #count the 50 most common words
subdomains = defaultdict(int)   #count the frequency of subdomains of ics.uci.edu
uci_count = 0  # number of pages of subdomains of ics.uci.edu

robot_dict = dict()  # store the urllib.robotparser.RobotFileParser() for the robot.txt of each domain url

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    
    global uci_count
    global longest_page
    global longest_url                                                                           ###########
    links = []
    if resp.status != 200:  # only process successful pages
        return links
    if resp.raw_response == None:  # avoid no content pages
        return links
    
    if resp.raw_response.content:    
        
        if not url + '/' == resp.raw_response.url:
            if resp.raw_response.url.endswith('/'):
                resp.raw_response.url = resp.raw_response.url[:-1]
            if not is_valid(resp.raw_response.url):       ########## check redirection to domains outside
                return []
                
        if len(resp.raw_response.content) > 6000000:    ######## detect large files
            return []
                
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        
        count = 0
        total_count = 0
        
        temp_freq = defaultdict(int)  # temp dict
        
        for line in soup.stripped_strings:
            word_list = word_tokenize(line) # tokenize 
            total_count += len(word_list)
            for word in word_list:
                if not word in stopwords_punctuation:  # remove stopwords
                    if word.isascii():
                        if word[-1].isalnum():
                            temp_freq[word] += 1
                            count += 1   # count total number of words
                    
        if longest_page == None or longest_page < total_count:  # update longest page
            longest_page = total_count
            longest_url = url
            
        if count <= 50:   # filter out low information pages
            return []
        else:
            for key in temp_freq.keys():    
                word_freq[key] += temp_freq[key]  # update word frequency
    
        for link in soup.find_all('a'):
            real_link = link.get('href')  # extract urls
            if real_link is not None:
                if is_valid(real_link):
                    real_link = urldefrag(real_link)[0]  # discard fragment
                    real_link = urljoin(resp.raw_response.url,real_link)   # get the absolute url address
                    if "/events/" in real_link or "share=" in real_link or "action=" in real_link or "replytocom=" in real_link or "filter%" in real_link or "/pdf/" in real_link or "/publications/" in real_link:  # avoid traps
                        continue
                                        
                    if not real_link in urlSet:   # only add unique pages
                        
                        parse = urlparse(real_link)
                            
                        links.append(real_link)
                        urlSet.add(real_link)
                        
                        if parse.netloc.endswith(".ics.uci.edu") or parse.netloc == "ics.uci.edu":  # count ics subdomain
                            
                            uci_count += 1
                            subdomains[parse.scheme + "://" + parse.netloc] += 1
    
    return links
    

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global robot_dict
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not parsed.netloc.endswith(".ics.uci.edu") and not parsed.netloc.endswith(".cs.uci.edu") and not parsed.netloc.endswith(".informatics.uci.edu") and not parsed.netloc.endswith(".stat.uci.edu") and not parsed.netloc == "ics.uci.edu" and not parsed.netloc == "cs.uci.edu" and not parsed.netloc == "informatics.uci.edu" and not parsed.netloc == "stat.uci.edu":
            if not parsed.netloc == "today.uci.edu":   # exclude urls that are not within the domains we want to crawl
                return False
            else:
                if not parsed.path.startswith("department/information_computer_sciences") and not parsed.path[1:].startswith("department/information_computer_sciences"):
                    return False
        try:
            rp = urllib.robotparser.RobotFileParser()          ##### code from python documentation: 
                                                               ##### https://docs.python.org/3/library/urllib.robotparser.html

            robot_url = parsed.scheme + '://' + parsed.netloc + '/robots.txt'
            if robot_url not in robot_dict:
                rp.set_url(robot_url)
                rp.read()
                robot_dict[robot_url] = rp
                
            if not robot_dict[robot_url].can_fetch("*",url):
                return False
        except:
            pass

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ppsx)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

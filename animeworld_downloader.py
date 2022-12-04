import sys # Need it to use command line argument or stop the program
import requests # Need it to make http request
from bs4 import BeautifulSoup # Need it to work easier with html page
from multiprocessing import cpu_count # Just the cpu_count of the machine
from multiprocessing.pool import ThreadPool # Need it to have parallel download
from tqdm import tqdm

# Default function where it finds espisodes and download them
def main():
    # Ask user for the link and how many simultaneos download
    url_thread = greetings()
    url = url_thread[0]
    thread_num = url_thread[1]

    # Start of the 'real program'
    create_files()
    soup = parse_page(url)
    find_episodes(soup)
    download_episodes(thread_num)

def greetings():
    # Colored version of the AnimeWorld name
    print("\n\033[1;30m▄▖  ▘     \033[1;36m▖  ▖    ▜  ▌\033[1;30m  ▄        ▜      ▌\033[1;0m")
    print("\033[1;30m▌▌▛▌▌▛▛▌█▌\033[1;36m▌▞▖▌▛▌▛▘▐ ▛▌\033[1;30m  ▌▌▛▌▌▌▌▛▌▐ ▛▌▀▌▛▌█▌▛▘\033[1;0m")
    print("\033[1;30m▛▌▌▌▌▌▌▌▙▖\033[1;36m▛ ▝▌▙▌▌ ▐▖▙▌\033[1;30m  ▙▘▙▌▚▚▘▌▌▐▖▙▌█▌▙▌▙▖▌\033[1;0m\n")

    url = input("Inserisci il link del Anime da scaricare: ")
    thread_num = input("\nInserisci il numero di download simultanei: ")
    return [url, thread_num]

# Function that create the files and remove everything inside of them if used in the past
def create_files():
    dlink = open(".download_link.txt", "w")
    dlink.close()
    elink = open(".episode_link.txt", "w")  
    elink.close()

# Parse the page through BeautifulSoup and return it
def parse_page(url):
    #print(f"parse_page " + url)
    page = requests.get(url) 
    if page.status_code == requests.codes.ok:
        soup = BeautifulSoup(page.content, "lxml")
        #print(f"parsed_page Title " + soup.find("title").string) ## debug
        return soup 
    else: # If page send error, print in red
        print("\n\033[1;31mErrore: Link errato!\n")
        sys.exit(0)

# Function to get the link of episodes from the web page
def find_episodes(soup1):
    # Look up the <div> element that have every episode link inside
    list_episodes = soup1.find("div", class_="server active")
    # Find the download link for each episode
    find_all_download_link(list_episodes)

def find_all_download_link(list_episodes):
    # File where it writes the link of the episodes
    elink = open(".episode_link.txt", "a")  
    # File where it writes the download link of the episodes
    dlink = open(".download_link.txt", "a")
    # For each a element in the <li> tag
    print("\nFinding the episodes' links to download...\n")
    for a in list_episodes.find_all("a"):
        # Assemble the link and add "\n" to save links one under the other
        link_episode = "https://www.animeworld.tv" + a["href"] + "\n"
        # Append the link inside the file
        elink.write(link_episode)
        #print(f"episode link: " + link_episode.strip())
        # Find the link to download the file of the webpage just written in the elink file
        download_link(parse_page(link_episode.strip()), dlink)
    elink.close()
    dlink.close()

# Function to get the link to download the episode from the page
def download_link(soup2, dlink):
    #print(f"find_download_link " + soup2.find("title").string) ## debug
    # Find the link
    download_link = soup2.find(id = 'alternativeDownloadLink').get("href") #link del download
    # save the link inside a file
    dlink.write(download_link + "\n")
    #print(download_link)

# Create a list from the file
def download_list():
    # Open the file to read the download link
    dlink = open(".download_link.txt", "r")
    # Read the file
    file_links = dlink.read()
    # Create the list
    links = []
    # For each line in the file it append it inside the list
    for link in file_links.split("\n"):
        links.append(link.strip())
    dlink.close()
    links.pop() # Remove the last element ''
    return links

def download_file(link):
    # Create the simpler name for saving
    name = "download/" + link[link.rfind("/")+1:]
    # Start the download
    r = requests.get(link, stream=True)
    if r.status_code == requests.codes.ok: # Rrequest went through without errors
        # Find the size of the file downloading
        total_size_in_bytes= int(r.headers.get('content-length', 0))
        # Give the right dimension to the progress bar
        progress_bar = tqdm(total=total_size_in_bytes, 
                            unit='iB', 
                            unit_scale=True,
                            desc=link[link.rfind("/")+1:])
        # Start the download writing the bytes on the file
        with open(name, 'wb') as f:
            for data in r:
                # Update the progress bar
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close() # Close the progress bar when finished

# Function that download all episodes found
def download_episodes(thread_num):
    # Create the list from the file link
    links_list = download_list()
    #print(links_list)
    # Start the parallel download
    results = ThreadPool(int(thread_num)).imap(download_file, links_list)
    # Print "Download" Complete after every donwload
    for x in results:
       print ("Download complete!", end='\r')

# Start the all program with the main function
if __name__ == "__main__":
    main()
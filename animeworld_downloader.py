import sys # Need it to use command line argument or stop the program
import os # Need it to look up at files before donwloading them twice
import requests # Need it to make http request
from bs4 import BeautifulSoup # Need it to work easier with html page
from multiprocessing import cpu_count # Just the cpu_count of the machine
from multiprocessing.pool import ThreadPool # Need it to have parallel download
from tqdm import tqdm
from colorama import init, Fore as F, Back as B, Style as S # Need it to color the output
from pathlib import Path # Need it to check if the path exists

init(convert=True)

# class for colors
class C:
    # Alias for fast usage colors and resets
    CFR = F.RED
    CFG = F.GREEN
    CFY = F.YELLOW
    CFB = F.BLUE
    CFM = F.MAGENTA
    CFC = F.CYAN
    CFW = F.WHITE
    RST = S.RESET_ALL

    # Alias for fast usage of light colors in F
    CFRL = F.LIGHTRED_EX
    CFGL = F.LIGHTGREEN_EX
    CFYL = F.LIGHTYELLOW_EX
    CFBL = F.LIGHTBLUE_EX
    CFML = F.LIGHTMAGENTA_EX
    CFCL = F.LIGHTCYAN_EX
    CFWL = F.LIGHTWHITE_EX
    CFBKL = F.LIGHTBLACK_EX

#def a function to ask for an integer an return it
def ask_int(question : str) -> int:
    while True:
        try:
            return int(input(question))
        except ValueError:
            print(f"{C.CFR}Errore: Inserisci un numero intero!{C.RST}")

# def a function to ask for a path, checking it and return it
def ask_path(question : str) -> Path:
    while True:
        try:
            path = Path(input(question))
            if not path.exists():
                print(f"{C.CFY}Errore: Percorso non trovato, provo a crearlo{C.RST}")
                path.mkdir()
            if not path.is_dir():
                raise Exception
            
            return path
        except:
            print(f"{C.CFR}Errore: Percorso non valido!{C.RST}")

def get_Path_path(path: str) -> Path:
    path = Path(path)
    if not path.exists():
        print(f"{C.CFY}Errore: Percorso non trovato, provo a crearlo{C.RST}")
        path.mkdir()
    if not path.is_dir():
        return ask_path("Inserisci il percorso dove salvare i file: ")
    
    return path


def greetings():
    # Colored version of the AnimeWorld name
    print()
    print(f"{C.CFBKL}▄▖  ▘     {C.CFC}▖  ▖    ▜  ▌{C.CFBKL}  ▄        ▜      ▌{C.RST}")  
    print(f"{C.CFBKL}▌▌▛▌▌▛▛▌█▌{C.CFC}▌▞▖▌▛▌▛▘▐ ▛▌{C.CFBKL}  ▌▌▛▌▌▌▌▛▌▐ ▛▌▀▌▛▌█▌▛▘{C.RST}")
    print(f"{C.CFBKL}▛▌▌▌▌▌▌▌▙▖{C.CFC}▛ ▝▌▙▌▌ ▐▖▙▌{C.CFBKL}  ▙▘▙▌▚▚▘▌▌▐▖▙▌█▌▙▌▙▖▌{C.RST}")
    print()


# Class that will download the episodes
class AnimeWorldDownloader():
    def __init__(self, url=None, thread_num=None, download_path=None):
        greetings()
        if url:
            print(f"{C.CFG}Link inserito: {C.CFW}{url}{C.RST}")
        self.url = url if url else input("Inserisci il link del Anime da scaricare: ")
        print()
        if thread_num:
            print(f"{C.CFG}Numero di download simultanei: {C.CFW}{thread_num}{C.RST}")
        self.thread_num = thread_num if thread_num else ask_int("Inserisci il numero di download simultanei: ")
        print()
        if download_path:
            print(f"{C.CFG}Percorso inserito: {C.CFW}{download_path}{C.RST}")
        self.download_path = get_Path_path(download_path) if download_path else ask_path("Inserisci il percorso dove salvare i file: ")
        print()

        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}

    def start(self):
        # create/initialize the files and put path in self.elink and self.dlink
        self.create_files()
        # parse page and retrieve the soup
        soup = self.parse_page()
        # parse soup finding all link, and write them in the files
        self.find_episodes(soup)

        self.download_episodes()
    
    # Method that create the files and remove everything inside of them if used in the past
    def create_files(self):
        # create/overwrite the file where it will write the link of the episodes
        self.elink = self.download_path / ".episode_link.txt"
        self.dlink = self.download_path / ".download_link.txt"
        self.elink.touch()
        self.elink.write_text("")
        self.dlink.touch()
        self.dlink.write_text("")
        
    # Parse the page through BeautifulSoup and return it
    def parse_page(self):
        #print(f"parse_page " + url)
        page = requests.get(self.url, headers=self.headers) 
        if page.status_code == requests.codes.ok:
            soup = BeautifulSoup(page.content, "lxml")
            print(f"parsed_page\n" + page.text) ## debug
            return soup
            
        else: # If page send error, print in red
            print(f"\n{C.CFR}Errore: Link errato!{C.RST}\n")
            sys.exit(1)

    # Function to get the link of episodes from the web page
    def find_episodes(self, soup):
        # Look up the <div> element that have every episode link inside
        list_episodes = soup.find("div", class_="server active")

        if not list_episodes:
            print(f"\n{C.CFR}Errore: Nessun episodio trovato!{C.RST}\n")
            sys.exit(1)
        # Find the download link for each episode
        self.find_all_download_link(list_episodes)

    def find_all_download_link(self, list_episodes):

        with self.elink.open("a") as elink:
            # episode_link  - File where it writes the link of the episodes
            # download_link - File where it writes the download link of the episodes

            # For each a element in the <li> tag
            print("\nCercando i link degli episodi da scaricare...\n")
            for a in list_episodes.find_all("a"):
                # Assemble the link and add "\n" to save links one under the other
                link_episode = "https://www.animeworld.tv" + a["href"] + "\n"
                # Append the link inside the file
                elink.write(link_episode)
                #print(f"episode link: " + link_episode.strip())
                # Find the link to download the file of the webpage just written in the elink file
                self.download_link(self.parse_page(link_episode.strip()))

    # Function to get the link to download the episode from the page
    def download_link(self,soup2):
        #print(f"find_download_link " + soup2.find("title").string) ## debug
        # Find the link
        download_link = soup2.find(id = 'alternativeDownloadLink').get("href") #link del download
        # save the link inside a file
        self.dlink.open("a").write(download_link + "\n")
        #print(download_link)

    # Function that download all episodes found
    def download_episodes(self):
        # Create the list from the file link
        links_list = self.download_list()
        #print(links_list)
        # Start the parallel download
        results = ThreadPool(self.thread_num).imap(download_file, links_list)
        # Print "Download complete" Complete after every donwload
        for x in results:
            print ("Download complete!\r", end='\r')

    # Create a list from the file
    def download_list(self) -> list:
        
        # get list of download from .download_link.txt as list of rows
        links = [l.strip() for l in self.dlink.read_text.split("\n") if l.strip() != ""]
        
        return links

    def download_file(self, link):
        # name of the file
        name = self.create_folder(link)
        # Check if the file exist
        if name.exists():
            return
        else: # if the files doesn't exist it will downlaod it
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
                with  name.open('wb') as f:
                    for data in r:
                        # Update the progress bar
                        progress_bar.update(len(data))
                        f.write(data)
                progress_bar.close() # Close the progress bar when finished

    def create_folder(self, link):
        #check if folder download exists

        # create anime folder if not exists and save it in a variable
        if getattr(self, "anime_folder", None) is None:
            name_folder = link[link.rfind("/")+1:link.find("_")]
            self.anime_folder = self.download_path / name_folder
            self.anime_folder.mkdir(parents=True, exist_ok=True)
        
        # create episode name
        name_file = link[link.rfind("/")+1:]
        name = self.anime_folder / name_file

        return name


# Default function where it finds espisodes and download them
def main():
    # Ask user for the link and how many simultaneos download
    AW = AnimeWorldDownloader("https://www.animeworld.tv/play/bleach-ita.Jd55r", 5, "C:\\Users\\raikoug\\Downloads\\Anime")
    AW.start()

    
    # Start of the 'real program'
    
    
    

# Start the all program with the main function
if __name__ == "__main__":
    main()
import requests
import multiprocessing
import time
from tff_match_detail import Scrape

session = None


def set_global_session():
    global session
    if not session:
        session = requests.Session()


def scrape_data(id):
    scrape = Scrape()
    scrape.get_match(id[0], id[1])


def download_site(match_id):
    url = f"https://www.tff.org/Default.aspx?pageId=29&macId={match_id}"
    with session.get(url) as response:
        name = multiprocessing.current_process().name
        print(f"{name}:Read {len(response.content)} from {url}")


def download_all_sites(ids):
    with multiprocessing.Pool(initializer=set_global_session) as pool:
        pool.map(scrape_data, ids)


if __name__ == "__main__":

    w1 = [
        ("207154", "3221071"),
        ("207155", "3221072"),
        ("207156", "3221073"),
        ("207157", "3221069"),
        ("207158", "3221068"),
        ("207159", "3221066"),
        ("207160", "3221070"),
        ("207161", "3221074"),
        ("207162", "3221067")]

    w2 = [
        ("207163", "3221085")
        ("207164", "3221086"),
        ("207165", "3221087"),
        ("207166", "3221088"),
        ("207167", "3221089"),
        ("207168", "3221090"),
        ("207169", "3221091"),
        ("207170", "3221092"),
        ("207171", "3221093")]

    w1 = [
        ("", ""),
        ("", ""),
        ("", ""),
        ("", ""),
        ("", ""),
        ("", ""),
        ("", ""),
        ("", ""),
        ("", "")]

    #id = ids[0]
    #scrape = Scrape()
    #scrape.get_match("207159", "3221066")

    # sites = [
    #    "https://www.jython.org",
    #    "http://olympus.realpython.org/dice",
    # ] * 80
    start_time = time.time()
    download_all_sites(ids)
    duration = time.time() - start_time
    print(f"Downloaded {len(ids)} in {duration} seconds")

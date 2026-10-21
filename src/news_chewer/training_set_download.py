import argparse
import csv
import logging
import os
import ollama_client
import fetcher
import extractor

# Configure basic logging to stderr so progress/errors don't corrupt CSV output
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUT_FILE = "articles_for_rating.csv"


def get_rss_articles(fetcher, extractor) -> list[tuple[str, str]]:
    """Fetch the RSS feeds and return a list of (title, url) tuples."""
    urls = []
    feed_urls = [
        #"https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", # main feed
        #"https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en" # world feed
        #"https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNRFJyZDJoakVnSmxiaWdBUAE?hl=en-US&gl=US&ceid=US:en" # US midterms
        #"https://news.google.com/rss/topics/CAAqKAgKIiJDQkFTRXdvTkwyY3ZNVEZyTlRob2FISnlhQklDWlc0b0FBUAE?hl=en-US&gl=US&ceid=US:en" # AI Safety
        #"https://news.google.com/rss/search?q=us%20diseases%20and%20health&hl=en-US&gl=US&ceid=US%3Aen" # US disease and health
        #"https://news.google.com/rss/search?q=nato%20stability%20and%20western%20cooperation%20and%20alliances+after:2026-01-01&hl=en-US&gl=US&ceid=US%3Aen"
        #"https://news.google.com/rss/search?q=rise%20of%20european%20far%20right%20parties+after:2026-01-01&hl=en-US&gl=US&ceid=US%3Aen"
        #"https://news.google.com/rss/topics/CAAqKAgKIiJDQkFTRXdvTkwyY3ZNVEZpZDJSa2VYbGljeElDWlc0b0FBUAE?hl=en-US&gl=US&ceid=US%3Aen"
        #"https://news.google.com/rss/topics/CAAqKAgKIiJDQkFTRXdvTkwyY3ZNVEZtTlRSeloyWjBkQklDWlc0b0FBUAE?hl=en-US&gl=US&ceid=US%3Aen"
        #"https://news.google.com/rss/search?q=US%20china%20technology%20competition+after:2026-01-01&hl=en-US&gl=US&ceid=US%3Aen&num=35"
        #"https://news.google.com/rss/search?q=israel%20gaza%20syria%20lebanon+after:2026-03-01&hl=en-US&gl=US&ceid=US%3Aen"
        #"https://news.google.com/rss/search?q=civil+unrest+france+after:2026-01-01&hl=en-US&gl=US&ceid=US%3Aen",
        #"https://news.google.com/rss/search?q=sports+after:2026-03-01&hl=en-US&gl=US&ceid=US%3Aen",
        #"https://news.google.com/rss/search?q=entertainment%20movies%20celebrities+after:2026-03-01&hl=en-US&gl=US&ceid=US%3Aen",
        #"https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen",
        "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR2RmWm13U0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US%3Aen",
        "https://news.google.com/rss/search?q=Tech%20product%20announcements%20and%20launches+after:2026-03-01&hl=en-US&gl=US&ceid=US%3Aen"
    ]
    
    for feed in feed_urls:
        try:
            rss_xml = fetcher.fetch_url(feed)
            urls.extend(extractor.extract_urls_from_rss(rss_xml))
        except Exception as e:
            logging.error(f"Failed to process RSS feed {feed}: {e}")
            
    return urls


def load_existing_articles(filepath: str) -> tuple[set[str], set[str]]:
    """Load existing titles and URLs from the CSV file to avoid duplicates."""
    seen_titles = set()
    seen_urls = set()

    if not os.path.exists(filepath):
        return seen_titles, seen_urls

    try:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("title"):
                    seen_titles.add(row["title"].strip().lower())
                if row.get("direct_url"):
                    seen_urls.add(row["direct_url"].strip())
        logging.info(f"Loaded {len(seen_titles)} existing titles and {len(seen_urls)} URLs from '{filepath}'.")
    except Exception as e:
        logging.error(f"Error reading existing CSV file '{filepath}': {e}")

    return seen_titles, seen_urls


def main():
    parser = argparse.ArgumentParser(description="Fetch Google News articles and incrementally append to CSV.")
    parser.add_argument(
        "--db",
        action="store_true",
        help="print a dump of the active topics and exit",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help="Path to the CSV output file (default: articles.csv)"
    )
    args = parser.parse_args()

    if args.db:
        dump_database(DB())
        return

    csv_filepath = args.output
    file_exists = os.path.exists(csv_filepath)

    # 0. Initialize LLM
    client = ollama_client.OllamaClient()

    # 1. Load seen titles and URLs from file
    seen_titles, seen_urls = load_existing_articles(csv_filepath)

    # 2. Fetch new RSS items
    urls_and_titles = get_rss_articles(fetcher, extractor)
    
    cutoff = 1000
    all_articles = len(urls_and_titles)
    processed_count = 0

    # 3. Open CSV file in append mode ('a') with UTF-8 encoding
    with open(csv_filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)

        # Write header if creating a new file
        if not file_exists:
            writer.writerow(["title", "body_text", "direct_url"])

        for counter, (title, url, date, source) in enumerate(urls_and_titles, start=1):
            if processed_count >= cutoff:
                break

            clean_title = title.strip()
            clean_url = url.strip()

            # Deduplication check (matches Title OR URL)
            if clean_title.lower() in seen_titles or clean_url in seen_urls:
                logging.info(f"Skipping article {counter}/{all_articles} (Already existing): {title}")
                continue

            processed_count += 1
            logging.info(f"Processing article {counter}/{all_articles}: {title}")

            try:
                html, full_url = fetcher.fetch_news_url(clean_url)
                if html.startswith("Failed to fetch URL"):
                    logging.error(f"Failed to fetch URL: {clean_url}")
                    continue

                text = extractor.extract_text(html, url=clean_url)
                if not text:
                    logging.error(f"No text extracted from {title}, skipping.")
                    continue

                summary = client.generate(model="gemma2:latest", prompt=f"Summarize the following article in one paragraph:\n\nArticle Title: {clean_title}\n\nArticle body:\n\n{text}. ### INSTRUCTIONS ### Summarize the article in one paragraph, focusing on the main points and key information. Avoid adding personal opinions or unrelated details. The summary should be concise, clear, and informative.")

                # Write directly to file and update memory sets
                writer.writerow([clean_title, summary, clean_url])
                f.flush()  # Ensures row is written immediately

                seen_titles.add(clean_title.lower())
                seen_urls.add(clean_url)

            except Exception as e:
                logging.error(f"An error occurred while processing {title}: {e}")
                continue


if __name__ == "__main__":
    main()
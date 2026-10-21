import argparse
import json
import re
from typing import Dict, Optional, Union
import fetcher
import extractor
import db
from db import DB
import ollama_client
import logging
import datetime
from article_classifier import ArticleClassifier
import dateutil
import prompts
import exporters

# github PAT 

# Configure logging to append messages to 'app.log' with timestamps
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TEMPORAL_PATTERNS = [
    r"\brecently\b",
    r"\blatest\b",
    r"\bcurrently\b",
    r"\bjust\b",
    r"\btoday\b",
    r"\bnewly\b",
    r"\bin recent (years|months|weeks|days)\b",
    r"\bas of late\b",
    r"\bbreaking\b",
    r"\bthis week\b"
]

def find_temporal_violations(text: str) -> list[str]:
    """Returns a list of matched temporal terms found in the generated text."""
    matches = []
    for pattern in TEMPORAL_PATTERNS:
        found = re.findall(pattern, text, flags=re.IGNORECASE)
        if found:
            matches.extend(found)
    return list(set(matches))


def parse_llm_inclusion(text: str) -> Dict[str, Union[Optional[bool], str]]:
    """
    Parses the LLM classification response to extract 'include' and 'reason'.
    
    Returns:
        dict: {
            "include": True (if yes), False (if no), or None (if unparsable),
            "reason": String containing the reason, or empty string if not found.
        }
    """
    result = {
        "include": None,
        "reason": ""
    }
    
    # Extract 'include' (case-insensitive, handles optional markdown stars **)
    include_match = re.search(r'(?i)\*?\*?include\*?\*?:\s*(yes|no)', text)
    if include_match:
        result["include"] = include_match.group(1).lower() == "yes"
        
    # Extract 'reason' (captures everything after "reason:" on that line)
    reason_match = re.search(r'(?i)\*?\*?reason\*?\*?:\s*(.+)', text)
    if reason_match:
        # Strip trailing quote marks or whitespace if the LLM adds any
        result["reason"] = reason_match.group(1).strip(' "\'\t\r\n')
        
    return result

def clean_and_parse_llm_json(raw_response: str) -> dict:
    # 1. Strip leading/trailing whitespace and backticks
    cleaned = raw_response.strip().strip("`")
    
    # 2. Remove the 'json' identifier if it was attached to the first backticks
    if cleaned.startswith("json"):
        cleaned = cleaned[4:]
        
    # 3. Strip any remaining newlines/spaces at the edges
    cleaned = cleaned.strip()
    
    # 4. Replace non-breaking spaces with standard spaces
    cleaned = cleaned.replace('\xa0', ' ')
    
    # Parse the cleaned string
    return json.loads(cleaned)

def format_topics_for_llm(topics_dict: dict) -> str:
    """
    Transforms the dictionary of topics into an XML-tagged text format 
    optimized for LLM comprehension.
    """
    formatted_topics = []
    
    for topic_data in topics_dict.values():
        # Fallbacks handle potential NULL values from the database
        topic = topic_data.get('topic') or "Unknown Topic"
        headline = topic_data.get('headline') or "No recent headline"
        summary = topic_data.get('summary') or "No summary available"
        
        # XML tags help the LLM isolate different attributes of the topic
        topic_block = (
            f"<topic>\n"
            f"  <name>{topic}</name>\n"
            f"  <headline>{headline}</headline>\n"
            f"  <summary>{summary}</summary>\n"
            f"</topic>"
        )
        formatted_topics.append(topic_block)
        
    # Separate each block with a newline for readability
    return "\n\n".join(formatted_topics)

# main flow
# get the list of news articles from rss feeds
# https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en Top Stories
# https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en Global News
def get_rss_articles() -> list[tuple[str, str, str, str]]:
    """Fetch the RSS feed and return a list of article URLs and titles."""
    rss_xml = fetcher.fetch_url("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
    urls = extractor.extract_urls_from_rss(rss_xml)
    rss_xml = fetcher.fetch_url("https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en")
    urls += extractor.extract_urls_from_rss(rss_xml)
    return urls

def curate_topics():
    """Curate topics in the database by checking if they are still active."""
    db_instance = db.DB(path="news_chewer.db")
    cur = db_instance.conn.cursor()
    cur.execute("SELECT topic, last_seen FROM topics WHERE status IS NULL OR status != 'inactive'")
    topics = cur.fetchall()
    for topic, last_seen in topics:
        # Check if the topic has been updated in the last 30 days
        if isinstance(last_seen, str):
            last_seen = datetime.date.fromisoformat(last_seen)
        if (datetime.date.today() - last_seen).days > 30:
            print(f"Topic '{topic}' has not been updated in over a month. Marking as inactive.")
            logging.info(f"Topic '{topic}' has not been updated in over a month. Marking as inactive.")
            cur.execute("UPDATE topics SET status = 'inactive' WHERE topic = ?", (topic,))
    db_instance.conn.commit()

def process_articles():
    print("Starting...")
    print("Curating logged topics...")

    db = DB()
    db.seed_initial_topics()
    curate_topics()
    current_topics = db.get_current_topics()

    print("Fetching and processing new articles...")

    urls_and_titles = get_rss_articles()
    cutoff = 200
    counter = 0
    all_articles = len(urls_and_titles)
    categorized = 0
    actual_news = 0
    updated_summary = 0

    classifier = ArticleClassifier()

    for title, url, article_date, source in urls_and_titles:
        counter += 1
        if counter >= cutoff:
            break
        print(f"Processing article {counter} of {all_articles}: {title}")
        logging.info(f"Processing article {counter} of {all_articles}: {title}")

        # 1. attempt to get the html contents of the URL
        html, final_url = fetcher.fetch_news_url(url)
        if html.startswith("Failed to fetch URL"):
            logging.error(f"** {html}")
            continue

        # 2. attempt to extract plain text from the website html
        text = extractor.extract_text(html, url=final_url)
        if not text:
            logging.error(f"** No text extracted from {title}, skipping.")
            continue

        client = ollama_client.OllamaClient()

    # 3. Generate a summary of the article using the LLM
        if not isinstance(text, str):
            logging.error(f"** Non-text response from fetcher/extractor.")
            continue

        summary_resp = client.generate(model="gemma2:latest", prompt=f"Summarize the following article in one paragraph:\n\nArticle Title: {title}\n\nArticle body:\n\n{text}. ### INSTRUCTIONS ### Summarize the article in one paragraph, focusing on the main points and key information. Avoid adding personal opinions or unrelated details. The summary should be concise, clear, and informative.")
        if "encoded text" in summary_resp:
            logging.error(f"** Error generating response for article: {title}")
            logging.error(f"** Original text follows:\n\n{text}\n\n ** End original text.")
            continue

    # 4. Classify the article into a topic using the classifier
        category_resp, category_confidence = classifier.predict(title, text)
        logging.info(f"{title}")
        logging.info(f"CATEGORY:{category_resp} (confidence: {category_confidence})")

    # 5. Discard articles that are not relevant to hard news focus
        if category_resp in ["Investment", "Tech Products and Launches", "Sports", "Entertainment, Celebrities, and Movies", "Science"]:
            logging.info(f"Category is not relevant to hard news focus. Skipping article.")
            continue

    # 6. Check the classifier confidence and drop out if it is below the threshold
        if category_confidence < 0.3:
            logging.info(f"Category confidence too low to use this article. It likely does not fit one of our categories.")
            db.save_article(final_url, title, summary_resp, article_date=dateutil.parser.parse(article_date).date(), authors="", topic="uncategorized", discovery_date=datetime.datetime.today())
            continue

    # 7. Double check the classification with a different type of system
        topic_summary = current_topics.get(category_resp, {}).get("summary")
        topic_headline = current_topics.get(category_resp, {}).get("headline")

        classification_resp = client.generate(model="gemma2:latest", prompt=prompts.classification_checker.format(topic = category_resp, topic_headline = topic_headline, topic_summary = topic_summary, article_title = title, article = summary_resp))
        classification_result = parse_llm_inclusion(classification_resp)

        if not classification_result['include']:
            logging.info(f"Category confidence was high enough, but LLM recheck failed to agree with the classification.")
            db.save_article(final_url, title, summary_resp, article_date=dateutil.parser.parse(article_date).date(), authors="", topic="uncategorized", discovery_date=datetime.datetime.today())
            continue

    # 8. Is the article "actual news" or should we ignore it? (e.g. opinion, analysis, or something that is not really news)
        categorized += 1

        inclusion_resp = client.generate(model="gemma2:latest", prompt=f"{prompts.the_big_prompt_a}\n{text}\n\n{prompts.the_big_prompt_b}")
        inclusion_result = parse_llm_inclusion(inclusion_resp)

        logging.info(f"include: {inclusion_result['include']}; reason: {inclusion_result['reason']}")

        if not inclusion_result['include']:
            logging.info(f"include: {inclusion_result['include']}; reason: {inclusion_result['reason']}")
            continue

    # 9. Generate a new title for the article, because we don't like traditional news headlines
        title_resp = client.generate(model="gemma2:latest", prompt=f"Summarize the following article in one sentence:\n\nTitle: {title}\n\nArticle body:\n\n{text}. ### INSTRUCTIONS ### Summarize the article in a single sentence, focusing on the main point or development. Avoid adding personal opinions or unrelated details. The sentence should be clear, concise, and informative.")

        actual_news += 1

    # 10. Check if the article is essentially something that has already been reported in the last 7 days
        # get last 7 days of summaries in this category.
        last_7_days_summaries = db.get_articles_for_topic(category_resp, 7)
        # feed those to the LLM along with the new summary, asking if the article appears to just be the same already present in one or more of the summaries
        new_article = client.generate(model="gemma2:latest", prompt=prompts.old_news_prompt.format(summaries = "\n\n".join(last_7_days_summaries), new_article = summary_resp), params={"options": { "temperature": 0.0, "top_p": 0.1}})
        if "yes" in new_article.lower():
            logging.info(f"Article appears to be a repeat of something already reported in the last 7 days. Skipping.")
            continue

    # 11. check if the article adds new macro info. if so, rewrite the topic summary. save the article.
        new_info_resp = client.generate(model="gemma2:latest", prompt=prompts.scope_prompt.format(topic_summary = topic_summary, article_summary = summary_resp), params={"options": { "temperature": 0.0, "top_p": 0.1}})

        if "yes" in new_info_resp.lower():
            updated_summary += 1
            db.save_article(final_url, title_resp, summary_resp, article_date=dateutil.parser.parse(article_date).date(), authors="", topic=category_resp, discovery_date=datetime.datetime.today())
            new_summary = client.generate(model="gemma2:latest", prompt=prompts.resummarize_prompt.format(topic_summary = topic_summary, article_summary = summary_resp))
            violations = find_temporal_violations(new_summary)
            if violations:
                logging.error("** we had a bad resummarizing attempt, trying one more time")
                formatted_violations = ", ".join([f'"{v}"' for v in violations])
                new_summary = client.generate(model="gemma2:latest", prompt=prompts.resummarize_try_again.format(topic_summary = topic_summary, article_summary = summary_resp, previous_output = new_summary, violations_list = formatted_violations))

            new_headline = client.generate(model="gemma2:latest", prompt=f"Generate a single sentence headline for the following topic summary:\n\n{new_summary}")
            db.save_topic_summary(id=f"{category_resp}_{datetime.date.today()}", headline=f"{new_headline}", summary=new_summary, summary_date=datetime.date.today(), topic=category_resp)
            logging.info(f"Article adds new information to topic '{category_resp}'. Updated topic summary saved.")
            logging.info(f"** Original topic summary: {topic_summary}")
            logging.info(f"** New topic summary: {new_summary}")
            logging.info(f"** New topic summary headline: {new_headline}")
            db.update_topic_last_seen(category_resp, datetime.date.today())
            current_topics = db.get_current_topics()
        else:
            logging.info(f"Article does not add new information to topic '{category_resp}'. Updating last_seen date.")
            db.save_article(final_url, title_resp, summary_resp, article_date=dateutil.parser.parse(article_date).date(), authors="", topic=category_resp, discovery_date=datetime.datetime.today())
            db.update_topic_last_seen(category_resp, datetime.date.today())

            
    print(f"Finished processing {all_articles} articles.")
    print(f"Categorized stories: {categorized}")
    print(f"Include articles: {actual_news}")
    print(f"Updated summaries: {updated_summary}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        action="store_true",
        help="print a dump of the active topics and exit",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="generate a self-contained html page of the news"
    )
    args = parser.parse_args()

    if args.db:
        exporters.dump_database_in_markdown(DB())
        return

    if args.html:
        exporters.export_to_html(DB(), "./latest_news.html")
        return

    process_articles()

if __name__ == "__main__":
    main()
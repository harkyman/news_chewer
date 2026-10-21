from db import DB

def main():
    db = DB()

    raw_articles = db.get_articles_for_categorization()

    if not raw_articles:
        print("No articles found with topic = 'uncategorized'.")
        return

    # 3. Output to console in Markdown format
    print("# Uncategorized Articles\n")
    
    for art in raw_articles:
        print(f"## {art['title']}")
        print(f"- **ID:** {art['id']}")
        print(f"- **Synopsis:** {art['synopsis']}\n")

if __name__ == "__main__":
    main()

import tldextract
import html
import datetime


def dump_database_in_markdown(db_instance, today: datetime.date | None = None) -> None:
    """Print active topics and any articles stored for them today in Markdown format."""
    today = today or datetime.date.today()
    topics = db_instance.get_current_topics()
    cursor = db_instance.conn.cursor()

    print("# Active Topics\n")
    
    if not topics:
        print("*No active topics.*")
        return

    # Iterate over the values of the dictionary, which contain the actual data dicts
    for topic_data in topics.values():
        print(f"## {topic_data['topic']}\n")
        print(f"**Last seen:** {topic_data['last_seen']}  ")
        print(f"**Latest headline:** {topic_data['headline'] or '(none)'}  \n")
        
        # Safely get summary or description using .get() to prevent KeyErrors
        summary_text = topic_data.get('summary') or topic_data.get('description') or '(none)'
        print("**Topic summary:**")
        print(f"> {summary_text}\n")
        
        print(f"### Articles from {today}:\n")

        cursor.execute(
            """
            SELECT title, synopsis
            FROM articles
            WHERE topic = ? AND article_date = ?
            ORDER BY id
            """,
            (topic_data["topic"], today),
        )
        articles = cursor.fetchall()
        
        if not articles:
            print("* *(none)*\n")
            print("---\n")
            continue
            
        for title, synopsis in articles:
            title_text = title or '(untitled)'
            synopsis_text = synopsis or '(no synopsis)'
            print(f"* **{title_text}**")
            print(f"  {synopsis_text}")
        
        print("\n---\n")

def export_to_html(
    db_instance, output_filepath: str, today: datetime.date | None = None
) -> None:
    """Export active topics and articles to a self-contained HTML page with CSS/JS."""
    # 1. actual_today represents true "today" for matching today's articles
    actual_today = today if today is not None else datetime.date.today()
    target_date_str = actual_today.strftime("%Y-%m-%d")

    # 2. cutoff_date defines how far back in SQL to query (e.g. past 7 days)
    cutoff_date = actual_today - datetime.timedelta(days=7)

    topics = db_instance.get_current_topics()
    cursor = db_instance.conn.cursor()

    processed_topics = []

    if topics:
        for topic_data in topics.values():
            topic_name = topic_data.get("topic", "")
            headline = topic_data.get("headline") or ""
            last_seen = topic_data.get("last_seen") or ""
            summary = (
                topic_data.get("summary")
                or topic_data.get("description")
                or ""
            )

            if topic_name in ["Investment", "Tech Products and Launches", "Sports", "Entertainment, Celebrities, and Movies", "Science"]:
                continue

            # Query database using cutoff_date
            cursor.execute(
                """
                SELECT title, synopsis, url, article_date, discovery_date
                FROM articles
                WHERE topic = ? AND article_date >= ? AND discovery_date >= ?
                ORDER BY discovery_date DESC
                """,
                (topic_name, cutoff_date, cutoff_date),
            )
            articles_rows = cursor.fetchall()

            today_articles = []
            older_articles = []

            for row in articles_rows:
                title = row[0] or "Untitled"
                synopsis = row[1] or "No synopsis available."
                url = row[2] if len(row) > 2 and row[2] else "#"
                article_date = str(row[3]) if len(row) > 3 and row[3] else ""
                discovery_date = str(row[4])[:10] if len(row) > 4 and row[4] else ""

                article_item = {
                    "title": title,
                    "synopsis": synopsis,
                    "url": url,
                    "article_date": article_date,
                    "discovery_date": discovery_date
                }

                if discovery_date == target_date_str:
                    today_articles.append(article_item)
                else:
                    older_articles.append(article_item)

            today_articles = sorted(today_articles, key=lambda x: x['article_date'], reverse=True)
            older_articles = sorted(older_articles, key=lambda x: x['article_date'], reverse=True)

            processed_topics.append(
                {
                    "topic": topic_name,
                    "headline": headline,
                    "summary": summary,
                    "last_seen": last_seen,
                    "today_articles": today_articles,
                    "older_articles": older_articles,
                    "total_count": len(articles_rows),
                    "today_count": len(today_articles),
                    "older_count": len(older_articles)
                }
            )

        processed_topics.sort(key=lambda x: (x['today_count'], x['last_seen'], x['older_count']), reverse=True)

    # Helper function to generate HTML for individual article cards
    def render_article_html(art):
        art_title = html.escape(art["title"])
        art_synopsis = html.escape(art["synopsis"])
        art_url = html.escape(art["url"])
        art_source = tldextract.extract(art["url"]).top_domain_under_public_suffix
        art_article_date = html.escape(art["article_date"])
        return f"""
                <div class="article-box">
                    <div class="article-title" onclick="toggleExpand(this)">
                        <span class="tag">Article</span> {art_title} ({art_article_date}, {art_source})
                    </div>
                    <!-- Smooth Wrapper -->
                    <div class="expandable-wrapper">
                        <div class="expandable-inner article-body">
                            <p>{art_synopsis}</p>
                            AI synopsis. <a href="{art_url}" target="_blank" rel="noopener noreferrer">Article from {art_source} &rarr;</a>
                        </div>
                    </div>
                </div>"""

    # HTML template with embedded CSS and JavaScript
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PiperNews</title>
    <style>
        :root {{
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border-color: #555555;
            --hover-bg: #2d2d2d;
            --accent-color: #4da3ff;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: Georgia, serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 10px;
            max-width: 600px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            padding: 15px 0;
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 15px;
        }}

        header h1 {{
            font-size: 1.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .topic-list {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            border: 1px solid var(--border-color);
        }}

        /* Topic Band Header */
        .topic-band {{
            background-color: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
        }}

        .topic-title {{
            padding: 14px 16px;
            font-weight: bold;
            font-size: 1.05rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }}

        .topic-title:hover {{
            background-color: var(--hover-bg);
        }}

        /* Smooth Expand/Collapse Wrappers */
        .expandable-wrapper {{
            display: grid;
            grid-template-rows: 0fr;
            opacity: 0;
            transition: grid-template-rows 100ms ease-in-out, opacity 100ms ease-in-out;
        }}

        .expandable-wrapper.open {{
            grid-template-rows: 1fr;
            opacity: 1;
        }}

        .expandable-inner {{
            overflow: hidden;
            min-height: 0;
        }}

        /* Expandable Topic Content */
        .topic-content {{
            padding-left: 15px;
            background-color: #181818;
            border-top: 1px solid #2a2a2a;
        }}

        /* Topic Headline & Summary */
        .topic-headline-box {{
            border-bottom: 1px solid #2a2a2a;
        }}

        .topic-headline {{
            padding: 10px 12px;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            user-select: none;
            background-color: #242424;
        }}

        .topic-headline:hover {{
            background-color: #2e2e2e;
        }}

        .topic-summary {{
            padding: 12px;
            font-size: 0.9rem;
            color: #cccccc;
            background-color: #1e1e1e;
            border-left: 3px solid var(--border-color);
            margin: 8px 0;
        }}

        /* Article Items */
        .article-box {{
            border-bottom: 1px solid #2a2a2a;
        }}

        .article-title {{
            padding: 10px 12px;
            font-size: 0.95rem;
            cursor: pointer;
            user-select: none;
        }}

        .article-title:hover {{
            background-color: var(--hover-bg);
        }}

        .article-body {{
            padding: 12px;
            background-color: #1e1e1e;
            font-size: 0.88rem;
            color: var(--text-secondary);
            border-top: 1px dashed #333333;
            border-left: 3px solid var(--border-color);
        }}

        .article-body a {{
            display: inline-block;
            margin-top: 8px;
            color: var(--accent-color);
            text-decoration: underline;
            word-break: break-all;
        }}

        /* Older Articles Section */
        .older-toggle {{
            padding: 10px 12px;
            font-size: 0.9rem;
            font-weight: bold;
            color: var(--text-secondary);
            background-color: #252525;
            cursor: pointer;
            user-select: none;
            border-bottom: 1px solid #333333;
        }}

        .older-toggle:hover {{
            background-color: #303030;
        }}

        .empty-notice {{
            padding: 10px 12px;
            font-style: italic;
            color: #777777;
            font-size: 0.9rem;
        }}

        .tag {{
            font-size: 0.5rem;
            background-color: #444444;
            color: #e0e0e0;
            padding: 2px;
            font-family: sans-serif;
        }}
    </style>
</head>
<body>

    <header>
        <h1>PiperNews</h1>
    </header>

    <main class="topic-list">
"""

    if not processed_topics:
        html_content += (
            '        <div class="empty-notice">No active topics.</div>\n'
        )
    else:
        for t in processed_topics:
            topic_escaped = html.escape(t["topic"])
            headline_escaped = (
                html.escape(t["headline"])
                if t["headline"]
                else "(No headline)"
            )
            summary_escaped = (
                html.escape(t["summary"])
                if t["summary"]
                else "No summary available."
            )
            last_seen_escaped = ""
            if t["last_seen"]:
                try:
                    ds = datetime.datetime.strptime(t["last_seen"], "%Y-%m-%d")
                    last_seen_escaped = html.escape(f"{ds:%b} {ds.day}")
                except ValueError:
                    last_seen_escaped = html.escape(t["last_seen"])

            html_content += f"""
        <!-- Topic Band -->
        <div class="topic-band">
            <div class="topic-title" onclick="toggleExpand(this)">
                <span>{topic_escaped} ({t["today_count"]}/{t["older_count"]}, 🌿 {last_seen_escaped})</span>
            </div>
            
            <div class="expandable-wrapper">
                <div class="expandable-inner topic-content">
                    <!-- Headline & Summary -->
                    <div class="topic-headline-box">
                        <div class="topic-headline" onclick="toggleExpand(this)">
                            {headline_escaped}
                        </div>
                        <div class="expandable-wrapper">
                            <div class="expandable-inner topic-summary">
                                {summary_escaped}
                            </div>
                        </div>
                    </div>

                    <!-- Articles -->
"""
            today_arts = t["today_articles"]
            older_arts = t["older_articles"]

            if not today_arts and not older_arts:
                html_content += '                <div class="empty-notice">(No articles available)</div>\n'
            else:
                # 1. Render today's articles directly
                if not today_arts:
                    html_content += '<div class="empty-notice">(No articles from today)</div>\n'
                else:
                    for art in today_arts:
                        html_content += render_article_html(art)

                # 2. Render older articles under collapsible toggle
                if older_arts:
                    older_count = len(older_arts)
                    html_content += f"""
                <div class="older-toggle" onclick="toggleExpand(this)">
                    older ({older_count})...
                </div>
                <div class="expandable-wrapper">
                    <div class="expandable-inner older-container">
"""
                    for art in older_arts:
                        html_content += render_article_html(art)

                    html_content += """
                    </div>
                </div>
"""
                

            html_content += """
                </div>
            </div>
        </div>
"""

    html_content += """
    </main>

    <script>
        function toggleExpand(element) {
            // Find the next sibling element which holds the details to show/hide
            const nextContent = element.nextElementSibling;
            if (nextContent) {
                // Toggles the class that initiates the CSS Grid row transition
                nextContent.classList.toggle('open');
            }
        }
    </script>
</body>
</html>
"""

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
import sqlite3
import datetime
from datetime import date
from typing import Any, Dict, List, Optional


class DB:
    def __init__(self, path: str = "news_chewer.db"):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                synopsis TEXT,
                article_date DATE,
                authors TEXT,
                topic TEXT,
                discovery_date TEXT
            )
            """
        )
        self.conn.commit()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                topic TEXT PRIMARY KEY,
                description TEXT,
                first_seen DATE,
                last_seen DATE,
                type TEXT,
                status TEXT
            )
            """
        )
        self.conn.commit()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_summaries (
                id TEXT PRIMARY KEY,
                headline TEXT,
                summary TEXT,
                summary_date DATE,
                topic TEXT
            )
            """
        )
        self.conn.commit()

    def seed_initial_topics(self) -> None:
        seed_data = {
            ("US mid-term elections 2026", "The 2026 U.S. midterms, in particular its federal congressional elections, are shaping up as a highly polarized battle for congressional control. While specific polling and outcomes are still developing as November approaches, key themes dominating the races include economic anxiety, shifting state-level reproductive rights battles, and deep partisan divides over foreign policy and immigration. Also at issue are attempts from both parties to redraw congressional maps to generate additional seats for their party, and from the Republican controlled executive branch to enact last minute changes to mail in balloting, as well as pre-posturing with unfounded assertions of election fraud.","US mid-term elections are November 3, and are likely to rebalance power in Washington."),
            
            ("Russia/Ukraine war", "The Russian invasion of Ukraine is a major ongoing military conflict in Eastern Europe that escalated into a full-scale war on February 24, 2022, building upon the initial 2014 annexation of Crimea and fighting in the eastern Donbas region. Russian forces launched a multi-pronged invasion originating from Russian territory to the east, Belarus to the north, and the Crimean Peninsula to the south. While Russia intended to end the war within days, Ukrainian forces have managed to stalemate them, and use their superior drone technology to inflict direct strikes on targets within Russia, including Moscow itself. As a result of the invasion, millions of Ukrainian civilians have been displaced, half a million lives have been lost between the sides, and significant territory in eastern and southern Ukraine remains under Russian military occupation.","Russia’s multi-pronged full-scale invasion of Ukraine resulted in a stalemated conflict marked by hundreds of thousands of casualties, civilian displacement, Russian occupation, and retaliatory strikes inside Russia."),
            
            ("Israel conflict", "Following the October 7, 2023 attack on southern Israel led by the Gaza-based militant group Hamas, Israel launched a large-scale, multi-front military campaign across its borders. To the south, Israeli forces initiated a intense air and ground offensive in the Gaza Strip. To the north along the Israeli-Lebanese border, persistent exchange of fire escalated into sustained air strikes and ground incursions into southern Lebanon targeting the militant group Hezbollah. Simultaneously, Israel carried out targeted air operations across the Syrian border to suppress Iranian-backed supply networks and proxy forces maintaining a presence in Syrian territory. Accusations of war crimes abound on all sides.","Israel launched multi-front military operations following Hamas's October 7 attack."),
            
            ("2026 Iran war and wider Middle East escalation", "The 2026 Iran war is a major military conflict in the Middle East that escalated into a direct campaign on February 28, 2026, building upon decades of regional proxy warfare and targeted strikes, including U.S. attacks on Iranian nuclear facilities in mid-2025. Operating jointly with Israeli defense forces, the United States launched widespread attacks against high-value military infrastructure, air defenses, and political leadership across major urban and strategic centers. In response, Iranian forces executed multi-front retaliatory missile and drone barrages targeting Allied bases and international maritime traffic, leading to a U.S. naval blockade around the critical choke point of the Strait of Hormuz. As a result of the ongoing engagements and economic standoffs, regional energy transport has been severely disrupted, hundreds of lives have been lost across both military and civilian populations, and key infrastructure across the Persian Gulf remains within active conflict zones.","The U.S.-Israeli campaign against Iran sparked retaliatory strikes, a Strait of Hormuz blockade, and severe global energy disruptions."),
            
            ("Climate change", "Global climate metrics continue to break recent records, with January through August 2026 ranking as the second warmest such period on record. The National Centers for Environmental Information (NCEI) project it is very likely that 2026 will rank among the five warmest years on record, further accelerating the severe weather phenomena and extreme heat events observed globally this year.","Global temperatures from January through August 2026 ranked among the highest on record, keeping the year on track to be one of the warmest ever."),
            
            ("Artificial intelligence safety and regulation", "2026 represents a shift from debating AI regulatory frameworks to enforcing them, as new technologies like \"Agentic AI\" challenge existing oversight capabilities. Key global milestones include South Korea's AI Basic Act taking full effect in January 2026, and stricter cybersecurity amendments in China. Globally, regulators are grappling with the rapid rise of scalable harms, including \"Deepfake-as-a-Service\" financial fraud, the unchecked scraping of private data for model training, and the unique security vulnerabilities of autonomous AI systems.","Global focus pivoted to enforcing AI regulations against emerging threats."),
            
            ("US-China trade tensions and technology competition", "Economic and technological friction between the U.S. and China remains intense in 2026, characterized by escalating export controls and a race for dominance in critical sectors like semiconductors, AI, and green technology. Both nations continue to implement protective industrial policies and tariffs, attempting to secure their domestic supply chains and limit the other's access to advanced technological capabilities.","The rivalry centers on export controls, tariffs, and industrial protectionism as both nations strive for dominance in key sectors and supply chain security."),

            ("The rise of European far-right political movements", "Throughout 2026, far-right and nationalist political parties have continued to consolidate power and influence across Europe, capitalizing on ongoing public anxieties regarding immigration, economic stagnation, and the cost of the green transition. This shift has significantly impacted both national elections and European Union policy, driving tougher border control measures and challenging established centrist coalitions.","Far-right and nationalist parties consolidate power across Europe in 2026, reshaping EU immigration and economic policies"),

            ("Disease and public health", "The spread of contagious diseases and their affect on public health is an ever-present concern around the world. Outbreaks require action from local, national, and sometimes international authorities. At the same time, the erosion of confidence in the role of vaccines threatens to allow some diseases which had effectively been wiped out to make a comeback.","Eroding public trust in vaccines and persistent global outbreaks threaten to bring back once-eradicated contagious diseases."),

            ("NATO stability and Western Cooperation","After enjoying strong support and adherence from its inception through the early 2000s, the North Atlantic Treaty Organization has recently been placed under enormous strain. Between agitation about leaving or defunding from the United States and regular incursions and disruptions from Russia, the resolve and coherence of the group is being tested. The could be a greater symptom of instability in the general coherence of the West, as countries like China, Russia, and Iran are emboldened on the international front.","Internal political pressures within the West and rising aggression from external rivals are subjecting NATO to unprecedented strain, testing the alliance's long-term coherence."),

            ("French Civil Unrest","The 2026 French civil unrest is a major ongoing sequence of nationwide protests and strikes that escalated significantly in September 2026, building upon France's long-standing tradition of street activism dating back to the 1789 Revolution. Originating as widespread high school and university student blockades over decaying educational infrastructure, class sizes, and government austerity, the movement rapidly expanded to include major labor unions and political factions protesting broader social and economic policy. Demonstrations originating in Paris and secondary metropolitan centers led to widespread school closures, industrial blockades, and violent street clashes between riot police and protesters. As a result of the escalating confrontations, thousands of arrests have been made across major urban centers, key public services and transport networks have faced operational shutdowns, and the country's political administration faces intense institutional pressure ahead of the upcoming presidential elections.","France faces an ongoing identity crisis as its histori support for protests, even violent ones, meets current socioeconomic conditions."),
                        
            ("Sports","Sporty McSportington, or, things that aren't news.","Sports go sports!"),

            ("Investment","Bros must make sure to short their longs and read every piece of money news.","I can beat the market, trust me bro."),

            ("Entertainment, Celebrities, and Movies","Once you get to know them, they're just like us!","Entertainment is art."),
            
            ("Science","Science is important, but it's not really news.","Always be curious."),
            
            ("Tech Products and Launches","You need the next thing, or you're a loser and maybe even poor.","Consume.")
        }

        cur = self.conn.cursor()

        # Fetch all existing topic names from the database in one query
        cur.execute("SELECT topic FROM topics")
        existing_topics = {row[0] for row in cur.fetchall()}

        # Check which items in seed_data are missing from existing_topics
        missing_seed_items = [
            item for item in seed_data if item[0] not in existing_topics
        ]

        # Early exit if all topics are already present
        if not missing_seed_items:
            return

        current_date = datetime.date.today()

        # Insert only the missing topics and their summaries
        for topic, summary, headline in missing_seed_items:
            # Insert overarching topic
            cur.execute(
                """
                INSERT OR IGNORE INTO topics (topic, description, first_seen, last_seen, type, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (topic, f"Global news tracking for {topic}", current_date, current_date, "Macro Trend", "Active")
            )

            # Insert initial summary snapshot
            summary_id = f"{topic}_{current_date}"
            cur.execute(
                """
                INSERT OR IGNORE INTO topic_summaries (id, headline, summary, summary_date, topic)
                VALUES (?, ?, ?, ?, ?)
                """,
                (summary_id, headline, summary, current_date, topic)
            )

        self.conn.commit()

    def save_article(self, url: str, title: Optional[str], text: str, article_date: datetime.date, authors: str, topic: str, discovery_date: datetime.date) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO articles (url, title, synopsis, article_date, authors, topic, discovery_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (url, title, text, article_date, authors, topic, discovery_date),
        )
        self.conn.commit()

    def save_topic(self, topic: str, first_seen: datetime.date, last_seen: datetime.date, type: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO topics (topic, first_seen, last_seen, type) VALUES (?, ?, ?, ?)",
            (topic, first_seen, last_seen, type),
        )
        self.conn.commit()

    def save_topic_summary(self, id: str, headline: str, summary: str, summary_date: datetime.date, topic: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO topic_summaries (id, headline, summary, summary_date, topic) VALUES (?, ?, ?, ?, ?)",
            (id, headline, summary, summary_date, topic),
        )
        self.conn.commit()

    def get_article(self, url: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, url, title, text, article_date, discovery_date FROM articles WHERE url = ?", (url,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "url": row[1],
            "title": row[2],
            "text": row[3],
            "article_date": row[4],
            "discovery_date": row[5],
            
        }
    
    def get_topic(self, topic: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT topic, first_seen, last_seen, type FROM topics WHERE topic = ?", (topic,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "topic": row[0],
            "first_seen": row[1],
            "last_seen": row[2],
            "type": row[3],
        }
    
    def get_topic_summary(self, id: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, headline, summary, summary_date, topic FROM topic_summaries WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "headline": row[1],
            "summary": row[2],
            "summary_date": row[3],
            "topic": row[4],
        }

    def get_current_topics(self) -> dict:
        cur = self.conn.cursor()
        query = """
        WITH latest_summaries AS (
            SELECT 
                topic, 
                summary, 
                headline, 
                summary_date,
                ROW_NUMBER() OVER (
                    PARTITION BY topic 
                    ORDER BY summary_date DESC
                ) as rn
            FROM topic_summaries
        )
        SELECT 
            t.topic, 
            t.first_seen, 
            t.last_seen, 
            t.type,
            ls.summary, 
            ls.headline, 
            ls.summary_date
        FROM topics t
        LEFT JOIN latest_summaries ls 
            ON t.topic = ls.topic AND ls.rn = 1
        WHERE t.status IS NULL OR t.status != 'inactive'
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        # Return a dictionary keyed by the topic string (row[0])
        return {
            row[0]: {
                "topic": row[0],
                "first_seen": row[1],
                "last_seen": row[2],
                "type": row[3],
                "summary": row[4],
                "headline": row[5],
                "summary_date": row[6],
            }
            for row in rows
        }

    def update_topic_last_seen(self, topic: str, last_seen: datetime.date) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE topics SET last_seen = ? WHERE topic = ?",
            (last_seen, topic),
        )
        self.conn.commit()

    def get_articles_for_topic(self, topic: str, date: datetime.date) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT title, synopsis FROM articles WHERE topic = ? AND article_date = ?", (topic, date))
        rows = cur.fetchall()
        return [
            {
                "title": row[0],
                "synopsis": row[1],
            }
            for row in rows
        ]
    
    def get_historic_articles_for_topic(self, topic: str, days: int) -> list:
            cur = self.conn.cursor()
            cur.execute("SELECT title, synopsis FROM articles WHERE topic = ? AND article_date >= DATE('now', '-{} days')".format(days), (topic))
            rows = cur.fetchall()
            return [
                {
                    "synopsis": row[1],
                }
                for row in rows
            ]
    
    def get_articles_for_categorization(self) -> List[Dict[str, Any]]:
        """Fetch up to `limit` articles where topic is 'uncategorized'."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, title, synopsis FROM articles WHERE topic = 'uncategorized' ORDER BY article_date DESC",
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "synopsis": row[2],
            }
            for row in rows
        ]

    def create_sample_topic(self) -> None:
        today = datetime.date.today()
        self.save_topic('Ukraine War', 'Coverage of the ongoing conflict in Ukraine', first_seen=today, last_seen=today, type='Conflict, Security & Geopolitics')
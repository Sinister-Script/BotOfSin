# Imports
import discord
import asyncio
import sqlite3
import requests
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser

# Token / Config
DB_PATH = "feeds.db"
from BotOfSin import GUILD_ID, CHANNEL_ID
from .FeedUtils import parse_feed, filter_recent, make_paginated_view, clean_summary

# ------------------ Feed Registry ------------------
# Fields:
#   name          - display name
#   url           - RSS feed URL
#   color         - embed color
#   category      - logical grouping for slash commands (news, gov, research, podcast)
#   include_audio - True only for podcast feeds with enclosures
#   days_recent   - how far back /news and /feedsearch show results

FEED_REGISTRY = [
    # ---- Private Sector ----
    {"name": "Graham Cluley",               "url": "https://grahamcluley.com/feed/",                                 "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Threatpost",                  "url": "https://threatpost.com/feed/",                                   "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Krebs on Security",           "url": "https://krebsonsecurity.com/feed/",                              "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Dark Reading",                "url": "https://www.darkreading.com/rss.xml",                            "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "We Live Security",            "url": "http://feeds.feedburner.com/eset/blog",                          "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Bleeping Computer",           "url": "https://www.bleepingcomputer.com/feed/",                         "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "The Hacker News",             "url": "http://feeds.feedburner.com/TheHackersNews?format=xml",          "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Schneier on Security",        "url": "https://www.schneier.com/feed/atom/",                            "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Securelist",                  "url": "https://securelist.com/feed/",                                   "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Checkpoint Research",         "url": "https://research.checkpoint.com/feed/",                          "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Microsoft Security",          "url": "https://msrc-blog.microsoft.com/feed/",                          "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Recorded Future",             "url": "https://www.recordedfuture.com/feed",                            "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "SentinelOne",                 "url": "https://www.sentinelone.com/feed/",                              "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Red Canary",                  "url": "https://redcanary.com/feed/",                                    "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "AT&T Cybersecurity",          "url": "https://cybersecurity.att.com/site/blog-all-rss",                "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Binary Defense",              "url": "https://www.binarydefense.com/feed/",                            "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Infosecurity Magazine",       "url": "https://www.infosecurity-magazine.com/rss/news/",                "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Google Security",             "url": "http://feeds.feedburner.com/GoogleOnlineSecurityBlog",           "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Trend Micro",                 "url": "http://feeds.trendmicro.com/TrendMicroResearch",                 "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Proof Point",                 "url": "https://www.proofpoint.com/us/rss.xml",                          "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "Cisco Security",              "url": "https://blogs.cisco.com/security/feed",                          "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "VirusBulletin",               "url": "https://www.virusbulletin.com/rss",                              "color": discord.Color.magenta(),      "category": "news",     "include_audio": False, "days_recent": 7},
    {"name": "James Forshaw",               "url": "https://www.tiraniddo.dev/feeds/posts/default",                  "color": discord.Color.teal(),         "category": "research", "include_audio": False, "days_recent": 30},
    {"name": "Adam Chester",                "url": "https://blog.xpnsec.com/rss.xml",                                "color": discord.Color.teal(),         "category": "research", "include_audio": False, "days_recent": 30},
    {"name": "Modexp",                      "url": "https://modexp.wordpress.com/feed/",                             "color": discord.Color.teal(),         "category": "research", "include_audio": False, "days_recent": 30},
    {"name": "DaVinci Forensics",           "url": "https://davinciforensics.co.za/cybersecurity/feed/",             "color": discord.Color.teal(),         "category": "research", "include_audio": False, "days_recent": 30},
    {"name": "PortSwigger Research",        "url": "https://portswigger.net/research/rss",                           "color": discord.Color.teal(),         "category": "research", "include_audio": False, "days_recent": 60},
    
    # ---- Government / CERT ----
    {"name": "US-CERT CISA",                "url": "https://www.cisa.gov/uscert/ncas/alerts.xml",                    "color": discord.Color.red(),          "category": "gov",      "include_audio": False, "days_recent": 14},
    {"name": "NCSC",                        "url": "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",  "color": discord.Color.red(),          "category": "gov",      "include_audio": False, "days_recent": 14},
    {"name": "Center of Internet Security", "url": "https://www.cisecurity.org/feed/advisories",                     "color": discord.Color.red(),          "category": "gov",      "include_audio": False, "days_recent": 14},

    # ---- CVE / Vulnerability ----
    {"name": "CISA KEV",                    "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", "color": discord.Color.orange(), "category": "cve", "include_audio": False, "days_recent": 7},
    
    # Dead source
    {"name": "NVD Recent CVEs",             "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml",  "color": discord.Color.orange(),       "category": "cve",      "include_audio": False, "days_recent": 7},
    
    # ---- Podcast ----
    {"name": "CyberWire Daily",             "url": "https://feeds.megaphone.fm/cyberwire-daily-podcast",             "color": discord.Color.brand_red(),    "category": "podcast",  "include_audio": True,  "days_recent": 7},
    {"name": "CTBB Podcast",                "url": "https://media.rss.com/ctbbpodcast/feed.xml",                     "color": discord.Color.brand_red(),    "category": "podcast",  "include_audio": True,  "days_recent": 30},
]

# Ransomware JSON source, not RSS - Useful for later
RANSOMWARE_SOURCE = "https://raw.githubusercontent.com/joshhighet/ransomwatch/main/posts.json"

# Build a quick lookup by name for commands
FEED_BY_NAME = {f["name"].lower(): f for f in FEED_REGISTRY}
CATEGORIES = list({f["category"] for f in FEED_REGISTRY})
# ------------------ Feed Registry End ------------------

# ------------------ Feed DB Setup ------------------
def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_name TEXT NOT NULL,
            guid      TEXT UNIQUE NOT NULL,
            title     TEXT,
            link      TEXT,
            summary   TEXT,
            published TEXT,
            audio     TEXT,
            posted    INTEGER DEFAULT 0,
            digested  INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    migrate_db(conn)
    return conn

def migrate_db(conn):
    '''
    Adds any columns that did not exist in older versions of the DB schema 

    Args:
        conn (sqlite3.Connection): Open connection to the feeds DB
    '''
    
    existing = {row[1] for row in conn.execute("PRAGMA table_info(entries)")}
    if "digested" not in existing:
        conn.execute("ALTER TABLE entries ADD COLUMN digested INTEGER DEFAULT 0")
        conn.commit()

def already_seen(cur, guid: str) -> bool:
    '''
    Checks whether an entry with the given GUID already exists in the DB

    Args:
        cur (sqlite3.Cursor): Active database cursor to query against
        guid (str): Unique identifier for the feed entry (entry id, url, or title fallback)

    Returns:
        bool: True if the entry already exists in the DB, False if new
    '''
    
    cur.execute("SELECT 1 FROM entries WHERE guid = ?", (guid,))
    return cur.fetchone() is not None

def insert_entry(cur, feed_name: str, e: dict, guid: str):
    '''
    Inserts a new feed entry into the DB

    Args:
        cur (sqlite3.Cursor): Active database cursor to insert with
        feed_name (str): Display name of the source feed (from FEED_REGISTRY)
        e (dict): Parsed feed entry containing title, link, summary, published, and audio fields
        guid (str): Unique identifier for the entry used to prevent duplicates
    '''
    
    published_val = e["published"].isoformat() if e.get("published") else None
    cur.execute(
        """INSERT OR IGNORE INTO entries
           (feed_name, guid, title, link, summary, published, audio, posted)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
        (feed_name, guid, e.get("title"), e.get("link"),
         e.get("summary"), published_val, e.get("audio")),
    )

def purge_old_entries(cur, days: int = 90):
    '''
    Removes entries older than the given number of days from the DB.
    Called at the end of each check_all_feeds cycle to keep the DB from growing indefinitely

    Args:
        cur (sqlite3.Cursor): Active database cursor to delete with
        days (int): Time until entries are removed, anything older is deleted (default: 90)
    '''
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cur.execute("SELECT guid, published FROM entries WHERE published IS NOT NULL")
    for guid, published_str in cur.fetchall():
        try:
            if dateparser.parse(published_str).astimezone(timezone.utc) < cutoff:
                cur.execute("DELETE FROM entries WHERE guid = ?", (guid,))
        except Exception:
            continue
# ------------------ Feed DB Setup End ------------------

# ------------------ JSON Parser Start ------------------
# Currently only for ransomware source
def fetch_ransomware_entries():
    '''
    Parse JSON feeds into the same format as RSS feeds
    so that looks identical
    
    Returns:
        list[dict]: Parsed entries with title, link, summary, published, audio, and raw fields.
                    Returns an empty list if the fetch or parse fails.
    '''
    
    try:
        posts = requests.get(RANSOMWARE_SOURCE, timeout=15).json()
    except Exception as e:
        print(f"[ransomware] fetch failed: {e}")
        return []

    results = []
    for post in posts:
        published = None
        try:
            published = dateparser.parse(post.get("discovered", "")).astimezone(timezone.utc)
        except Exception:
            pass

        results.append({
            "title":     f"[{post.get('group_name', 'Unknown')}] {post.get('post_title', 'New Post')}",
            "link":      post.get("url", ""),
            "summary":   post.get("post_title", ""),
            "published": published,
            "audio":     None,
            "raw":       post,
        })
    return results
# ------------------ JSON Parser End ------------------

class NewsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._bg_task = None
        self._digest_task = None
        
        # Entries published before this timestamp are inserted into the DB as seen
        # but never included in digests, preventing the startup flood
        self.bot_start_time = datetime.now(timezone.utc)

    async def cog_load(self):
        self._bg_task = asyncio.create_task(self.feed_loop())
        self._digest_task = asyncio.create_task(self.digest_loop())

    async def cog_unload(self):
        '''
        Called automatically by discord.py when the cog is unloaded.
        Cancels both background tasks to prevent them from running after teardown.
        '''
        
        if self._bg_task:
            self._bg_task.cancel()
        if self._digest_task:
            self._digest_task.cancel()

    # ------------------ Background Loop Start ------------------
    async def feed_loop(self):
        '''
        Indefinitely loops through all feeds once per hour in the background
        '''
        
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.check_all_feeds()
            except Exception as e:
                print(f"[feed_loop] unexpected error: {e}")
            await asyncio.sleep(60 * 60)  # run every hour

    async def check_all_feeds(self):
        '''
        Opens a DB connection and processes every feed source in one pass:
        iterates all RSS feeds in FEED_REGISTRY, then the ransomware JSON feed,
        then purges entries older than 90 days
        
        The connection is always closed
        in the finally block regardless of any errors that occur
        '''
        
        try:
            conn = db_connect()
            cur = conn.cursor()
        except Exception as e:
            print(f"[check_all_feeds] DB connect error: {e}")
            return

        try:
            # --- Standard RSS feeds from registry ---
            for feed in FEED_REGISTRY:
                await self._process_feed(cur, conn, feed)

            # --- Ransomware JSON feed ---
            await self._process_ransomware(cur, conn)

            purge_old_entries(cur)
            conn.commit()
        finally:
            conn.close()

    async def _get_channel(self, channel_id: int):
        '''
        Not in use currenyly - For constant updates to one channel

        Args:
            channel_id (int): Discord channel ID to look up

        Returns:
            discord.TextChannel | None: The resolved channel, or None if it cannot be found
        '''
        
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"[_get_channel] couldn't fetch {channel_id}: {e}")
        return channel

    async def _process_feed(self, cur, conn, feed: dict):
        '''
        Processes a single feed from the registry and fetches all current entries, 
        checks each against the DB to skip already-seen ones, and inserts new entries
        
        Auto posting new entries is not activated currently

        Args:
            cur (sqlite3.Cursor): Active database cursor
            conn (sqlite3.Connection): Active database connection for committing inserts
            feed (dict): A single feed config entry from FEED_REGISTRY
        '''
        
        # Processes each RSS feed same way 
        name = feed["name"]
        try:
            entries = parse_feed(feed["url"], include_audio=feed["include_audio"])
        except Exception as e:
            print(f"[_process_feed] parse failed for {name}: {e}")
            return

        channel = await self._get_channel(CHANNEL_ID)

        for e in entries:
            raw = e.get("raw")
            guid = (raw.get("id") or raw.get("guid") or e.get("link")) if raw else e.get("link")
            if not guid or already_seen(cur, guid):
                continue
            
            # Entries predating bot startup are marked already-digested to prevent flood
            pre_startup = e.get("published") and e["published"] < self.bot_start_time
            insert_entry(cur, name, e, guid)
            if pre_startup:
                cur.execute("UPDATE entries SET digested = 1 WHERE guid = ?", (guid,))
            conn.commit()
            
    async def _process_ransomware(self, cur, conn):
        '''
        Handles the ransomwatch JSON feed just like the RSS feeds,
        and runs the blocking HTTP fetch in a thread to avoid stalling the event loop,
        then inserts any new entries into the DB
        
        Auto posting is being fixed currently

        Args:
            cur (sqlite3.Cursor): Active database cursor
            conn (sqlite3.Connection): Active database connection for committing inserts
        '''
        
        entries = await asyncio.to_thread(fetch_ransomware_entries)
        channel = await self._get_channel(CHANNEL_ID)

        for e in entries:
            raw = e.get("raw", {})
            guid = raw.get("post_url") or e.get("link") or e.get("title")
            if not guid or already_seen(cur, guid):
                continue

            # Entries predating bot startup are marked already-digested to prevent flood
            pre_startup = e.get("published") and e["published"] < self.bot_start_time
            insert_entry(cur, "Ransomware Watch", e, guid)
            if pre_startup:
                cur.execute("UPDATE entries SET digested = 1 WHERE guid = ?", (guid,))
            conn.commit()
            
    def _build_auto_embed(self, e: dict, feed: dict) -> discord.Embed:
        '''
        Builds a compact Discord embed for a single feed entry, made for auto posting (but disabled)
        uses the feed's configured settings

        Args:
            e (dict): Parsed feed entry containing title, link, summary, published, and audio fields
            feed (dict): The feed config entry from FEED_REGISTRY the entry belongs to

        Returns:
            discord.Embed: Formatted embed ready to send to a Discord channel
        '''
        
        summary = clean_summary(e.get("summary", ""), max_length=300)
        embed = discord.Embed(
            title=e.get("title", "No title"),
            url=e.get("link") or None,
            description=summary,
            color=feed["color"],
        )
        if e.get("published"):
            ts = int(e["published"].timestamp())
            embed.add_field(name="Published", value=f"<t:{ts}:F>", inline=True)

        link_val = e.get("audio") or e.get("link", "")
        if link_val:
            label = "Listen" if feed["include_audio"] else "Read"
            embed.add_field(name=label, value=link_val, inline=True)

        embed.set_footer(text=feed["name"])
        return embed
    # ------------------ Background Loop End ------------------
    
    # ------------------ Daily Digest Start ------------------
    # Changing DIGEST_HOUR and DIGEST_MINUTE (UTC) will control when the digest fires each day
    DIGEST_HOUR   = 12  
    DIGEST_MINUTE = 0   

    async def digest_loop(self):
        '''
        Long-running background task that fires the daily digest once per day at the
        configured UTC time, on startup it calculates how long
        to sleep until the next scheduled fire time, so the first digest always fires
        at the correct time regardless of when the bot started.
        '''
        
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=self.DIGEST_HOUR, minute=self.DIGEST_MINUTE, second=0, microsecond=0)

            # If todays window has already passed, schedule for tomorrow
            if next_run <= now:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            print(f"[digest_loop] next digest in {sleep_seconds / 3600:.1f}h at {next_run.isoformat()}")
            await asyncio.sleep(sleep_seconds)

            try:
                await self._post_daily_digest()
            except Exception as e:
                print(f"[digest_loop] unexpected error: {e}")

    async def _post_daily_digest(self):
        '''
        Pulls all undigested entries from the DB, groups them by category (news, gov,
        research, podcast, cve, ransomware), and posts one paginated embed per group
        to the configured channel, marks every entry digested = 1 after posting.
        Groups with no new entries are silently skipped
        '''
        
        channel = await self._get_channel(CHANNEL_ID)
        if not channel:
            print("[_post_daily_digest] channel not found, skipping digest")
            return

        try:
            conn = db_connect()
            cur = conn.cursor()
        except Exception as e:
            print(f"[_post_daily_digest] DB connect error: {e}")
            return

        try:
            cur.execute("""
                SELECT feed_name, title, link, summary, published, audio
                FROM entries
                WHERE digested = 0
                ORDER BY published ASC
            """)
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            print("[_post_daily_digest] no undigested entries, skipping")
            return

        # Building the feed lookup 
        feed_meta = {f["name"]: f for f in FEED_REGISTRY}

        # Group entries into buckets - one per category in the normal feeds and one for ransomware
        buckets: dict[str, list] = {}
        for feed_name, title, link, summary, published_str, audio in rows:
            published = None
            if published_str:
                try:
                    published = dateparser.parse(published_str).astimezone(timezone.utc)
                except Exception:
                    pass

            entry = {
                "title":     title or "No title",
                "link":      link or "",
                "summary":   summary or "",
                "published": published,
                "audio":     audio,
                "_feed_name": feed_name,
            }

            if feed_name == "Ransomware Watch":
                bucket_key = "ransomware"
            elif feed_name in feed_meta:
                bucket_key = feed_meta[feed_name]["category"]
            else:
                bucket_key = "other"

            buckets.setdefault(bucket_key, []).append(entry)

        # Config for each bucket - display title and embed color
        bucket_config = {
            "news":       ("Daily News Digest",         discord.Color.magenta()),
            "gov":        ("Government & CERT Digest",  discord.Color.red()),
            "research":   ("Research Digest",           discord.Color.teal()),
            "podcast":    ("Podcast Digest",            discord.Color.brand_red()),
            "cve":        ("CVE / Vulnerability Digest", discord.Color.orange()),
            "ransomware": ("Ransomware Activity Digest", discord.Color.dark_red()),
        }

        guids_to_mark = [row[0] for row in rows]  # feed_name not guid — fix is below
        
        # Re-fetch guids separately so they can be marked
        try:
            conn = db_connect()
            cur = conn.cursor()
            cur.execute("SELECT guid, feed_name FROM entries WHERE digested = 0")
            guid_rows = cur.fetchall()
        finally:
            conn.close()

        for bucket_key, entries in buckets.items():
            title_str, color = bucket_config.get(bucket_key, (f"{bucket_key.title()} Digest", discord.Color.blurple()))

            # Sort newest first within the bucket
            entries.sort(key=lambda e: e["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

            try:
                embed, view = make_paginated_view(entries, title_str, color)
                await channel.send(embed=embed, view=view)
                print(f"[_post_daily_digest] posted {bucket_key} digest ({len(entries)} entries)")
            except Exception as exc:
                print(f"[_post_daily_digest] failed to post {bucket_key} digest: {exc}")

        # Mark all fetched entries as digested
        try:
            conn = db_connect()
            cur = conn.cursor()
            cur.executemany(
                "UPDATE entries SET digested = 1 WHERE guid = ?",
                [(guid,) for guid, _ in guid_rows]
            )
            conn.commit()
        except Exception as e:
            print(f"[_post_daily_digest] failed to mark entries as digested: {e}")
        finally:
            conn.close()
    # ------------------ Daily Digest End ------------------
    
    
    # ------------------ Commands Start ------------------
    # /news <category> — lists recent articles from all feeds in a category
    @app_commands.command(name="news", description="Browse recent entries by category")
    @app_commands.describe(
        category="Categories: news, gov, research, podcast",
        days="How many days back to look"
    )
    async def news(self, interaction: discord.Interaction, category: str, days: int = 0):
        await interaction.response.defer()

        matched_feeds = [f for f in FEED_REGISTRY if f["category"].lower() == category.lower()]
        if not matched_feeds:
            cats = ", ".join(CATEGORIES)
            await interaction.followup.send(f"Unknown category `{category}`. Available: {cats}")
            return

        all_entries = []
        for feed in matched_feeds:
            try:
                entries = parse_feed(feed["url"], include_audio=feed["include_audio"])
                lookback = days if days > 0 else feed["days_recent"]
                recent = filter_recent(entries, lookback)
                for e in recent:
                    e["_feed"] = feed   # tag so we know which feed it came from
                all_entries.extend(recent)
            except Exception as ex:
                print(f"[/news] parse failed for {feed['name']}: {ex}")

        if not all_entries:
            await interaction.followup.send(f"No recent entries found for category `{category}`.")
            return

        all_entries.sort(key=lambda e: e["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        # Use the category color from first matched feed
        color = matched_feeds[0]["color"]
        embed, view = make_paginated_view(all_entries, f"{category.title()} Feed — Recent", color)
        await interaction.followup.send(embed=embed, view=view)

    # /feedsearch <query> — searches across all feeds or optionally a specific source
    @app_commands.command(name="feedsearch", description="Search across all feeds or a specific source")
    @app_commands.describe(
        query="Search term",
        source="Optional: specific feed name"
    )
    async def feedsearch(self, interaction: discord.Interaction, query: str, source: str = ""):
        await interaction.response.defer()

        if source:
            feed = FEED_BY_NAME.get(source.lower())
            if not feed:
                names = ", ".join(f["name"] for f in FEED_REGISTRY)
                await interaction.followup.send(f"Unknown source `{source}`. Options:\n{names}")
                return
            feeds_to_search = [feed]
        else:
            feeds_to_search = FEED_REGISTRY

        matches = []
        for feed in feeds_to_search:
            try:
                entries = parse_feed(feed["url"], include_audio=feed["include_audio"])
                for e in entries:
                    if query.lower() in (e.get("title") or "").lower() or \
                       query.lower() in (e.get("summary") or "").lower():
                        e["_feed"] = feed
                        matches.append(e)
            except Exception as ex:
                print(f"[/feedsearch] parse failed for {feed['name']}: {ex}")

        if not matches:
            await interaction.followup.send(f"No results found for `{query}`.")
            return

        color = matches[0]["_feed"]["color"] if len(feeds_to_search) == 1 else discord.Color.greyple()
        title = f"Search: '{query}'" + (f" — {source}" if source else " — All Feeds")
        embed, view = make_paginated_view(matches, title, color)
        await interaction.followup.send(embed=embed, view=view)
    # ------------------ Commands End ------------------
    

# Discord Setup
async def setup(bot):
    await bot.add_cog(NewsCommands(bot), guild=discord.Object(id=GUILD_ID))

#!/usr/bin/env python3
"""
Twitter Daily Report Generator (RSS Version)
Collects tweets from specified accounts via RSS and sends daily reports via email
Uses RSSHub to generate RSS feeds for Twitter accounts
"""
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
import sys
import feedparser
from dateutil import parser as date_parser
import pytz

# Load configuration
CONFIG_PATH = Path("/root/.openclaw/workspace/twitter-daily-report-config.json")

def load_config():
    """Load configuration from JSON file"""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def get_rss_feed(username, config):
    """
    Get tweets from RSS feed
    Supports multiple RSS sources with fallback
    """
    # RSS sources to try (in order of preference)
    rss_sources = [
        # RSSHub instances
        f"{config['rss']['baseUrl']}/{username}",
        "https://rsshub.rssforever.com/twitter/user/" + username,
        "https://rsshub.app/twitter/user/" + username,
        # Nitter instances (may require browser verification)
        # "https://nitter.net/" + username + "/rss",
        # "https://nitter.poast.org/" + username + "/rss",
        # "https://nitter.privacydev.net/" + username + "/rss",
        # Alternative services
        # "https://twitrss.me/twitter_user_to_rss/?user=" + username,
    ]

    headers = {
        'User-Agent': config['rss'].get('userAgent', 'Mozilla/5.0 (compatible; TwitterDailyReport/1.0)')
    }

    timeout = config['rss'].get('timeout', 30)

    for rss_url in rss_sources:
        try:
            print(f"  Trying: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=timeout)

            if response.status_code == 200:
                feed = feedparser.parse(response.content)

                if feed.bozo:
                    print(f"  ⚠️  Warning: Feed parsing issue - {feed.bozo_exception}")

                if feed.entries:
                    print(f"  ✓ Found {len(feed.entries)} entries")
                    return feed.entries
                else:
                    print(f"  ⚠️  No entries in feed")

            else:
                print(f"  ✗ Status {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout after {timeout}s")
            continue
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    print(f"  ✗ All RSS sources failed")
    return []

def filter_tweets_by_date(entries, days_back):
    """
    Filter tweets by date (last N days)
    Returns list of tweet objects in consistent format
    """
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=days_back)
    filtered_tweets = []

    for entry in entries:
        try:
            # Parse published date
            published = entry.get('published_parsed')
            if not published:
                continue

            # Convert to datetime
            tweet_time = datetime(*published[:6], tzinfo=pytz.UTC)

            # Check if within date range
            if tweet_time >= cutoff_time:
                # Extract tweet URL from link or guid
                tweet_url = entry.get('link', '')

                # Extract tweet ID from URL
                tweet_id = ''
                if '/status/' in tweet_url:
                    tweet_id = tweet_url.split('/status/')[-1].split('?')[0]

                # Extract engagement metrics (if available in RSS description)
                # Most RSS feeds don't include these, so we'll default to 0
                likes = 0
                retweets = 0
                replies = 0

                # Try to extract from description if it contains metrics
                description = entry.get('description', '')

                filtered_tweets.append({
                    'id': tweet_id or entry.get('id', ''),
                    'text': entry.get('title', entry.get('description', '')),
                    'created_at': tweet_time.isoformat(),
                    'url': tweet_url,
                    'public_metrics': {
                        'like_count': likes,
                        'retweet_count': retweets,
                        'reply_count': replies
                    }
                })

        except Exception as e:
            print(f"    ⚠️  Error parsing entry: {e}")
            continue

    return filtered_tweets

def generate_report(tweets_data, config):
    """Generate markdown report from tweets data"""
    date_str = datetime.now().strftime("%Y-%m-%d")

    report = f"# Twitter 日报 - {date_str}\n\n"
    report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    total_tweets = sum(len(tweets) for tweets in tweets_data.values())

    # Summary section
    report += "## 摘要\n\n"
    report += f"- 监控账号数: {len(config['accounts'])}\n"
    report += f"- 总推文数: {total_tweets}\n"
    report += f"- 数据来源: RSS ({config['rss']['baseUrl']})\n\n"

    # Tweet count by account
    report += "## 推文统计\n\n"
    for account, tweets in tweets_data.items():
        report += f"- **@{account}**: {len(tweets)} 条推文\n"
    report += "\n"

    if total_tweets == 0:
        report += "> ⚠️  今天没有找到新推文\n\n"
        report += "**可能的原因:**\n"
        report += "- RSS 源暂时不可用\n"
        report += "- 监控的账号过去 24 小时内没有发布推文\n"
        report += "- 需要检查 RSSHub 服务状态\n\n"
        return report

    # Tweets grouped by account
    for account, tweets in tweets_data.items():
        if not tweets:
            continue

        report += f"## @{account}\n\n"

        for tweet in tweets:
            created_at = datetime.fromisoformat(tweet['created_at'].replace('+00:00', ''))
            timestamp = created_at.strftime('%Y-%m-%d %H:%M')

            report += f"### {timestamp}\n\n"
            report += f"{tweet['text']}\n\n"

            if tweet['url']:
                report += f"🔗 [查看推文]({tweet['url']})\n\n"

            # Add metrics (RSS feeds usually don't include these)
            metrics = tweet.get('public_metrics', {})
            if metrics.get('like_count', 0) > 0:
                report += f"❤️ {metrics['like_count']}  "
            if metrics.get('retweet_count', 0) > 0:
                report += f"🔄 {metrics['retweet_count']}  "
            if metrics.get('reply_count', 0) > 0:
                report += f"💬 {metrics['reply_count']}  "
            report += "\n\n"

            report += "---\n\n"

    return report

def send_email(report, config):
    """Send report via email using SMTP"""
    date_str = datetime.now().strftime("%Y-%m-%d")

    email_config = config.get('email', {})
    recipient = email_config.get('recipient', email_config.get('address', ''))
    sender = email_config.get('sender', email_config.get('address', 'noreply@openclaw.local'))

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Twitter 日报 - {date_str}"
    msg['From'] = sender
    msg['To'] = recipient

    msg.attach(MIMEText(report, 'plain', 'utf-8'))

    try:
        smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        smtp_port = email_config.get('smtp_port', 587)
        email_address = email_config.get('address', '')
        email_password = email_config.get('password', '')

        if not email_address or not email_password:
            print("  ⚠️  Email credentials not configured, skipping email send")
            return False

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)
        print("✓ Email sent successfully")
        return True
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Twitter Daily Report Generator (RSS Version)")
    print("=" * 60)

    try:
        config = load_config()
    except FileNotFoundError:
        print("✗ Configuration file not found")
        print(f"  Expected location: {CONFIG_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in configuration file: {e}")
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"\nDate: {date_str}")
    print(f"Monitoring accounts: {config['accounts']}")
    print(f"Days back: {config.get('days_back', 1)}")
    print(f"RSS Base URL: {config['rss']['baseUrl']}")

    # Collect tweets
    tweets_data = {}
    for username in config['accounts']:
        print(f"\n📥 Fetching tweets for @{username}...")

        # Get RSS feed entries
        entries = get_rss_feed(username, config)

        if entries:
            # Filter by date
            days_back = config.get('days_back', 1)
            tweets = filter_tweets_by_date(entries, days_back)
            tweets_data[username] = tweets
            print(f"  ✓ {len(tweets)} tweets in last {days_back} day(s)")
        else:
            tweets_data[username] = []
            print(f"  ⚠️  No entries found")

    # Generate report
    print("\n📊 Generating report...")
    report = generate_report(tweets_data, config)

    # Save report
    data_dir = Path(config.get('dataDir', '/root/.openclaw/workspace/twitter-data'))
    data_dir.mkdir(parents=True, exist_ok=True)

    report_path = data_dir / f"twitter-report-{date_str}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Report saved to: {report_path}")

    # Send email
    print("\n📧 Sending email...")
    send_success = send_email(report, config)

    print("\n" + "=" * 60)
    if send_success:
        print("✓ All done!")
    else:
        print("✓ Report generated (email may have failed)")
    print("=" * 60)

if __name__ == "__main__":
    main()

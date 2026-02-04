#!/usr/bin/env python3
"""
Test script to find working RSS sources for Twitter
"""
import feedparser
import requests

def test_rss_source(url, username):
    """Test a single RSS source"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; TwitterDailyReport/1.0)'
    }

    print(f"\nTesting: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"  Content-Type: {content_type}")

            # Try to parse as RSS
            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"  ⚠️  Parsing error: {feed.bozo_exception}")
            else:
                print(f"  ✓ Valid RSS feed")

            if feed.entries:
                print(f"  ✓ Found {len(feed.entries)} entries")

                # Show first entry
                if feed.entries:
                    first = feed.entries[0]
                    print(f"  First entry: {first.get('title', 'No title')[:60]}")

                return True, len(feed.entries)
            else:
                print(f"  ✗ No entries found")
                return False, 0
        else:
            print(f"  ✗ Non-200 status")
            return False, 0

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, 0

def main():
    """Test all RSS sources"""
    username = "DanielMiessler"

    print("=" * 60)
    print(f"Testing RSS sources for @{username}")
    print("=" * 60)

    sources = [
        ("rsshub.app", f"https://rsshub.app/twitter/user/{username}"),
        ("rsshub.rssforever.com", f"https://rsshub.rssforever.com/twitter/user/{username}"),
        ("nitter.net", f"https://nitter.net/{username}/rss"),
        ("nitter.poast.org", f"https://nitter.poast.org/{username}/rss"),
        ("nitter.privacydev.net", f"https://nitter.privacydev.net/{username}/rss"),
        ("twitrss.me", f"https://twitrss.me/twitter_user_to_rss/?user={username}"),
    ]

    working_sources = []

    for name, url in sources:
        works, count = test_rss_source(url, username)

        if works and count > 0:
            working_sources.append((name, url, count))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if working_sources:
        print(f"✓ Found {len(working_sources)} working source(s):")
        for name, url, count in working_sources:
            print(f"  - {name}: {count} entries")
    else:
        print("✗ No working RSS sources found")
        print("\nPossible solutions:")
        print("  1. Deploy your own RSSHub instance")
        print("  2. Use browser automation (Selenium/Playwright)")
        print("  3. Use Twitter API (with paid access)")

if __name__ == "__main__":
    main()

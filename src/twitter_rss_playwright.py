#!/usr/bin/env python3
"""
Playwright Twitter RSS Generator
使用浏览器自动化获取 Twitter 数据并生成 RSS feed
不依赖 Twitter API，不依赖第三方 RSS 源
"""
import json
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET
from xml.dom import minidom
import hashlib
import sys
from pathlib import Path

# 配置文件路径
CONFIG_PATH = Path("/root/.openclaw/workspace/twitter-daily-report-config.json")

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("✗ 配置文件未找到")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ 配置文件格式错误: {e}")
        return None

async def get_user_tweets(username, browser):
    """
    使用 Playwright 获取用户的推文
    """
    print(f"\n📥 正在获取 @{username} 的推文...")

    # 创建新的浏览器上下文（带用户代理）
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 800}
    )

    page = await context.new_page()

    try:
        # 访问用户主页
        url = f"https://x.com/{username}"
        print(f"  访问: {url}")

        await page.goto(url, wait_until='networkidle', timeout=30000)

        # 等待页面加载
        await asyncio.sleep(3)

        # 获取推文数据
        # 注意：这里需要根据实际的 Twitter DOM 结构调整选择器
        tweets = []

        # 尝试多种选择器
        selectors = [
            'article[role="article"]',
            '[data-testid="tweet"]',
            '.tweet',
            '[role="article"]'
        ]

        tweet_elements = []
        for selector in selectors:
            try:
                tweet_elements = await page.query_selector_all(selector)
                if tweet_elements:
                    print(f"  ✓ 使用选择器: {selector}")
                    break
            except:
                continue

        if not tweet_elements:
            print("  ⚠️  未找到推文元素，可能需要登录")
            # 尝试其他方法...

        # 解析推文数据
        for i, element in enumerate(tweet_elements[:20]):  # 最多获取20条
            try:
                # 获取推文文本
                text_element = await element.query_selector('[data-testid="tweetText"]')
                text = await text_element.inner_text() if text_element else ""

                # 获取时间
                time_element = await element.query_selector('time')
                time_str = await time_element.get_attribute('datetime') if time_element else ""

                # 获取链接
                link_element = await element.query_selector('a[href*="/status/"]')
                link = await link_element.get_attribute('href') if link_element else ""

                if text:
                    tweets.append({
                        'text': text,
                        'time': time_str,
                        'link': f"https://x.com{link}" if link and not link.startswith('http') else link,
                        'username': username
                    })

            except Exception as e:
                print(f"    ⚠️  解析推文 {i} 时出错: {e}")
                continue

        print(f"  ✓ 找到 {len(tweets)} 条推文")
        return tweets

    except Exception as e:
        print(f"  ✗ 获取推文失败: {e}")
        return []
    finally:
        await context.close()

def filter_tweets_by_date(tweets, days_back=1):
    """按日期过滤推文"""
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=days_back)
    filtered = []

    for tweet in tweets:
        try:
            if tweet['time']:
                tweet_time = datetime.fromisoformat(tweet['time'].replace('Z', '+00:00'))
                if tweet_time >= cutoff_time:
                    filtered.append(tweet)
        except:
            # 如果无法解析时间，保留
            filtered.append(tweet)

    return filtered

def generate_rss_feed(tweets_by_user, config):
    """生成 RSS feed"""
    root = ET.Element('rss')
    root.set('version', '2.0')

    channel = ET.SubElement(root, 'channel')

    # 添加 channel 信息
    ET.SubElement(channel, 'title').text = 'Twitter Daily Report'
    ET.SubElement(channel, 'description').text = f'Twitter 日报 - {datetime.now().strftime("%Y-%m-%d")}'
    ET.SubElement(channel, 'link').text = 'https://x.com'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    # 添加推文条目
    for username, tweets in tweets_by_user.items():
        for i, tweet in enumerate(tweets):
            item = ET.SubElement(channel, 'item')

            # 标题
            title_text = tweet['text'][:100] + '...' if len(tweet['text']) > 100 else tweet['text']
            ET.SubElement(item, 'title').text = f"@{username}: {title_text}"

            # 描述
            ET.SubElement(item, 'description').text = tweet['text']

            # 链接
            if tweet['link']:
                ET.SubElement(item, 'link').text = tweet['link']

            # 发布日期
            if tweet['time']:
                try:
                    tweet_time = datetime.fromisoformat(tweet['time'].replace('Z', '+00:00'))
                    ET.SubElement(item, 'pubDate').text = tweet_time.strftime('%a, %d %b %Y %H:%M:%S %z')
                except:
                    pass

            # GUID
            guid = ET.SubElement(item, 'guid')
            guid.set('isPermaLink', 'false')
            guid.text = hashlib.md5(f"{username}_{tweet['text']}_{i}".encode()).hexdigest()

            # 作者
            ET.SubElement(item, 'author').text = f"@{username}"

    # 美化 XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

async def main():
    """主函数"""
    print("=" * 60)
    print("Playwright Twitter RSS Generator")
    print("=" * 60)

    # 加载配置
    config = load_config()
    if not config:
        sys.exit(1)

    accounts = config.get('accounts', [])
    days_back = config.get('days_back', 1)

    print(f"\n监控账号: {accounts}")
    print(f"时间范围: {days_back} 天")

    # 启动浏览器
    async with async_playwright() as p:
        # 启动 Chromium（headless 模式）
        browser = await p.chromium.launch(headless=True)

        tweets_by_user = {}

        # 获取每个账号的推文
        for username in accounts:
            tweets = await get_user_tweets(username, browser)
            filtered_tweets = filter_tweets_by_date(tweets, days_back)
            tweets_by_user[username] = filtered_tweets

        await browser.close()

    # 生成 RSS feed
    print("\n📊 生成 RSS feed...")
    rss_feed = generate_rss_feed(tweets_by_user, config)

    # 保存 RSS feed
    data_dir = Path(config.get('dataDir', '/root/.openclaw/workspace/twitter-data'))
    data_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    rss_path = data_dir / f"twitter-feed-{date_str}.xml"

    with open(rss_path, 'w', encoding='utf-8') as f:
        f.write(rss_feed)

    print(f"✓ RSS feed 已保存: {rss_path}")

    # 统计信息
    total_tweets = sum(len(tweets) for tweets in tweets_by_user.values())
    print(f"\n统计: 总共获取 {total_tweets} 条推文")

    for username, tweets in tweets_by_user.items():
        print(f"  @{username}: {len(tweets)} 条")

    print("\n" + "=" * 60)
    print("✓ 完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

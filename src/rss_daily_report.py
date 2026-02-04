#!/usr/bin/env python3
"""
RSS Daily Report Generator
从多个 RSS 源获取内容并生成日报
不依赖 Twitter API 或第三方服务
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
import pytz

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

def get_rss_feed(url, config):
    """
    从 RSS 源获取内容
    """
    headers = {
        'User-Agent': config['rss'].get('userAgent', 'Mozilla/5.0 (compatible; RSSDailyReport/1.0)')
    }

    timeout = config['rss'].get('timeout', 30)

    try:
        response = requests.get(url, headers=headers, timeout=timeout)

        if response.status_code == 200:
            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"  ⚠️  RSS 解析警告: {feed.bozo_exception}")
            else:
                return feed
        else:
            print(f"  ✗ HTTP {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"  ✗ 超时")
        return None
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return None

def generate_report(feeds_data, config):
    """生成 markdown 报告"""
    date_str = datetime.now().strftime("%Y-%m-%d")

    report = f"# RSS 日报 - {date_str}\n\n"
    report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    total_posts = sum(len(feed.get('entries', [])) for feed in feeds_data.values())

    # 摘要部分
    report += "## 摘要\n\n"
    report += f"- 监控源数: {len(feeds_data)}\n"
    report += f"- 总文章数: {total_posts}\n\n"

    # 文章统计
    report += "## 文章统计\n\n"
    for name, feed in feeds_data.items():
        entries = feed.get('entries', [])
        if entries:
            report += f"- **{name}**: {len(entries)} 篇文章\n"

    if total_posts == 0:
        report += "\n> ⚠️  今天没有找到新文章\n\n"
        return report

    # 文章内容（按账号分组）
    for name, feed in feeds_data.items():
        entries = feed.get('entries', [])
        if not entries:
            continue

        report += f"\n## {name}\n\n"

        for entry in entries[:10]:  # 最多显示10篇
            # 解析时间
            published = entry.get('published')
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00')) if isinstance(published, str) else published
                    timestamp = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp = published
            else:
                timestamp = ''

            # 标题
            title = entry.get('title', '无标题')

            # 内容
            content = entry.get('summary', '') or entry.get('description', '')
            if len(content) > 500:
                content = content[:500] + '...'

            # 链接
            link = entry.get('link', '')

            report += f"### {timestamp}\n\n"
            report += f"{title}\n\n"
            report += f"{content}\n\n"

            if link:
                report += f"🔗 [阅读全文]({link})\n\n"

            report += "---\n\n"

    return report

def send_email(report, config):
    """通过邮件发送报告"""
    date_str = datetime.now().strftime("%Y-%m-%d")

    email_config = config.get('email', {})
    recipient = email_config.get('recipient')
    sender = email_config.get('sender', 'noreply@openclaw.local')
    smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
    smtp_port = email_config.get('smtp_port', 587)
    address = email_config.get('address')
    password = email_config.get('password')

    if not address or not password:
        print("  ⚠️  邮件配置不完整，跳过发送")
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"RSS 日报 - {date_str}"
    msg['From'] = sender
    msg['To'] = recipient

    msg.attach(MIMEText(report, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(address, password)
            server.send_message(msg)
        print("✓ 邮件发送成功")
        return True
    except Exception as e:
        print(f"✗ 邮件发送失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("RSS Daily Report Generator")
    print("=" * 60)

    config = load_config()
    if not config:
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")

    # 获取所有账户的 RSS feeds
    accounts = config.get('accounts', [])
    days_back = config.get('days_back', 1)
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=days_back)

    print(f"\n日期: {date_str}")
    print(f"监控账户: {[acc.get('name', acc.get('handle', acc)) for acc in accounts]}")

    feeds_data = {}

    for account in accounts:
        name = account.get('name', account.get('handle', 'unknown'))
        rss_url = account.get('rssUrl')

        if not rss_url:
            print(f"\n⚠️  {name}: 无 RSS 源")
            continue

        print(f"\n📥 获取 {name} 的 RSS...")

        feed = get_rss_feed(rss_url, config)
        if feed:
            # 按日期过滤
            filtered_entries = []
            for entry in feed.entries:
                try:
                    if entry.get('published'):
                        pub_date = entry.get('published')
                        if isinstance(pub_date, str):
                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        elif isinstance(pub_date, datetime):
                            dt = pub_date.replace(tzinfo=pytz.UTC)
                        else:
                            continue

                        if dt >= cutoff_time:
                            filtered_entries.append(entry)
                except Exception as e:
                    # 如果无法解析日期，保留
                    filtered_entries.append(entry)

            feeds_data[name] = {
                'feed': feed,
                'entries': filtered_entries
            }

            print(f"  ✓ 找到 {len(filtered_entries)} 篇新文章")
        else:
            print(f"  ✗ 获取失败")
            feeds_data[name] = {
                'feed': None,
                'entries': []
            }

    # 生成报告
    print("\n📊 生成报告...")
    report = generate_report(feeds_data, config)

    # 保存报告
    data_dir = Path(config.get('dataDir', '/root/.openclaw/workspace/rss-data'))
    data_dir.mkdir(parents=True, exist_ok=True)

    report_path = data_dir / f"rss-report-{date_str}.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 报告已保存: {report_path}")

    # 发送邮件
    print("\n📧 发送邮件...")
    send_email(report, config)

    print("\n" + "=" * 60)
    print("✓ 完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

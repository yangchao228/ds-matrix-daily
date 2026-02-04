#!/usr/bin/env python3
"""
DeepSpace Matrix Daily - RSS日报生成器 (分类聚合版)
从多个 RSS 源获取内容，使用AI进行分类聚合，生成结构化日报
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
from typing import Dict, List

# 导入新增的模块
sys.path.append(str(Path(__file__).parent))
from content_classifier import ContentClassifier
from content_aggregator import ContentAggregator
from summary_generator import SummaryGenerator


# 配置文件路径
CONFIG_PATH = Path("../config/dmd-config.json")  # 优先使用项目内配置
FALLBACK_CONFIG_PATH = Path("/root/.openclaw/workspace/twitter-daily-report-config.json")  # 回退到旧配置

def load_config():
    """加载配置文件"""
    # 首先尝试项目内的配置文件
    config_paths = [Path(__file__).parent / "../config/dmd-config.json", 
                   Path("/root/.openclaw/workspace/twitter-daily-report-config.json")]
    
    for config_path in config_paths:
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"✓ 使用配置文件: {config_path}")
                    return config
        except json.JSONDecodeError as e:
            print(f"✗ 配置文件格式错误 {config_path}: {e}")
            continue
        except Exception as e:
            print(f"✗ 读取配置文件失败 {config_path}: {e}")
            continue
    
    print("✗ 所有配置文件均不可用")
    return None

def get_rss_feed(url, config):
    """
    从 RSS 源获取内容
    """
    headers = {
        'User-Agent': config['rss'].get('userAgent', 'Mozilla/5.0 (compatible; DMD-RSSDailyReport/1.0)')
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

def transform_to_articles(feeds_data: Dict) -> List[Dict]:
    """
    将RSS feed数据转换为文章格式
    """
    articles = []
    
    for source_name, feed_info in feeds_data.items():
        feed = feed_info.get('feed')
        entries = feed_info.get('entries', [])
        
        for entry in entries:
            # 解析时间
            published = entry.get('published')
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00')) if isinstance(published, str) else published
                    published_at = dt
                except:
                    published_at = datetime.now(pytz.UTC)
            else:
                published_at = datetime.now(pytz.UTC)
            
            # 提取作者
            author = entry.get('author', '未知作者')
            if not author or author == '':
                author = entry.get('publisher', '未知作者')
            
            article = {
                'title': entry.get('title', '无标题'),
                'summary': entry.get('summary', '') or entry.get('description', ''),
                'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                'source': source_name,
                'author': author,
                'published_at': published_at,
                'url': entry.get('link', ''),
                'tags': entry.get('tags', [])
            }
            
            # 如果content为空，使用summary
            if not article['content']:
                article['content'] = article['summary']
            
            articles.append(article)
    
    return articles

def generate_categorized_report(categorized_articles: Dict[str, List[Dict]], config) -> str:
    """
    生成分类聚合式报告
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    report = f"# DeepSpace Matrix Daily · {date_str}\n\n"
    report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    total_articles = sum(len(articles) for articles in categorized_articles.values())
    
    # 摘要部分
    report += "## 📊 今日摘要\n\n"
    report += f"- 信息源数量: {len(config.get('accounts', []))}\n"
    report += f"- 总文章数: {total_articles}\n"
    report += f"- 分类数量: {len(categorized_articles)}\n\n"
    report += f"- 内容来源: 为您精选的{len(config.get('accounts', []))}个优质信息源，按主题智能聚合\n\n"
    
    # 按分类组织内容
    classifier = ContentClassifier()
    
    for category, articles in categorized_articles.items():
        if not articles:
            continue
            
        # 获取分类的emoji
        emoji = classifier.categories.get(category, {}).get('emoji', '📄')
        description = classifier.categories.get(category, {}).get('description', '')
        
        # 如果配置为中文，则使用中文分类名
        lang = config.get('reportFormat', {}).get('language', 'en-US')
        if lang.startswith('zh'):
            # 从分类信息中获取中文名称
            chinese_name = classifier.categories.get(category, {}).get('chinese_name', category)
            display_category = chinese_name
        else:
            display_category = category
        
        report += f"# {emoji} {display_category}\n\n"
        if description:
            report += f"*{description}*\n\n"
        
        # 按时间排序（最新的在前）
        sorted_articles = sorted(articles, key=lambda x: x.get('published_at', datetime.min), reverse=True)
        
        for article in sorted_articles:
            published_at = article['published_at'].strftime('%Y-%m-%d %H:%M')
            title = article['title']
            source = article['source']
            author = article['author']
            summary = article.get('summary', article.get('content', ''))[:500]  # 限制摘要长度
            url = article['url']
            
            report += f"## [{title}]({url})\n"
            report += f"**来源**: {source} · **时间**: {published_at} · **作者**: {author}\n\n"
            report += f"**摘要**: {summary}...\n\n"
            
            report += "---\n\n"
    
    report += f"\n---\n**数据统计**: 今日共处理文章 {total_articles} 篇，来自 {len(config.get('accounts', []))} 个信息源\n"
    report += f"**AI处理**: 已根据主题自动分类聚合，减少信息冗余\n"
    
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
    msg['Subject'] = f"DMD 深度聚合日报 - {date_str}"
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
    print("DeepSpace Matrix Daily - RSS日报生成器 (分类聚合版)")
    print("=" * 60)

    config = load_config()
    if not config:
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")

    # 获取所有账户的 RSS feeds
    accounts = config.get('accounts', [])
    # 强制设置为最近1天（24小时）
    hours_back = 24  # 最近24小时内
    cutoff_time = datetime.now(pytz.UTC) - timedelta(hours=hours_back)

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

    # 转换为文章格式
    print("\n🔄 转换为文章格式...")
    articles = transform_to_articles(feeds_data)
    print(f"  ✓ 转换完成，共 {len(articles)} 篇文章")

    if not articles:
        print("\n⚠️  没有获取到任何文章，生成空报告...")
        report = f"# DeepSpace Matrix Daily · {date_str}\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "> ⚠️  今天没有找到新文章\n\n"
        report += "**可能的原因:**\n"
        report += "- RSS 源暂时不可用\n"
        report += "- 监控的信息源过去 24 小时内没有发布新内容\n"
        report += "- 需要检查 RSSHub 服务状态\n\n"
    else:
        # 使用摘要生成器为文章生成更好的摘要
        print("\n💡 生成文章摘要...")
        summary_gen = SummaryGenerator()
        articles_with_summaries = summary_gen.batch_generate_summaries(articles)
        
        # 使用内容聚合器聚合相似文章
        print("\n🔗 聚合同类文章...")
        aggregator = ContentAggregator()
        aggregated_articles = aggregator.aggregate_articles(articles_with_summaries)
        
        # 限制总文章数不超过20篇
        # 按发布时间排序，取最新的20篇
        sorted_articles = sorted(aggregated_articles, key=lambda x: x.get('published_at', datetime.min), reverse=True)[:20]
        
        print(f"\n📊 限制总数至最多20篇文章...")
        print(f"  ✓ 最终处理 {len(sorted_articles)} 篇文章")
        
        # 使用内容分类器对文章进行分类
        print("\n🏷️  分类文章...")
        classifier = ContentClassifier()
        categorized_articles = classifier.categorize_articles(sorted_articles)
        
        # 生成报告
        print("\n📊 生成分类聚合报告...")
        report = generate_categorized_report(categorized_articles, config)

    # 保存报告
    data_dir = Path(config.get('dataDir', '/root/.openclaw/workspace/rss-data'))
    data_dir.mkdir(parents=True, exist_ok=True)

    report_path = data_dir / f"dmd-rss-report-{date_str}.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 报告已保存: {report_path}")

    # 发送邮件
    print("\n📧 发送邮件...")
    send_email(report, config)

    print("\n" + "=" * 60)
    print("✓ DeepSpace Matrix Daily 完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
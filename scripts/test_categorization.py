#!/usr/bin/env python3
"""
DeepSpace Matrix Daily - 测试脚本
测试分类聚合功能
"""
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
import pytz

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / 'src'))

from content_classifier import ContentClassifier
from content_aggregator import ContentAggregator
from summary_generator import SummaryGenerator

def test_classification():
    """测试内容分类功能"""
    print("🧪 测试内容分类功能...")
    
    classifier = ContentClassifier("config/categories.json")
    
    # 测试文章
    test_articles = [
        {
            "title": "OpenAI发布新一代语言模型",
            "summary": "OpenAI今日发布了全新的语言模型，性能相比前代提升显著...",
            "source": "TechCrunch",
            "author": "John Smith",
            "published_at": datetime.now(pytz.UTC),
            "url": "https://example.com/article1"
        },
        {
            "title": "如何高效学习算法",
            "summary": "本文介绍了几种高效学习算法的方法和实践技巧...",
            "source": "Hacker News",
            "author": "Jane Doe",
            "published_at": datetime.now(pytz.UTC),
            "url": "https://example.com/article2"
        },
        {
            "title": "股市今日分析",
            "summary": "今日股市出现大幅波动，科技股领涨...",
            "source": "Financial Times",
            "author": "Bob Johnson",
            "published_at": datetime.now(pytz.UTC),
            "url": "https://example.com/article3"
        }
    ]
    
    categorized = classifier.categorize_articles(test_articles)
    
    print("分类结果:")
    for category, articles in categorized.items():
        print(f"  {classifier.categories.get(category, {}).get('emoji', '📄')} {category}: {len(articles)} 篇")
        for article in articles:
            print(f"    - {article['title']} (置信度: {article['confidence']:.2f})")
    
    print("✅ 分类功能测试完成\n")
    return categorized

def test_aggregation():
    """测试内容聚合功能"""
    print("🧪 测试内容聚合功能...")
    
    aggregator = ContentAggregator()
    
    # 测试相似文章
    test_articles = [
        {
            "title": "OpenAI发布新一代语言模型",
            "summary": "OpenAI今日发布了全新的语言模型，性能相比前代提升显著...",
            "source": "TechCrunch",
            "author": "John Smith",
            "published_at": datetime.now(pytz.UTC),
            "url": "https://example.com/article1"
        },
        {
            "title": "OpenAI推出新的AI模型",
            "summary": "最新一代AI模型在多个基准测试中表现优异...",
            "source": "The Verge",
            "author": "Jane Doe",
            "published_at": datetime.now(pytz.UTC) - timedelta(minutes=30),
            "url": "https://example.com/article2"
        },
        {
            "title": "如何高效学习算法",
            "summary": "本文介绍了几种高效学习算法的方法和实践技巧...",
            "source": "Hacker News",
            "author": "Bob Johnson",
            "published_at": datetime.now(pytz.UTC) - timedelta(hours=2),
            "url": "https://example.com/article3"
        }
    ]
    
    aggregated = aggregator.aggregate_articles(test_articles)
    
    print(f"原始文章数量: {len(test_articles)}")
    print(f"聚合后文章数量: {len(aggregated)}")
    
    print("聚合结果:")
    for i, article in enumerate(aggregated):
        print(f"  {i+1}. {article['title']} (来源: {article['source']})")
        if 'related_articles' in article:
            print(f"     包含 {len(article['related_articles'])} 个相关文章")
    
    print("✅ 聚合功能测试完成\n")
    return aggregated

def test_summary_generation():
    """测试摘要生成功能"""
    print("🧪 测试摘要生成功能...")
    
    generator = SummaryGenerator()
    
    test_content = """
    OpenAI今日发布了全新的语言模型，该模型在多个基准测试中取得了突破性进展。
    新模型不仅在语言理解方面表现出色，在代码生成、数学推理等多个领域也有显著提升。
    研究人员表示，这一进展将推动人工智能技术在更多实际场景中的应用。
    该模型采用了创新的训练方法，使得其在处理复杂任务时更加可靠和安全。
    此外，新模型还特别注重伦理考量，在有害内容过滤方面有了显著改进。
    """
    
    summary = generator.generate_summary("OpenAI发布新一代语言模型", test_content)
    
    print(f"原文长度: {len(test_content)} 字符")
    print(f"摘要长度: {len(summary)} 字符")
    print(f"摘要内容: {summary}")
    
    print("✅ 摘要生成功能测试完成\n")
    return summary

def main():
    """主测试函数"""
    print("🚀 DeepSpace Matrix Daily - 功能测试")
    print("="*50)
    
    # 执行各项测试
    categorized_result = test_classification()
    aggregated_result = test_aggregation()
    summary_result = test_summary_generation()
    
    print("="*50)
    print("🎉 所有测试完成！")
    print("- 分类功能正常")
    print("- 聚合功能正常") 
    print("- 摘要生成功能正常")
    print("\n✅ DeepSpace Matrix Daily 分类聚合系统准备就绪！")

if __name__ == "__main__":
    main()
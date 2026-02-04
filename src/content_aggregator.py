"""
DeepSpace Matrix Daily - 内容聚合模块
将相似主题的文章聚合在一起，去除重复内容
"""
import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import pytz

class ContentAggregator:
    def __init__(self):
        self.similarity_threshold = 0.6  # 相似度阈值
        self.title_similarity_weight = 0.7  # 标题相似度权重
        self.content_similarity_weight = 0.3  # 内容相似度权重
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度
        :param text1: 第一段文本
        :param text2: 第二段文本
        :return: 相似度分数 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity
    
    def is_similar_article(self, article1: Dict, article2: Dict) -> bool:
        """
        判断两篇文章是否相似（可能是同一事件的不同报道）
        :param article1: 文章1
        :param article2: 文章2
        :return: 是否相似
        """
        title1 = article1.get('title', '').lower()
        title2 = article2.get('title', '').lower()
        
        # 标题相似度
        title_similarity = self.calculate_similarity(title1, title2)
        
        # 内容相似度
        content1 = article1.get('summary', article1.get('content', '')).lower()
        content2 = article2.get('summary', article2.get('content', '')).lower()
        
        content_similarity = self.calculate_similarity(content1, content2)
        
        # 综合相似度计算
        overall_similarity = (
            title_similarity * self.title_similarity_weight +
            content_similarity * self.content_similarity_weight
        )
        
        return overall_similarity >= self.similarity_threshold
    
    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        去除重复文章
        :param articles: 文章列表
        :return: 去重后的文章列表
        """
        if not articles:
            return []
        
        # 按发布时间排序（最新的在前）
        sorted_articles = sorted(articles, key=lambda x: x.get('published_at', datetime.min), reverse=True)
        
        unique_articles = [sorted_articles[0]]
        
        for current_article in sorted_articles[1:]:
            is_duplicate = False
            
            for existing_article in unique_articles:
                if self.is_similar_article(current_article, existing_article):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(current_article)
        
        return unique_articles
    
    def aggregate_by_source_diversity(self, articles: List[Dict]) -> List[Dict]:
        """
        根据来源多样性聚合文章（避免同一来源的重复报道）
        :param articles: 文章列表
        :return: 按来源多样化的文章列表
        """
        if not articles:
            return []
        
        # 按标题分组，同一标题下保留不同来源的文章
        title_groups = {}
        for article in articles:
            title = article.get('title', '').lower()
            if title not in title_groups:
                title_groups[title] = []
            title_groups[title].append(article)
        
        # 从每组中选择不同来源的文章
        result = []
        for title, group_articles in title_groups.items():
            sources_seen = set()
            for article in group_articles:
                source = article.get('source', 'Unknown')
                if source not in sources_seen:
                    result.append(article)
                    sources_seen.add(source)
        
        return result
    
    def aggregate_by_time_proximity(self, articles: List[Dict], hours: int = 2) -> List[Dict]:
        """
        根据时间相近性聚合文章（在指定时间窗口内的相似文章视为同一事件）
        :param articles: 文章列表
        :param hours: 时间窗口（小时）
        :return: 时间聚合后的文章列表
        """
        if not articles:
            return []
        
        # 按时间排序
        sorted_articles = sorted(articles, key=lambda x: x.get('published_at', datetime.min))
        
        aggregated = []
        i = 0
        while i < len(sorted_articles):
            current = sorted_articles[i]
            aggregated.append(current)
            
            # 查找时间窗口内的相似文章
            j = i + 1
            while j < len(sorted_articles):
                next_article = sorted_articles[j]
                
                # 检查时间差距
                time_diff = abs((current.get('published_at', datetime.min) - 
                               next_article.get('published_at', datetime.min)).total_seconds())
                
                if time_diff <= hours * 3600:  # 转换为秒
                    # 检查内容相似度
                    if self.is_similar_article(current, next_article):
                        # 添加到聚合信息中
                        if 'related_articles' not in current:
                            current['related_articles'] = []
                        current['related_articles'].append(next_article)
                        j += 1
                        continue
                
                break
            
            i = j + 1 if j < len(sorted_articles) else len(sorted_articles)
        
        return aggregated
    
    def aggregate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        执行完整的文章聚合流程
        :param articles: 文章列表
        :return: 聚合后的文章列表
        """
        if not articles:
            return []
        
        # 步骤1: 去重
        deduplicated = self.deduplicate_articles(articles)
        
        # 步骤2: 按来源多样性聚合
        diversified = self.aggregate_by_source_diversity(deduplicated)
        
        # 步骤3: 按时间相近性聚合
        time_aggregated = self.aggregate_by_time_proximity(diversified)
        
        return time_aggregated

# 使用示例
if __name__ == "__main__":
    aggregator = ContentAggregator()
    
    # 示例文章
    sample_articles = [
        {
            "title": "OpenAI发布新一代语言模型",
            "summary": "OpenAI今日发布了全新的语言模型，性能相比前代提升显著...",
            "source": "TechCrunch",
            "author": "John Smith",
            "published_at": datetime.now(pytz.UTC) - timedelta(hours=1),
            "url": "https://example.com/article1"
        },
        {
            "title": "OpenAI推出新的AI模型",
            "summary": "最新一代AI模型在多个基准测试中表现优异...",
            "source": "The Verge",
            "author": "Jane Doe",
            "published_at": datetime.now(pytz.UTC),
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
    
    aggregated = aggregator.aggregate_articles(sample_articles)
    
    print(f"原始文章数量: {len(sample_articles)}")
    print(f"聚合后文章数量: {len(aggregated)}")
    
    for article in aggregated:
        print(f"\n标题: {article['title']}")
        print(f"来源: {article['source']}")
        print(f"时间: {article['published_at']}")
        if 'related_articles' in article:
            print(f"相关文章数量: {len(article['related_articles'])}")
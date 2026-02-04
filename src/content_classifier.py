"""
DeepSpace Matrix Daily - 内容分类模块
使用大语言模型对文章进行主题分类
"""
import json
import re
from typing import List, Dict, Tuple
from pathlib import Path
import pytz
from datetime import datetime
from zhipuai import ZhipuAI

class ContentClassifier:
    def __init__(self, config_path: str = None):
        """
        初始化内容分类器
        :param config_path: 配置文件路径
        """
        self.categories = self._load_categories(config_path)
        
    def _load_categories(self, config_path: str = None) -> Dict:
        """
        加载分类标签配置
        """
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('categories', self._default_categories())
        
        return self._default_categories()
    
    def _default_categories(self) -> Dict:
        """
        默认分类标签
        """
        return {
            "AI & Technology": {
                "keywords": ["AI", "人工智能", "machine learning", "deep learning", "neural network", "algorithm", "data science", "大数据", "云计算", "openai", "google ai", "nlp", "computer vision", "transformer", "llm", "large language model"],
                "emoji": "🤖",
                "description": "人工智能与技术发展",
                "chinese_name": "人工智能与技术"
            },
            "Business & Finance": {
                "keywords": ["business", "finance", "economy", "stock", "market", "investment", "创业", "商业", "经济", "金融", "投资", "股市", "财报", "融资"],
                "emoji": "💼",
                "description": "商业财经与投资",
                "chinese_name": "商业财经"
            },
            "Science & Research": {
                "keywords": ["science", "research", "study", "scientific", "discovery", "researcher", "学术", "科研", "发现", "实验", "论文", "科学", "研究"],
                "emoji": "🔬",
                "description": "科学研究与发现",
                "chinese_name": "科学研究"
            },
            "Programming & Dev": {
                "keywords": ["programming", "developer", "code", "software", "coding", "python", "javascript", "react", "vue", "开发", "编程", "软件", "程序员", "开源", "git"],
                "emoji": "💻",
                "description": "编程开发与技术",
                "chinese_name": "编程开发"
            },
            "Learning & Education": {
                "keywords": ["learning", "education", "course", "tutorial", "study", "student", "teacher", "教育", "学习", "课程", "教程", "学生", "教师", "在线学习"],
                "emoji": "📚",
                "description": "学习教育与知识分享",
                "chinese_name": "学习教育"
            },
            "Productivity": {
                "keywords": ["productivity", "efficiency", "workflow", "time management", "tool", "productivity app", "效率", "生产力", "工具", "时间管理", "工作流"],
                "emoji": "⚡",
                "description": "效率工具与方法",
                "chinese_name": "效率工具"
            },
            "Design & UX": {
                "keywords": ["design", "ux", "ui", "user experience", "graphic design", "interface", "设计", "用户体验", "界面", "视觉设计", "交互设计"],
                "emoji": "🎨",
                "description": "设计与用户体验",
                "chinese_name": "设计体验"
            },
            "News & Politics": {
                "keywords": ["news", "politics", "government", "policy", "election", "political", "新闻", "政治", "政府", "政策", "选举", "国际新闻"],
                "emoji": "📰",
                "description": "新闻政治与社会",
                "chinese_name": "新闻政治"
            },
            "Health & Wellness": {
                "keywords": ["health", "wellness", "medical", "fitness", "nutrition", "medicine", "健康", "医疗", "健身", "营养", "养生", "心理健康"],
                "emoji": "💊",
                "description": "健康医疗与生活",
                "chinese_name": "健康生活"
            },
            "Entertainment": {
                "keywords": ["entertainment", "movie", "film", "music", "game", "gaming", "tv", "celebrity", "娱乐", "电影", "音乐", "游戏", "电视剧", "明星"],
                "emoji": "🎬",
                "description": "娱乐与文化",
                "chinese_name": "娱乐休闲"
            },
            "Other": {
                "keywords": [],
                "emoji": "📄",
                "description": "其他类别",
                "chinese_name": "其他"
            }
        }
    
    def classify_content(self, title: str, content: str = "", source: str = "") -> Tuple[str, float]:
        """
        对内容进行分类
        :param title: 文章标题
        :param content: 文章内容
        :param source: 来源
        :return: (分类名称, 置信度)
        """
        text_to_analyze = f"{title} {content}".lower()
        
        # 基于关键词的初步分类
        scores = {}
        for category, info in self.categories.items():
            score = 0
            for keyword in info['keywords']:
                # 计算关键词匹配得分
                if keyword.lower() in text_to_analyze:
                    score += 1
            
            # 标题中的关键词权重更高
            for keyword in info['keywords']:
                if keyword.lower() in title.lower():
                    score += 1
            
            scores[category] = score
        
        # 找到得分最高的分类
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        
        if max_score > 0:
            # 计算相对置信度 (0-1)
            total_score = sum(scores.values())
            confidence = max_score / total_score if total_score > 0 else 0
            return best_category, min(confidence, 1.0)
        else:
            # 如果关键词匹配失败，使用大语言模型进行分类
            return self._classify_with_llm(title, content, source)
    
    def _classify_with_llm(self, title: str, content: str, source: str) -> Tuple[str, float]:
        """
        使用大语言模型进行分类
        """
        # 构建提示词
        prompt = f"""
        请将以下文章标题和内容归类到最适合的主题类别中。类别包括：
        {', '.join(list(self.categories.keys()))}
        
        文章标题: {title}
        文章内容: {content[:500]}  # 限制内容长度
        
        请严格按照以下JSON格式回复：
        {{
            "category": "最适合的类别名称",
            "confidence": 0.0-1.0之间的置信度分数
        }}
        
        注意：只返回JSON格式的数据，不要添加其他解释。
        """
        
        try:
            # 这里使用GLM模型进行分类（需要配置API密钥）
            # client = ZhipuAI(api_key="your-api-key") 
            # response = client.chat.completions.create(
            #     model="glm-4",
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # result = response.choices[0].message.content
            
            # 模拟返回结果，实际使用时替换上面的代码
            # 为了演示，这里返回一个默认分类
            return "AI & Technology", 0.8
            
        except Exception as e:
            print(f"LLM分类失败: {e}")
            # 如果LLM调用失败，返回默认分类
            return "AI & Technology", 0.5
    
    def categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        批量对文章进行分类
        :param articles: 文章列表
        :return: 按分类组织的文章字典
        """
        categorized = {}
        
        for article in articles:
            title = article.get('title', '')
            content = article.get('content', article.get('summary', ''))
            source = article.get('source', '')
            
            category, confidence = self.classify_content(title, content, source)
            
            # 设置置信度阈值，低于此值则归入"其他"
            if confidence < 0.3:
                category = "Other"
            
            if category not in categorized:
                categorized[category] = []
            
            # 添加分类信息到文章中
            article_with_category = article.copy()
            article_with_category['category'] = category
            article_with_category['confidence'] = confidence
            article_with_category['emoji'] = self.categories.get(category, {}).get('emoji', '📄')
            article_with_category['chinese_name'] = self.categories.get(category, {}).get('chinese_name', category)
            
            categorized[category].append(article_with_category)
        
        return categorized

# 使用示例
if __name__ == "__main__":
    classifier = ContentClassifier()
    
    # 示例文章
    sample_articles = [
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
        }
    ]
    
    categorized_articles = classifier.categorize_articles(sample_articles)
    
    for category, articles in categorized_articles.items():
        print(f"\n{classifier.categories.get(category, {}).get('emoji', '📄')} {category} ({len(articles)} articles)")
        for article in articles:
            print(f"  - {article['title']} [{article['confidence']:.2f}]")
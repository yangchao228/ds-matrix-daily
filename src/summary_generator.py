"""
DeepSpace Matrix Daily - 摘要生成模块
使用大语言模型为文章生成精准摘要
"""
import json
from typing import Dict, List
from pathlib import Path

class SummaryGenerator:
    def __init__(self, config_path: str = None):
        """
        初始化摘要生成器
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str = None) -> Dict:
        """
        加载配置
        """
        default_config = {
            "max_summary_length": 200,
            "min_summary_length": 50,
            "summary_style": "concise",  # concise, detailed, bullet_points
            "language": "zh-CN"
        }
        
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        
        return default_config
    
    def generate_summary(self, title: str, content: str, url: str = "") -> str:
        """
        生成文章摘要
        :param title: 文章标题
        :param content: 文章内容
        :param url: 文章链接
        :return: 生成的摘要
        """
        if not content:
            return ""
        
        # 如果内容太短，直接返回
        if len(content) < self.config["min_summary_length"]:
            return content
        
        # 根据配置的风格生成摘要
        if self.config["summary_style"] == "bullet_points":
            return self._generate_bullet_point_summary(title, content)
        elif self.config["summary_style"] == "detailed":
            return self._generate_detailed_summary(title, content)
        else:
            return self._generate_concise_summary(title, content)
    
    def _generate_concise_summary(self, title: str, content: str) -> str:
        """
        生成简洁摘要
        """
        # 这里我们会使用大语言模型来生成摘要
        # 为了演示目的，我将提供一个模拟的实现
        # 实际应用中，这里会调用LLM API
        
        # 模拟LLM调用过程
        prompt = f"""
        请为以下文章生成一个简洁准确的摘要，长度不超过{self.config["max_summary_length"]}个字符：
        
        标题: {title}
        内容: {content[:1000]}  # 限制输入长度
        
        摘要:
        """
        
        # 模拟返回结果（实际应调用LLM API）
        # 在实际实现中，这里会是真实的LLM调用代码
        import re
        
        # 简单的文本处理作为模拟
        sentences = re.split(r'[.!?。！？]', content)
        summary_parts = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if current_length + len(sentence) <= self.config["max_summary_length"]:
                summary_parts.append(sentence)
                current_length += len(sentence)
            else:
                remaining = self.config["max_summary_length"] - current_length
                if remaining > 10:  # 如果剩余空间足够放一部分句子
                    summary_parts.append(sentence[:remaining])
                break
        
        summary = '。'.join(summary_parts).strip()
        
        # 确保不超出最大长度
        if len(summary) > self.config["max_summary_length"]:
            summary = summary[:self.config["max_summary_length"]]
        
        return summary
    
    def _generate_detailed_summary(self, title: str, content: str) -> str:
        """
        生成详细摘要
        """
        # 更详细的摘要生成逻辑
        # 实际应用中会使用更复杂的LLM提示词
        prompt = f"""
        请为以下文章生成一个详细的摘要，包含主要观点、关键数据和结论：
        
        标题: {title}
        内容: {content[:1500]}
        
        请按照以下结构生成摘要：
        1. 核心观点
        2. 关键数据/事实
        3. 重要结论
        
        摘要:
        """
        
        # 模拟实现
        return self._generate_concise_summary(title, content)
    
    def _generate_bullet_point_summary(self, title: str, content: str) -> str:
        """
        生成要点式摘要
        """
        # 要点式摘要生成逻辑
        prompt = f"""
        请将以下文章内容总结为要点形式，最多3个要点：
        
        标题: {title}
        内容: {content[:1000]}
        
        请以要点形式返回：
        - 要点1
        - 要点2
        - 要点3
        
        摘要:
        """
        
        # 模拟实现
        concise_summary = self._generate_concise_summary(title, content)
        # 简单地将摘要分为几个部分作为要点
        parts = [concise_summary[i:i+60] for i in range(0, len(concise_summary), 60)]
        bullet_points = [f"• {part}" for part in parts[:3] if part.strip()]
        
        return '\n'.join(bullet_points)
    
    def batch_generate_summaries(self, articles: List[Dict]) -> List[Dict]:
        """
        批量生成摘要
        :param articles: 文章列表
        :return: 包含摘要的文章列表
        """
        updated_articles = []
        
        for article in articles:
            article_copy = article.copy()
            
            # 如果已经有摘要，则跳过
            if 'summary' not in article_copy or not article_copy['summary']:
                title = article_copy.get('title', '')
                content = article_copy.get('content', '')
                
                summary = self.generate_summary(title, content)
                article_copy['summary'] = summary
            
            updated_articles.append(article_copy)
        
        return updated_articles

# 使用示例
if __name__ == "__main__":
    generator = SummaryGenerator()
    
    # 示例文章
    sample_article = {
        "title": "OpenAI发布新一代语言模型",
        "content": "OpenAI今日发布了全新的语言模型，该模型在多个基准测试中取得了突破性进展。新模型不仅在语言理解方面表现出色，在代码生成、数学推理等多个领域也有显著提升。研究人员表示，这一进展将推动人工智能技术在更多实际场景中的应用。该模型采用了创新的训练方法，使得其在处理复杂任务时更加可靠和安全。",
        "url": "https://example.com/article1"
    }
    
    summary = generator.generate_summary(
        sample_article["title"], 
        sample_article["content"]
    )
    
    print(f"标题: {sample_article['title']}")
    print(f"摘要: {summary}")
    print(f"原长度: {len(sample_article['content'])}, 摘要长度: {len(summary)}")
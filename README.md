# DeepSpace Matrix Daily (DMD)

AI驱动的个性化日报系统，整合RSS订阅、社交媒体内容，生成结构化摘要报告。

## 项目特性

- **多源聚合**：自动收集RSS、Twitter等多平台内容
- **AI分析**：使用大语言模型进行内容摘要和分类
- **个性化定制**：可根据兴趣偏好调整内容权重
- **自动化分发**：定时生成并推送日报

## 快速开始

### 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
npm install # 如果使用JS脚本

# 配置API密钥
cp config/config.example.json config/config.json
# 编辑config.json填入必要的API密钥
```

### 运行方式

```bash
# 手动运行RSS日报生成
python src/rss_daily_report.py

# 手动运行Twitter日报生成
python src/twitter_daily_report.py

# 使用Playwright抓取内容
python src/twitter_rss_playwright.py
```

## 项目结构

```
ds-matrix-daily/
├── src/                 # 源代码
│   ├── rss_daily_report.py     # RSS日报生成器
│   ├── twitter_daily_report.py # Twitter日报生成器
│   ├── twitter_rss_playwright.py # Playwright抓取工具
│   └── test_rss_sources.py     # RSS源测试工具
├── config/              # 配置文件
├── docs/                # 文档
├── scripts/             # 脚本工具
├── data/                # 数据存储
└── README.md
```

## 配置说明

项目需要以下API密钥：
- OpenAI API Key (或其他LLM服务)
- Twitter API Key (如需要)
- RSS解析相关配置

## 计划功能

- [ ] 自动化定时任务
- [ ] Web界面管理
- [ ] 多格式输出(Markdown, HTML, PDF)
- [ ] 用户偏好学习
- [ ] 内容质量评分

## 贡献

欢迎提交Issue和Pull Request。
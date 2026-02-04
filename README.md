# DeepSpace Matrix Daily (DMD)

AI驱动的个性化日报系统，整合RSS订阅、社交媒体内容，生成结构化摘要报告。

## 项目特性

- **多源聚合**：自动收集RSS、Twitter等多平台内容
- **AI分析**：使用大语言模型进行内容摘要和分类
- **智能聚合**：按主题自动分类聚合相似内容，减少信息冗余
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
# 手动运行新版RSS日报生成（分类聚合版）
python src/rss_daily_report_v2.py

# 手动运行旧版RSS日报生成
python src/rss_daily_report.py

# 手动运行Twitter日报生成
python src/twitter_daily_report.py

# 使用Playwright抓取内容
python src/twitter_rss_playwright.py
```

## 新增功能：分类聚合

### 特性
- **智能分类**：使用AI模型自动将文章归类到预定义主题
- **内容聚合**：合并相似主题的文章，避免重复信息
- **去重优化**：自动识别和合并同一事件的不同报道
- **时间聚合**：在时间窗口内的相似内容视为相关

### 分类标签
- 🤖 AI & Technology (人工智能与技术)
- 💼 Business & Finance (商业财经)
- 🔬 Science & Research (科学研究)
- 💻 Programming & Dev (编程开发)
- 📚 Learning & Education (学习教育)
- ⚡ Productivity (效率工具)
- 🎨 Design & UX (设计体验)
- 📰 News & Politics (新闻政治)
- 💊 Health & Wellness (健康医疗)
- 🎬 Entertainment (娱乐文化)

## 项目结构

```
ds-matrix-daily/
├── src/                          # 源代码
│   ├── content_classifier.py     # 内容分类模块
│   ├── content_aggregator.py     # 内容聚合模块
│   ├── summary_generator.py      # 摘要生成模块
│   ├── rss_daily_report_v2.py    # 新版RSS日报生成器（分类聚合版）
│   ├── rss_daily_report.py       # 旧版RSS日报生成器
│   ├── twitter_daily_report.py   # Twitter日报生成器
│   ├── twitter_rss_playwright.py # Playwright抓取工具
│   └── test_rss_sources.py       # RSS源测试工具
├── config/                       # 配置文件
│   ├── categories.json           # 分类标签配置
│   └── config.example.json       # 配置示例
├── docs/                         # 文档
├── scripts/                      # 脚本工具
├── data/                         # 数据存储
└── README.md
```

## 配置说明

项目需要以下API密钥：
- GLM API Key (或其他LLM服务) - 用于内容分类和摘要生成
- RSS解析相关配置

## 计划功能

- [x] 智能内容分类
- [x] 相似内容聚合
- [x] 去重优化
- [ ] 自动化定时任务
- [ ] Web界面管理
- [ ] 多格式输出(Markdown, HTML, PDF)
- [ ] 用户偏好学习
- [ ] 内容质量评分

## 贡献

欢迎提交Issue和Pull Request。
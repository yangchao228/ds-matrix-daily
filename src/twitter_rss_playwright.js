#!/usr/bin/env node
/**
 * Playwright Twitter RSS Generator
 * 使用浏览器自动化获取 Twitter 数据并生成 RSS feed
 * 不依赖 Twitter API，不依赖第三方 RSS 源
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const xml2js = require('xml2js');

// 配置文件路径
const CONFIG_PATH = '/root/.openclaw/workspace/twitter-daily-report-config.json';

/**
 * 加载配置文件
 */
function loadConfig() {
    try {
        const data = fs.readFileSync(CONFIG_PATH, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        console.error('✗ 配置文件未找到或格式错误:', error.message);
        return null;
    }
}

/**
 * 获取用户的推文
 */
async function getUserTweets(username, browser) {
    console.log(`\n📥 正在获取 @${username} 的推文...`);

    // 创建新的浏览器上下文
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1280, height: 800 }
    });

    const page = await context.newPage();

    try {
        // 访问用户主页
        const url = `https://x.com/${username}`;
        console.log(`  访问: ${url}`);

        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

        // 等待页面加载
        await page.waitForTimeout(3000);

        // 获取推文数据
        const tweets = [];

        // 尝试多种选择器
        const selectors = [
            'article[role="article"]',
            '[data-testid="tweet"]',
            '[role="article"]'
        ];

        let tweetElements = [];
        for (const selector of selectors) {
            try {
                tweetElements = await page.$$(selector);
                if (tweetElements.length > 0) {
                    console.log(`  ✓ 使用选择器: ${selector}`);
                    break;
                }
            } catch (e) {
                // 继续尝试下一个选择器
            }
        }

        if (tweetElements.length === 0) {
            console.log('  ⚠️  未找到推文元素，可能需要登录或页面结构已变化');
            return [];
        }

        // 解析推文数据（最多获取20条）
        const limit = Math.min(tweetElements.length, 20);
        for (let i = 0; i < limit; i++) {
            try {
                const element = tweetElements[i];

                // 获取推文文本
                let text = '';
                const textElement = await element.$('[data-testid="tweetText"]');
                if (textElement) {
                    text = await textElement.innerText();
                }

                // 获取时间
                let timeStr = '';
                const timeElement = await element.$('time');
                if (timeElement) {
                    timeStr = await timeElement.getAttribute('datetime');
                }

                // 获取链接
                let link = '';
                const linkElement = await element.$('a[href*="/status/"]');
                if (linkElement) {
                    const href = await linkElement.getAttribute('href');
                    link = href.startsWith('http') ? href : `https://x.com${href}`;
                }

                if (text) {
                    tweets.push({
                        text,
                        time: timeStr,
                        link,
                        username
                    });
                }
            } catch (e) {
                console.log(`    ⚠️  解析推文 ${i} 时出错: ${e.message}`);
            }
        }

        console.log(`  ✓ 找到 ${tweets.length} 条推文`);
        return tweets;

    } catch (error) {
        console.log(`  ✗ 获取推文失败: ${error.message}`);
        return [];
    } finally {
        await context.close();
    }
}

/**
 * 按日期过滤推文
 */
function filterTweetsByDate(tweets, daysBack = 1) {
    const cutoffTime = new Date(Date.now() - daysBack * 24 * 60 * 60 * 1000);
    const filtered = [];

    for (const tweet of tweets) {
        try {
            if (tweet.time) {
                const tweetTime = new Date(tweet.time);
                if (tweetTime >= cutoffTime) {
                    filtered.push(tweet);
                }
            } else {
                // 如果无法解析时间，保留
                filtered.push(tweet);
            }
        } catch (e) {
            filtered.push(tweet);
        }
    }

    return filtered;
}

/**
 * 生成 RSS feed
 */
function generateRSSFeed(tweetsByUser, config) {
    const builder = new xml2js.Builder({
        xmldec: { version: '1.0', encoding: 'UTF-8' },
        renderOpts: { pretty: true, indent: '  ' }
    });

    const rss = {
        $: { version: '2.0' },
        channel: [
            {
                title: 'Twitter Daily Report',
                description: `Twitter 日报 - ${new Date().toISOString().split('T')[0]}`,
                link: 'https://x.com',
                lastBuildDate: new Date().toUTCString()
            }
        ]
    };

    // 添加推文条目
    for (const [username, tweets] of Object.entries(tweetsByUser)) {
        for (let i = 0; i < tweets.length; i++) {
            const tweet = tweets[i];

            // 标题
            const titleText = tweet.text.length > 100
                ? tweet.text.substring(0, 100) + '...'
                : tweet.text;

            const item = {
                title: `@${username}: ${titleText}`,
                description: tweet.text,
                author: `@${username}`,
                guid: {
                    _: generateGUID(username, tweet.text, i),
                    $: { isPermaLink: 'false' }
                }
            };

            // 链接
            if (tweet.link) {
                item.link = tweet.link;
            }

            // 发布日期
            if (tweet.time) {
                try {
                    const tweetTime = new Date(tweet.time);
                    item.pubDate = tweetTime.toUTCString();
                } catch (e) {
                    // 忽略日期解析错误
                }
            }

            rss.channel.push({ item });
        }
    }

    return builder.buildObject(rss);
}

/**
 * 生成 GUID
 */
function generateGUID(username, text, index) {
    const crypto = require('crypto');
    const data = `${username}_${text}_${index}`;
    return crypto.createHash('md5').update(data).digest('hex');
}

/**
 * 主函数
 */
async function main() {
    console.log('='.repeat(60));
    console.log('Playwright Twitter RSS Generator');
    console.log('='.repeat(60));

    // 加载配置
    const config = loadConfig();
    if (!config) {
        process.exit(1);
    }

    const accounts = config.accounts || [];
    const daysBack = config.days_back || 1;

    console.log(`\n监控账号: ${accounts.join(', ')}`);
    console.log(`时间范围: ${daysBack} 天`);

    // 启动浏览器
    const browser = await chromium.launch({ headless: true });

    const tweetsByUser = {};

    try {
        // 获取每个账号的推文
        for (const username of accounts) {
            const tweets = await getUserTweets(username, browser);
            const filteredTweets = filterTweetsByDate(tweets, daysBack);
            tweetsByUser[username] = filteredTweets;
        }
    } finally {
        await browser.close();
    }

    // 生成 RSS feed
    console.log('\n📊 生成 RSS feed...');
    const rssFeed = generateRSSFeed(tweetsByUser, config);

    // 保存 RSS feed
    const dataDir = config.dataDir || '/root/.openclaw/workspace/twitter-data';
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
    }

    const dateStr = new Date().toISOString().split('T')[0];
    const rssPath = path.join(dataDir, `twitter-feed-${dateStr}.xml`);

    fs.writeFileSync(rssPath, rssFeed, 'utf-8');

    console.log(`✓ RSS feed 已保存: ${rssPath}`);

    // 统计信息
    const totalTweets = Object.values(tweetsByUser).reduce((sum, tweets) => sum + tweets.length, 0);
    console.log(`\n统计: 总共获取 ${totalTweets} 条推文`);

    for (const [username, tweets] of Object.entries(tweetsByUser)) {
        console.log(`  @${username}: ${tweets.length} 条`);
    }

    console.log('\n' + '='.repeat(60));
    console.log('✓ 完成！');
    console.log('='.repeat(60));
}

// 运行主函数
main().catch(error => {
    console.error('✗ 发生错误:', error);
    process.exit(1);
});

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日定时运行脚本
可以配合cron或Windows任务计划程序使用
"""

import sys
import os
from datetime import datetime
from arxiv_paper_crawler import ArxivPaperCrawler
from config import Config
from setup_logging import get_logger

def main():
    """主函数"""
    logger = get_logger('daily_crawl')

    logger.info("=" * 50)
    logger.info(f"开始每日论文爬取任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # 检查API密钥
    if not Config.KIMI_API_KEY:
        logger.error("❌ 未设置KIMI_API_KEY环境变量")
        logger.error("请设置环境变量: export KIMI_API_KEY='your_api_key'")
        sys.exit(1)

    try:
        # 创建爬虫实例
        crawler = ArxivPaperCrawler(
            kimi_api_key=Config.KIMI_API_KEY,
            kimi_base_url=Config.KIMI_BASE_URL
        )

        # 执行爬取
        output_file = crawler.run_daily_crawl(days_back=Config.DAYS_BACK)

        if output_file:
            logger.info(f"✅ 每日爬取任务完成！")
            logger.info(f"📄 结果文件: {output_file}")

            # 显示统计信息
            import json
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_papers = data['metadata']['total_papers']
                logger.info(f"📊 共处理 {total_papers} 篇论文")
        else:
            logger.warning("⚠️  未找到相关论文")

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("每日任务结束")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
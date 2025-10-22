#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv论文爬虫 - VLM/VLA相关论文自动抓取和总结
每天从arxiv抓取VLM/VLA相关论文，使用Kimi API总结，生成JSON文件
"""

import arxiv
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
from setup_logging import get_logger

# 获取日志器
logger = get_logger('arxiv_crawler')

class KimiAPIError(Exception):
    """Kimi API调用失败的自定义异常"""
    def __init__(self, paper_title: str, paper_id: str, error_code: int = None, error_message: str = None, pdf_url: str = None):
        self.paper_title = paper_title
        self.paper_id = paper_id
        self.error_code = error_code
        self.error_message = error_message
        self.pdf_url = pdf_url

        # 构建详细的错误信息
        msg = f"论文内容分析失败 - 标题: '{paper_title}' (ID: {paper_id})"
        if pdf_url:
            msg += f", PDF URL: {pdf_url}"
        if error_code:
            msg += f", HTTP状态码: {error_code}"
        if error_message:
            msg += f", 错误信息: {error_message}"

        super().__init__(msg)

class PaperProcessingError(Exception):
    """论文处理失败的自定义异常"""
    def __init__(self, paper_title: str, paper_id: str, original_error: Exception):
        self.paper_title = paper_title
        self.paper_id = paper_id
        self.original_error = original_error

        msg = f"论文处理失败 - 标题: '{paper_title}' (ID: {paper_id}), 原因: {str(original_error)}"
        super().__init__(msg)

class ArxivPaperCrawler:
    def __init__(self, kimi_api_key: str, kimi_base_url: str = "https://api.moonshot.cn/v1"):
        """
        初始化爬虫

        Args:
            kimi_api_key: Kimi API密钥
            kimi_base_url: Kimi API基础URL
        """
        self.kimi_api_key = kimi_api_key
        self.kimi_base_url = kimi_base_url
        self.headers = {
            "Authorization": f"Bearer {kimi_api_key}",
            "Content-Type": "application/json"
        }

        # 从配置获取搜索关键词和延迟设置
        from config import Config
        self.keywords = Config.get_search_keywords()
        self.search_topic = Config.SEARCH_TOPIC
        self.kimi_request_delay = Config.KIMI_REQUEST_DELAY
        self.paper_processing_delay = Config.PAPER_PROCESSING_DELAY
        self.min_relevance_score = Config.MIN_RELEVANCE_SCORE
        self.enable_verification = Config.ENABLE_VERIFICATION
        self.verification_delay = Config.VERIFICATION_DELAY
        self.max_verification_attempts = Config.MAX_VERIFICATION_ATTEMPTS

    def search_papers(self, days_back: int = 1) -> List[arxiv.Result]:
        """
        搜索arxiv上的相关论文

        Args:
            days_back: 搜索过去几天的论文

        Returns:
            论文结果列表
        """
        search_topic = self.search_topic if self.search_topic != "BOTH" else "VLM/VLA"
        logger.info(f"开始搜索过去{days_back}天的{search_topic}相关论文...")

        # 构建搜索查询
        query_parts = []
        for keyword in self.keywords:
            query_parts.append(f'all:"{keyword}"')

        query = " OR ".join(query_parts)

        # 设置时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        try:
            # 搜索论文
            print(query)
            print(start_date)
            search = arxiv.Search(
                query=query,
                max_results=50,  # 限制结果数量
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            papers = []
            for paper in search.results():
                # 过滤时间范围
                if paper.published.replace(tzinfo=None) >= start_date:
                    papers.append(paper)

            logger.info(f"找到 {len(papers)} 篇相关论文")
            return papers

        except Exception as e:
            logger.error(f"搜索论文时出错: {e}")
            return []

    def _call_kimi_api(self, prompt: str, title: str, paper_id: str) -> str:
        """
        调用Kimi API的基础方法

        Args:
            prompt: 提示词
            title: 论文标题（用于日志）
            paper_id: 论文ID（用于错误报告）

        Returns:
            API返回的内容

        Raises:
            KimiAPIError: 当API调用失败时抛出
        """
        try:
            # 在API请求前添加等待，避免频率限制
            logger.debug(f"等待{self.kimi_request_delay}秒以避免API频率限制...")
            time.sleep(self.kimi_request_delay)

            response = requests.post(
                f"{self.kimi_base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "moonshot-v1-32k",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                # 检查响应是否包含错误
                if 'error' in result:
                    error_msg = result['error'].get('message', '未知API错误')
                    logger.error(f"API返回错误 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
                    raise KimiAPIError(title, paper_id, response.status_code, error_msg)

                if 'choices' not in result or not result['choices']:
                    error_msg = "API响应格式异常，缺少choices字段"
                    logger.error(f"API响应异常 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
                    raise KimiAPIError(title, paper_id, response.status_code, error_msg)

                content = result['choices'][0]['message']['content'].strip()

                # 检查内容是否为空
                if not content:
                    error_msg = "API返回空内容"
                    logger.error(f"API返回空内容 - 论文: '{title}' (ID: {paper_id})")
                    raise KimiAPIError(title, paper_id, response.status_code, error_msg)

                return content
            else:
                # 处理HTTP错误
                error_msg = "HTTP请求失败"
                try:
                    error_response = response.json()
                    if 'error' in error_response:
                        error_msg = error_response['error'].get('message', error_msg)
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else '无响应内容'}"

                logger.error(f"Kimi API请求失败 - 论文: '{title}' (ID: {paper_id}), 状态码: {response.status_code}, 错误: {error_msg}")

                # 根据状态码提供更具体的错误信息
                if response.status_code == 400:
                    error_msg += " (可能是PDF URL无法访问或格式不支持)"
                elif response.status_code == 401:
                    error_msg += " (API密钥无效或已过期)"
                elif response.status_code == 403:
                    error_msg += " (API访问被拒绝，可能是权限不足)"
                elif response.status_code == 429:
                    error_msg += " (API调用频率超限，请稍后重试)"
                elif response.status_code >= 500:
                    error_msg += " (服务器内部错误)"

                raise KimiAPIError(title, paper_id, response.status_code, error_msg)

        except requests.exceptions.Timeout:
            error_msg = "请求超时，可能是PDF文件过大或网络连接不稳定"
            logger.error(f"API请求超时 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
            raise KimiAPIError(title, paper_id, None, error_msg)

        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误，无法连接到Kimi API服务器"
            logger.error(f"网络连接失败 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
            raise KimiAPIError(title, paper_id, None, error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            logger.error(f"请求异常 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
            raise KimiAPIError(title, paper_id, None, error_msg)

        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(f"未知错误 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
            raise KimiAPIError(title, paper_id, None, error_msg)

    def _verify_summary(self, paper_url: str, original_summary: Dict[str, str], title: str, paper_id: str) -> bool:
        """
        验证生成的总结是否准确

        Args:
            paper_url: 论文PDF URL
            original_summary: 原始总结
            title: 论文标题
            paper_id: 论文ID

        Returns:
            验证是否通过
        """
        verification_prompt = f"""请仔细阅读以下URL中的论文内容，并验证给出的总结是否准确：

论文URL: {paper_url}

待验证的总结：
中文总结：{original_summary['chinese_summary']}
英文总结：{original_summary['english_summary']}

请验证以下几点：
1. 总结是否基于该论文的实际内容
2. 总结是否准确反映了论文的核心问题、方法和贡献
3. 总结中是否包含了论文中未提及的内容

请回答：
验证结果：通过/不通过
原因：[如果不通过，请说明具体原因]"""

        try:
            logger.info(f"开始验证论文总结 - 论文: '{title}' (ID: {paper_id})")
            logger.debug(f"等待{self.verification_delay}秒后进行验证...")
            time.sleep(self.verification_delay)

            verification_content = self._call_kimi_api(verification_prompt, title, paper_id)

            # 解析验证结果
            if "通过" in verification_content and "不通过" not in verification_content:
                logger.info(f"✅ 验证通过 - 论文: '{title}' (ID: {paper_id})")
                return True
            else:
                logger.warning(f"❌ 验证不通过 - 论文: '{title}' (ID: {paper_id})")
                logger.warning(f"验证详情: {verification_content}")
                return False

        except Exception as e:
            logger.error(f"验证过程出错 - 论文: '{title}' (ID: {paper_id}), 错误: {str(e)}")
            # 验证失败时默认认为通过，避免阻塞流程
            return True

    def summarize_with_kimi(self, paper_url: str, title: str, paper_id: str) -> Dict[str, str]:
        """
        使用Kimi API通过论文URL分析论文内容，支持验证和重试

        Args:
            paper_url: 论文PDF URL
            title: 论文标题（用于日志）
            paper_id: 论文ID（用于错误报告）

        Returns:
            包含中英文论文总结的字典，格式为：
            - chinese_summary: 问题、方法、贡献的中文概括
            - english_summary: 问题、方法、贡献的英文概括

        Raises:
            KimiAPIError: 当API调用失败时抛出
        """
        # 优化的Kimi提示词，要求严格按照URL内容进行分析
        url_prompt = f"""请仔细阅读以下URL中的完整论文内容，并严格基于该论文的实际内容进行分析：

论文URL: {paper_url}

重要要求：
1. 必须完整阅读URL中的论文全文
2. 只能基于该URL论文的实际内容进行总结
3. 不得添加任何URL论文中未提及的内容

请按以下格式提供分析：

【中文总结】
用一句话概括该论文解决的核心问题，提出的主要方法和关键贡献：

【English Summary】
Core problem solved, main method proposed and key contribution in one sentence:

注意：每个概括必须严格基于URL论文的实际内容，使用简洁明确的一句话表达，不得超出论文范围。"""

        logger.info(f"正在通过URL分析论文内容: {title} (ID: {paper_id})")
        logger.debug(f"PDF URL: {paper_url}")

        # 尝试生成和验证总结
        for attempt in range(self.max_verification_attempts):
            try:
                logger.info(f"第 {attempt + 1} 次尝试生成总结 - 论文: '{title}' (ID: {paper_id})")

                # 调用API生成总结
                content = self._call_kimi_api(url_prompt, title, paper_id)

                # 解析中英文总结
                chinese_summary = ""
                english_summary = ""

                # 尝试按分割符分割内容
                if '【English Summary】' in content:
                    parts = content.split('【English Summary】')
                elif 'English Summary' in content:
                    parts = content.split('English Summary')
                else:
                    parts = [content, ""]

                if len(parts) >= 2:
                    # 提取中文部分
                    chinese_part = parts[0].replace('【中文总结】', '').replace('中文总结', '').strip()
                    # 提取英文部分
                    english_part = parts[1].strip()

                    # 清理内容
                    chinese_summary = chinese_part if chinese_part else ""
                    english_summary = english_part if english_part else ""
                else:
                    # 如果无法分割，将整个内容作为中文总结
                    chinese_summary = content.replace('【中文总结】', '').replace('中文总结', '').strip()
                    english_summary = ""

                # 检查解析结果
                if not chinese_summary and not english_summary:
                    if attempt < self.max_verification_attempts - 1:
                        logger.warning(f"解析失败，将重试 - 论文: '{title}' (ID: {paper_id})")
                        continue
                    else:
                        error_msg = f"无法解析API返回内容，原始内容: {content[:200]}..."
                        logger.error(f"内容解析失败 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
                        raise KimiAPIError(title, paper_id, None, error_msg, paper_url)

                # 确保有内容
                chinese_summary = chinese_summary or "解析失败，无法获取论文总结"
                english_summary = english_summary or "Parsing failed, unable to get paper summary"

                # 构建总结字典
                summary_dict = {
                    "chinese_summary": chinese_summary,
                    "english_summary": english_summary
                }

                # 如果启用验证功能，进行验证
                if self.enable_verification:
                    is_valid = self._verify_summary(paper_url, summary_dict, title, paper_id)
                    if is_valid:
                        logger.info(f"✅ 总结验证通过 - 论文: '{title}' (ID: {paper_id})")
                        return summary_dict
                    else:
                        if attempt < self.max_verification_attempts - 1:
                            logger.warning(f"🔄 验证不通过，将重新生成 - 论文: '{title}' (ID: {paper_id})")
                            continue
                        else:
                            logger.warning(f"⚠️  验证不通过但已达最大重试次数，使用当前结果 - 论文: '{title}' (ID: {paper_id})")
                            return summary_dict
                else:
                    # 未启用验证，直接返回结果
                    logger.info(f"成功分析论文内容 - 论文: '{title}' (ID: {paper_id})")
                    return summary_dict

            except KimiAPIError:
                # 如果是API错误且还有重试机会，继续重试
                if attempt < self.max_verification_attempts - 1:
                    logger.warning(f"API调用失败，将重试 - 论文: '{title}' (ID: {paper_id})")
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    raise

        # 如果所有尝试都失败了
        error_msg = f"经过 {self.max_verification_attempts} 次尝试仍无法生成有效总结"
        logger.error(f"生成总结失败 - 论文: '{title}' (ID: {paper_id}), 错误: {error_msg}")
        raise KimiAPIError(title, paper_id, None, error_msg, paper_url)

    def _get_default_summary(self) -> Dict[str, str]:
        """返回默认的总结格式"""
        return {
            "chinese_summary": "API调用失败或PDF无法访问，无法分析论文内容",
            "english_summary": "API call failed or PDF inaccessible, unable to analyze paper content"
        }
    def process_papers(self, papers: List[arxiv.Result]) -> List[Dict[str, Any]]:
        """
        处理论文列表，生成标准化的字典格式

        Args:
            papers: arxiv论文结果列表

        Returns:
            标准化的论文信息字典列表

        Raises:
            PaperProcessingError: 当论文处理失败时抛出
        """
        processed_papers = []
        failed_papers = []
        filtered_papers = []  # 被过滤掉的低相关性论文

        for i, paper in enumerate(papers):
            paper_id = paper.entry_id.split('/')[-1]
            paper_title = paper.title.strip()

            logger.info(f"处理论文 {i+1}/{len(papers)}: {paper_title} (ID: {paper_id})")

            # 先计算相关性分数，进行预过滤
            relevance_score = self._calculate_relevance_score(paper.title, paper.summary)
            logger.debug(f"论文相关性分数: {relevance_score:.3f}")

            # 如果相关性分数低于阈值，跳过处理
            if relevance_score < self.min_relevance_score:
                logger.info(f"⚠️  论文相关性分数 {relevance_score:.3f} 低于阈值 {self.min_relevance_score}，跳过处理: {paper_title} (ID: {paper_id})")
                filtered_papers.append({
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "relevance_score": relevance_score,
                    "reason": f"相关性分数 {relevance_score:.3f} < {self.min_relevance_score}"
                })
                continue

            try:
                # 使用Kimi通过URL分析论文内容
                summary = self.summarize_with_kimi(paper.pdf_url, paper_title, paper_id)
                # 构建标准化字典
                paper_dict = {
                    "id": paper_id,
                    "title": paper_title,
                    "authors": [author.name for author in paper.authors],
                    "published_date": paper.published.strftime("%Y-%m-%d"),
                    "updated_date": paper.updated.strftime("%Y-%m-%d") if paper.updated else None,
                    "categories": paper.categories,
                    "primary_category": paper.primary_category,
                    "pdf_url": paper.pdf_url,
                    "arxiv_url": paper.entry_id,
                    "summary": {
                        "chinese_summary": summary["chinese_summary"],
                        "english_summary": summary["english_summary"]
                    },
                    "crawl_timestamp": datetime.now().isoformat(),
                    "relevance_score": relevance_score,
                    "processing_status": "success"
                }

                processed_papers.append(paper_dict)
                logger.info(f"✅ 成功处理论文: {paper_title} (ID: {paper_id}), 相关性: {relevance_score:.3f}")

            except KimiAPIError as e:
                # 记录API调用失败的详细信息
                logger.error(f"❌ Kimi API调用失败: {str(e)}")
                failed_papers.append({
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "error_type": "KimiAPIError",
                    "error_message": str(e),
                    "pdf_url": paper.pdf_url,
                    "relevance_score": relevance_score
                })

                # 抛出异常，让调用者决定如何处理
                raise PaperProcessingError(paper_title, paper_id, e)

            except Exception as e:
                # 记录其他类型的错误
                logger.error(f"❌ 论文处理失败: {paper_title} (ID: {paper_id}), 错误: {str(e)}")
                failed_papers.append({
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "pdf_url": paper.pdf_url,
                    "relevance_score": relevance_score
                })

                # 抛出异常
                raise PaperProcessingError(paper_title, paper_id, e)

            # 在处理下一篇论文前添加额外延迟
            if i < len(papers) - 1:  # 不是最后一篇论文
                logger.debug(f"处理完成，等待{self.paper_processing_delay}秒后处理下一篇论文...")
                time.sleep(self.paper_processing_delay)

        # 记录处理统计信息
        total_found = len(papers)
        total_processed = len(processed_papers)
        total_filtered = len(filtered_papers)
        total_failed = len(failed_papers)

        logger.info(f"📊 论文处理统计:")
        logger.info(f"  - 总找到论文: {total_found} 篇")
        logger.info(f"  - 成功处理: {total_processed} 篇")
        logger.info(f"  - 相关性过滤: {total_filtered} 篇")
        logger.info(f"  - 处理失败: {total_failed} 篇")

        if filtered_papers:
            logger.info(f"🔍 被过滤的低相关性论文 (相关性 < {self.min_relevance_score}):")
            for filtered in filtered_papers:
                logger.info(f"  - {filtered['paper_title']} (ID: {filtered['paper_id']}) - 相关性: {filtered['relevance_score']:.3f}")

        if failed_papers:
            logger.warning(f"❌ 处理失败的论文:")
            for failed in failed_papers:
                logger.warning(f"  - {failed['paper_title']} (ID: {failed['paper_id']}) - {failed['error_message']}")

        return processed_papers

    def _calculate_relevance_score(self, title: str, abstract: str) -> float:
        """
        计算论文与搜索主题的相关性分数

        Args:
            title: 论文标题
            abstract: 论文摘要

        Returns:
            相关性分数 (0-1)
        """
        text = (title + " " + abstract).lower()
        score = 0.0

        # 根据搜索主题定义不同的权重关键词
        if self.search_topic == 'VLM':
            # VLM高权重关键词
            high_weight_keywords = ["vlm", "vision language model", "multimodal", "vision-language"]
            medium_weight_keywords = ["visual reasoning", "visual instruction", "image captioning", "visual grounding"]
            low_weight_keywords = ["cross-modal", "image-text", "visual understanding"]
        elif self.search_topic == 'VLA':
            # VLA高权重关键词
            high_weight_keywords = ["vla", "vision language action", "embodied ai", "embodied agent"]
            medium_weight_keywords = ["robotic manipulation", "action planning", "visual navigation", "robot learning"]
            low_weight_keywords = ["policy learning", "motor control", "behavioral cloning"]
        else:  # BOTH
            # 综合关键词
            high_weight_keywords = ["vlm", "vla", "vision language model", "vision language action", "embodied ai"]
            medium_weight_keywords = ["multimodal", "vision-language", "visual reasoning", "robotic manipulation"]
            low_weight_keywords = ["visual instruction", "image captioning", "action planning", "cross-modal"]

        # 计算分数
        for keyword in high_weight_keywords:
            if keyword in text:
                score += 0.3

        for keyword in medium_weight_keywords:
            if keyword in text:
                score += 0.2

        for keyword in low_weight_keywords:
            if keyword in text:
                score += 0.1

        return min(score, 1.0)

    def save_to_json(self, papers: List[Dict[str, Any]], filename: str = None) -> str:
        """
        保存论文数据到JSON文件

        Args:
            papers: 处理后的论文数据列表
            filename: 输出文件名，默认使用日期

        Returns:
            保存的文件路径
        """
        if filename is None:
            today = datetime.now().strftime("%Y-%m-%d")
            # topic_suffix = self.search_topic.lower()
            filename = f"arxiv_papers_{today}.json"

        # 创建输出目录
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        # 构建最终的JSON结构
        output_data = {
            "metadata": {
                "crawl_date": datetime.now().isoformat(),
                "total_papers": len(papers),
                "search_keywords": self.keywords,
                "search_topic": self.search_topic,
                "min_relevance_score": self.min_relevance_score,
                "data_source": "arxiv.org"
            },
            "papers": papers
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info(f"成功保存 {len(papers)} 篇论文到 {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存文件时出错: {e}")
            raise

    def run_daily_crawl(self, days_back: int = 1) -> str:
        """
        执行每日爬取任务

        Args:
            days_back: 爬取过去几天的论文

        Returns:
            输出文件路径
        """
        logger.info("开始执行每日论文爬取任务...")

        try:
            # 搜索论文
            papers = self.search_papers(days_back)

            if not papers:
                logger.warning("未找到相关论文")
                return None

            # 处理论文
            processed_papers = self.process_papers(papers)

            # 按相关性分数排序
            processed_papers.sort(key=lambda x: x['relevance_score'], reverse=True)

            # 保存到JSON文件
            output_file = self.save_to_json(processed_papers)

            logger.info(f"每日爬取任务完成，共处理 {len(processed_papers)} 篇论文")
            return output_file

        except Exception as e:
            logger.error(f"执行爬取任务时出错: {e}")
            raise


def main():
    """主函数"""
    # 从环境变量获取API密钥
    kimi_api_key = os.getenv('KIMI_API_KEY')

    if not kimi_api_key:
        logger.error("请设置环境变量 KIMI_API_KEY")
        return

    # 创建爬虫实例
    crawler = ArxivPaperCrawler(kimi_api_key)

    try:
        # 执行每日爬取
        output_file = crawler.run_daily_crawl(days_back=3)

        if output_file:
            print(f"✅ 爬取完成！结果已保存到: {output_file}")
        else:
            print("❌ 未找到相关论文")

    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    main()
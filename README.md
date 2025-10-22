# ArXiv VLM/VLA 论文爬虫

这是一个基于Python的自动化工具，用于每天从arXiv抓取VLM（Vision Language Model）和VLA（Vision Language Action）相关的最新论文，并使用Kimi API对论文进行智能总结，最终生成结构化的JSON文件。支持在VLM和VLA主题之间灵活切换。

## 功能特性

- 🔍 **智能搜索**: 自动搜索arXiv上VLM/VLA相关的最新论文，支持主题切换
- 🤖 **AI论文分析**: 使用Kimi API直接读取PDF文件，精准分析论文核心内容
- 📊 **结构化输出**: 生成标准化的JSON格式数据
- ⏰ **定时运行**: 支持每日自动执行
- 📈 **相关性评分**: 自动计算论文与主题的相关性
- 🎯 **主题切换**: 支持VLM、VLA或两者同时搜索
- 🔍 **智能过滤**: 自动过滤低相关性论文，节省API调用
- 🌐 **双语论文总结**: 同时提供中文和英文的问题-方法-贡献总结
- 📝 **详细日志**: 完整的运行日志记录

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

### 1. 设置Kimi API密钥

```bash
# Linux/Mac
export KIMI_API_KEY="your_kimi_api_key_here"

# Windows
set KIMI_API_KEY=your_kimi_api_key_here
```

### 2. 可选环境变量

```bash
# 搜索配置
export SEARCH_TOPIC="VLM"                         # 搜索主题: VLM, VLA, 或 BOTH
export MAX_RESULTS="50"                           # 最大搜索结果数
export DAYS_BACK="1"                             # 搜索过去几天的论文

# API配置
export KIMI_BASE_URL="https://api.moonshot.cn/v1"  # Kimi API基础URL
export KIMI_MODEL="moonshot-v1-32k"               # Kimi模型
export REQUEST_TIMEOUT="30"                       # API请求超时时间
export REQUEST_DELAY="2.0"                        # 请求间隔时间
export KIMI_REQUEST_DELAY="3.0"                   # Kimi API请求前等待时间
export PAPER_PROCESSING_DELAY="5.0"               # 论文处理间隔时间
export MIN_RELEVANCE_SCORE="0.2"                  # 最小相关性分数阈值

# 验证配置
export ENABLE_VERIFICATION="true"                 # 是否启用验证功能
export VERIFICATION_DELAY="30.0"                  # 验证前等待时间
export MAX_VERIFICATION_ATTEMPTS="2"              # 最大验证重试次数

# 输出配置
export OUTPUT_DIR="output"                         # 输出目录
export LOG_DIR="logs"                             # 日志目录
export LOG_LEVEL="INFO"                           # 日志级别
```

## 使用方法

### 方法1: 直接运行主程序

```bash
python arxiv_paper_crawler.py
```

### 方法2: 使用每日运行脚本

```bash
python run_daily.py
```

### 方法3: 在代码中使用

```python
from arxiv_paper_crawler import ArxivPaperCrawler

# 创建爬虫实例
crawler = ArxivPaperCrawler(kimi_api_key="your_api_key")

# 执行爬取
output_file = crawler.run_daily_crawl(days_back=1)
print(f"结果保存到: {output_file}")
```

## 输出格式

生成的JSON文件包含以下结构：

```json
{
  "metadata": {
    "crawl_date": "2024-01-15T10:30:00",
    "total_papers": 25,
    "search_keywords": ["VLM", "VLA", "vision language model", ...],
    "data_source": "arxiv.org"
  },
  "papers": [
    {
      "id": "2401.12345",
      "title": "论文标题",
      "authors": ["作者1", "作者2"],
      "published_date": "2024-01-15",
      "updated_date": "2024-01-15",
      "categories": ["cs.CV", "cs.AI"],
      "primary_category": "cs.CV",
      "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
      "arxiv_url": "https://arxiv.org/abs/2401.12345",
      "summary": {
        "chinese_summary": "问题：解决视觉语言模型的跨模态理解问题 | 方法：提出基于注意力机制的多模态融合框架 | 贡献：在多个基准数据集上达到最优性能",
        "english_summary": "Problem: Addressing cross-modal understanding in vision-language models | Method: Proposing attention-based multimodal fusion framework | Contribution: Achieving state-of-the-art performance on multiple benchmarks"
      },
      "crawl_timestamp": "2024-01-15T10:30:00",
      "relevance_score": 0.85
    }
  ]
}
```

## 定时任务设置

### Linux/Mac (使用cron)

```bash
# 编辑crontab
crontab -e

# 添加每日上午9点执行的任务
0 9 * * * cd /path/to/your/project && python run_daily.py
```

### Windows (使用任务计划程序)

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器为"每天"
4. 设置操作为启动程序: `python`
5. 添加参数: `/path/to/your/project/run_daily.py`
6. 设置起始于: `/path/to/your/project`

## 搜索主题和关键词

### 主题切换

系统支持三种搜索主题：

1. **VLM (Vision Language Model)**: 专注于视觉语言模型
2. **VLA (Vision Language Action)**: 专注于视觉语言动作模型
3. **BOTH**: 同时搜索VLM和VLA相关论文

### 关键词列表

**VLM关键词**:
- vision language model, VLM, vision-language, multimodal
- visual instruction, visual reasoning, visual question answering
- image captioning, visual grounding, multimodal learning
- cross-modal, vision-and-language, visual understanding

**VLA关键词**:
- vision language action, VLA, embodied AI, embodied agent
- robotic manipulation, action planning, visual navigation
- robot learning, embodied intelligence, action prediction
- behavioral cloning, imitation learning, policy learning

### 切换方法

```bash
# 搜索VLM论文
export SEARCH_TOPIC=VLM

# 搜索VLA论文
export SEARCH_TOPIC=VLA

# 搜索两种类型的论文
export SEARCH_TOPIC=BOTH
```

## 相关性过滤

系统会自动计算每篇论文与搜索主题的相关性分数（0-1），并过滤掉低相关性的论文。

### 相关性分数计算

- **高权重关键词** (0.3分): 核心主题词如"VLM"、"VLA"、"embodied AI"等
- **中权重关键词** (0.2分): 相关技术词如"multimodal"、"visual reasoning"等
- **低权重关键词** (0.1分): 辅助概念词如"cross-modal"、"image-text"等

### 过滤阈值设置

```bash
# 设置最小相关性分数阈值
export MIN_RELEVANCE_SCORE=0.2  # 默认值，推荐范围 0.1-0.3
```

### 分数含义

- **0.0-0.1**: 几乎无关，会被过滤
- **0.2-0.3**: 中等相关，通常保留
- **0.4+**: 高度相关，必定保留

### 优势

- 🚀 **节省API调用**: 避免处理不相关论文
- ⏱️ **提高效率**: 减少处理时间
- 💰 **降低成本**: 减少API费用
- 📊 **提升质量**: 结果更精准

## AI分析优化

### 精准提示词设计

系统使用优化的提示词确保Kimi API严格按照论文内容进行分析：

- **强制要求**: 必须完整阅读指定URL的论文全文
- **内容限制**: 只能基于该论文的实际内容，不得添加外部信息
- **格式规范**: 要求用一句话分别概括问题、方法、贡献
- **防止跑题**: 明确禁止使用其他论文或外部知识补充

### 输出格式

每篇论文的分析包含：
- **核心问题**: 论文解决的主要问题（一句话）
- **主要方法**: 论文提出的解决方案（一句话）
- **关键贡献**: 论文的核心贡献点（一句话）

### 质量保证

- ✅ 严格基于原文内容
- ✅ 避免主观臆测和外部信息
- ✅ 简洁明确的一句话概括
- ✅ 中英文双语对照

## 智能验证机制

### 双重验证流程

系统采用创新的双重验证机制确保总结质量：

1. **生成阶段**: 使用优化提示词生成初始总结
2. **等待间隔**: 30秒冷却期，避免API频率限制
3. **验证阶段**: 再次调用API验证总结准确性
4. **重试机制**: 验证失败时自动重新生成

### 验证标准

- ✅ 总结是否基于论文实际内容
- ✅ 是否准确反映核心问题、方法、贡献
- ✅ 是否包含论文中未提及的内容
- ✅ 格式和语言是否符合要求

### 配置选项

```bash
# 启用/禁用验证功能
export ENABLE_VERIFICATION=true

# 验证前等待时间（避免API限制）
export VERIFICATION_DELAY=30.0

# 最大重试次数
export MAX_VERIFICATION_ATTEMPTS=2
```

### 处理流程

1. 📝 生成初始总结
2. ⏱️ 等待30秒
3. 🔍 验证总结准确性
4. ✅ 通过 → 保存结果
5. ❌ 不通过 → 重新生成（最多2次）

### 优势

- 🎯 **更高准确性**: 双重检查确保质量
- 🚫 **防止幻觉**: 避免AI生成虚假内容
- 🔄 **自动重试**: 失败时自动重新生成
- ⚙️ **可配置**: 支持启用/禁用验证功能

## 注意事项

1. **API限制**: Kimi API有调用频率限制，程序已内置多重延迟机制：
   - API请求前延迟: 3秒（可配置）
   - 论文处理间隔: 5秒（可配置）
2. **网络连接**: 需要稳定的网络连接访问arXiv和Kimi API，以及PDF文件
3. **存储空间**: JSON文件会随时间累积，注意定期清理
4. **API费用**: 使用Kimi API会产生费用，每篇论文需要1次API调用（通过URL分析PDF），但使用32k模型费用较高
5. **PDF访问**: 需要确保Kimi API能够访问arXiv的PDF文件，某些论文可能访问受限
6. **处理时间**: PDF分析比文本总结需要更长时间，请耐心等待
7. **相关性过滤**: 系统会自动过滤相关性分数低于0.2的论文，减少不必要的API调用

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   请检查KIMI_API_KEY环境变量是否正确设置
   ```

2. **网络连接问题**
   ```
   检查网络连接，确保可以访问arxiv.org和api.moonshot.cn
   ```

3. **依赖包问题**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **日志文件位置**
   ```
   所有日志文件都存放在 logs/ 目录下：
   - logs/arxiv_crawler_YYYYMMDD.log: 主程序日志
   - logs/daily_crawl_YYYYMMDD.log: 每日任务日志
   ```

## 文件说明

- `arxiv_paper_crawler.py`: 主要的爬虫类
- `config.py`: 配置文件
- `run_daily.py`: 每日运行脚本
- `setup_logging.py`: 统一日志配置模块
- `requirements.txt`: Python依赖包
- `output/`: 输出目录（自动创建）
- `logs/`: 日志文件目录（自动创建）

## 许可证

MIT License
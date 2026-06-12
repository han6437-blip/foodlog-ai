# 健康饮食记录与推荐系统：个人低成本线上部署方案

## 1. 项目定位

本项目面向个人使用，目标是构建一个低成本、低维护的健康饮食记录与推荐系统。用户可以通过拍照和文字描述记录每日饮食，系统调用多模态大模型识别饮食内容，分析当前饮食是否均衡，并结合近期饮食记录推荐下一餐饮食方案。系统还可以定期生成周报，指出饮食问题、营养缺口和改善建议。

核心目标不是商业化部署，而是：

- 尽量使用免费组件
- 降低服务器和运维成本
- 支持长期个人使用
- 能够保存饮食记录和图片
- 支持后续扩展为 Agent 项目

---

## 2. 推荐总体方案

个人使用推荐采用：

```text
前端：Vue3 + Vite
前端部署：Cloudflare Pages 免费版

后端：FastAPI
后端部署：Render Free Web Service

数据库：Supabase Free Postgres
图片存储：Supabase Storage

AI 模型：多模态大模型 API
定时任务：GitHub Actions
AI 编排：第一版可不用 LangGraph，第二版再加入
```

整体架构如下：

```text
用户浏览器
   ↓
Cloudflare Pages 前端
   ↓
Render FastAPI 后端
   ↓
Supabase Postgres / Supabase Storage
   ↓
大模型 API
   ↓
GitHub Actions 定时触发周报生成
```

一句话总结：

> 用 Cloudflare Pages 放前端，用 Render 放 FastAPI，用 Supabase 存数据和图片，用 GitHub Actions 做定时任务，模型只在上传饮食记录和生成报告时调用。

---

## 3. 为什么适合个人项目

相比云服务器、Kubernetes、自建对象存储等方案，这套架构更适合个人长期使用。

### 优点

| 方面 | 说明 |
|---|---|
| 成本低 | 大部分组件都有免费额度 |
| 维护少 | 不需要自己维护服务器、数据库和 HTTPS |
| 部署简单 | GitHub 推送代码后自动部署 |
| 易扩展 | 后续可以逐步加入 LangGraph、向量库、更多报告功能 |
| 适合个人使用 | 访问量小，免费额度通常够用 |

### 不建议一开始使用的方案

| 不建议方案 | 原因 |
|---|---|
| Kubernetes | 个人项目过重，学习和维护成本高 |
| 自建云服务器 | 需要维护系统、安全、证书、备份 |
| 自建 MinIO | 增加对象存储维护成本 |
| Redis / Celery | 第一版不是必须 |
| 独立 Agent 服务 | 初期可以和 FastAPI 放在一起 |

---

## 4. 系统功能范围

### 第一版 MVP 功能

第一版只做最核心功能：

1. 用户上传饮食图片
2. 用户添加文字描述
3. 模型识别食物内容
4. 生成本餐健康评价
5. 保存饮食记录
6. 查看最近 7 天饮食记录
7. 推荐下一餐饮食
8. 每周生成饮食报告

### 暂时不做的功能

为了降低开发和部署成本，第一版暂时不做：

- 精确热量计算
- 复杂营养数据库
- 多人社交系统
- 外卖平台 API 接入
- 运动手环接入
- 医生或营养师模块
- 商业化付费系统

---

## 5. 前端部署设计

### 技术选型

```text
Vue3 + Vite + TypeScript
```

### 部署平台

```text
Cloudflare Pages
```

### 前端页面建议

| 页面 | 作用 |
|---|---|
| 首页 | 展示今日饮食状态和下一餐推荐 |
| 饮食记录页 | 上传图片、填写描述、选择餐次 |
| 分析结果页 | 展示健康评分、问题标签和建议 |
| 历史记录页 | 查看最近饮食记录 |
| 周报页面 | 查看饮食总结和补偿计划 |
| 用户设置页 | 设置目标、忌口、偏好、预算等 |

### 前端环境变量

```env
VITE_API_BASE_URL=https://你的-render-api地址
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

---

## 6. 后端部署设计

### 技术选型

```text
FastAPI
```

### 部署平台

```text
Render Free Web Service
```

### 后端职责

后端主要负责：

- 接收前端请求
- 校验用户输入
- 上传图片到 Supabase Storage
- 调用多模态大模型
- 保存饮食分析结果
- 查询历史饮食记录
- 生成下一餐推荐
- 生成日报 / 周报

### 后端 API 设计

```text
POST /api/meal/upload
上传饮食图片

POST /api/meal/analyze
分析本餐饮食

GET /api/meal/history
获取饮食历史

GET /api/recommend/next-meal
获取下一餐推荐

POST /api/report/weekly-generate
生成周报

GET /api/report/weekly
获取周报

POST /api/user/profile
更新用户饮食画像
```

### 后端环境变量

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
MODEL_API_KEY=
JWT_SECRET=
CRON_SECRET=
```

### 注意事项

Render 免费服务可能会休眠，因此第一次访问可能较慢。不要把图片或数据库文件保存在 Render 本地，因为免费服务的本地文件不适合持久化保存。图片和数据都应该放在 Supabase 中。

---

## 7. 数据存储设计

### 推荐使用 Supabase

Supabase 可以同时承担：

- PostgreSQL 数据库
- 用户认证
- 图片存储
- 简单权限管理
- 后续 pgvector 扩展

### 第一版只需要 3 张核心表

#### 1. user_profile

保存用户饮食偏好和目标。

```sql
create table user_profile (
  user_id uuid primary key,
  nickname text,
  goal text,
  allergies text[],
  disliked_foods text[],
  preferred_foods text[],
  budget_level text,
  cook_type text,
  updated_at timestamp default now()
);
```

字段说明：

| 字段 | 含义 |
|---|---|
| goal | 健康饮食、减脂、增肌、控糖等 |
| allergies | 过敏食物 |
| disliked_foods | 不喜欢的食物 |
| preferred_foods | 偏好的食物 |
| budget_level | 预算水平 |
| cook_type | 外卖、食堂、自己做饭等 |

#### 2. meal_record

保存每次饮食记录和模型分析结果。

```sql
create table meal_record (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  meal_type text,
  image_url text,
  description text,
  foods jsonb,
  nutrition_result jsonb,
  health_score int,
  risk_tags text[],
  next_meal_advice text,
  created_at timestamp default now()
);
```

字段说明：

| 字段 | 含义 |
|---|---|
| meal_type | 早餐、午餐、晚餐、加餐 |
| image_url | 饮食图片地址 |
| description | 用户补充描述 |
| foods | 模型识别出的食物 |
| nutrition_result | 营养分析结果 |
| health_score | 健康评分 |
| risk_tags | 高油、高糖、蔬菜不足等标签 |
| next_meal_advice | 下一餐建议 |

#### 3. weekly_report

保存每周饮食报告。

```sql
create table weekly_report (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  week_start date,
  week_end date,
  summary text,
  nutrition_lack text[],
  risk_analysis text,
  compensation_plan text,
  created_at timestamp default now()
);
```

字段说明：

| 字段 | 含义 |
|---|---|
| summary | 本周饮食总结 |
| nutrition_lack | 缺少的营养或饮食类型 |
| risk_analysis | 风险分析 |
| compensation_plan | 下周补偿措施 |

---

## 8. 图片存储设计

### 推荐方式

第一版建议直接使用：

```text
Supabase Storage
```

不建议一开始使用 S3、阿里云 OSS、腾讯云 COS 或自建 MinIO，因为配置和维护成本更高。

### 图片处理策略

为了节省存储空间和模型调用成本，建议：

- 前端上传前压缩图片
- 最大宽度控制在 1024px
- 图片质量控制在 0.7 左右
- 单张图片控制在 500KB - 1MB
- 长期保存结构化分析结果，原图可以定期删除
- 周报生成时不再读取原图，只读取结构化分析结果

---

## 9. AI 调用设计

### 第一版：不用 LangGraph

第一版可以先采用简单流程：

```text
FastAPI 接收图片和描述
   ↓
读取用户最近饮食记录
   ↓
拼接 Prompt
   ↓
调用多模态大模型
   ↓
解析 JSON
   ↓
保存结果到 Supabase
   ↓
返回前端展示
```

优点：

- 实现简单
- 部署容易
- 成本低
- 更适合快速上线

缺点：

- Agent 感不强
- 后续流程复杂后维护困难

### 第二版：加入 LangGraph

当第一版跑通后，可以把 AI 流程改造成 LangGraph：

```text
FastAPI
   ↓
LangGraph Workflow
   ↓
food_recognition_node
   ↓
nutrition_analysis_node
   ↓
memory_summary_node
   ↓
recommendation_node
   ↓
report_node
```

第二版不需要单独部署 Agent 服务，直接把 LangGraph 放在 FastAPI 项目中即可。

推荐目录结构：

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── meal.py
│   │   ├── report.py
│   │   └── user.py
│   ├── agents/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── prompts.py
│   ├── services/
│   │   ├── model_service.py
│   │   ├── supabase_service.py
│   │   └── image_service.py
│   └── schemas/
│       ├── meal.py
│       └── report.py
```

---

## 10. 定时任务设计

个人项目不建议一开始上 Celery，可以用 GitHub Actions 定时调用后端接口。

### 任务设计

```text
每天晚上：生成当天饮食总结
每周日晚上：生成本周饮食报告
```

### GitHub Actions 示例

```yaml
name: Generate Weekly Report

on:
  schedule:
    - cron: "0 14 * * 0"  # 每周日 22:00，新加坡时间
  workflow_dispatch:

jobs:
  call-api:
    runs-on: ubuntu-latest
    steps:
      - name: Call weekly report API
        run: |
          curl -X POST "${{ secrets.API_BASE_URL }}/api/report/weekly-generate" \
          -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"
```

---

## 11. 成本控制策略

项目主要成本来自：

1. 模型调用
2. 图片存储
3. 数据库存储
4. 后端服务运行

### 1. 控制模型调用次数

不要每次打开页面都重新调用模型。

推荐做法：

```text
上传饮食图片时调用一次模型
分析结果保存到数据库
用户查看历史记录时直接读数据库
周报每周只生成一次
用户主动刷新时才重新生成
```

### 2. 控制图片大小

前端上传前压缩：

```text
最大宽度：1024px
格式：WebP 或 JPEG
单张大小：500KB - 1MB
```

### 3. 保存结构化结果

每餐保存结构化 JSON，例如：

```json
{
  "foods": ["米饭", "鸡腿", "青菜"],
  "score": 68,
  "risk_tags": ["高油", "蔬菜偏少"],
  "suggestion": "下一餐建议增加绿叶菜和豆制品"
}
```

后续生成周报时，只读取这些结构化结果，不再读取原图。

### 4. 周报使用摘要数据

不要把 7 天所有记录完整发送给模型。可以先在后端整理成摘要：

```text
最近 7 天：
- 早餐缺失 3 次
- 午餐米饭类 5 次
- 油炸 / 重口味 4 次
- 蔬菜偏少 5 次
- 水果记录 1 次
- 蛋白质摄入中等
```

再把摘要发送给模型生成周报。

---

## 12. 部署步骤

### 第一步：本地跑通

本地先完成：

```text
Vue3 前端
FastAPI 后端
Supabase 数据库
Supabase Storage
模型 API Key
```

确保核心链路可用：

```text
上传图片 → 后端接收 → 调用模型 → 保存 Supabase → 前端展示
```

### 第二步：配置 Supabase

在 Supabase 中创建：

```text
Project
Database tables
Storage bucket: meal-images
Auth，可选
```

### 第三步：部署后端到 Render

配置：

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

添加环境变量：

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
MODEL_API_KEY=
JWT_SECRET=
CRON_SECRET=
```

### 第四步：部署前端到 Cloudflare Pages

配置：

```text
Build Command: npm run build
Output Directory: dist
```

添加环境变量：

```env
VITE_API_BASE_URL=https://你的-render-api地址
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

### 第五步：配置 GitHub Actions

在 GitHub 仓库中添加 Secrets：

```text
API_BASE_URL
CRON_SECRET
```

创建 `.github/workflows/weekly-report.yml`，定时调用后端接口生成周报。

---

## 13. 后续升级方向

第一版跑通后，可以逐步升级：

### 方向一：加入 LangGraph

把饮食分析流程改成多节点 Agent：

```text
食物识别节点
营养分析节点
近期饮食记忆节点
下一餐推荐节点
周报生成节点
```

### 方向二：加入长期记忆

建立 `diet_memory` 表，保存用户长期饮食习惯：

```text
用户经常不吃早餐
用户偏好米饭类主食
用户最近蔬菜摄入偏少
用户经常选择高油外卖
```

### 方向三：加入向量检索

使用 Supabase pgvector 保存：

- 健康饮食知识
- 食物营养知识
- 用户长期饮食总结
- 历史推荐记录

### 方向四：支持更多输入方式

例如：

- 纯文字记录
- 语音输入
- 手动选择食物
- 外卖截图识别

---

## 14. 最终推荐结论

个人低成本部署建议采用：

```text
Vue3 + Vite
Cloudflare Pages
FastAPI
Render Free
Supabase Postgres
Supabase Storage
GitHub Actions
多模态大模型 API
```

这套方案的核心优势是：

- 免费组件多
- 部署简单
- 维护成本低
- 适合个人长期使用
- 可以从 MVP 平滑升级到 Agent 项目

最终架构可以概括为：

```text
前端免费托管
后端轻量部署
数据和图片放 Supabase
定时任务用 GitHub Actions
模型调用按需触发
第一版先简单跑通，第二版再加入 LangGraph
```

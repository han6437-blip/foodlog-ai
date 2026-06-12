# 健康饮食记录与推荐系统 V1

根据 `docs/prd/PRD-001.md` 实现的个人 MVP，包含 Vue3 + Vite 前端和 FastAPI 后端。

## 功能

- 个人饮食画像：目标、过敏、偏好、预算、就餐方式
- 单餐图片上传：前端压缩，限制 JPG/PNG/WebP
- 本餐分析：食物识别、健康评分、风险标签、调整建议
- 本餐追问：仅围绕当前餐食回复
- 最近 7 天历史：评分、标签、早餐缺失、详情查看
- 下一餐推荐：支持临时条件重新生成，并处理过敏冲突
- 每周报告：基于结构化记录生成，不依赖原图

## 本地运行

后端：

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`。

## 部署

前端部署到 Cloudflare Pages：

```text
Build Command: npm run build
Output Directory: dist
Root Directory: frontend
```

后端部署到 Render：

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Root Directory: backend
```

## 后续接入

当前后端使用本地 JSON 保证第一版可运行。模型配置优先从 Supabase Vault 读取，未配置时会使用 mock AI 兜底。

## 大模型密钥配置

生产环境不要把模型 URL 和 API Key 写进代码或前端环境变量。先在 Supabase SQL Editor 执行 [supabase/schema.sql](/C:/Users/user/Desktop/food/supabase/schema.sql)，它会启用 Vault 并创建 `public.get_app_secret(secret_name)`。

然后继续在 SQL Editor 执行。文本模型用于追问、下一餐推荐和周报，图片识别模型用于上传餐食图片后的识别与本餐分析：

```sql
select vault.create_secret('https://api.openai.com/v1', 'TEXT_MODEL_BASE_URL');
select vault.create_secret('你的文本模型 API Key', 'TEXT_MODEL_API_KEY');
select vault.create_secret('gpt-4o-mini', 'TEXT_MODEL_NAME');

select vault.create_secret('https://api.openai.com/v1', 'VISION_MODEL_BASE_URL');
select vault.create_secret('你的图片识别模型 API Key', 'VISION_MODEL_API_KEY');
select vault.create_secret('gpt-4o-mini', 'VISION_MODEL_NAME');
```

后端会通过该 RPC 读取 Vault 中的密钥。

后端部署环境仍需要配置 Supabase 连接信息：

```env
SUPABASE_URL=你的 Supabase Project URL
SUPABASE_SERVICE_ROLE_KEY=你的 Supabase service_role key
SUPABASE_STORAGE_BUCKET=meal-images
APP_USER_ID=00000000-0000-0000-0000-000000000001
```

`SUPABASE_SERVICE_ROLE_KEY` 只放在 Render 后端环境变量里，不要放到前端 Cloudflare Pages。

后端会优先使用 Supabase Postgres 保存结构化数据，并使用 Supabase Storage 的 `meal-images` bucket 保存图片。未配置 Supabase 时才回退到本地 JSON 和本地文件，方便开发调试。

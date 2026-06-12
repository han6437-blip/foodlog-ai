# PRD 总集

| 版本 | 标题 | 需求内容（详细摘要） | PRD链接 |
|---|---|---|---|
| PRD-001 | 健康饮食记录与推荐系统 V1.0 | 面向个人用户的低成本健康饮食记录与推荐 MVP。范围包括饮食画像、单餐图片上传、AI 本餐分析、围绕本餐的有限追问、最近 7 天历史、下一餐推荐和每周饮食报告。系统采用 Vue3 + Vite、Cloudflare Pages、FastAPI、Render Free、Supabase Postgres 和 Supabase Storage 的轻量部署方案。图片允许存储在 Supabase Storage，但需上传前压缩、MVP 单餐限制 1 张，并定期清理原图，长期保留结构化饮食记录和分析结果。第一版不包含完整聊天、精确热量计算、复杂营养数据库、社交、医生模块、外卖平台 API、运动设备接入和商业化付费。 | docs/prd/PRD-001.md |

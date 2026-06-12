# 大模型配置

项目支持两组 OpenAI-compatible 模型配置，均优先从 Supabase Vault 读取。

## 文本模型

用于：

- 本餐追问
- 下一餐推荐
- 每周报告

Secret 名称：

```text
TEXT_MODEL_BASE_URL
TEXT_MODEL_API_KEY
TEXT_MODEL_NAME
```

## 图片识别模型

用于：

- 饮食图片识别
- 本餐评分、风险标签和建议

Secret 名称：

```text
VISION_MODEL_BASE_URL
VISION_MODEL_API_KEY
VISION_MODEL_NAME
```

## Supabase SQL

```sql
select vault.create_secret('https://api.openai.com/v1', 'TEXT_MODEL_BASE_URL');
select vault.create_secret('你的文本模型 API Key', 'TEXT_MODEL_API_KEY');
select vault.create_secret('gpt-4o-mini', 'TEXT_MODEL_NAME');

select vault.create_secret('https://api.openai.com/v1', 'VISION_MODEL_BASE_URL');
select vault.create_secret('你的图片识别模型 API Key', 'VISION_MODEL_API_KEY');
select vault.create_secret('gpt-4o-mini', 'VISION_MODEL_NAME');
```

为兼容旧配置，后端仍会在找不到 `TEXT_*` 或 `VISION_*` 时回退读取：

```text
MODEL_BASE_URL
MODEL_API_KEY
MODEL_NAME
```

from collections import Counter
from datetime import datetime, timedelta
from .store import read_db
from app.schemas.models import MealAnalysis, Recommendation, UserProfile, WeeklyReport
from app.services.model_client import chat_json, vision_json


def _contains(text: str, words: list[str]) -> bool:
    return any(word and word in text for word in words)


def analyze_meal(
    description: str,
    profile: UserProfile | None,
    image_bytes: bytes | None = None,
    image_mime: str = "image/jpeg",
) -> MealAnalysis:
    model_result = _analyze_meal_with_model(description, profile, image_bytes, image_mime)
    if model_result:
        return model_result

    return _mock_analyze_meal(description, profile)


def _analyze_meal_with_model(
    description: str,
    profile: UserProfile | None,
    image_bytes: bytes | None,
    image_mime: str,
) -> MealAnalysis | None:
    if not image_bytes:
        return None
    profile_text = profile.model_dump_json() if profile else "未设置画像"
    try:
        data = vision_json(
            "你是健康饮食记录系统的图片识别与饮食分析助手。只返回 JSON，不做医疗诊断。",
            f"""
请根据饮食图片、用户补充描述和饮食画像生成本餐分析。

饮食画像：
{profile_text}

本餐描述：
{description or "用户未填写补充描述"}

返回 JSON 字段：
- foods: string[]，识别出的食物
- health_score: number，0-100
- risk_tags: string[]，例如高油、高糖、蔬菜不足、蛋白质不足、主食偏多
- summary: string，本餐评价
- next_meal_advice: string，下一餐调整建议
""",
            image_bytes,
            image_mime,
        )
        if not data:
            return None
        return MealAnalysis(
            foods=list(data.get("foods") or ["待确认食物"]),
            health_score=int(data.get("health_score", 70)),
            risk_tags=list(data.get("risk_tags") or ["结构待确认"]),
            summary=str(data.get("summary") or "本餐已完成智能分析。"),
            next_meal_advice=str(data.get("next_meal_advice") or "下一餐建议清淡、增加蔬菜和优质蛋白。"),
        )
    except Exception:
        return None


def _mock_analyze_meal(description: str, profile: UserProfile | None) -> MealAnalysis:
    text = description or ""
    foods = [item.strip() for item in text.replace("，", ",").replace("、", ",").split(",") if item.strip()]
    if not foods:
        foods = ["主食", "蛋白质食物", "蔬菜"]

    risk_tags: list[str] = []
    score = 78
    if _contains(text, ["炸", "油", "煎", "麻辣", "奶茶"]):
        risk_tags.append("高油")
        score -= 12
    if _contains(text, ["甜", "糖", "奶茶", "可乐", "蛋糕"]):
        risk_tags.append("高糖")
        score -= 10
    if not _contains(text, ["菜", "青菜", "蔬菜", "生菜", "西兰花", "菠菜"]):
        risk_tags.append("蔬菜不足")
        score -= 8
    if not _contains(text, ["鸡", "鱼", "牛", "蛋", "豆", "奶", "虾"]):
        risk_tags.append("蛋白质不足")
        score -= 6

    if profile and profile.goal == "控糖" and _contains(text, ["米饭", "面", "粉", "粥"]):
        risk_tags.append("主食偏多")
        score -= 5

    score = max(35, min(95, score))
    tags_text = "、".join(risk_tags) if risk_tags else "结构较均衡"
    return MealAnalysis(
        foods=foods,
        health_score=score,
        risk_tags=risk_tags or ["结构较均衡"],
        summary=f"本餐识别到{ '、'.join(foods) }，整体判断为{tags_text}。",
        next_meal_advice="下一餐建议增加绿叶菜和优质蛋白，少选油炸与含糖饮品。",
    )


def answer_follow_up(question: str, meal: dict, profile: UserProfile | None) -> str:
    allowed = ["饭", "餐", "吃", "饮食", "晚餐", "早餐", "午餐", "补", "油", "糖", "菜", "蛋白"]
    if not _contains(question, allowed):
        return "当前仅支持围绕本餐饮食进行追问。"
    model_answer = _answer_follow_up_with_model(question, meal, profile)
    if model_answer:
        return model_answer

    return _mock_answer_follow_up(question, meal, profile)


def _answer_follow_up_with_model(question: str, meal: dict, profile: UserProfile | None) -> str | None:
    try:
        result = chat_json(
            "你是健康饮食追问助手。只能围绕当前这顿饭回答，不做医疗诊断。只返回 JSON。",
            f"""
饮食画像：
{profile.model_dump_json() if profile else "未设置画像"}

当前餐食记录：
{meal}

用户问题：
{question}

返回 JSON 字段：
- answer: string，简洁回答用户问题
""",
        )
        if not result:
            return None
        return str(result.get("answer") or "")
    except Exception:
        return None


def _mock_answer_follow_up(question: str, meal: dict, profile: UserProfile | None) -> str:
    goal = profile.goal if profile else "健康饮食"
    tags = "、".join((meal.get("analysis") or {}).get("risk_tags", []))
    if "晚餐" in question or "补" in question:
        return f"围绕{goal}目标，晚餐优先选清淡蛋白和两份蔬菜，主食减半；本餐需要重点补偿：{tags or '保持均衡'}。"
    return f"这顿饭最大的问题集中在：{tags or '没有明显风险'}。下一餐保持少油、足量蔬菜和稳定蛋白质即可。"


def recommend_next_meal(profile: UserProfile | None, temporary_conditions: str = "") -> Recommendation:
    model_result = _recommend_next_meal_with_model(profile, temporary_conditions)
    if model_result:
        return model_result

    return _mock_recommend_next_meal(profile, temporary_conditions)


def _recommend_next_meal_with_model(profile: UserProfile | None, temporary_conditions: str = "") -> Recommendation | None:
    data = read_db()
    meals = data["meals"][-20:]
    try:
        result = chat_json(
            "你是健康饮食推荐助手。必须遵守过敏和预算约束。只返回 JSON，不做医疗诊断。",
            f"""
饮食画像：
{profile.model_dump_json() if profile else "未设置画像"}

最近记录：
{meals}

临时条件：
{temporary_conditions or "无"}

返回 JSON 字段：
- meal_type: 早餐/午餐/晚餐/加餐
- basis: 推荐依据
- combo: string[] 推荐组合
- reason: 推荐理由
- avoid: string[] 需要避免
- budget_note: 预算适配说明
- warning: string，可为空；若与过敏冲突，说明冲突
""",
        )
        if not result:
            return None
        return Recommendation(
            meal_type=result.get("meal_type") or "晚餐",
            basis=result.get("basis") or "基于饮食画像和近期记录生成。",
            combo=list(result.get("combo") or []),
            reason=result.get("reason") or "该方案更均衡。",
            avoid=list(result.get("avoid") or []),
            budget_note=result.get("budget_note") or "预算适配信息不足。",
            warning=result.get("warning") or "",
        )
    except Exception:
        return None


def _mock_recommend_next_meal(profile: UserProfile | None, temporary_conditions: str = "") -> Recommendation:
    data = read_db()
    meals = data["meals"][-20:]
    allergy_terms = profile.allergies if profile else []
    if temporary_conditions and _contains(temporary_conditions, allergy_terms):
        return Recommendation(
            meal_type="晚餐",
            basis="临时条件与过敏强约束冲突",
            combo=[],
            reason="你输入的可选食物包含过敏项，系统不会推荐该方案。",
            avoid=allergy_terms,
            budget_note="请更换不含过敏食材的选项后重新生成。",
            warning="该食物与过敏约束冲突。",
        )

    risks = Counter(tag for meal in meals for tag in ((meal.get("analysis") or {}).get("risk_tags") or []))
    needs_veg = risks["蔬菜不足"] >= 1
    low_budget = profile and profile.budget_level.startswith("低")
    cook_type = profile.cook_type if profile else "食堂"

    combo = ["杂粮饭半碗", "清蒸鱼或鸡胸肉", "两份绿叶菜", "无糖饮品"]
    if low_budget:
        combo = ["米饭半碗", "番茄炒蛋", "时令青菜", "白开水或无糖茶"]
    if temporary_conditions:
        if "鸡腿饭" in temporary_conditions:
            combo = ["鸡腿饭去皮少酱", "额外加一份青菜", "米饭吃半份", "无糖饮品"]
        elif "牛肉面" in temporary_conditions:
            combo = ["牛肉面少汤少油", "加青菜或海带", "不加辣油", "不配含糖饮料"]
        elif "麻辣烫" in temporary_conditions:
            combo = ["清汤麻辣烫", "多选青菜豆腐菌菇", "少选丸子油条", "主食半份"]

    avoid = ["油炸食物", "奶茶或含糖饮料"]
    if allergy_terms:
        avoid.extend(allergy_terms)

    budget = profile.budget_level if profile else "未设置预算"
    return Recommendation(
        meal_type="晚餐",
        basis=f"最近 7 天高频问题：{ '、'.join([k for k, _ in risks.most_common(3)]) or '记录较少' }；就餐方式：{cook_type}",
        combo=combo,
        reason=("近期蔬菜不足较明显，推荐优先补充蔬菜和清淡蛋白。" if needs_veg else "这份搭配结构均衡，适合作为下一餐选择。"),
        avoid=avoid,
        budget_note=f"预算适配：{budget}，推荐方案按该预算层级控制。",
    )


def generate_weekly_report() -> WeeklyReport | None:
    model_result = _generate_weekly_report_with_model()
    if model_result:
        return model_result

    return _mock_generate_weekly_report()


def _generate_weekly_report_with_model() -> WeeklyReport | None:
    data = read_db()
    now = datetime.utcnow()
    start = now - timedelta(days=7)
    meals = [m for m in data["meals"] if datetime.fromisoformat(m["eaten_at"]) >= start]
    if not meals:
        return None
    try:
        result = chat_json(
            "你是健康饮食周报助手。表达需避免绝对化，只给饮食建议，不做医疗诊断。只返回 JSON。",
            f"""
最近 7 天结构化饮食记录：
{meals}

返回 JSON 字段：
- summary: string
- completeness: string
- average_score: number 或 null
- frequent_risks: string[]
- nutrition_lack: string[]
- risk_analysis: string
- compensation_plan: string[]
- note: string，可为空；记录少时提示“记录较少，结论仅供参考”
""",
        )
        if not result:
            return None
        return WeeklyReport(
            week_start=start.date(),
            week_end=now.date(),
            completeness=result.get("completeness") or f"本周记录 {len(meals)} 餐",
            average_score=result.get("average_score"),
            summary=result.get("summary") or "本周饮食已有记录，可继续完善。",
            frequent_risks=list(result.get("frequent_risks") or []),
            nutrition_lack=list(result.get("nutrition_lack") or []),
            risk_analysis=result.get("risk_analysis") or "建议继续观察高频风险。",
            compensation_plan=list(result.get("compensation_plan") or []),
            note=result.get("note") or "",
        )
    except Exception:
        return None


def _mock_generate_weekly_report() -> WeeklyReport | None:
    data = read_db()
    now = datetime.utcnow()
    start = now - timedelta(days=7)
    meals = [m for m in data["meals"] if datetime.fromisoformat(m["eaten_at"]) >= start]
    if not meals:
        return None
    analyzed = [m for m in meals if m.get("analysis")]
    scores = [(m["analysis"] or {}).get("health_score") for m in analyzed]
    scores = [score for score in scores if isinstance(score, int)]
    risks = Counter(tag for m in analyzed for tag in (m["analysis"].get("risk_tags") or []))
    breakfast_count = sum(1 for m in meals if m["meal_type"] == "早餐")
    avg = round(sum(scores) / len(scores)) if scores else None
    note = "记录较少，结论仅供参考。" if len(meals) < 3 else ""
    return WeeklyReport(
        week_start=start.date(),
        week_end=now.date(),
        completeness=f"本周记录 {len(meals)} 餐，早餐缺失约 {max(0, 7 - breakfast_count)} 次",
        average_score=avg,
        summary="本周饮食整体有记录基础，建议重点关注高频风险并保持规律早餐。",
        frequent_risks=[f"{tag} {count} 次" for tag, count in risks.most_common(3)] or ["暂无明显高频问题"],
        nutrition_lack=["绿叶菜摄入可能不足", "早餐蛋白质可能不足", "水果记录较少"],
        risk_analysis="若高油或高糖记录持续出现，可能影响体重管理和餐后状态，建议优先从晚餐和饮品调整。",
        compensation_plan=["每天至少增加一份绿叶菜", "早餐增加鸡蛋、牛奶或豆制品", "晚餐减少油炸和重口味外卖"],
        note=note,
    )

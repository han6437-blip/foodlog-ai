const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "请求失败，请稍后重试");
  }
  return response.json();
}

export type Profile = {
  goal: "健康饮食" | "减脂" | "增肌" | "控糖";
  allergies: string[];
  disliked_foods: string[];
  preferred_foods: string[];
  budget_level: "低：≤20元" | "中：21-50元" | "高：>50元";
  cook_type: "外卖" | "食堂" | "自己做饭";
};

export type Analysis = {
  foods: string[];
  health_score: number;
  risk_tags: string[];
  summary: string;
  next_meal_advice: string;
};

export type Meal = {
  id: string;
  meal_type: "早餐" | "午餐" | "晚餐" | "加餐";
  eaten_at: string;
  image_url: string;
  description: string;
  status: "待分析" | "已分析" | "分析失败" | "仅保存原始记录";
  analysis: Analysis | null;
};

export type Recommendation = {
  meal_type: string;
  basis: string;
  combo: string[];
  reason: string;
  avoid: string[];
  budget_note: string;
  warning: string;
};

export type WeeklyReport = {
  week_start: string;
  week_end: string;
  completeness: string;
  average_score: number | null;
  summary: string;
  frequent_risks: string[];
  nutrition_lack: string[];
  risk_analysis: string;
  compensation_plan: string[];
  note: string;
};

export const api = {
  getProfile: () => request<Profile | null>("/api/user/profile"),
  saveProfile: (profile: Profile) =>
    request<Profile>("/api/user/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile)
    }),
  createMeal: (payload: FormData) =>
    request<{ record: Meal }>("/api/meal/analyze", { method: "POST", body: payload }),
  history: () => request<Meal[]>("/api/meal/history"),
  followUp: (mealId: string, question: string) =>
    request<{ answer: string }>(`/api/meal/${mealId}/follow-up`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    }),
  nextMeal: (temporary_conditions = "") =>
    request<Recommendation>("/api/recommend/next-meal", {
      method: temporary_conditions ? "POST" : "GET",
      headers: temporary_conditions ? { "Content-Type": "application/json" } : undefined,
      body: temporary_conditions ? JSON.stringify({ temporary_conditions }) : undefined
    }),
  weekly: () => request<WeeklyReport | null>("/api/report/weekly"),
  generateWeekly: () => request<WeeklyReport>("/api/report/weekly-generate", { method: "POST" })
};

export function imageUrl(path: string) {
  return `${API_BASE}${path}`;
}

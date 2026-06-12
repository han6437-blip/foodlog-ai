<template>
  <div v-if="!isAuthenticated" class="login-screen">
    <section class="login-panel">
      <div class="brand login-brand">
        <div class="brand-mark">食</div>
        <div>
          <h1>健康饮食记录</h1>
          <p>仅限授权账号</p>
        </div>
      </div>
      <label>
        邮箱
        <input v-model="loginForm.email" type="email" autocomplete="email" />
      </label>
      <label>
        密码
        <input v-model="loginForm.password" type="password" autocomplete="current-password" @keyup.enter="login" />
      </label>
      <button :disabled="loggingIn" @click="login">
        <LoaderCircle v-if="loggingIn" class="spin" :size="18" />
        <span>{{ loggingIn ? "登录中" : "登录" }}</span>
      </button>
      <p v-if="notice" class="notice inline">{{ notice }}</p>
    </section>
  </div>

  <div v-else class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">食</div>
        <div>
          <h1>健康饮食记录</h1>
          <p>个人 MVP</p>
        </div>
      </div>
      <nav>
        <button v-for="item in tabs" :key="item.key" :class="{ active: tab === item.key }" @click="tab = item.key">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </button>
      </nav>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main>
      <section v-if="notice" class="notice">{{ notice }}</section>

      <section v-if="tab === 'profile'" class="panel">
        <div class="panel-head">
          <h2>个人饮食画像</h2>
          <span :class="['status', profileSaved ? 'ok' : 'muted']">{{ profileSaved ? "已保存" : "未保存" }}</span>
        </div>
        <div class="form-grid">
          <label>
            健康目标
            <select v-model="profile.goal">
              <option>健康饮食</option>
              <option>减脂</option>
              <option>增肌</option>
              <option>控糖</option>
            </select>
          </label>
          <label>
            单餐预算
            <select v-model="profile.budget_level">
              <option>低：≤20元</option>
              <option>中：21-50元</option>
              <option>高：>50元</option>
            </select>
          </label>
          <label>
            就餐方式
            <select v-model="profile.cook_type">
              <option>外卖</option>
              <option>食堂</option>
              <option>自己做饭</option>
            </select>
          </label>
          <label>
            过敏食物
            <input v-model="profileText.allergies" placeholder="花生、海鲜" />
          </label>
          <label>
            不喜欢的食物
            <input v-model="profileText.disliked_foods" placeholder="香菜、肥肉" />
          </label>
          <label>
            偏好的食物
            <input v-model="profileText.preferred_foods" placeholder="鸡胸肉、米饭、青菜" />
          </label>
        </div>
        <div class="actions">
          <button class="ghost" @click="tab = 'record'">稍后再说</button>
          <button @click="saveProfile">保存</button>
        </div>
      </section>

      <section v-if="tab === 'record'" class="panel">
        <div class="panel-head">
          <h2>记录饮食</h2>
          <span class="status muted">单餐 1 张</span>
        </div>
        <div class="form-grid">
          <label>
            餐次
            <select v-model="mealForm.meal_type">
              <option>早餐</option>
              <option>午餐</option>
              <option>晚餐</option>
              <option>加餐</option>
            </select>
          </label>
          <label>
            就餐时间
            <input type="datetime-local" v-model="mealForm.eaten_at" />
          </label>
        </div>
        <label class="drop">
          <UploadCloud :size="28" />
          <strong>上传饮食图片</strong>
          <span>点击选择，支持 JPG PNG WebP</span>
          <input type="file" accept="image/jpeg,image/png,image/webp" @change="onFile" />
        </label>
        <div v-if="preview" class="preview">
          <img :src="preview" alt="饮食图片预览" />
          <button class="icon-button" title="删除图片" @click="clearImage"><Trash2 :size="18" /></button>
        </div>
        <label>
          补充描述
          <textarea v-model="mealForm.description" placeholder="半碗米饭，鸡腿去皮，青菜较少..." />
        </label>
        <div class="actions">
          <button class="ghost" @click="clearMeal">取消</button>
          <button :disabled="submitting" @click="submitMeal">
            <LoaderCircle v-if="submitting" class="spin" :size="18" />
            <Send v-else :size="18" />
            {{ submitting ? "分析中" : "提交分析" }}
          </button>
        </div>
      </section>

      <section v-if="tab === 'analysis'" class="panel">
        <div class="panel-head">
          <h2>本餐分析结果</h2>
          <span v-if="selectedMeal" class="status ok">{{ selectedMeal.status }}</span>
        </div>
        <div v-if="selectedMeal" class="analysis-layout">
          <img class="meal-image" :src="imageUrl(selectedMeal.image_url)" alt="饮食图片" />
          <div>
            <p class="meta">{{ selectedMeal.meal_type }} · {{ formatTime(selectedMeal.eaten_at) }}</p>
            <div v-if="selectedMeal.analysis">
              <div class="score">{{ selectedMeal.analysis.health_score }}<span>/100</span></div>
              <div class="tags"><span v-for="tag in selectedMeal.analysis.risk_tags" :key="tag">{{ tag }}</span></div>
              <h3>识别食物</h3>
              <ul><li v-for="food in selectedMeal.analysis.foods" :key="food">{{ food }}</li></ul>
              <h3>本餐评价</h3>
              <p>{{ selectedMeal.analysis.summary }}</p>
              <h3>调整建议</h3>
              <p>{{ selectedMeal.analysis.next_meal_advice }}</p>
            </div>
          </div>
        </div>
        <div v-else class="empty">提交或从历史中选择一餐后查看分析。</div>
        <div v-if="selectedMeal" class="follow">
          <input v-model="question" placeholder="晚餐怎么补回来？" />
          <button @click="sendQuestion"><MessageSquare :size="18" />发送</button>
        </div>
        <p v-if="answer" class="answer">{{ answer }}</p>
      </section>

      <section v-if="tab === 'history'" class="panel">
        <div class="panel-head">
          <h2>最近 7 天饮食记录</h2>
          <button class="ghost" @click="loadHistory">刷新</button>
        </div>
        <div v-if="historyStats" class="stats">
          <span>记录餐数：{{ historyStats.count }}</span>
          <span>平均评分：{{ historyStats.avg ?? "暂无" }}</span>
          <span>早餐缺失：{{ historyStats.missingBreakfast }} 次</span>
        </div>
        <div v-if="!meals.length" class="empty">
          <p>最近 7 天还没有记录。</p>
          <button @click="tab = 'record'">记录第一餐</button>
        </div>
        <article v-for="meal in meals" :key="meal.id" class="history-item">
          <img :src="imageUrl(meal.image_url)" alt="饮食缩略图" />
          <div>
            <p class="meta">{{ meal.meal_type }} · {{ formatTime(meal.eaten_at) }}</p>
            <strong>{{ meal.analysis?.foods.join("、") || meal.description || "原始记录" }}</strong>
            <div class="tags small">
              <span v-for="tag in meal.analysis?.risk_tags || [meal.status]" :key="tag">{{ tag }}</span>
            </div>
          </div>
          <button class="ghost" @click="openMeal(meal)">查看分析</button>
        </article>
      </section>

      <section v-if="tab === 'recommend'" class="panel">
        <div class="panel-head">
          <h2>下一餐推荐</h2>
          <button class="ghost" @click="loadRecommendation()">刷新</button>
        </div>
        <div v-if="recommendation">
          <p class="meta">推荐餐次：{{ recommendation.meal_type }}</p>
          <p>{{ recommendation.basis }}</p>
          <h3>推荐组合</h3>
          <ul><li v-for="item in recommendation.combo" :key="item">{{ item }}</li></ul>
          <h3>推荐理由</h3>
          <p>{{ recommendation.reason }}</p>
          <h3>需要避免</h3>
          <div class="tags"><span v-for="item in recommendation.avoid" :key="item">{{ item }}</span></div>
          <p class="answer">{{ recommendation.warning || recommendation.budget_note }}</p>
        </div>
        <div class="follow">
          <input v-model="conditions" placeholder="食堂只有鸡腿饭、牛肉面、麻辣烫..." />
          <button @click="loadRecommendation(conditions)"><RefreshCw :size="18" />重新生成</button>
        </div>
      </section>

      <section v-if="tab === 'report'" class="panel">
        <div class="panel-head">
          <h2>每周饮食报告</h2>
          <button @click="generateReport"><RefreshCw :size="18" />重新生成</button>
        </div>
        <div v-if="weekly">
          <p class="meta">周期：{{ weekly.week_start }} 至 {{ weekly.week_end }}</p>
          <div class="stats">
            <span>{{ weekly.completeness }}</span>
            <span>平均评分：{{ weekly.average_score ?? "暂无" }}</span>
          </div>
          <p v-if="weekly.note" class="notice inline">{{ weekly.note }}</p>
          <h3>本周总结</h3>
          <p>{{ weekly.summary }}</p>
          <h3>高频问题</h3>
          <div class="tags"><span v-for="risk in weekly.frequent_risks" :key="risk">{{ risk }}</span></div>
          <h3>可能缺口</h3>
          <ul><li v-for="item in weekly.nutrition_lack" :key="item">{{ item }}</li></ul>
          <h3>风险分析</h3>
          <p>{{ weekly.risk_analysis }}</p>
          <h3>下周补偿计划</h3>
          <ol><li v-for="item in weekly.compensation_plan" :key="item">{{ item }}</li></ol>
        </div>
        <div v-else class="empty">
          <p>暂无周报。最近 7 天无记录时不会生成。</p>
          <button @click="tab = 'record'">记录饮食</button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { BarChart3, ClipboardList, History, LoaderCircle, MessageSquare, RefreshCw, Send, Settings, Sparkles, Trash2, UploadCloud } from "lucide-vue-next";
import { api, clearToken, getToken, imageUrl, setToken, type Meal, type Profile, type Recommendation, type WeeklyReport } from "./api";
import { compressImage } from "./image";

const tabs = [
  { key: "profile", label: "饮食画像", icon: Settings },
  { key: "record", label: "记录饮食", icon: ClipboardList },
  { key: "analysis", label: "本餐分析", icon: Sparkles },
  { key: "history", label: "历史趋势", icon: History },
  { key: "recommend", label: "下一餐", icon: BarChart3 },
  { key: "report", label: "周报", icon: RefreshCw }
] as const;

const tab = ref<(typeof tabs)[number]["key"]>("profile");
const notice = ref("");
const isAuthenticated = ref(Boolean(getToken()));
const loggingIn = ref(false);
const loginForm = reactive({ email: "", password: "" });
const profileSaved = ref(false);
const profile = reactive<Profile>({
  goal: "健康饮食",
  allergies: [],
  disliked_foods: [],
  preferred_foods: [],
  budget_level: "中：21-50元",
  cook_type: "食堂"
});
const profileText = reactive({ allergies: "", disliked_foods: "", preferred_foods: "" });
const mealForm = reactive({ meal_type: "午餐", eaten_at: new Date().toISOString().slice(0, 16), description: "" });
const selectedFile = ref<File | null>(null);
const preview = ref("");
const submitting = ref(false);
const selectedMeal = ref<Meal | null>(null);
const meals = ref<Meal[]>([]);
const question = ref("");
const answer = ref("");
const recommendation = ref<Recommendation | null>(null);
const conditions = ref("");
const weekly = ref<WeeklyReport | null>(null);

const historyStats = computed(() => {
  if (!meals.value.length) return null;
  const scores = meals.value.map((meal) => meal.analysis?.health_score).filter((score): score is number => typeof score === "number");
  return {
    count: meals.value.length,
    avg: scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : null,
    missingBreakfast: Math.max(0, 7 - meals.value.filter((meal) => meal.meal_type === "早餐").length)
  };
});

function splitList(value: string) {
  return value.split(/[，,、]/).map((item) => item.trim()).filter(Boolean);
}

function show(message: string) {
  notice.value = message;
  window.setTimeout(() => (notice.value = ""), 3200);
}

async function login() {
  if (!loginForm.email || !loginForm.password) {
    show("请输入邮箱和密码");
    return;
  }
  loggingIn.value = true;
  try {
    const result = await api.login(loginForm.email, loginForm.password);
    setToken(result.access_token);
    isAuthenticated.value = true;
    await bootstrap();
    show("登录成功");
  } catch (error) {
    show((error as Error).message);
  } finally {
    loggingIn.value = false;
  }
}

function logout() {
  clearToken();
  isAuthenticated.value = false;
}

async function saveProfile() {
  try {
    profile.allergies = splitList(profileText.allergies);
    profile.disliked_foods = splitList(profileText.disliked_foods);
    profile.preferred_foods = splitList(profileText.preferred_foods);
    await api.saveProfile(profile);
    profileSaved.value = true;
    show(profile.preferred_foods.length ? "画像已保存。" : "画像已保存，推荐可能不够个性化。");
  } catch (error) {
    show((error as Error).message);
  }
}

async function onFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    selectedFile.value = await compressImage(file);
    preview.value = URL.createObjectURL(selectedFile.value);
  } catch (error) {
    clearImage();
    show((error as Error).message);
  }
}

function clearImage() {
  selectedFile.value = null;
  preview.value = "";
}

function clearMeal() {
  mealForm.description = "";
  clearImage();
}

async function submitMeal() {
  if (!selectedFile.value) {
    show("请先上传饮食图片");
    return;
  }
  if (submitting.value) return;
  submitting.value = true;
  const form = new FormData();
  form.append("image", selectedFile.value);
  form.append("meal_type", mealForm.meal_type);
  form.append("eaten_at", mealForm.eaten_at);
  form.append("description", mealForm.description);
  try {
    const result = await api.createMeal(form);
    selectedMeal.value = result.record;
    tab.value = "analysis";
    await Promise.all([loadHistory(), loadRecommendation()]);
    show("本餐分析已生成。");
  } catch (error) {
    show((error as Error).message);
  } finally {
    submitting.value = false;
  }
}

async function loadHistory() {
  meals.value = await api.history();
}

function openMeal(meal: Meal) {
  selectedMeal.value = meal;
  tab.value = "analysis";
}

async function sendQuestion() {
  if (!selectedMeal.value || !question.value.trim()) return;
  try {
    const result = await api.followUp(selectedMeal.value.id, question.value);
    answer.value = result.answer;
  } catch (error) {
    show((error as Error).message);
  }
}

async function loadRecommendation(input = "") {
  try {
    recommendation.value = await api.nextMeal(input);
  } catch (error) {
    show((error as Error).message);
  }
}

async function generateReport() {
  try {
    weekly.value = await api.generateWeekly();
  } catch (error) {
    show((error as Error).message);
  }
}

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

async function bootstrap() {
  try {
    const saved = await api.getProfile();
    if (saved) {
      Object.assign(profile, saved);
      profileText.allergies = saved.allergies.join("、");
      profileText.disliked_foods = saved.disliked_foods.join("、");
      profileText.preferred_foods = saved.preferred_foods.join("、");
      profileSaved.value = true;
      tab.value = "record";
    }
    await Promise.all([loadHistory(), loadRecommendation(), api.weekly().then((data) => (weekly.value = data)).catch(() => null)]);
  } catch {
    show("登录状态无效或后端暂不可用。");
  }
}

onMounted(async () => {
  if (isAuthenticated.value) {
    await bootstrap();
  }
});
</script>

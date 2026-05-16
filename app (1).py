import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Оценка риска девиантного поведения", layout="wide")

# ============================================================
# ЗАГРУЗКА РЕГИОНОВ ИЗ ФАЙЛА
# ============================================================

@st.cache_data
def load_region_data():
    df = pd.read_excel('датасет_регионы.xlsx')
    # Очистка
    df = df.replace('-', pd.NA).dropna(subset=['регион', 'сумма_нарушений'])
    df['сумма_нарушений'] = pd.to_numeric(df['сумма_нарушений'], errors='coerce')
    df = df.dropna(subset=['сумма_нарушений'])
    
    # Нормировка risk_score
    max_offenses = df['сумма_нарушений'].max()
    df['risk_score'] = df['сумма_нарушений'] / max_offenses
    
    # Словари для быстрого доступа
    region_risk = dict(zip(df['регион'], df['risk_score']))
    region_level = dict(zip(df['регион'], df['уровень_риска']))
    
    # Список регионов для выпадающего списка
    region_list = sorted(df['регион'].tolist())
    
    return region_risk, region_level, region_list

# Загружаем данные
REGION_RISK, REGION_LEVEL, REGION_LIST = load_region_data()

print(f"✅ Загружено {len(REGION_LIST)} регионов")
print(f"   Диапазон риска: {min(REGION_RISK.values()):.3f} - {max(REGION_RISK.values()):.3f}")

# ============================================================
# КОНТАКТЫ СЛУЖБ ПО РЕГИОНАМ
# ============================================================

SERVICES_DB = {
    # Центральный федеральный округ
    "Московская область": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-495-624-60-01",
        "social": "8-495-608-65-06",
        "emergency": "112",
        "local_center": "Центр 'Доверие' (Москва, ул. Новослободская, 45)"
    },
    "г. Москва": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-495-624-60-01",
        "social": "8-495-608-65-06",
        "emergency": "112",
        "local_center": "Московская служба психологической помощи (ул. Селезнёвская, 11)"
    },
    "г. Санкт-Петербург": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-812-718-22-16",
        "social": "8-812-576-10-15",
        "emergency": "112",
        "local_center": "Центр 'Анна' (СПб, наб. реки Фонтанки, 120)"
    },
    "Ленинградская область": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-812-718-22-16",
        "social": "8-812-576-10-15",
        "emergency": "112",
        "local_center": "Ленинградский областной центр психологической помощи"
    },
    "Республика Татарстан": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-843-279-26-00",
        "social": "8-843-236-62-67",
        "emergency": "112",
        "local_center": "Республиканский центр психологической поддержки (Казань, ул. Кремлевская, 33)"
    },
    "Краснодарский край": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-861-214-58-88",
        "social": "8-861-214-58-00",
        "emergency": "112",
        "local_center": "Центр 'Доверие' (Краснодар, ул. Северная, 405)"
    },
    "Новосибирская область": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-383-223-22-33",
        "social": "8-383-223-22-33",
        "emergency": "112",
        "local_center": "Новосибирский центр психологической помощи"
    },
    "Свердловская область": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-343-370-70-70",
        "social": "8-343-370-70-70",
        "emergency": "112",
        "local_center": "Центр социальной помощи 'Апрель' (Екатеринбург)"
    },
    "Республика Ингушетия": {
        "child_helpline": "8-800-2000-122",
        "psychology": "8-873-222-22-55",
        "social": "8-873-222-22-55",
        "emergency": "112",
        "local_center": "Центр психологической помощи (Магас)"
    },
}

def get_services(region):
    """Возвращает контакты служб для региона"""
    if region in SERVICES_DB:
        return SERVICES_DB[region]
    else:
        return {
            "child_helpline": "8-800-2000-122",
            "psychology": "8-800-250-00-88",
            "social": "8-800-700-88-88",
            "emergency": "112",
            "local_center": "Центр социальной помощи (федеральный)"
        }

# ============================================================
# FUZZY-МОДЕЛЬ
# ============================================================

def create_left(b, c):
    def func(x):
        if x <= b: return 1.0
        elif x <= c: return (c - x) / (c - b)
        else: return 0.0
    return func

def create_trap(a, b, c, d):
    def func(x):
        if x <= a: return 0.0
        elif x <= b: return (x - a) / (b - a) if b > a else 1.0
        elif x <= c: return 1.0
        elif x <= d: return (d - x) / (d - c) if d > c else 0.0
        else: return 0.0
    return func

def create_right(b, c):
    def func(x):
        if x <= b: return 0.0
        elif x <= c: return (x - b) / (c - b)
        else: return 1.0
    return func

# Функции принадлежности
internet_low = create_left(15, 35)
internet_medium = create_trap(20, 35, 50, 65)
internet_high = create_right(50, 70)

cyber_low = create_left(10, 30)
cyber_medium = create_trap(15, 30, 45, 60)
cyber_high = create_right(45, 65)

psycho_low = create_left(10, 30)
psycho_medium = create_trap(15, 30, 45, 60)
psycho_high = create_right(45, 65)

behavior_low = create_left(15, 35)
behavior_medium = create_trap(20, 35, 50, 65)
behavior_high = create_right(50, 70)

family_low = create_left(25, 45)
family_medium = create_trap(30, 45, 60, 75)
family_high = create_right(60, 80)

risk_low = create_left(15, 35)
risk_medium = create_trap(20, 35, 60, 75)
risk_high = create_right(60, 80)

MEMBERSHIP = {
    'internet': {'low': internet_low, 'medium': internet_medium, 'high': internet_high},
    'cyber': {'low': cyber_low, 'medium': cyber_medium, 'high': cyber_high},
    'psycho': {'low': psycho_low, 'medium': psycho_medium, 'high': psycho_high},
    'behavior': {'low': behavior_low, 'medium': behavior_medium, 'high': behavior_high},
    'family': {'low': family_low, 'medium': family_medium, 'high': family_high},
}

# Правила
RULES = [
    {'conditions': [('region', 'high'), ('internet', 'high'), ('cyber', 'high')], 'result': 'high'},
    {'conditions': [('region', 'high'), ('internet', 'high')], 'result': 'high'},
    {'conditions': [('region', 'high'), ('cyber', 'high')], 'result': 'high'},
    {'conditions': [('internet', 'high'), ('cyber', 'high')], 'result': 'high'},
    {'conditions': [('cyber', 'high'), ('psycho', 'high')], 'result': 'high'},
    {'conditions': [('region', 'high')], 'result': 'medium'},
    {'conditions': [('internet', 'high')], 'result': 'medium'},
    {'conditions': [('cyber', 'high')], 'result': 'medium'},
    {'conditions': [('psycho', 'high')], 'result': 'medium'},
    {'conditions': [('region', 'low')], 'result': 'low'},
    {'conditions': [('region', 'low'), ('internet', 'low'), ('cyber', 'low')], 'result': 'low'},
    {'conditions': [('internet', 'low'), ('cyber', 'low'), ('psycho', 'low')], 'result': 'low'},
]

def evaluate_risk(region, internet_score, cyber_score, psycho_score, behavior_score, family_score):
    region_risk = REGION_RISK.get(region, 0.5)
    
    if region_risk <= 0.33:
        region_membership = {'low': 1.0, 'medium': 0.0, 'high': 0.0}
    elif region_risk <= 0.66:
        region_membership = {'low': 0.0, 'medium': 1.0, 'high': 0.0}
    else:
        region_membership = {'low': 0.0, 'medium': 0.0, 'high': 1.0}
    
    fuzzified = {
        'region': region_membership,
        'internet': {'low': MEMBERSHIP['internet']['low'](internet_score), 'medium': MEMBERSHIP['internet']['medium'](internet_score), 'high': MEMBERSHIP['internet']['high'](internet_score)},
        'cyber': {'low': MEMBERSHIP['cyber']['low'](cyber_score), 'medium': MEMBERSHIP['cyber']['medium'](cyber_score), 'high': MEMBERSHIP['cyber']['high'](cyber_score)},
        'psycho': {'low': MEMBERSHIP['psycho']['low'](psycho_score), 'medium': MEMBERSHIP['psycho']['medium'](psycho_score), 'high': MEMBERSHIP['psycho']['high'](psycho_score)},
        'behavior': {'low': MEMBERSHIP['behavior']['low'](behavior_score), 'medium': MEMBERSHIP['behavior']['medium'](behavior_score), 'high': MEMBERSHIP['behavior']['high'](behavior_score)},
        'family': {'low': MEMBERSHIP['family']['low'](family_score), 'medium': MEMBERSHIP['family']['medium'](family_score), 'high': MEMBERSHIP['family']['high'](family_score)},
    }
    
    activation = {'low': 0.0, 'medium': 0.0, 'high': 0.0}
    for rule in RULES:
        rule_strength = 1.0
        for cat, term in rule['conditions']:
            rule_strength = min(rule_strength, fuzzified[cat][term])
        if rule_strength > 0.01:
            activation[rule['result']] = max(activation[rule['result']], rule_strength)
    
    x_vals = np.linspace(0, 100, 500)
    aggregated = np.zeros_like(x_vals)
    for i, x in enumerate(x_vals):
        low = min(risk_low(x), activation['low'])
        medium = min(risk_medium(x), activation['medium'])
        high = min(risk_high(x), activation['high'])
        aggregated[i] = max(low, medium, high)
    
    if np.sum(aggregated) > 0:
        risk_percent = np.sum(x_vals * aggregated) / np.sum(aggregated)
    else:
        risk_percent = 0
    
    if risk_percent <= 33:
        risk_level = 'low'
    elif risk_percent <= 66:
        risk_level = 'medium'
    else:
        risk_level = 'high'
    
    return {'risk_percent': round(risk_percent, 1), 'risk_level': risk_level, 'region_risk_score': region_risk}

def get_recommendations(scores, risk_level, risk_percent):
    recommendations = []
    
    if risk_level == "high":
        recommendations.append({"type": "critical", "title": "🚨 СРОЧНАЯ РЕКОМЕНДАЦИЯ", "text": f"Ваш уровень риска — {risk_percent}% (ВЫСОКИЙ). Обратитесь к психологу как можно скорее."})
    elif risk_level == "medium":
        recommendations.append({"type": "warning", "title": "⚠️ ВАЖНАЯ РЕКОМЕНДАЦИЯ", "text": f"Ваш уровень риска — {risk_percent}% (СРЕДНИЙ). Рекомендуется консультация школьного психолога."})
    else:
        recommendations.append({"type": "success", "title": "✅ ХОРОШИЕ НОВОСТИ", "text": f"Ваш уровень риска — {risk_percent}% (НИЗКИЙ). Продолжайте в том же духе."})
    
    if scores.get('internet', 0) > 50:
        recommendations.append({"type": "warning", "title": "🌐 Интернет-активность", "text": "Сократите время в интернете до 3-4 часов в день. Отпишитесь от агрессивных пабликов."})
    if scores.get('cyber', 0) > 45:
        recommendations.append({"type": "critical", "title": "💻 Кибербуллинг", "text": "Обратитесь к психологу — кибербуллинг требует поддержки. Сохраняйте скриншоты."})
    if scores.get('psycho', 0) > 45:
        recommendations.append({"type": "warning", "title": "🧠 Психологическое состояние", "text": "Практикуйте дыхательные упражнения при стрессе. Ведите дневник эмоций."})
    if scores.get('behavior', 0) > 50:
        recommendations.append({"type": "warning", "title": "👊 Поведение", "text": "Найдите альтернативные способы выражения эмоций (спорт, творчество)."})
    if scores.get('family', 0) > 60:
        recommendations.append({"type": "info", "title": "🏠 Семейная ситуация", "text": "Попробуйте спокойно поговорить с родителями о своих чувствах."})
    
    return recommendations

# ============================================================
# ВОПРОСЫ АНКЕТЫ
# ============================================================

def question_block(category, questions):
    scores = []
    for q in questions:
        answer = st.radio(q["text"], q["options"], index=2, key=f"{category}_{q['id']}", horizontal=True)
        answer_map = {opt: score for opt, score in zip(q["options"], q["scores"])}
        scores.append(answer_map[answer])
    return sum(scores)

questions_internet = [
    {"id": 1, "text": "Сколько часов в день ты проводишь в интернете?", "options": ["0-2ч", "3-4ч", "5-6ч", "7-8ч", "9+ч"], "scores": [0, 5, 10, 15, 20]},
    {"id": 2, "text": "На какие паблики/каналы ты подписан?", "options": ["Образовательные", "Юмор", "Черный юмор", "Агрессия", "Экстремизм"], "scores": [0, 5, 10, 15, 20]},
    {"id": 3, "text": "Сколько у тебя интернет-друзей (не из реальной жизни)?", "options": ["0", "1-2", "3-5", "6-10", "10+"], "scores": [0, 5, 10, 15, 20]},
    {"id": 4, "text": "Участвовал ли ты в сомнительных онлайн-челленджах?", "options": ["Никогда", "Слышал, но нет", "1 раз", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 5, "text": "Сколько у тебя анонимных аккаунтов?", "options": ["0", "1", "2-3", "4-5", "5+"], "scores": [0, 5, 10, 15, 20]},
]

questions_cyber = [
    {"id": 1, "text": "Оскорблял ли ты кого-то в интернете?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 2, "text": "Участвовал ли ты в травле (буллинге) онлайн?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 3, "text": "Был ли ты жертвой травли в интернете?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 4, "text": "Получал ли ты угрозы в интернете?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 5, "text": "Распространял ли ты слухи/фейки о ком-то?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
]

questions_psycho = [
    {"id": 1, "text": "Как часто ты чувствуешь одиночество?", "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 2, "text": "Бывают ли у тебя мысли, что ты никому не нужен?", "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 3, "text": "Как часто у тебя бывают вспышки гнева/агрессии?", "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 4, "text": "Есть ли у тебя проблемы со сном?", "options": ["Нет", "Редко", "Иногда", "Часто", "Почти всегда"], "scores": [0, 5, 10, 15, 20]},
    {"id": 5, "text": "Были ли у тебя мысли причинить вред себе или другим?", "options": ["Никогда", "Были, но не серьезно", "Серьезные мысли", "Планировал", "Были попытки"], "scores": [0, 5, 10, 15, 20]},
]

questions_behavior = [
    {"id": 1, "text": "Как часто ты прогуливаешь школу?", "options": ["Никогда", "1-2р/мес", "Раз/нед", "2-3р/нед", "Почти ежедневно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 2, "text": "Бывают ли у тебя конфликты с учителями?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 3, "text": "Есть ли у тебя друзья, которые нарушают закон?", "options": ["Нет", "1 друг", "2-3 друга", "Много", "Все друзья"], "scores": [0, 5, 10, 15, 20]},
    {"id": 4, "text": "Участвовал ли ты в драках?", "options": ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 5, "text": "Забирали ли тебя в полицию?", "options": ["Нет", "1 раз", "2-3 раза", "Несколько раз", "Стою на учёте"], "scores": [0, 5, 10, 15, 20]},
]

questions_family = [
    {"id": 1, "text": "С кем ты живешь?", "options": ["С обоими родителями", "С одним родителем", "С родственниками", "С опекунами", "В интернате"], "scores": [0, 5, 10, 15, 20]},
    {"id": 2, "text": "Как часто бывают конфликты с родителями?", "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], "scores": [0, 5, 10, 15, 20]},
    {"id": 3, "text": "Насколько родители контролируют твою жизнь?", "options": ["Полностью", "Частично", "Минимально", "Почти нет", "Совсем нет"], "scores": [0, 5, 10, 15, 20]},
    {"id": 4, "text": "Есть ли в семье проблемы с алкоголем/наркотиками?", "options": ["Нет", "Не уверен", "Дальние родственники", "Близкий родственник", "Родители"], "scores": [0, 5, 10, 15, 20]},
    {"id": 5, "text": "Какой уровень дохода в семье?", "options": ["Высокий", "Средний", "Ниже среднего", "Низкий", "Очень низкий"], "scores": [0, 5, 10, 15, 20]},
]

# ============================================================
# СТИЛИ
# ============================================================

st.markdown("""
<style>
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-high { background: linear-gradient(135deg, #ff6b6b, #ee5a24); padding: 2rem; border-radius: 20px; text-align: center; color: white; }
    .risk-medium { background: linear-gradient(135deg, #ffa502, #e67e22); padding: 2rem; border-radius: 20px; text-align: center; color: white; }
    .risk-low { background: linear-gradient(135deg, #2ed573, #00b894); padding: 2rem; border-radius: 20px; text-align: center; color: white; }
    .risk-percent { font-size: 4rem; font-weight: bold; }
    .rec-critical { border-left: 4px solid #ee5a24; background: #fff5f0; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; }
    .rec-warning { border-left: 4px solid #ffa502; background: #fffbf0; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; }
    .rec-info { border-left: 4px solid #1e90ff; background: #f0f8ff; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; }
    .rec-success { border-left: 4px solid #00b894; background: #f0fff4; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; }
    .sidebar-info { background: #f8f9fa; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; }
    .card { background: white; padding: 1.5rem; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ИНТЕРФЕЙС
# ============================================================

st.markdown('<div class="main-title"><h1>🧠 Оценка риска девиантного поведения</h1><p>Анонимная анкета для подростков 10-18 лет</p></div>', unsafe_allow_html=True)

# Боковая панель
with st.sidebar:
    st.markdown("### 📞 Контакты (федеральные)")
    st.markdown('<div class="sidebar-info"><strong>8-800-2000-122</strong><br>Детский телефон доверия</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-info"><strong>8-800-250-00-88</strong><br>Психологическая помощь</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-info"><strong>112</strong><br>Экстренная помощь</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption(f"✅ Загружено {len(REGION_LIST)} регионов")
    st.caption("Все данные анонимны. Результат не является медицинским диагнозом.")

# Форма
with st.form("anketa"):
    st.markdown('<div class="card"><h3>📋 Личная информация</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Возраст", min_value=10, max_value=18, value=14, step=1)
    with col2:
        gender = st.selectbox("Пол", ["Мужской", "Женский"])
    with col3:
        region = st.selectbox("Регион проживания", REGION_LIST)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>🌐 Интернет-активность (5 вопросов)</h3>', unsafe_allow_html=True)
    internet_score = question_block("internet", questions_internet)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>💻 Кибербуллинг (5 вопросов)</h3>', unsafe_allow_html=True)
    cyber_score = question_block("cyber", questions_cyber)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>🧠 Психологическое состояние (5 вопросов)</h3>', unsafe_allow_html=True)
    psycho_score = question_block("psycho", questions_psycho)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>👊 Поведение в реальной жизни (5 вопросов)</h3>', unsafe_allow_html=True)
    behavior_score = question_block("behavior", questions_behavior)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>🏠 Семейная ситуация (5 вопросов)</h3>', unsafe_allow_html=True)
    family_score = question_block("family", questions_family)
    st.markdown('</div>', unsafe_allow_html=True)
    
    submitted = st.form_submit_button("📊 Получить результат", use_container_width=True, type="primary")
    
    if submitted:
        with st.spinner("Анализируем ответы..."):
            result = evaluate_risk(region, internet_score, cyber_score, psycho_score, behavior_score, family_score)
            
            # Возрастная корректировка
            if 14 <= age <= 16:
                result['risk_percent'] = min(100, result['risk_percent'] * 1.1)
            elif age <= 12:
                result['risk_percent'] = result['risk_percent'] * 0.8
            
            scores = {
                'internet': internet_score,
                'cyber': cyber_score,
                'psycho': psycho_score,
                'behavior': behavior_score,
                'family': family_score
            }
            
            recommendations = get_recommendations(scores, result['risk_level'], result['risk_percent'])
            
            st.markdown("---")
            st.markdown("## 📊 Результат оценки")
            
            # Результат
            region_level = REGION_LEVEL.get(region, 'средний')
            region_icon = "🔴" if region_level == 'высокий' else "🟡" if region_level == 'средний' else "🟢"
            
            if result['risk_level'] == 'high':
                st.markdown(f'<div class="risk-high"><div class="risk-percent">{result["risk_percent"]:.0f}%</div><div>🔴 ВЫСОКИЙ РИСК</div><div style="margin-top: 0.5rem;">{region_icon} {region}: риск региона {result["region_risk_score"]*100:.0f}% ({region_level})</div></div>', unsafe_allow_html=True)
            elif result['risk_level'] == 'medium':
                st.markdown(f'<div class="risk-medium"><div class="risk-percent">{result["risk_percent"]:.0f}%</div><div>🟡 СРЕДНИЙ РИСК</div><div style="margin-top: 0.5rem;">{region_icon} {region}: риск региона {result["region_risk_score"]*100:.0f}% ({region_level})</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="risk-low"><div class="risk-percent">{result["risk_percent"]:.0f}%</div><div>🟢 НИЗКИЙ РИСК</div><div style="margin-top: 0.5rem;">{region_icon} {region}: риск региона {result["region_risk_score"]*100:.0f}% ({region_level})</div></div>', unsafe_allow_html=True)
            
            # График
            fig, ax = plt.subplots(figsize=(8, 5))
            categories = ['Интернет', 'Кибербуллинг', 'Психология', 'Поведение', 'Семья']
            values = [internet_score, cyber_score, psycho_score, behavior_score, family_score]
            colors_bar = ['#2ed573' if v < 40 else '#ffa502' if v < 70 else '#ff6b6b' for v in values]
            bars = ax.bar(categories, values, color=colors_bar, edgecolor='white', linewidth=1.5)
            ax.axhline(y=50, color='#ffa502', linestyle='--', linewidth=2, label='Порог риска (50 баллов)')
            ax.set_ylim(0, 105)
            ax.set_ylabel('Баллы (0-100)')
            ax.set_title('Ваши баллы по категориям')
            ax.legend()
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{val}', ha='center', fontsize=11, fontweight='bold')
            st.pyplot(fig)
            
            # Рекомендации
            st.markdown("## 💡 Персональные рекомендации")
            for rec in recommendations:
                if rec['type'] == 'critical':
                    st.markdown(f'<div class="rec-critical"><strong>{rec["title"]}</strong><br>{rec["text"]}</div>', unsafe_allow_html=True)
                elif rec['type'] == 'warning':
                    st.markdown(f'<div class="rec-warning"><strong>{rec["title"]}</strong><br>{rec["text"]}</div>', unsafe_allow_html=True)
                elif rec['type'] == 'info':
                    st.markdown(f'<div class="rec-info"><strong>{rec["title"]}</strong><br>{rec["text"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="rec-success"><strong>{rec["title"]}</strong><br>{rec["text"]}</div>', unsafe_allow_html=True)
            
            # Контакты служб ПО РЕГИОНУ
            services = get_services(region)
            st.markdown("## 📞 Куда обратиться в вашем регионе")
            st.markdown(f"""
            <div style="background: #f0f4ff; padding: 1.5rem; border-radius: 16px;">
                <p><strong>🏢 {services['local_center']}</strong></p>
                <p>📞 <strong>Детский телефон доверия:</strong> {services['child_helpline']}</p>
                <p>🧠 <strong>Психологическая помощь:</strong> {services['psychology']}</p>
                <p>🤝 <strong>Социальная помощь:</strong> {services['social']}</p>
                <p>🚨 <strong>Экстренная помощь:</strong> {services['emergency']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("📞 Если вы в кризисной ситуации, немедленно позвоните: **8-800-2000-122** или **112**")

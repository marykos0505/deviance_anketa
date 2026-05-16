import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Оценка риска девиантного поведения", layout="wide")

# ============================================================
# МОДЕЛЬ
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

# Категории
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

REGION_RISK = {
    'Республика Татарстан': 0.95, 'Республика Ингушетия': 0.05,
    'Московская область': 0.72, 'Краснодарский край': 0.55,
    'г. Санкт-Петербург': 0.48, 'Республика Адыгея': 0.02,
}

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
        recommendations.append("🚨 ВЫСОКИЙ РИСК: Обратитесь к психологу как можно скорее")
    elif risk_level == "medium":
        recommendations.append("⚠️ СРЕДНИЙ РИСК: Рекомендуется консультация школьного психолога")
    else:
        recommendations.append("✅ НИЗКИЙ РИСК: Продолжайте в том же духе")
    
    if scores.get('internet', 0) > 50:
        recommendations.append("🌐 Сократите время в интернете до 3-4 часов в день")
    if scores.get('cyber', 0) > 45:
        recommendations.append("💻 Обратитесь к психологу — кибербуллинг требует поддержки")
    if scores.get('psycho', 0) > 45:
        recommendations.append("🧠 Подумайте о консультации психолога")
    return recommendations

# ============================================================
# ИНТЕРФЕЙС
# ============================================================

st.title("🧠 Оценка риска девиантного поведения")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Личная информация")
    age = st.number_input("Возраст", min_value=10, max_value=18, value=14)
    gender = st.selectbox("Пол", ["Мужской", "Женский"])
    region = st.selectbox("Регион", list(REGION_RISK.keys()))

with col2:
    st.subheader("🌐 Интернет-активность")
    internet_hours = st.radio("Часов в интернете в день", ["0-2ч", "3-4ч", "5-6ч", "7-8ч", "9+ч"], index=2)
    internet_pubs = st.radio("Подписки на паблики", ["Образовательные", "Юмор", "Черный юмор", "Агрессия", "Экстремизм"], index=2)
    
    internet_score = 0
    if internet_hours == "0-2ч": internet_score += 0
    elif internet_hours == "3-4ч": internet_score += 5
    elif internet_hours == "5-6ч": internet_score += 10
    elif internet_hours == "7-8ч": internet_score += 15
    else: internet_score += 20
    
    if internet_pubs == "Образовательные": internet_score += 0
    elif internet_pubs == "Юмор": internet_score += 5
    elif internet_pubs == "Черный юмор": internet_score += 10
    elif internet_pubs == "Агрессия": internet_score += 15
    else: internet_score += 20

st.markdown("---")

st.subheader("💻 Кибербуллинг")
cyber_offend = st.radio("Оскорблял ли ты кого-то в интернете?", ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], index=2)
cyber_victim = st.radio("Был ли ты жертвой травли?", ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], index=2)

cyber_map = {"Никогда": 0, "1 раз": 5, "2-3 раза": 10, "Несколько раз": 15, "Регулярно": 20}
cyber_score = cyber_map[cyber_offend] + cyber_map[cyber_victim]

st.markdown("---")

st.subheader("🧠 Психологическое состояние")
psycho_lonely = st.radio("Чувство одиночества", ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], index=2)
psycho_anger = st.radio("Вспышки гнева", ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], index=2)

psycho_map = {"Никогда": 0, "Редко": 5, "Иногда": 10, "Часто": 15, "Постоянно": 20}
psycho_score = psycho_map[psycho_lonely] + psycho_map[psycho_anger]

st.markdown("---")

st.subheader("👊 Поведение")
behavior_truancy = st.radio("Прогулы школы", ["Никогда", "1-2р/мес", "Раз/нед", "2-3р/нед", "Почти ежедневно"], index=2)
behavior_fight = st.radio("Участие в драках", ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], index=2)

behavior_map1 = {"Никогда": 0, "1-2р/мес": 5, "Раз/нед": 10, "2-3р/нед": 15, "Почти ежедневно": 20}
behavior_map2 = {"Никогда": 0, "1 раз": 5, "2-3 раза": 10, "Несколько раз": 15, "Регулярно": 20}
behavior_score = behavior_map1[behavior_truancy] + behavior_map2[behavior_fight]

st.markdown("---")

st.subheader("🏠 Семейная ситуация")
family_conflict = st.radio("Конфликты с родителями", ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], index=2)
family_income = st.radio("Доход семьи", ["Высокий", "Средний", "Ниже среднего", "Низкий", "Очень низкий"], index=2)

family_map1 = {"Никогда": 0, "Редко": 5, "Иногда": 10, "Часто": 15, "Постоянно": 20}
family_map2 = {"Высокий": 0, "Средний": 5, "Ниже среднего": 10, "Низкий": 15, "Очень низкий": 20}
family_score = family_map1[family_conflict] + family_map2[family_income]

if st.button("📊 Получить результат", type="primary", use_container_width=True):
    with st.spinner("Анализируем..."):
        result = evaluate_risk(region, internet_score, cyber_score, psycho_score, behavior_score, family_score)
        
        if 14 <= age <= 16:
            result['risk_percent'] = min(100, result['risk_percent'] * 1.1)
        elif age <= 12:
            result['risk_percent'] = result['risk_percent'] * 0.8
        
        recommendations = get_recommendations(
            {'internet': internet_score, 'cyber': cyber_score, 'psycho': psycho_score},
            result['risk_level'], result['risk_percent']
        )
        
        st.markdown("---")
        
        if result['risk_level'] == 'high':
            st.error(f"## 🔴 РИСК: {result['risk_percent']:.0f}% — ВЫСОКИЙ")
        elif result['risk_level'] == 'medium':
            st.warning(f"## 🟡 РИСК: {result['risk_percent']:.0f}% — СРЕДНИЙ")
        else:
            st.success(f"## 🟢 РИСК: {result['risk_percent']:.0f}% — НИЗКИЙ")
        
        st.markdown(f"*Регион: {region} (риск {result['region_risk_score']*100:.0f}%)*")
        
        st.subheader("💡 Рекомендации")
        for rec in recommendations:
            st.write(f"• {rec}")
        
        st.subheader("📞 Телефоны доверия")
        st.write("📞 Детский телефон доверия: **8-800-2000-122**")
        st.write("🧠 Психологическая помощь: **8-800-250-00-88**")
        st.write("🚨 Экстренная помощь: **112**")

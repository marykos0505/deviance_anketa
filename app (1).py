import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Оценка риска девиантного поведения",
    page_icon="🧠",
    layout="wide"
)

# ============================================================
# СТИЛИ (CSS)
# ============================================================

st.markdown("""
<style>
    /* Главный заголовок */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-title h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-title p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Карточки */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
    }
    .card h3 {
        color: #667eea;
        margin-bottom: 1rem;
        font-size: 1.3rem;
    }
    
    /* Результат */
    .result-high {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
    }
    .result-medium {
        background: linear-gradient(135deg, #ffa502, #e67e22);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
    }
    .result-low {
        background: linear-gradient(135deg, #2ed573, #00b894);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
    }
    .risk-percent {
        font-size: 4rem;
        font-weight: bold;
    }
    
    /* Рекомендации */
    .rec-critical {
        border-left: 4px solid #ee5a24;
        background: #fff5f0;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .rec-warning {
        border-left: 4px solid #ffa502;
        background: #fffbf0;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .rec-info {
        border-left: 4px solid #1e90ff;
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .rec-success {
        border-left: 4px solid #00b894;
        background: #f0fff4;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    /* Боковая панель */
    .sidebar-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    /* Прогресс-бар */
    .progress-bar {
        height: 8px;
        border-radius: 4px;
        background: #e0e0e0;
        margin: 5px 0;
    }
    .progress-fill {
        height: 8px;
        border-radius: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        width: 0%;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# МОДЕЛЬ (fuzzy-логика)
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
    'Свердловская область': 0.65, 'Новосибирская область': 0.60,
    'Челябинская область': 0.82, 'Иркутская область': 0.88,
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

# ============================================================
# СТАТИСТИКА ПО РЕГИОНАМ
# ============================================================

region_stats = pd.DataFrame([
    {'region': 'Республика Татарстан', 'risk_score': 0.95, 'level': 'high'},
    {'region': 'Иркутская область', 'risk_score': 0.88, 'level': 'high'},
    {'region': 'Челябинская область', 'risk_score': 0.82, 'level': 'high'},
    {'region': 'Московская область', 'risk_score': 0.72, 'level': 'medium'},
    {'region': 'г. Санкт-Петербург', 'risk_score': 0.48, 'level': 'medium'},
    {'region': 'Республика Адыгея', 'risk_score': 0.02, 'level': 'low'},
    {'region': 'Республика Ингушетия', 'risk_score': 0.05, 'level': 'low'},
])

# ============================================================
# РЕКОМЕНДАЦИИ
# ============================================================

def get_detailed_recommendations(scores, risk_level, risk_percent, age, gender):
    recommendations = []
    
    # Общие рекомендации по уровню риска
    if risk_level == "high":
        recommendations.append({
            "type": "critical",
            "title": "🚨 СРОЧНАЯ РЕКОМЕНДАЦИЯ",
            "text": f"Ваш уровень риска — {risk_percent}% (ВЫСОКИЙ). Рекомендуется как можно скорее обратиться к психологу или психиатру. Не откладывайте визит к специалисту.",
            "action": "Запишитесь на приём к психологу в ближайшие дни"
        })
    elif risk_level == "medium":
        recommendations.append({
            "type": "warning",
            "title": "⚠️ ВАЖНАЯ РЕКОМЕНДАЦИЯ",
            "text": f"Ваш уровень риска — {risk_percent}% (СРЕДНИЙ). Рекомендуется обратиться к школьному психологу для профилактической беседы.",
            "action": "Поговорите со школьным психологом на следующей неделе"
        })
    else:
        recommendations.append({
            "type": "success",
            "title": "✅ ХОРОШИЕ НОВОСТИ",
            "text": f"Ваш уровень риска — {risk_percent}% (НИЗКИЙ). Это хороший результат.",
            "action": "Продолжайте следить за своим состоянием"
        })
    
    # Рекомендации по категориям
    category_details = [
        {"name": "🌐 Интернет-активность", "score": scores['internet'], "threshold": 50, 
         "advice": "Постарайтесь сократить время в интернете до 3-4 часов в день. Отпишитесь от агрессивных пабликов.", 
         "resource": "Приложение 'Экранное время' для контроля"},
        {"name": "💻 Кибербуллинг", "score": scores['cyber'], "threshold": 45,
         "advice": "Обратитесь к психологу — кибербуллинг требует поддержки. Сохраняйте скриншоты обидчиков.", 
         "resource": "stopbullying.ru — помощь жертвам травли"},
        {"name": "🧠 Психологическое состояние", "score": scores['psycho'], "threshold": 45,
         "advice": "Практикуйте дыхательные упражнения при стрессе. Ведите дневник эмоций.", 
         "resource": "Медитация в приложении 'Calm' или 'Headspace'"},
        {"name": "👊 Поведение", "score": scores['behavior'], "threshold": 50,
         "advice": "Найдите альтернативные способы выражения эмоций (спорт, творчество).", 
         "resource": "Кружки и секции в вашем городе"},
        {"name": "🏠 Семейная ситуация", "score": scores['family'], "threshold": 60,
         "advice": "Попробуйте спокойно поговорить с родителями о своих чувствах.", 
         "resource": "Семейные консультации в центре 'Диалог'"},
    ]
    
    for cat in category_details:
        if cat["score"] >= cat["threshold"]:
            recommendations.append({
                "type": "warning" if cat["score"] < 70 else "critical",
                "title": cat["name"],
                "text": cat["advice"],
                "action": cat["resource"],
                "score": cat["score"]
            })
        elif cat["score"] >= cat["threshold"] - 15:
            recommendations.append({
                "type": "info",
                "title": cat["name"],
                "text": f"Ваш показатель ({cat['score']}/100) в зоне внимания. " + cat["advice"],
                "action": cat["resource"],
                "score": cat["score"]
            })
    
    return recommendations

# ============================================================
# ИНТЕРФЕЙС
# ============================================================

# Шапка
st.markdown("""
<div class="main-title">
    <h1>🧠 Оценка риска девиантного поведения</h1>
    <p>Анонимная анкета для подростков 10-18 лет</p>
</div>
""", unsafe_allow_html=True)

# Боковая панель со статистикой
with st.sidebar:
    st.markdown("## 📊 Статистика регионов")
    
    # Диаграмма рисков регионов
    fig_regions = px.bar(region_stats, x='region', y='risk_score', color='level',
                          color_discrete_map={'high': '#ff6b6b', 'medium': '#ffa502', 'low': '#2ed573'},
                          title="Уровень риска по регионам")
    fig_regions.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_regions, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📞 Телефоны доверия")
    st.markdown("""
    <div class="sidebar-info">
        <strong>📞 Детский телефон доверия:</strong><br>
        <span style="font-size: 1.2rem;">8-800-2000-122</span><br>
        <small>круглосуточно, анонимно, бесплатно</small>
    </div>
    <div class="sidebar-info">
        <strong>🧠 Психологическая помощь:</strong><br>
        <span style="font-size: 1.2rem;">8-800-250-00-88</span>
    </div>
    <div class="sidebar-info">
        <strong>🚨 Экстренная помощь:</strong><br>
        <span style="font-size: 1.2rem;">112</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("*Все данные анонимны*")
    st.markdown("*Результат не является медицинским диагнозом*")

# Основная форма
with st.form("questionnaire_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card"><h3>📋 Личная информация</h3>', unsafe_allow_html=True)
        age = st.number_input("Возраст", min_value=10, max_value=18, value=14, step=1)
        gender = st.selectbox("Пол", ["Мужской", "Женский"])
        region = st.selectbox("Регион проживания", list(REGION_RISK.keys()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card"><h3>🌐 Интернет-активность</h3>', unsafe_allow_html=True)
        internet_hours = st.radio("Часов в интернете в день", ["0-2ч", "3-4ч", "5-6ч", "7-8ч", "9+ч"], index=2, horizontal=True)
        internet_pubs = st.radio("Подписки на паблики", ["Образовательные", "Юмор", "Черный юмор", "Агрессия", "Экстремизм"], index=2, horizontal=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Расчёт баллов интернета
    internet_score = 0
    internet_map = {"0-2ч": 0, "3-4ч": 5, "5-6ч": 10, "7-8ч": 15, "9+ч": 20}
    pubs_map = {"Образовательные": 0, "Юмор": 5, "Черный юмор": 10, "Агрессия": 15, "Экстремизм": 20}
    internet_score += internet_map[internet_hours] + pubs_map[internet_pubs]
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown('<div class="card"><h3>💻 Кибербуллинг</h3>', unsafe_allow_html=True)
        cyber_offend = st.radio("Оскорблял ли ты кого-то в интернете?", ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], index=2)
        cyber_victim = st.radio("Был ли ты жертвой травли?", ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], index=2)
        st.markdown('</div>', unsafe_allow_html=True)
        
        cyber_map = {"Никогда": 0, "1 раз": 5, "2-3 раза": 10, "Несколько раз": 15, "Регулярно": 20}
        cyber_score = cyber_map[cyber_offend] + cyber_map[cyber_victim]
    
    with col4:
        st.markdown('<div class="card"><h3>🧠 Психологическое состояние</h3>', unsafe_allow_html=True)
        psycho_lonely = st.radio("Чувство одиночества", ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], index=2)
        psycho_anger = st.radio("Вспышки гнева", ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], index=2)
        st.markdown('</div>', unsafe_allow_html=True)
        
        psycho_map = {"Никогда": 0, "Редко": 5, "Иногда": 10, "Часто": 15, "Постоянно": 20}
        psycho_score = psycho_map[psycho_lonely] + psycho_map[psycho_anger]
    
    st.markdown("---")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown('<div class="card"><h3>👊 Поведение</h3>', unsafe_allow_html=True)
        behavior_truancy = st.radio("Прогулы школы", ["Никогда", "1-2р/мес", "Раз/нед", "2-3р/нед", "Почти ежедневно"], index=2)
        behavior_fight = st.radio("Участие в драках", ["Никогда", "1 раз", "2-3 раза", "Несколько раз", "Регулярно"], index=2)
        st.markdown('</div>', unsafe_allow_html=True)
        
        behavior_map1 = {"Никогда": 0, "1-2р/мес": 5, "Раз/нед": 10, "2-3р/нед": 15, "Почти ежедневно": 20}
        behavior_map2 = {"Никогда": 0, "1 раз": 5, "2-3 раза": 10, "Несколько раз": 15, "Регулярно": 20}
        behavior_score = behavior_map1[behavior_truancy] + behavior_map2[behavior_fight]
    
    with col6:
        st.markdown('<div class="card"><h3>🏠 Семейная ситуация</h3>', unsafe_allow_html=True)
        family_conflict = st.radio("Конфликты с родителями", ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"], index=2)
        family_income = st.radio("Доход семьи", ["Высокий", "Средний", "Ниже среднего", "Низкий", "Очень низкий"], index=2)
        st.markdown('</div>', unsafe_allow_html=True)
        
        family_map1 = {"Никогда": 0, "Редко": 5, "Иногда": 10, "Часто": 15, "Постоянно": 20}
        family_map2 = {"Высокий": 0, "Средний": 5, "Ниже среднего": 10, "Низкий": 15, "Очень низкий": 20}
        family_score = family_map1[family_conflict] + family_map2[family_income]
    
    st.markdown("---")
    
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
            
            recommendations = get_detailed_recommendations(scores, result['risk_level'], result['risk_percent'], age, gender)
            
            # Отображение результата
            st.markdown("---")
            st.markdown("## 📊 Результат оценки")
            
            # Карточка результата
            if result['risk_level'] == 'high':
                st.markdown(f"""
                <div class="result-high">
                    <div class="risk-percent">{result['risk_percent']:.0f}%</div>
                    <div style="font-size: 1.5rem;">🔴 ВЫСОКИЙ РИСК</div>
                    <div style="margin-top: 1rem;">Регион: {region} (риск {result['region_risk_score']*100:.0f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            elif result['risk_level'] == 'medium':
                st.markdown(f"""
                <div class="result-medium">
                    <div class="risk-percent">{result['risk_percent']:.0f}%</div>
                    <div style="font-size: 1.5rem;">🟡 СРЕДНИЙ РИСК</div>
                    <div style="margin-top: 1rem;">Регион: {region} (риск {result['region_risk_score']*100:.0f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-low">
                    <div class="risk-percent">{result['risk_percent']:.0f}%</div>
                    <div style="font-size: 1.5rem;">🟢 НИЗКИЙ РИСК</div>
                    <div style="margin-top: 1rem;">Регион: {region} (риск {result['region_risk_score']*100:.0f}%)</div>
                </div>
                """, unsafe_allow_html=True)
            
            # График баллов по категориям (радарная диаграмма)
            categories = ['Интернет', 'Кибербуллинг', 'Психология', 'Поведение', 'Семья']
            values = [internet_score, cyber_score, psycho_score, behavior_score, family_score]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Ваши баллы',
                line_color='#667eea',
                fillcolor='rgba(102, 126, 234, 0.3)'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[50, 45, 45, 50, 60],
                theta=categories,
                fill='none',
                name='Порог риска',
                line_color='#ffa502',
                line_dash='dash'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title="Профиль риска по категориям",
                height=400,
                margin=dict(l=80, r=80, t=60, b=40)
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # График категорий (столбцы)
            colors = ['#2ed573' if v < 40 else '#ffa502' if v < 70 else '#ff6b6b' for v in values]
            fig_bars = go.Figure(data=[
                go.Bar(x=categories, y=values, marker_color=colors, text=values, textposition='auto')
            ])
            fig_bars.update_layout(
                title="Баллы по категориям (0-100)",
                yaxis=dict(title="Баллы", range=[0, 100]),
                height=350,
                margin=dict(l=0, r=0, t=40, b=20)
            )
            st.plotly_chart(fig_bars, use_container_width=True)
            
            # Рекомендации
            st.markdown("## 💡 Персональные рекомендации")
            
            for rec in recommendations:
                if rec['type'] == 'critical':
                    st.markdown(f"""
                    <div class="rec-critical">
                        <strong>{rec['title']}</strong><br>
                        {rec['text']}<br>
                        <span style="color: #ee5a24;">👉 {rec['action']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif rec['type'] == 'warning':
                    st.markdown(f"""
                    <div class="rec-warning">
                        <strong>{rec['title']}</strong><br>
                        {rec['text']}<br>
                        <span style="color: #ffa502;">👉 {rec['action']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif rec['type'] == 'info':
                    st.markdown(f"""
                    <div class="rec-info">
                        <strong>{rec['title']}</strong><br>
                        {rec['text']}<br>
                        <span style="color: #1e90ff;">👉 {rec['action']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="rec-success">
                        <strong>{rec['title']}</strong><br>
                        {rec['text']}<br>
                        <span style="color: #00b894;">👉 {rec['action']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Телефоны
            st.markdown("---")
            st.markdown("## 📞 Куда обратиться за помощью")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.info("📞 **Детский телефон доверия**\n\n8-800-2000-122\n\nкруглосуточно, анонимно")
            with col_b:
                st.info("🧠 **Психологическая помощь**\n\n8-800-250-00-88\n\nежедневно 9:00-21:00")
            with col_c:
                st.error("🚨 **Экстренная помощь**\n\n112\n\nпри угрозе жизни")

# -*- coding: utf-8 -*-
"""Untitled4.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1p863UnxRBtaTOHW3y-GBzf6MtAYwsilq
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from scipy.interpolate import griddata
import joblib

st.set_page_config(page_title="Прогноз шероховатости Ra", layout="wide")
st.title("📊 Прогноз Ra и обратный поиск режимы по желаемому Ra")
st.markdown("""
**Студент**: Нгуен Нгок Шон - МТ3/МГТУ им. Баумана

**Операция**: Торцевое фрезерование стали 20

**Инструмент**: Торцевая фреза BAP300R-40-22 (D=40 мм, зубьев), пластины APMT1135PDER-M2 OP1215.


""")
@st.cache_data
def load_and_train_model():
    df = pd.read_excel("du_lieu_frezing.xlsx")
    X = df[['V', 'S', 't']]
    y = df['Ra']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    param_grid = {
        'hidden_layer_sizes': [(30, 20)],
        'learning_rate_init': [0.0005],
        'activation': ['tanh']
    }
    grid = GridSearchCV(MLPRegressor(max_iter=5000, early_stopping=True, random_state=42),
                        param_grid, cv=3, scoring='r2', n_jobs=-1, return_train_score=True)
    grid.fit(X_train, y_train)
    model = grid.best_estimator_
    results_df = pd.DataFrame(grid.cv_results_)
    return df, scaler, model, X_test, y_test, X_train, y_train, results_df, param_grid
df, scaler, model, X_test, y_test, X_train, y_train, results_df, param_grid = load_and_train_model()

tab1, tab2, tab3 = st.tabs(["\U0001F4CA Данные и графики", "\U0001F50D Обратный поиск по Ra", "\U0001F4C8 Прогноз Ra"])

with tab1:
    st.subheader("📊 График Ra: прогноз против факта")
    train_pred = model.predict(X_train)
    y_pred = model.predict(X_test)
    fig, ax = plt.subplots(figsize=(8,6))
    ax.scatter(y_train, train_pred, color='red', label='Обучающая выборка')
    ax.scatter(y_test, y_pred, color='blue', label='Тестовая выборка')
    ax.plot([min(df['Ra']), max(df['Ra'])], [min(df['Ra']), max(df['Ra'])], 'k--', label='Идеал')
    ax.set_xlabel('Фактическое Ra (μm)')
    ax.set_ylabel('Прогнозируемое Ra (μm)')
    ax.set_title('Ra: прогноз против факта (Обучение: красный, Тест: синий)')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.markdown("### 📋 Таблица прогнозов")
    X_test_orig = scaler.inverse_transform(X_test)
    df_pred = pd.DataFrame(X_test_orig, columns=['V', 'S', 't'])
    df_pred['Ra факт'] = y_test.values
    df_pred['Ra прогноз'] = y_pred
    df_pred['Ошибка'] = abs(df_pred['Ra факт'] - df_pred['Ra прогноз'])
    st.dataframe(df_pred.round(4))

    st.markdown("### 📉 Обучающая кривая")
    if hasattr(model, 'loss_curve_'):
        fig2, ax2 = plt.subplots()
        ax2.plot(model.loss_curve_)
        ax2.set_title("Кривая обучения")
        ax2.set_xlabel("Эпохи")
        ax2.set_ylabel("Ошибка")
        st.pyplot(fig2)

    st.markdown("### 🌐 График зависимости Ra от (S, V)")
    x, yv, z = df['S'], df['V'], df['Ra']
    xi = np.linspace(x.min(), x.max(), 100)
    yi = np.linspace(yv.min(), yv.max(), 100)
    xi, yi = np.meshgrid(xi, yi)
    zi = griddata((x, yv), z, (xi, yi), method='cubic')
    fig3, ax3 = plt.subplots()
    cp = ax3.contourf(xi, yi, zi, cmap='viridis')
    fig3.colorbar(cp)
    ax3.set_xlabel('S (мм/зуб)')
    ax3.set_ylabel('V (м/мин)')
    ax3.set_title('Ra по (S, V)')
    st.pyplot(fig3)

    st.markdown("### 🌐 График зависимости Ra от (S, t)")
    x, yt, z = df['S'], df['t'], df['Ra']
    xi = np.linspace(x.min(), x.max(), 100)
    yi = np.linspace(yt.min(), yt.max(), 100)
    xi, yi = np.meshgrid(xi, yi)
    zi = griddata((x, yt), z, (xi, yi), method='cubic')
    fig4, ax4 = plt.subplots()
    cp = ax4.contourf(xi, yi, zi, cmap='plasma')
    fig4.colorbar(cp)
    ax4.set_xlabel('S (мм/зуб)')
    ax4.set_ylabel('t (мм)')
    ax4.set_title('Ra по (S, t)')
    st.pyplot(fig4)

    st.markdown("### 🧠 Информация о модели MLP")
    st.write(f"**Архитектура скрытых слоёв**: {model.hidden_layer_sizes}")
    st.write(f"**Функция активации**: {model.activation}")
    st.write(f"**Инициализация скорости обучения**: {model.learning_rate_init}")
    st.write(f"**Общее количество итераций обучения**: {model.n_iter_}")

with tab2:
    st.subheader("\U0001F50D Обратный поиск по Ra")
    target_ra = st.number_input("Желаемое значение Ra (μm):", 0.1, 10.0, 1.2, 0.1)
    num_results = st.slider("Количество комбинаций для вывода:", 1, 10, 4)

    if st.button("\U0001F50E Найти параметры"):
        V_range = np.linspace(df['V'].min(), df['V'].max(), 30)
        S_range = np.linspace(df['S'].min(), df['S'].max(), 30)
        t_range = np.linspace(df['t'].min(), df['t'].max(), 30)
        results = []
        for v in V_range:
            for s in S_range:
                for t in t_range:
                    input_df = pd.DataFrame([[v, s, t]], columns=['V', 'S', 't'])
                    input_scaled = scaler.transform(input_df)
                    ra = model.predict(input_scaled)[0]
                    err = abs(ra - target_ra)
                    results.append((err, v, s, t, ra))
        results.sort()
        out_df = pd.DataFrame(results[:num_results], columns=['Ошибка', 'V (м/мин)', 'S (мм/зуб)', 't (мм)', 'Ra прогноз'])
        st.dataframe(out_df)

with tab3:
    st.subheader("\U0001F4C8 Прогноз Ra")
    v = st.number_input("Скорость резания V (м/мин):",60.0, 120.0, 60.0, 5.0)
    s = st.number_input("Подача на зуб S (мм/зуб):", 0.05, 0.25, 0.05, 0.01)
    t = st.number_input("Глубина резания t (мм):", 0.3, 1.5, 0.3, 0.1)

    if st.button("\U0001F4C9 Прогнозировать Ra"):
        input_df = pd.DataFrame([[v, s, t]], columns=['V', 'S', 't'])
        input_scaled = scaler.transform(input_df)
        ra_pred = model.predict(input_scaled)[0]
        st.success(f"Прогнозируемое Ra: {ra_pred:.4f} μm при V={v} м/мин, S={s} мм/зуб, t={t} мм")

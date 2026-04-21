import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de consumo de materiais", layout="wide")

# --- GERAÇÃO DE DADOS MOCK ---
@st.cache_data
def gerar_dados_pesagem():
    precos = {"COR-450": 120.50, "QUIM-088": 1.50, "QUIM-015": 4.20}
    receita = [
        {"item": "COR-450 (Azul Reativo)", "perc": 3.2, "cod": "COR-450"},
        {"item": "QUIM-088 (Sal de Cozinha)", "perc": 6.0, "cod": "QUIM-088"},
        {"item": "QUIM-015 (Barrilha Leve)", "perc": 2.0, "cod": "QUIM-015"}
    ]
    
    turnos_ops = {
        "Turno A": ["Carlos Silva", "Maria Santos"],
        "Turno B": ["Joao Pereira", "Ana Costa"],
        "Turno C": ["Ricardo Melo", "Beatriz Lima"]
    }
    
    dados = []
    hoje = datetime.now().date()
    data_inicio_base = hoje - timedelta(days=40)
    
    # Gerando 30 Ordens de Produção (10 iniciais + 20 novas)
    for i in range(1, 31):
        op = f"OP-2026-{i:03d}"
        peso_tecido = float(np.random.choice([100, 150, 200, 250]))
        
        # Sorteio de Data, Turno e Operador
        dias_adicionais = np.random.randint(0, 41)
        data_apontamento = data_inicio_base + timedelta(days=dias_adicionais)
        
        turno = np.random.choice(list(turnos_ops.keys()))
        operador = np.random.choice(turnos_ops[turno])
        
        for comp in receita:
            padrao = peso_tecido * (comp["perc"] / 100)
            fator_erro = np.random.uniform(-0.05, 0.05)
            realizado = padrao * (1 + fator_erro)
            
            desvio_kg = realizado - padrao
            desvio_perc = (desvio_kg / padrao) * 100
            custo_perda = desvio_kg * precos[comp["cod"]] if desvio_kg > 0 else 0.0
            
            if abs(desvio_perc) <= 1.0:
                status = "OK"
            elif desvio_perc > 1.0:
                status = "Excesso"
            else:
                status = "Falta"

            dados.append({
                "Ordem de Produção": op,
                "Data": data_apontamento,
                "Turno": turno,
                "Operador": operador,
                "Peso Tecido (kg)": peso_tecido,
                "Componente": comp["item"],
                "Padrão (kg)": round(padrao, 3),
                "Realizado (kg)": round(realizado, 3),
                "Desvio (kg)": round(desvio_kg, 3),
                "Desvio (%)": round(desvio_perc, 2),
                "Status": status,
                "Custo Desperdício (R$)": round(custo_perda, 2)
            })
            
    return pd.DataFrame(dados)

df_pesagens_bruto = gerar_dados_pesagem()

# --- MENU LATERAL ESQUERDO ---
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; margin-bottom: 20px;'>
        <h1 style='color: rgba(32, 32, 32, 1); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-weight: bold; font-size: 72px; letter-spacing: -2px; margin: 0;'>TOTVS</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Globais")

# 1. Filtro de Data
min_data = df_pesagens_bruto["Data"].min()
max_data = df_pesagens_bruto["Data"].max()
datas_selecionadas = st.sidebar.date_input("Período de Apontamento", value=(min_data, max_data), min_value=min_data, max_value=max_data)

# 2. Filtro de Turno
turnos_disponiveis = sorted(df_pesagens_bruto["Turno"].unique())
turnos_selecionados = st.sidebar.multiselect("Turno", options=turnos_disponiveis, default=turnos_disponiveis)

# 3. Filtro de Operador
operadores_disponiveis = sorted(df_pesagens_bruto["Operador"].unique())
operadores_selecionados = st.sidebar.multiselect("Operador", options=operadores_disponiveis, default=operadores_disponiveis)

# Aplicação dos Filtros
df_pesagens = df_pesagens_bruto[
    (df_pesagens_bruto["Turno"].isin(turnos_selecionados)) &
    (df_pesagens_bruto["Operador"].isin(operadores_selecionados))
]

if len(datas_selecionadas) == 2:
    data_inicio, data_fim = datas_selecionadas
    df_pesagens = df_pesagens[(df_pesagens["Data"] >= data_inicio) & (df_pesagens["Data"] <= data_fim)]

st.sidebar.markdown("---")
menu_selection = st.sidebar.radio("Módulos de Gestão", options=["Histórico de Pesagens", "Gestão de Performance e Perdas"], index=0)

# --- INTERFACE PRINCIPAL ---
st.title("Gestão de consumo de materiais")
st.markdown("---")

def colorir_linhas(row):
    if row["Status"] == "Excesso": return ['background-color: #ffcccc'] * len(row)
    elif row["Status"] == "Falta": return ['background-color: #ffe6cc'] * len(row)
    return [''] * len(row)

if df_pesagens.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    if menu_selection == "Histórico de Pesagens":
        st.header("Histórico de Apontamentos por Ordem de Produção")
        receita_selecionada = st.selectbox("Selecione a Receita:", options=["Ficha #1024 - Azul Marinho"])
        
        op_filtro = st.multiselect("Filtrar por OP específica:", options=sorted(df_pesagens["Ordem de Produção"].unique()))
        df_exibicao = df_pesagens if not op_filtro else df_pesagens[df_pesagens["Ordem de Produção"].isin(op_filtro)]
        
        st.dataframe(
            df_exibicao.style.apply(colorir_linhas, axis=1).format({
                "Padrão (kg)": "{:.3f}", "Realizado (kg)": "{:.3f}", "Desvio (kg)": "{:.3f}",
                "Desvio (%)": "{:.2f}%", "Custo Desperdício (R$)": "R$ {:.2f}",
                "Data": lambda t: t.strftime("%d/%m/%Y")
            }),
            use_container_width=True, height=600
        )

    elif menu_selection == "Gestão de Performance e Perdas":
        st.header("Dashboard de Performance e Perdas Financeiras")
        
        total_ops = df_pesagens["Ordem de Produção"].nunique()
        custo_total_perdas = df_pesagens["Custo Desperdício (R$)"].sum()
        desvio_maximo = df_pesagens["Desvio (%)"].max()
        acertos = df_pesagens[df_pesagens["Status"] == "OK"].shape[0]
        total_pesagens = df_pesagens.shape[0]
        taxa_assertividade = (acertos / total_pesagens) * 100 if total_pesagens > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de OPs Analisadas", total_ops)
        c2.metric("Assertividade (Tolerância 1%)", f"{taxa_assertividade:.1f}%")
        c3.metric("Custo Total de Desperdício", f"R$ {custo_total_perdas:.2f}")
        c4.metric("Maior Desvio", f"+{desvio_maximo:.1f}%")

        st.markdown("---")
        col_grafico, col_tabela = st.columns([3, 2])

        with col_grafico:
            st.subheader("Desvio em Kg por OP")
            df_grafico = df_pesagens.pivot_table(index="Ordem de Produção", columns="Componente", values="Desvio (kg)", aggfunc='sum')
            st.bar_chart(df_grafico)

        with col_tabela:
            st.subheader("Perdas por Componente")
            df_resumo = df_pesagens.groupby("Componente").agg(
                Total_Padrao=("Padrão (kg)", "sum"),
                Total_Realizado=("Realizado (kg)", "sum"),
                Custo_Perda=("Custo Desperdício (R$)", "sum")
            ).reset_index()
            
            st.dataframe(
                df_resumo.rename(columns={"Total_Padrao": "Padrão (kg)", "Total_Realizado": "Realizado (kg)", "Custo_Perda": "Perda (R$)"})
                .style.format({"Padrão (kg)": "{:.2f}", "Realizado (kg)": "{:.2f}", "Perda (R$)": "R$ {:.2f}"}),
                use_container_width=True
            )
            
        st.subheader("Tendência de Assertividade por OP (% de Desvio)")
        df_tendencia = df_pesagens.pivot_table(index="Ordem de Produção", columns="Componente", values="Desvio (%)", aggfunc='mean')
        st.line_chart(df_tendencia)

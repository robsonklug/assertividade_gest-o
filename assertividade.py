import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ERP Têxtil - Gestão de Pesagens", layout="wide")

# --- GERAÇÃO DE DADOS MOCK (10 OPs com a mesma receita e divergências) ---
@st.cache_data
def gerar_dados_pesagem():
    # Preços para cálculo de perda
    precos = {"COR-450": 120.50, "QUIM-088": 1.50, "QUIM-015": 4.20}
    
    # Receita Padrão (% sobre o peso do tecido)
    receita = [
        {"item": "COR-450 (Azul Reativo)", "perc": 3.2, "cod": "COR-450"},
        {"item": "QUIM-088 (Sal de Cozinha)", "perc": 6.0, "cod": "QUIM-088"},
        {"item": "QUIM-015 (Barrilha Leve)", "perc": 2.0, "cod": "QUIM-015"}
    ]
    
    dados = []
    # Gerando 10 Ordens de Produção
    for i in range(1, 11):
        op = f"OP-2026-{i:03d}"
        peso_tecido = np.random.choice([100.0, 150.0, 200.0, 250.0])
        
        for comp in receita:
            padrao = peso_tecido * (comp["perc"] / 100)
            
            # Simulando erro humano na pesagem: divergência entre -5% e +5%
            fator_erro = np.random.uniform(-0.05, 0.05)
            realizado = padrao * (1 + fator_erro)
            
            desvio_kg = realizado - padrao
            desvio_perc = (desvio_kg / padrao) * 100
            
            # Custo gerado (apenas se pesou a mais. Se pesou a menos, o custo é de qualidade/reprocesso)
            custo_perda = desvio_kg * precos[comp["cod"]] if desvio_kg > 0 else 0.0
            
            # Definindo status com base em tolerância de 1%
            if abs(desvio_perc) <= 1.0:
                status = "✅ OK"
            elif desvio_perc > 1.0:
                status = "⚠️ Excesso"
            else:
                status = "❌ Falta"

            dados.append({
                "Ordem de Produção": op,
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

# Carrega os dados
df_pesagens = gerar_dados_pesagem()

# --- INTERFACE PRINCIPAL ---
st.title("🏭 ERP Têxtil - Gestão de Cozinha de Cores")
st.markdown("---")

# Criando as abas solicitadas
aba1, aba2 = st.tabs(["📋 Histórico de Pesagens (Auditoria)", "📈 Gestão de Performance e Perdas"])

# --- ABA 1: LISTAGEM DE OPERAÇÕES DE PESAGEM ---
with aba1:
    st.header("Histórico de Apontamentos por Ordem de Produção")
    st.markdown("Lista das últimas 10 OPs executadas para a receita **Ficha #1024 - Azul Marinho**. Compare o padrão teórico com o peso real aferido na balança.")
    
    # Filtro opcional por OP
    op_filtro = st.multiselect("Filtrar por Ordem de Produção:", options=df_pesagens["Ordem de Produção"].unique())
    df_exibicao = df_pesagens if not op_filtro else df_pesagens[df_pesagens["Ordem de Produção"].isin(op_filtro)]
    
    # Função para colorir a tabela
    def colorir_linhas(row):
        if "Excesso" in row["Status"]:
            return ['background-color: #ffcccc'] * len(row)
        elif "Falta" in row["Status"]:
            return ['background-color: #ffe6cc'] * len(row)
        return [''] * len(row)

    # Exibindo o DataFrame estilizado
    st.dataframe(
        df_exibicao.style.apply(colorir_linhas, axis=1).format({
            "Padrão (kg)": "{:.3f}", 
            "Realizado (kg)": "{:.3f}",
            "Desvio (kg)": "{:.3f}",
            "Desvio (%)": "{:.2f}%",
            "Custo Desperdício (R$)": "R$ {:.2f}"
        }),
        use_container_width=True,
        height=500
    )

# --- ABA 2: GESTÃO DE PERFORMANCE E PERDAS ---
with aba2:
    st.header("Dashboard de Performance e Perdas Financeiras")
    
    # Métricas Globais
    total_ops = df_pesagens["Ordem de Produção"].nunique()
    custo_total_perdas = df_pesagens["Custo Desperdício (R$)"].sum()
    desvio_maximo = df_pesagens["Desvio (%)"].max()
    acertos = df_pesagens[df_pesagens["Status"] == "✅ OK"].shape[0]
    total_pesagens = df_pesagens.shape[0]
    taxa_assertividade = (acertos / total_pesagens) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de OPs Analisadas", total_ops)
    col2.metric("Taxa de Assertividade (Tolerância 1%)", f"{taxa_assertividade:.1f}%")
    col3.metric("Custo Total de Desperdício", f"R$ {custo_total_perdas:.2f}")
    col4.metric("Maior Desvio Encontrado", f"+{desvio_maximo:.1f}%")

    st.markdown("---")

    col_grafico, col_tabela = st.columns([3, 2])

    with col_grafico:
        st.subheader("Desvio em Kg por OP e Componente")
        # Preparando dados para o gráfico de barras
        df_grafico = df_pesagens.pivot(index="Ordem de Produção", columns="Componente", values="Desvio (kg)")
        st.bar_chart(df_grafico)

    with col_tabela:
        st.subheader("Resumo de Perdas por Componente")
        st.markdown("Visão financeira dos excessos de dosagem.")
        
        # Agrupando dados para resumo
        df_resumo = df_pesagens.groupby("Componente").agg(
            Total_Padrão_kg=("Padrão (kg)", "sum"),
            Total_Realizado_kg=("Realizado (kg)", "sum"),
            Custo_Perda_R$=("Custo Desperdício (R$)", "sum")
        ).reset_index()
        
        st.dataframe(
            df_resumo.style.format({
                "Total_Padrão_kg": "{:.2f}",
                "Total_Realizado_kg": "{:.2f}",
                "Custo_Perda_R$": "R$ {:.2f}"
            }),
            use_container_width=True
        )
        
    st.subheader("Tendência de Assertividade (% de Desvio)")
    df_tendencia = df_pesagens.pivot(index="Ordem de Produção", columns="Componente", values="Desvio (%)")
    st.line_chart(df_tendencia)

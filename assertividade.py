import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
# Renomeação do título da página
st.set_page_config(page_title="Gestão de consumo de materiais", layout="wide")

# --- GERAÇÃO DE DADOS MOCK (10 OPs com a mesma receita e divergências) ---
# Função ajustada para remover os ícones dos status
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
            
            # Definindo status limpos (sem ícones) com base em tolerância de 1%
            if abs(desvio_perc) <= 1.0:
                status = "OK"
            elif desvio_perc > 1.0:
                status = "Excesso"
            else:
                status = "Falta"

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

# --- MENU LATERAL ESQUERDO ---
# Adição do texto "TOTVS" no mesmo formato e tipo de letra do modelo
# Usamos HTML para garantir a formatação: negrito, cor escura e fonte sans-serif
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; margin-bottom: 20px;'>
        <h1 style='color: rgba(32, 32, 32, 1); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; font-weight: bold; margin: 0;'>TOTVS</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Criação do menu lateral com as opções das antigas abas (sem ícones)
menu_selection = st.sidebar.radio(
    "Módulos de Gestão",
    options=["Histórico de Pesagens (Auditoria)", "Gestão de Performance e Perdas"],
    index=0
)

# --- INTERFACE PRINCIPAL ---
# Título renomeado e sem ícone
st.title("Gestão de consumo de materiais")
st.markdown("---")

# Função de coloração da tabela ajustada para os novos status limpos
def colorir_linhas(row):
    if row["Status"] == "Excesso":
        return ['background-color: #ffcccc'] * len(row)
    elif row["Status"] == "Falta":
        return ['background-color: #ffe6cc'] * len(row)
    return [''] * len(row)

# Lógica de exibição baseada na seleção do menu lateral
if menu_selection == "Histórico de Pesagens (Auditoria)":
    # --- VISÃO 1: HISTÓRICO DE PESAGENS ---
    # Título sem ícone
    st.header("Histórico de Apontamentos por Ordem de Produção")
    st.markdown("Lista das últimas 10 OPs executadas para a receita **Ficha #1024 - Azul Marinho**. Compare o padrão teórico com o peso real aferido na balança.")
    
    # Filtro opcional por OP
    op_filtro = st.multiselect("Filtrar por Ordem de Produção:", options=df_pesagens["Ordem de Produção"].unique())
    df_exibicao = df_pesagens if not op_filtro else df_pesagens[df_pesagens["Ordem de Produção"].isin(op_filtro)]
    
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

elif menu_selection == "Gestão de Performance e Perdas":
    # --- VISÃO 2: GESTÃO DE PERFORMANCE E PERDAS ---
    # Título sem ícone
    st.header("Dashboard de Performance e Perdas Financeiras")
    
    # Métricas Globais (ícones já estavam ausentes)
    total_ops = df_pesagens["Ordem de Produção"].nunique()
    custo_total_perdas = df_pesagens["Custo Desperdício (R$)"].sum()
    desvio_maximo = df_pesagens["Desvio (%)"].max()
    acertos = df_pesagens[df_pesagens["Status"] == "OK"].shape[0]
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
        
        # Agrupando dados para resumo com nomes de variáveis válidos no Python
        df_resumo = df_pesagens.groupby("Componente").agg(
            Total_Padrao_kg=("Padrão (kg)", "sum"),
            Total_Realizado_kg=("Realizado (kg)", "sum"),
            Custo_Perda_Reais=("Custo Desperdício (R$)", "sum")
        ).reset_index()
        
        # Renomeando as colunas para exibição na tela
        df_resumo = df_resumo.rename(columns={
            "Total_Padrao_kg": "Total Padrão (kg)",
            "Total_Realizado_kg": "Total Realizado (kg)",
            "Custo_Perda_Reais": "Custo Perda (R$)"
        })
        
        st.dataframe(
            df_resumo.style.format({
                "Total Padrão (kg)": "{:.2f}",
                "Total Realizado (kg)": "{:.2f}",
                "Custo Perda (R$)": "R$ {:.2f}"
            }),
            use_container_width=True
        )
        
    st.subheader("Tendência de Assertividade (% de Desvio)")
    df_tendencia = df_pesagens.pivot(index="Ordem de Produção", columns="Componente", values="Desvio (%)")
    st.line_chart(df_tendencia)

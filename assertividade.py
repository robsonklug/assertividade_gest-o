import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ERP Têxtil - Módulo de Assertividade", layout="wide")

# --- PILAR 4: BASE DE DATOS FIXA (MOCK DATA) ---
if 'db_insumos' not in st.session_state:
    st.session_state.db_insumos = pd.DataFrame({
        'Codigo': ['COR-450', 'COR-120', 'QUIM-001', 'QUIM-088', 'QUIM-015'],
        'Descricao': ['Azul Reativo RGB', 'Preto Reativo B', 'Umectante T-2', 'Sal de Cozinha', 'Barrilha Leve'],
        'Estoque_kg': [50.0, 30.0, 100.0, 500.0, 250.0],
        'Preco_kg': [120.50, 95.00, 12.30, 1.50, 4.20]
    })

if 'receitas' not in st.session_state:
    # Receita Padrão de Exemplo
    st.session_state.receitas = {
        "Ficha #1024 - Azul Marinho": [
            {"item": "COR-450", "tipo": "%", "valor": 3.2},
            {"item": "QUIM-088", "tipo": "g/L", "valor": 60.0},
            {"item": "QUIM-015", "tipo": "g/L", "valor": 20.0}
        ]
    }

# --- INTERFACE PRINCIPAL ---
st.title("🚀 Sistema de Gestão de Banhos e Receituários")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🏗️ Engenharia de Receitas", "⚖️ Operação de Pesagem", "📊 Dashboard de Assertividade"])

# --- PILAR 1: ENGENHARIA E ASSERTIVIDADE NOS PREPAROS ---
with tab1:
    st.header("Cadastro Técnico de Receitas")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        nome_receita = st.text_input("Nome da Nova Receita", "Ficha #1025 - Verde Militar")
        relacao_banho = st.number_input("Relação de Banho (1:X)", value=10)
        if st.button("Salvar Estrutura"):
            st.success("Estrutura da receita salva com sucesso!")

    with col2:
        st.subheader("Itens da Receita")
        st.table(st.session_state.db_insumos[['Codigo', 'Descricao']])

# --- PILAR 2: INTERFACE DE OPERAÇÃO (PESAGEM ASSISTIDA) ---
with tab2:
    st.header("Execução de Banho (Chão de Fábrica)")
    
    # Simulação de Ordem de Produção
    op_selecionada = st.selectbox("Selecione a OP (Ordem de Produção)", ["OP-2024-001 (Algodão 200kg)", "OP-2024-002 (Poliéster 150kg)"])
    peso_tecido = 200.0 if "200kg" in op_selecionada else 150.0
    
    st.info(f"Peso do Lote: **{peso_tecido} kg** | Receita Vinculada: **#1024 - Azul Marinho**")
    
    # Cálculo em tempo real
    st.subheader("Itens para Preparação")
    
    dados_preparo = []
    for i in st.session_state.receitas["Ficha #1024 - Azul Marinho"]:
        # Cálculo: Se %, multiplica pelo peso. Se g/L, multiplica pelo volume de água (peso * relacao_banho)
        qtd_teorica = (peso_tecido * (i['valor']/100)) if i['tipo'] == "%" else (peso_tecido * 10 * i['valor'] / 1000)
        dados_preparo.append({
            "Insumo": i['item'],
            "Qtd Teórica (kg)": round(qtd_teorica, 3),
            "Status": "Aguardando"
        })
    
    df_preparo = pd.DataFrame(dados_preparo)
    
    # Simulando a balança
    item_atual = st.selectbox("Selecione o item para pesagem atual", df_preparo["Insumo"])
    qtd_alvo = df_preparo[df_preparo["Insumo"] == item_atual]["Qtd Teórica (kg)"].values[0]
    
    col_bal1, col_bal2 = st.columns(2)
    with col_bal1:
        st.metric(label="Peso Alvo (Teórico)", value=f"{qtd_alvo} kg")
        peso_real = st.number_input("LEITURA DA BALANÇA (kg)", value=0.0, step=0.001)
    
    with col_bal2:
        # Lógica de Assertividade (Trava de Segurança)
        margem = 0.01 # 1%
        erro = abs(peso_real - qtd_alvo)
        assertividade = (1 - (erro/qtd_alvo)) * 100 if peso_real > 0 else 0
        
        if peso_real == 0:
            st.warning("Aguardando estabilização da balança...")
        elif qtd_alvo * (1-margem) <= peso_real <= qtd_alvo * (1+margem):
            st.success(f"DENTRO DA TOLERÂNCIA! Assertividade: {assertividade:.2f}%")
            if st.button("Confirmar Pesagem e Baixar Estoque"):
                st.balloons()
        else:
            st.error(f"FORA DA TOLERÂNCIA! Erro de {erro:.3f}kg. Corrija o peso.")

# --- PILAR 3: DASHBOARD DE BENEFÍCIOS ESPERADOS ---
with tab3:
    st.header("Gestão de Performance e Perdas")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Redução de Reprocessos", "12%", "-2% este mês")
    c2.metric("Assertividade Média", "99.4%", "+5.2% vs Manual")
    c3.metric("Economia de Corantes", "R$ 4.500,00", "Baseado em precisão")

    # Gráfico de exemplo de erros humanos evitados
    st.subheader("Histórico de Assertividade por Turno")
    chart_data = pd.DataFrame(
        np.random.uniform(95, 100, size=(20, 3)),
        columns=['Turno A', 'Turno B', 'Turno C']
    )
    st.line_chart(chart_data)

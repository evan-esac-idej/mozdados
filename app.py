import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 1. Configuração da Página
st.set_page_config(
    page_title='Mozdados - Dashboard',
    page_icon='🇲🇿',
    layout='wide'
)


# 2. Função de Carregamento de Dados com Cache
# O @st.cache_data faz com que o Excel seja lido apenas uma vez, melhorando a performance.
@st.cache_data
def carregar_dados():
    try:
        # Tenta carregar o arquivo original
        df = pd.read_excel('dados/database.xlsx')

        # Tratamento da coluna de data
        # Verifica se existe coluna 'Mês', senão tenta usar o índice ou cria dados fictícios para teste
        if 'Mês' in df.columns:
            df.set_index('Mês', inplace=True)

        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
    except FileNotFoundError:
        st.error("Arquivo 'dados/database.xlsx' não encontrado. Por favor, verifique o caminho.")
        return pd.DataFrame()  # Retorna vazio para não quebrar o app
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


# Carrega os dados
df_raw = carregar_dados()

# Verifica se o dataframe não está vazio antes de continuar
if not df_raw.empty:

    # 3. Sidebar (Barra Lateral) para Filtros Globais
    st.sidebar.subheader('Moçambique')
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Flag_of_Mozambique.svg/320px-Flag_of_Mozambique.svg.png",
        width=100)
    st.sidebar.header("Filtros")

    # Filtro de Data
    min_date = df_raw.index.min().date()
    max_date = df_raw.index.max().date()

    data_inicio = st.sidebar.date_input("Data Início", min_date, min_value=min_date, max_value=max_date)
    data_fim = st.sidebar.date_input("Data Fim", max_date, min_value=min_date, max_value=max_date)

    # Filtrar o DataFrame principal
    if data_inicio <= data_fim:
        df = df_raw.loc[data_inicio:data_fim]
    else:
        st.sidebar.error("A Data de Início deve ser menor que a Data Fim.")
        df = df_raw

    # 4. Interface Principal
    a, e, i = st.columns(3)
    with e:
        st.success('# **🇲🇿DADOS**')


    # Criação das Abas
    tab1, tab2, tab3, tab4 = st.tabs(['🏥 Saúde', '🎓 Educação', '💰 Finanças', '🏦 Banca'])


    # Função auxiliar para criar o conteúdo de cada aba (evita repetição de código)
    def criar_dashboard_aba(tab_context, df_filtrado, categoria_nome):
        with tab_context:
            st.subheader(f"Análise de {categoria_nome}")

            # Seletor de Variáveis Específico para a Aba
            cols = df_filtrado.columns.tolist()
            # Dica: Aqui você poderia filtrar colunas específicas por categoria se souber os nomes
            vars = st.multiselect(
                f'Selecione indicadores de {categoria_nome}:',
                options=cols,
                default=cols[0] if cols else None,
                key=f"multi_{categoria_nome}"  # Chave única para evitar conflito
            )

            if vars:
                # --- Área de Métricas (KPIs) ---
                st.markdown("#### Indicadores Recentes")
                cols_kpi = st.columns(len(vars))

                for i, var in enumerate(vars):
                    if i < 4:  # Limita a 4 cartões para não quebrar o layout visualmente
                        valor_atual = df_filtrado[var].iloc[-1]
                        valor_anterior = df_filtrado[var].iloc[-2] if len(df_filtrado) > 1 else valor_atual
                        delta = ((valor_atual - valor_anterior) / valor_anterior) * 100 if valor_anterior != 0 else 0
                        with cols_kpi[i]:
                            st.metric(
                                label=var,
                                value=f"{valor_atual:,.2f}",
                                delta=f"{delta:.1f}% (Mês ant.)"
                            )

                st.markdown("---")

                # --- Gráfico ---
                fig = px.line(
                    df_filtrado,
                    x=df_filtrado.index,
                    y=vars,
                    markers=True,
                    template="plotly_white"
                )

                fig.update_layout(
                    title=f"Evolução Temporal: {', '.join(vars)}",
                    xaxis_title='Período',
                    yaxis_title='Valor',
                    legend_title='Indicadores',
                    hovermode="x unified",  # Mostra todos os valores ao passar o mouse
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True, key=f"grafico_{categoria_nome}")

                fig_area = px.area(df_filtrado, x=df_filtrado.index, y=vars,
                                   template="plotly_white", title=f"Volume Acumulado (Área) {', '.join(vars)}",)
                fig_area.update_layout(
                    xaxis_title='Período',
                    yaxis_title='Valor',
                    legend_title='Indicadores',
                    hovermode="x unified",  # Mostra todos os valores ao passar o mouse
                    height=500
                )
                st.plotly_chart(fig_area, use_container_width=True, key=f"graph_area_{categoria_nome}")

                fig_hist = px.histogram(df_filtrado, x=vars, nbins=15,
                                        title="Distribuição/Frequência dos Valores", marginal="rug")
                fig_hist.update_layout(
                    xaxis_title='Valor',
                    yaxis_title='Frequência',
                    legend_title='Indicadores',
                    hovermode="x unified",  # Mostra todos os valores ao passar o mouse
                    height=500
                )
                st.plotly_chart(fig_hist, use_container_width=True, key=f"graph_hist_{categoria_nome}")

                # --- Área de Dados e Download ---
                st.subheader("Dados Detalhados")
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.dataframe(df_filtrado[vars].sort_index(ascending=False), height=200,
                                 use_container_width=True)

                with col2:
                    st.write("📥 **Exportar Dados**")

                    # Converter para CSV
                    csv = df_filtrado[vars].to_csv().encode('utf-8')
                    st.download_button(
                        label="Baixar CSV",
                        data=csv,
                        file_name=f'mozdados_{categoria_nome}.csv',
                        mime='text/csv',
                        key=f"dl_csv_{categoria_nome}"
                    )

                    # Converter para Excel
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_filtrado[vars].to_excel(writer, sheet_name='Dados')

                    st.download_button(
                        label="Baixar Excel",
                        data=buffer,
                        file_name=f'mozdados_{categoria_nome}.xlsx',
                        mime='application/vnd.ms-excel',
                        key=f"dl_excel_{categoria_nome}"
                    )
            else:
                st.info("Por favor, selecione pelo menos uma variável acima para visualizar.")


    # Renderiza as abas (Como não sei quais colunas são de qual categoria,
    # deixei genérico, mas você pode passar listas de colunas específicas)
    criar_dashboard_aba(tab1, df, "Saúde")
    criar_dashboard_aba(tab2, df, "Educação")
    criar_dashboard_aba(tab3, df, "Finanças")
    criar_dashboard_aba(tab4, df, "Banca")

else:
    st.warning("Aguardando carregamento da base de dados.")
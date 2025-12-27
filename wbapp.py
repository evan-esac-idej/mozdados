import streamlit as st
import pandas as pd
import plotly.express as px
import wbgapi as wb

# ------------------ Page config ------------------
st.set_page_config(
    page_title="Mozdados - Dashboard",
    page_icon="🇲🇿",
    layout="wide"
)
a, e, i = st.columns(3)
with e:
    st.info("## **🇲o🇿dados🌍**")
st.caption("ℹ Os dados utilizados neste projecto são fornecidos pelo **Banco Mundial** através da *world bank api*")
tab1, tab2, tab3 = st.tabs(['🏦 Indicador', '🤖 Análise IA', 'ℹ️ Sobre o Projecto'])
try:

    # ------------------ Cache functions ------------------
    @st.cache_data
    def get_topics():
        return list(wb.topic.list())

    @st.cache_data
    def get_indicators(topic_id):
        return list(wb.series.list())

    @st.cache_data
    def get_countries():
        return list(wb.economy.list())

    # ------------------ Sidebar ------------------
    st.sidebar.subheader('Moçambique')
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Flag_of_Mozambique.svg/320px-Flag_of_Mozambique.svg.png",
        width=100)
    st.sidebar.header("Filtros")
    with st.sidebar.expander('Como encontrar as variáveis'):
        st.write("""Por exemplo: Como encontro e inflação? 
        Comece escrevendo com letra maiúscula em inglês na barra de seleção de indicadores: **Inflation** ... e selecione o seu indicador.
        Noutros casos como **PIB** deve ser GDP...
        Caso ainda enfrente dificuldade pergunte ao **Chat**""")
    topic = get_topics()
    country = get_countries()
    ind = get_indicators(5)

    dic = {}
    for big in country:
        dic[big['value']] = big['id']
    sel_country = st.sidebar.multiselect('Selecione o(s) País(es):',
                                         options=sorted(dic.keys()), default='Mozambique')

    if not sel_country:
        st.stop()
    c_lis = []
    for c in sel_country:
        c_lis.append(dic[c])

    dice = {}
    for big in ind:
        dice[big['value']] = big['id']
    sel_ind = st.sidebar.multiselect('Selecione o(s) Indicador(es):',
                                     options=sorted(dice.keys()), default="Agricultural land (sq. km)")
    if not sel_ind:
        st.stop()
    i_lis = []
    for c in sel_ind:
        i_lis.append(dice[c])

    years = list(range(1960, 2024))
    start_year, end_year = st.sidebar.select_slider(
        "Selecione o intervalo de anos",
        options=years,
        value=(2000, 2020)
    )

    df = wb.data.DataFrame(
        series=i_lis,
        economy=c_lis,
        time=range(start_year, end_year + 1)
    )
    lista = []
    df.columns = df.columns.str.replace("YR", "").astype(int)
    df.reset_index(inplace=True)

    if 'series' in df.columns:
        df['series'] = df['series'].replace(i_lis, sel_ind)
        df = df.rename(columns={'series': 'Indicador'})
    else:
        df['Indicador'] = sel_ind * len(df)

    if 'economy' in df.columns:
        df['economy'] = df['economy'].replace(c_lis, sel_country)
        df = df.rename(columns={'economy': 'País'})
    else:
        df['País'] = sel_country*len(df)


    # 1. Transformar colunas de anos em uma única coluna 'Ano' (Melt)
    df_long = df.melt(
        id_vars=['País', 'Indicador'],
        var_name='Ano',
        value_name='Valor'
    )

    # 2. Garantir que o Ano seja numérico para o eixo X
    df_long['Ano'] = pd.to_numeric(df_long['Ano'])
    with tab1:
        # Supondo que 'sel_ind' são os indicadores selecionados e 'sel_pais' o país escolhido
        # Se você tiver mais de um país selecionado, o KPI mostrará apenas o primeiro
        for k, countr in enumerate(sel_country):
            st.markdown(f"##### Indicadores Recentes de {countr} - {end_year} vs {end_year - 1}")
            pais_kpi = sel_country[k] if sel_country else sel_country[k]
            cols_kpi = st.columns(len(sel_ind))

            for i, var in enumerate(sel_ind):
                if i < 4:  # Limita a 4 cartões
                    # Filtra os dados para o indicador e país específicos
                    dados_kpi = df_long.query("País == @pais_kpi and Indicador == @var").sort_values("Ano")

                    if len(dados_kpi) >= 2:
                        valor_atual = dados_kpi.iloc[-1]['Valor']  # Ano 2020
                        valor_anterior = dados_kpi.iloc[-2]['Valor']  # Ano 2019

                        delta = ((valor_atual - valor_anterior) / valor_anterior) * 100 if valor_anterior != 0 else 0

                        with cols_kpi[i]:
                            st.metric(
                                label=f"{var[:30]}...",  # Abrevia o nome se for muito longo
                                value=f"{valor_atual:,.2f}",
                                delta=f"{delta:.1f}% vs ano ant."
                            )
                    elif len(dados_kpi) == 1:
                        # Se só houver um ano de dados
                        valor_atual = dados_kpi.iloc[-1]['Valor']
                        with cols_kpi[i]:
                            st.metric(label=var, value=f"{valor_atual:,.2f}")

        st.markdown(f"#### Resumo dos dados {sel_country[0]} - {end_year} vs {end_year - 1}")
        st.dataframe(df_long, hide_index=True, use_container_width=True, height=100)

        a, b, c = st.columns(3)

        # Converter para CSV
        csv = df_long.to_csv().encode('utf-8')
        with a:
            st.write("📥 **Exportar Dados**")
        with b:
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name=f'mozdados.csv',
                mime='text/csv',
                key=f"dl_csv"
            )
        # Converter para Excel
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_long.to_excel(writer, sheet_name='Dados', index=False)
        with c:
            st.download_button(
                label="Baixar Excel",
                data=buffer,
                file_name=f'mozdados.xlsx',
                mime='application/vnd.ms-excel',
                key=f"dl_excel"
            )


        # 1. Filtre o dataframe usando a lista completa 'sel_ind'
        # O operador 'in' funciona perfeitamente com listas no .query()
        df_filtered = df_long.query("Indicador in @sel_ind")

        # 2. Crie o gráfico FORA do loop
        df_filtered['Legenda'] = df_filtered['País'] + " - " + df_filtered['Indicador']
        fig = px.line(
            df_filtered,
            x='Ano',
            y='Valor',
            color='Legenda',# Uma linha por país
            line_dash='Indicador', # Diferencia os indicadores por tipo de linha (pontilhada, sólida, etc)
            markers=True,
            template='plotly_white'
        )
        fig.update_layout(
                            title=f"Evolução Temporal: {', '.join(sel_ind)}",
                            legend_title='Indicadores',
                            hovermode="x unified",  # Mostra todos os valores ao passar o mouse
                            height=500,
                            width=1500
                        )
        fig.update_layout(
            legend=dict(
                orientation="h",   # Define a orientação horizontal
                yanchor="bottom",
                y=-0.2,            # Posição vertical (valores negativos descem a legenda)
                xanchor="center",
                x=0.5              # Centraliza horizontalmente
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # Use a mesma coluna 'Legenda' que criamos para o gráfico de linhas
        fig_area = px.area(
            df_filtered,
            x='Ano',
            y='Valor',
            color='Legenda', # Essencial para separar as áreas
            template="plotly_white",
            title=f"Volume Acumulado (Área): {', '.join(sel_ind)}"
        )

        fig_area.update_layout(
            xaxis_title='Período',
            yaxis_title='Valor',
            legend_title='Indicadores',
            hovermode="x unified",
            height=500,
            # Colocando a legenda abaixo também para manter o padrão
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
        )

        st.plotly_chart(fig_area, use_container_width=True)
    with tab2:
        st.header("🤖 Análise Inteligente")
        st.caption("Um assistente virtual para explorar dados e responder sobre economia")

        import google.generativeai as genai

        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        #for m in genai.list_models():
            #st.write(m.name, m.supported_generation_methods)
        # --- Configuração da API Key do Gemini ---
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

        except (FileNotFoundError, KeyError):
            st.sidebar.header("🔑 Configuração")
            api_key = st.sidebar.text_input(
                "Cole sua API Key do Google Gemini aqui:",
                type="password",
                help="Obtenha sua chave em https://aistudio.google.com/"
            )

        if not api_key:
            st.warning("⚠️ Por favor, insira sua API Key do Google Gemini na barra lateral para começar.")
            st.stop()

        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            st.error(f"❌ Erro ao configurar a API do Gemini: {e}")
            st.stop()

        # --- Instrução inicial (contexto) ---
        indicadores = list(df_filtered['Indicador'].unique())
        paises = list(df_filtered['País'].unique())

        # Cria instrução com base nos dados filtrados atuais
        indicadores = list(df_filtered['Indicador'].unique())
        paises = list(df_filtered['País'].unique())
        nomes = list(df['Indicador'])

        system_instruction = f"""
        Você é o Databot. Explique indicadores económicos e traduza nomes em inglês.
        Indicadores disponíveis: {indicadores}
        Países selecionados: {paises}
        indicadores de busca:{nomes}. Esses indicadores devem ser apresentados quando o utilizador precisar de dica de como,
        ecnontrar-los: Por exemplo: como encontro e inflação. Responde: Comece escrevendo na barra de seleção de indicadores: Inflation ... e selecione o seu indicador
        Explique dizendo que nos dados deve escrever com letra maiuscula a primeira letra e em inglês de acorco com cada caso. Noutros casos como PIB deve ser GDP..
        """

        MODEL_NAME = "gemini-2.5-flash"

        # Reinicializa sempre que filtros mudarem
        model = genai.GenerativeModel(MODEL_NAME)
        st.session_state.chat = model.start_chat(history=[
            {'role': 'user', 'parts': [system_instruction]},
            {'role': 'model', 'parts': ["Entendido. Estou pronto para analisar os novos dados."]}
        ])

        # Reinicia também as mensagens
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Olá! Eu sou o Databot. Pergunte sobre os indicadores que deseja explorar."}
        ]

        MODEL_NAME = "gemini-2.5-flash"
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant",
                 "content": "👋 Olá! Eu sou o Databot, o seu assistente virtual para explorar os dados económicos. Como posso ajudar?"}
            ]

        if "chat" not in st.session_state:
            model = genai.GenerativeModel(MODEL_NAME)
            initial_history = [
                {'role': 'user', 'parts': [system_instruction]},
                {'role': 'model', 'parts': [
                    "Entendido. Olá! Eu sou o Databot, pronto para analisar os dados. O que deseja explorar?"]}
            ]
            st.session_state.chat = model.start_chat(history=initial_history)

        # --- Layout em colunas para histórico e interação ---
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("💬 Histórico da Conversa")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        with col2:
            st.success("📌 Dica: Pergunte sobre indicadores económicos ou tendências nos dados.")
            st.info("Exemplo: *Explique o indicador Agricultural land (sq. km)*")
            st.error("Caso não leve em conta os dados, copie e cole os dados que deseja analisar. Assim que os tiver, "
                     "posso prosseguir com a análise.")

        # --- Função para enviar mensagem ---
        def send_message_to_gemini(prompt):
            try:
                response = st.session_state.chat.send_message(prompt)
                return response.text
            except Exception as e:
                st.error(f"⚠️ Ocorreu um erro ao comunicar com a API: {e}")
                return None

        try:
            if prompt := st.chat_input("Digite sua mensagem..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("🤔 Pensando..."):
                        response_text = send_message_to_gemini(prompt)
                        if response_text:
                            st.markdown(response_text)
                            st.session_state.messages.append({"role": "assistant", "content": response_text})
        except:
            st.info("🚫 Não foi possível aceder ao Databot. Por favor, tente novamente mais tarde.")

    with tab3:
        # --- Mensagem final com efeito ---
        st.markdown("🌍 O **Mozdados** é mais do que um dashboard: é um passo em direção a uma cultura de **dados abertos e acessíveis**,"
                    "feita por quem acredita que informação é poder quando compartilhada.")

        # --- Layout em colunas ---
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("###### 🧩 Utilidade")
            st.success("""
            - Permite comparar países e indicadores de forma dinâmica.  
            - Facilita o acesso a dados históricos e tendências recentes.  
            - Apoia pesquisadores, estudantes, jornalistas e cidadãos na análise de informações confiáveis.  
            - Transforma estatísticas complexas em gráficos interativos e compreensíveis.  
            """)

        with col2:
            st.markdown("###### 👨‍💻 Sobre o Desenvolvedor")
            st.info("""
            Este projecto foi criado por **Ginelio Hermílio**, desenvolvedor apaixonado por transparência de dados
            e pelo uso de tecnologia para aproximar a sociedade da informação.  
    
            Seu foco é construir ferramentas que democratizem o acesso a dados, incentivem o debate público 
            e fortaleçam a tomada de decisão baseada em evidências.  
            📧 **Contacto**: *gineliohermilio@gmail.com*
            """)
except:
    st.error('Ocorreu um erro. Por favor, recarregue a página e tente novamente')
import streamlit as st
    import pandas as pd
    from datetime import datetime, date

    # --- CONFIGURAÇÃO DA PÁGINA ---
    st.set_page_config(
        page_title="Apuração Mesa 2026 - Espumoso/RS",
        page_icon="🗳️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- ESTILOS CSS PERSONALIZADOS ---
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            height: 3em;
            font-weight: bold;
        }
        .big-font {
            font-size: 20px !important;
        }
        .vencedor-card {
            padding: 20px;
            background-color: #d4edda;
            border-left: 6px solid #28a745;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- DADOS (HUMINT) ---
    # Cargo Atual: 0=Nenhum, 1=Pres, 2=Vice, 3=Geral, 4=Adjunto
    VEREADORES = [
        {"nome": "Dayana Soares (PDT)", "nasc": "1979-06-08", "cargo_atual": 4},
        {"nome": "Denner Senhor (PL)", "nasc": "1983-02-26", "cargo_atual": 3},
        {"nome": "Eduardo Signor (UB)", "nasc": "1994-12-23", "cargo_atual": 0},
        {"nome": "Fabiana Otoni (PP)", "nasc": "1982-02-12", "cargo_atual": 0},
        {"nome": "Leandro Colleraus (PDT)", "nasc": "1979-03-05", "cargo_atual": 0},
        {"nome": "Paulo Flores (PDT)", "nasc": "1969-05-18", "cargo_atual": 2},
        {"nome": "Tomas Fiuza (PP)", "nasc": "1989-10-17", "cargo_atual": 1},
    ]

    CARGOS = ["PRESIDENTE", "VICE-PRESIDENTE", "SECRETÁRIO GERAL", "SECRETÁRIO ADJUNTO"]
    TOTAL_VOTOS = 9

    # --- FUNÇÕES DE LÓGICA ---

    def calcular_idade_dias(data_nasc_str):
        nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
        return (date.today() - nasc).days

    def get_texto_idade(data_nasc_str):
        nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
        hoje = date.today()
        anos = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
        return f"{anos} anos ({nasc.strftime('%d/%m/%Y')})"

    def is_elegivel(vereador, indice_cargo_disputa):
        cargo_alvo = indice_cargo_disputa + 1 
        cargo_atual = vereador["cargo_atual"]
        
        # Regra 1: Se não tem cargo, é elegível
        if cargo_atual == 0: return True
        # Regra 2: Reeleição (mesmo cargo)
        if cargo_atual == cargo_alvo: return False
        # Regra 3: Cargo Inferior (hierarquia 1>2>3>4)
        if cargo_alvo > cargo_atual: return False
        
        return True

    # --- GERENCIAMENTO DE ESTADO (SESSION STATE) ---
    if 'indice_cargo' not in st.session_state:
        st.session_state.indice_cargo = 0
    if 'votos_atuais' not in st.session_state:
        st.session_state.votos_atuais = []
    if 'historico_resultados' not in st.session_state:
        st.session_state.historico_resultados = []
    if 'eleitos_nomes' not in st.session_state:
        st.session_state.eleitos_nomes = []
    if 'fim_eleicao' not in st.session_state:
        st.session_state.fim_eleicao = False

    # --- FUNÇÕES DE AÇÃO ---

    def registrar_voto(nome_candidato):
        st.session_state.votos_atuais.append(nome_candidato)
        st.toast(f"Voto registrado: {nome_candidato}")

    def desfazer_ultimo_voto():
        if st.session_state.votos_atuais:
            removed = st.session_state.votos_atuais.pop()
            st.toast(f"Voto de {removed} cancelado!")

    def finalizar_cargo():
        cargo_nome = CARGOS[st.session_state.indice_cargo]
        votos = st.session_state.votos_atuais
        
        # Contagem
        contagem = pd.Series(votos).value_counts()
        if contagem.empty:
             st.error("Nenhum voto registrado!")
             return

        ranking = contagem.sort_values(ascending=False)
        
        primeiro = ranking.index[0]
        votos_primeiro = ranking.iloc[0]
        
        # Verifica Empate
        empatados = ranking[ranking == votos_primeiro].index.tolist()
        
        vencedor = ""
        motivo = ""
        detalhe_idade = ""
        
        if len(empatados) == 1:
            vencedor = primeiro
            motivo = "Maioria Simples"
        else:
            # Lógica de Desempate (Idade)
            # Filtra Nulos da disputa de idade
            candidatos_empate = [v for v in VEREADORES if v["nome"] in empatados and v["nome"] != "NULO/BRANCO"]
            
            if not candidatos_empate:
                vencedor = "NENHUM (Empate Nulo)"
                motivo = "Empate de votos inválidos"
            else:
                # Ordena por idade (mais dias de vida = mais velho)
                candidatos_empate.sort(key=lambda x: calcular_idade_dias(x["nasc"]), reverse=True)
                
                mais_velho = candidatos_empate[0]
                vencedor = mais_velho["nome"]
                idade_texto = get_texto_idade(mais_velho["nasc"])
                motivo = "Critério de Idade (Mais Velho)"
                detalhe_idade = f"Venceu com {idade_texto}"

        # Salvar Resultado
        st.session_state.historico_resultados.append({
            "Cargo": cargo_nome,
            "Vencedor": vencedor,
            "Votos": votos_primeiro,
            "Motivo": motivo,
            "Detalhe": detalhe_idade
        })
        
        if vencedor not in ["NULO/BRANCO", "NENHUM (Empate Nulo)"]:
            st.session_state.eleitos_nomes.append(vencedor)
        
        # Avançar
        st.session_state.votos_atuais = []
        if st.session_state.indice_cargo < len(CARGOS) - 1:
            st.session_state.indice_cargo += 1
        else:
            st.session_state.fim_eleicao = True
        
        st.rerun()

    def reiniciar_sistema():
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- INTERFACE GRÁFICA (SIDEBAR) ---
    with st.sidebar:
        st.title("⚙️ Controle")
        st.progress(st.session_state.indice_cargo / len(CARGOS), text="Progresso Geral")
        
        if st.session_state.historico_resultados:
            st.markdown("### 📜 Eleitos")
            for res in st.session_state.historico_resultados:
                st.success(f"**{res['Cargo']}**\n\n👤 {res['Vencedor']}")
                
        st.divider()
        if st.button("🔄 Reiniciar Tudo", type="secondary"):
            reiniciar_sistema()

    # --- INTERFACE PRINCIPAL ---

    st.title("🗳️ Apuração Mesa Diretora 2026")
    st.markdown("### Câmara Municipal de Vereadores de Espumoso/RS")
    st.divider()

    if not st.session_state.fim_eleicao:
        # TELA DE VOTAÇÃO
        cargo_atual = CARGOS[st.session_state.indice_cargo]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"Em votação: **{cargo_atual}**")
            
            # Barra de Votos
            qtd_votos = len(st.session_state.votos_atuais)
            st.info(f"Votos Computados: **{qtd_votos}** de **{TOTAL_VOTOS}**")
            st.progress(qtd_votos / TOTAL_VOTOS)
            
            # Grade de Candidatos
            st.write("#### Selecione o Candidato:")
            
            # Filtra Candidatos Elegíveis
            candidatos_display = []
            for v in VEREADORES:
                # Não pode ter sido eleito antes E tem que ser elegível para o cargo
                if v["nome"] not in st.session_state.eleitos_nomes and is_elegivel(v, st.session_state.indice_cargo):
                    candidatos_display.append(v)
            
            # Botões
            cols = st.columns(2)
            for i, cand in enumerate(candidatos_display):
                if cols[i % 2].button(f"👤 {cand['nome']}", key=cand['nome'], disabled=qtd_votos >= TOTAL_VOTOS):
                    registrar_voto(cand['nome'])
                    st.rerun()
                    
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("⚪ NULO / BRANCO", disabled=qtd_votos >= TOTAL_VOTOS):
                registrar_voto("NULO/BRANCO")
                st.rerun()
                
            if c2.button("↩️ Desfazer Último", disabled=qtd_votos == 0):
                desfazer_ultimo_voto()
                st.rerun()
                
            # Botão de Finalizar Cargo (Só aparece com 9 votos)
            if qtd_votos == TOTAL_VOTOS:
                st.success("Votação Completa!")
                if st.button("🚀 Apurar Resultado e Próximo Cargo", type="primary"):
                    finalizar_cargo()

        with col2:
            st.subheader("📊 Placar ao Vivo")
            if st.session_state.votos_atuais:
                df = pd.DataFrame(st.session_state.votos_atuais, columns=["Candidato"])
                contagem = df["Candidato"].value_counts()
                st.bar_chart(contagem)
                st.write(contagem)
            else:
                st.caption("Aguardando votos...")

    else:
        # TELA DE ENCERRAMENTO (ATA)
        st.balloons()
        st.success("🎉 Eleição Concluída com Sucesso!")
        
        st.subheader("📄 Ata Final de Apuração")
        
        df_final = pd.DataFrame(st.session_state.historico_resultados)
        st.table(df_final)
        
        # Preparar Texto para Download
        texto_ata = f"ATA DE APURAÇÃO - MESA DIRETORA 2026\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        for res in st.session_state.historico_resultados:
            texto_ata += f"CARGO: {res['Cargo']}\n"
            texto_ata += f"ELEITO: {res['Vencedor']}\n"
            texto_ata += f"VOTOS: {res['Votos']}\n"
            texto_ata += f"OBS: {res['Motivo']} {res['Detalhe']}\n"
            texto_ata += "-"*40 + "\n"
            
        st.download_button(
            label="📥 Baixar Ata (.txt)",
            data=texto_ata,
            file_name=f"Ata_Mesa2026_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

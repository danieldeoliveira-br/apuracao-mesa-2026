import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Apuração Mesa Diretora 2026",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DADOS E CONSTANTES ---
VEREADORES = [
    {"nome": "Dayana Soares (PDT)", "nasc": "1979-06-08", "cargo_atual": 4, "apelidos": ["dayana", "day"]},
    {"nome": "Denner Senhor (PL)", "nasc": "1983-02-26", "cargo_atual": 3, "apelidos": ["denner", "senhor"]},
    {"nome": "Eduardo Signor (UB)", "nasc": "1994-12-23", "cargo_atual": 0, "apelidos": ["eduardo", "signor"]},
    {"nome": "Fabiana Otoni (PP)", "nasc": "1982-02-12", "cargo_atual": 0, "apelidos": ["fabiana", "otoni"]},
    {"nome": "Leandro Colleraus (PDT)", "nasc": "1979-03-05", "cargo_atual": 0, "apelidos": ["leandro", "colleraus"]},
    {"nome": "Paulo Flores (PDT)", "nasc": "1969-05-18", "cargo_atual": 2, "apelidos": ["paulo", "flores"]},
    {"nome": "Tomas Fiuza (PP)", "nasc": "1989-10-17", "cargo_atual": 1, "apelidos": ["tomas", "fiuza"]},
]

CARGOS = ["PRESIDENTE", "VICE-PRESIDENTE", "SECRETÁRIO GERAL", "SECRETÁRIO ADJUNTO"]
TOTAL_VOTOS = 9

# --- FUNÇÕES UTILITÁRIAS ---

def calcular_idade_detalhada(data_nasc_str):
    nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
    hoje = date.today()
    anos = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    dias_vida = (hoje - nasc).days
    return dias_vida, f"{anos} anos ({nasc.strftime('%d/%m/%Y')})"

def is_elegivel(vereador, indice_cargo):
    cargo_alvo = indice_cargo + 1 # 1 a 4
    cargo_atual = vereador["cargo_atual"]
    
    if cargo_atual == 0: return True
    if cargo_atual == cargo_alvo: return False # Reeleição
    if cargo_alvo > cargo_atual: return False # Cargo Inferior
    return True

def inicializar_estado():
    if 'indice_cargo' not in st.session_state:
        st.session_state.indice_cargo = 0
    if 'votos_atuais' not in st.session_state:
        st.session_state.votos_atuais = []
    if 'resultados' not in st.session_state:
        st.session_state.resultados = []
    if 'eleitos_nomes' not in st.session_state:
        st.session_state.eleitos_nomes = []
    if 'fim_eleicao' not in st.session_state:
        st.session_state.fim_eleicao = False

def registrar_voto(candidato_nome):
    st.session_state.votos_atuais.append(candidato_nome)
    st.toast(f"Voto registrado para: {candidato_nome}", icon="✅")

def desfazer_voto():
    if st.session_state.votos_atuais:
        removido = st.session_state.votos_atuais.pop()
        st.toast(f"Voto para {removido} removido!", icon="↩️")

def processar_resultado_cargo():
    cargo_atual_nome = CARGOS[st.session_state.indice_cargo]
    votos = st.session_state.votos_atuais
    
    contagem = pd.Series(votos).value_counts()
    
    if contagem.empty:
        vencedor_nome = "NINGUÉM"
        motivo = "Sem votos registrados"
    else:
        max_votos = contagem.max()
        candidatos_empatados = contagem[contagem == max_votos].index.tolist()
        
        if len(candidatos_empatados) == 1:
            vencedor_nome = candidatos_empatados[0]
            motivo = "Maioria Simples"
        else:
            # Empate - Critério de Idade
            candidatos_empate_objs = [v for v in VEREADORES if v["nome"] in candidatos_empatados]
            
            if not candidatos_empate_objs: # Pode acontecer se empate for entre Nulos/Brancos
                 vencedor_nome = candidatos_empatados[0] # Assume o primeiro (NULO/BRANCO)
                 motivo = "Empate (Votos não nominais)"
            else:
                candidatos_empate_objs.sort(key=lambda x: calcular_idade_detalhada(x["nasc"])[0], reverse=True)
                mais_velho = candidatos_empate_objs[0]
                _, texto_idade = calcular_idade_detalhada(mais_velho["nasc"])
                vencedor_nome = mais_velho["nome"]
                motivo = f"Desempate: Mais Idoso ({texto_idade})"

    # Salvar resultado
    st.session_state.resultados.append({
        "cargo": cargo_atual_nome,
        "vencedor": vencedor_nome,
        "votos": contagem.get(vencedor_nome, 0),
        "motivo": motivo,
        "detalhes_votos": contagem.to_dict()
    })
    
    if vencedor_nome not in ["NULO", "BRANCO", "NINGUÉM"]:
        st.session_state.eleitos_nomes.append(vencedor_nome)

    # Avançar para próximo cargo ou finalizar
    st.session_state.votos_atuais = []
    if st.session_state.indice_cargo < len(CARGOS) - 1:
        st.session_state.indice_cargo += 1
    else:
        st.session_state.fim_eleicao = True
    
    st.rerun()

def gerar_ata_texto():
    texto_ata = f"ATA FINAL DE APURAÇÃO - ELEIÇÃO MESA DIRETORA 2026\n"
    texto_ata += f"Câmara Municipal de Vereadores de Espumoso/RS\n"
    texto_ata += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    texto_ata += "-" * 60 + "\n"
    texto_ata += f"{'CARGO':<20} | {'ELEITO':<25} | {'VOTOS':<5} | {'OBSERVAÇÃO'}\n"
    texto_ata += "-" * 60 + "\n"
    
    for res in st.session_state.resultados:
        texto_ata += f"{res['cargo']:<20} | {res['vencedor']:<25} | {str(res['votos']):<5} | {res['motivo']}\n"
    
    texto_ata += "-" * 60 + "\n\n"
    texto_ata += "Assinaturas:\n\n"
    texto_ata += "_" * 40 + "\nPresidente da Sessão\n\n"
    texto_ata += "_" * 40 + "\n1º Secretário\n"
    
    return texto_ata

# --- INTERFACE PRINCIPAL ---

inicializar_estado()

st.title("🗳️ Sistema de Apuração Eletrônica - Mesa 2026")
st.markdown("**Câmara Municipal de Vereadores de Espumoso/RS**")
st.divider()

# --- SIDEBAR (HISTÓRICO E CONTROLES) ---
with st.sidebar:
    st.header("📋 Painel de Controle")
    
    if st.button("🔄 Reiniciar Eleição", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    st.divider()
    st.subheader("📜 Histórico de Eleitos")
    
    if not st.session_state.resultados:
        st.info("Nenhum cargo apurado ainda.")
    else:
        for res in st.session_state.resultados:
            st.success(f"**{res['cargo']}**\n\n🏆 {res['vencedor']}\n\nℹ️ {res['motivo']}")

# --- TELA DE VOTAÇÃO ---
if not st.session_state.fim_eleicao:
    cargo_atual = CARGOS[st.session_state.indice_cargo]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Votação para: **{cargo_atual}**")
        
        # Barra de progresso
        votos_computados = len(st.session_state.votos_atuais)
        progresso = votos_computados / TOTAL_VOTOS
        st.progress(progresso, text=f"Votos Computados: {votos_computados} de {TOTAL_VOTOS}")
        
        st.write("### Selecione o Candidato:")
        
        candidatos_elegiveis = []
        for v in VEREADORES:
            # Filtra elegibilidade e se já foi eleito
            if v["nome"] not in st.session_state.eleitos_nomes and is_elegivel(v, st.session_state.indice_cargo):
                candidatos_elegiveis.append(v)
        
        # Grid de botões para candidatos
        cols = st.columns(2)
        for i, cand in enumerate(candidatos_elegiveis):
            with cols[i % 2]:
                if st.button(f"👤 {cand['nome']}", key=cand['nome'], use_container_width=True, disabled=votos_computados >= TOTAL_VOTOS):
                    registrar_voto(cand['nome'])
                    st.rerun()
        
        st.markdown("---")
        col_nulo, col_desfazer = st.columns(2)
        with col_nulo:
            if st.button("⚪ VOTO NULO / BRANCO", use_container_width=True, disabled=votos_computados >= TOTAL_VOTOS):
                registrar_voto("NULO / BRANCO")
                st.rerun()
        with col_desfazer:
            if st.button("↩️ Desfazer Último Voto", use_container_width=True, type="secondary", disabled=votos_computados == 0):
                desfazer_voto()
                st.rerun()

        if votos_computados == TOTAL_VOTOS:
            st.success("Votação para este cargo concluída!")
            if st.button("🚀 Apurar e Próximo Cargo", type="primary", use_container_width=True):
                processar_resultado_cargo()

    with col2:
        st.subheader("📊 Placar em Tempo Real")
        if st.session_state.votos_atuais:
            df_votos = pd.DataFrame(st.session_state.votos_atuais, columns=["Candidato"])
            contagem = df_votos["Candidato"].value_counts()
            st.bar_chart(contagem)
            st.write(contagem)
        else:
            st.info("Aguardando votos...")

# --- TELA DE ENCERRAMENTO (ATA) ---
else:
    st.balloons()
    st.success("🎉 Eleição Concluída! A Mesa Diretora para 2026 está formada.")
    
    st.subheader("📄 Resumo da Eleição (Ata)")
    
    # Criar DataFrame para exibição bonita
    df_resultados = pd.DataFrame(st.session_state.resultados)
    st.table(df_resultados[["cargo", "vencedor", "votos", "motivo"]])
    
    # Botão de Download da Ata
    ata_texto = gerar_ata_texto()
    st.download_button(
        label="📥 Baixar Ata Oficial (.txt)",
        data=ata_texto,
        file_name=f"Ata_Mesa2026_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )
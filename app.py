import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configurazione pagina
st.set_page_config(
    page_title="Simulatore Forfettario 2025",
    page_icon="📊",
    layout="wide"
)

# Database completo codici ATECO con coefficienti
COEFFICIENTI_ATECO = {
    # Industrie alimentari e bevande
    "10": 40, "11": 40,
    # Industrie tessili, abbigliamento, pelli
    "13": 67, "14": 67, "15": 67,
    # Industria del legno, carta, stampa
    "16": 67, "17": 67, "18": 67,
    # Fabbricazione coke, prodotti petroliferi
    "19": 40,
    # Industrie chimiche, farmaceutiche
    "20": 67, "21": 67,
    # Fabbricazione prodotti in gomma e plastica
    "22": 67,
    # Metallurgia, fabbricazione prodotti in metallo
    "24": 67, "25": 67,
    # Fabbricazione computer, elettronica, ottica
    "26": 67,
    # Fabbricazione apparecchiature elettriche
    "27": 67,
    # Fabbricazione macchinari
    "28": 67,
    # Fabbricazione autoveicoli
    "29": 67,
    # Fabbricazione altri mezzi di trasporto
    "30": 67,
    # Fabbricazione mobili
    "31": 67,
    # Altre industrie manifatturiere
    "32": 67,
    # Riparazione, manutenzione, installazione
    "33": 67,
    # Costruzioni e attività immobiliari
    "41": 86, "42": 86, "43": 86,
    # Commercio all'ingrosso e al dettaglio
    "45": 40, "46": 40, "47": 40,
    # Commercio ambulante prodotti alimentari e bevande
    "4781": 40,
    # Commercio ambulante altri prodotti
    "4782": 54,
    # Trasporto e magazzinaggio
    "49": 67, "50": 67, "51": 67, "52": 67, "53": 67,
    # Servizi alloggio e ristorazione
    "55": 40, "56": 40,
    # Servizi informazione e comunicazione
    "58": 67, "59": 67, "60": 67, "61": 67, "62": 67, "63": 67,
    # Attività finanziarie e assicurative
    "64": 67, "65": 67, "66": 67,
    # Attività immobiliari
    "68": 86,
    # Attività professionali, scientifiche, tecniche
    "69": 78, "70": 78, "71": 78, "72": 78, "73": 78, "74": 78, "75": 78,
    # Noleggio, agenzie viaggio, servizi supporto imprese
    "77": 67, "78": 67, "79": 67, "80": 67, "81": 67, "82": 67,
    # Istruzione
    "85": 78,
    # Sanità e assistenza sociale
    "86": 78, "87": 78, "88": 78,
    # Attività artistiche, sportive, intrattenimento
    "90": 67, "91": 67, "92": 67, "93": 67,
    # Altre attività di servizi
    "94": 67, "95": 67, "96": 67,
    # Intermediari del commercio
    "461": 62,
}

def get_coefficiente(codice_ateco):
    """Cerca il coefficiente per un codice ATECO"""
    codice = str(codice_ateco).strip().replace(".", "")

    # Prova match esatto
    if codice in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice]

    # Prova con primi 4 caratteri
    if len(codice) >= 4 and codice[:4] in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice[:4]]

    # Prova con primi 3 caratteri
    if len(codice) >= 3 and codice[:3] in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice[:3]]

    # Prova con primi 2 caratteri
    if len(codice) >= 2 and codice[:2] in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice[:2]]

    return None

def calcola_forfettario(ricavi, coefficiente, contributi_anno_prec, 
                        aliquota_imposta, tipo_cassa, riduzione_contrib=0):
    # Calcolo reddito imponibile
    reddito_imponibile_lordo = ricavi * (coefficiente / 100)
    reddito_imponibile_netto = reddito_imponibile_lordo - contributi_anno_prec

    # Calcolo imposta sostitutiva
    imposta_sostitutiva = reddito_imponibile_netto * (aliquota_imposta / 100)

    # Calcolo contributi
    if tipo_cassa == 'Gestione Separata INPS':
        aliquota_inps = 26.07
        contributi_inps = reddito_imponibile_lordo * (aliquota_inps / 100)
        riduzione_applicata = 0
    else:
        contributo_fisso = 4460.64
        minimale = 18555
        eccedenza = max(0, reddito_imponibile_lordo - minimale)
        aliquota_eccedenza = 24

        if riduzione_contrib == 35:
            contributo_fisso = contributo_fisso * 0.65
            aliquota_eccedenza = aliquota_eccedenza * 0.65
            riduzione_applicata = 35
        elif riduzione_contrib == 50:
            contributo_fisso = contributo_fisso * 0.50
            aliquota_eccedenza = aliquota_eccedenza * 0.50
            riduzione_applicata = 50
        else:
            riduzione_applicata = 0

        contributi_variabili = eccedenza * (aliquota_eccedenza / 100)
        contributi_inps = contributo_fisso + contributi_variabili

    totale_imposte_contributi = imposta_sostitutiva + contributi_inps
    tax_rate = (totale_imposte_contributi / ricavi) * 100
    netto = ricavi - totale_imposte_contributi

    return {
        'reddito_lordo': reddito_imponibile_lordo,
        'reddito_netto': reddito_imponibile_netto,
        'imposta': imposta_sostitutiva,
        'contributi': contributi_inps,
        'totale': totale_imposte_contributi,
        'tax_rate': tax_rate,
        'netto': netto,
        'riduzione': riduzione_applicata
    }

# Titolo
st.title("📊 Simulatore Regime Forfettario 2025")
st.markdown("**by Fisco Chiaro Consulting**")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Parametri Input")

    ricavi = st.number_input(
        "Ricavi annui (€)",
        min_value=0,
        max_value=85000,
        value=50000,
        step=1000,
        help="Inserisci il tuo fatturato annuo previsto (max 85.000€)"
    )

    metodo = st.radio(
        "Come vuoi inserire l'attività?",
        ["Codice ATECO", "Settore generico"],
        help="Il codice ATECO è più preciso"
    )

    if metodo == "Codice ATECO":
        st.info("💡 Inserisci il tuo codice ATECO (es. 69.20.11, 47.11.40, 86.90.29)")

        codice_ateco = st.text_input(
            "Codice ATECO",
            value="",
            placeholder="es. 69.20.11 o 692011",
            help="Puoi inserire con o senza punti"
        )

        if codice_ateco:
            coefficiente = get_coefficiente(codice_ateco)
            if coefficiente:
                st.success(f"✅ Coefficiente trovato: **{coefficiente}%**")
            else:
                st.warning("⚠️ Codice ATECO non trovato. Seleziona 'Settore generico' o verifica il codice.")
                st.info("Esempi comuni: 69=Professioni legali, 86=Sanità, 47=Commercio al dettaglio")
                coefficiente = 67
        else:
            coefficiente = 67
            st.info("👆 Inserisci il tuo codice ATECO per calcolare il coefficiente")
    else:
        attivita = st.selectbox(
            "Settore di attività",
            [
                "Attività professionali, scientifiche, tecniche (78%)",
                "Costruzioni e attività immobiliari (86%)",
                "Intermediari commercio (62%)",
                "Commercio all'ingrosso e dettaglio (40%)",
                "Servizi alloggio e ristorazione (40%)",
                "Altre attività economiche (67%)"
            ]
        )
        coefficiente = int(attivita.split("(")[1].split("%")[0])

    contributi_prec = st.number_input(
        "Contributi versati anno precedente (€)",
        min_value=0,
        max_value=30000,
        value=5000,
        step=500,
        help="Contributi previdenziali deducibili dall'anno precedente"
    )

    aliquota = st.radio(
        "Aliquota imposta sostitutiva",
        [5, 15],
        format_func=lambda x: f"{x}% - {'Startup (primi 5 anni)' if x == 5 else 'Ordinaria'}",
        help="5% per nuove attività che rispettano i requisiti, 15% ordinaria"
    )

    cassa = st.selectbox(
        "Cassa previdenziale",
        ["Gestione Separata INPS", "Artigiani e Commercianti"]
    )

    riduzione = 0
    if cassa == "Artigiani e Commercianti":
        riduzione = st.selectbox(
            "Riduzione contributiva",
            [0, 35, 50],
            format_func=lambda x: {
                0: "Nessuna riduzione",
                35: "Riduzione 35% (da rinnovare annualmente)",
                50: "Riduzione 50% (nuove attività 2025, primi 36 mesi)"
            }[x],
            help="Le riduzioni sono disponibili solo per Artigiani/Commercianti"
        )
    else:
        st.info("ℹ️ La Gestione Separata NON prevede riduzioni contributive")

with col2:
    st.header("📊 Risultati")

    if metodo == "Codice ATECO" and codice_ateco and get_coefficiente(codice_ateco) is None:
        st.error("⚠️ Inserisci un codice ATECO valido o seleziona 'Settore generico'")
    else:
        risultato = calcola_forfettario(
            ricavi, coefficiente, contributi_prec, 
            aliquota, cassa, riduzione
        )

        st.metric(
            label="Tax Rate Effettivo",
            value=f"{risultato['tax_rate']:.2f}%",
            delta=None
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.metric(
                label="Netto Annuo",
                value=f"€ {risultato['netto']:,.0f}",
                delta=None
            )

        with col_b:
            st.metric(
                label="Netto Mensile",
                value=f"€ {risultato['netto']/12:,.0f}",
                delta=None
            )

        st.markdown("---")
        st.subheader("Dettaglio Calcolo")

        st.write(f"**Coefficiente redditività:** {coefficiente}%")
        st.write(f"**Reddito imponibile lordo:** € {risultato['reddito_lordo']:,.2f}")
        st.write(f"**Reddito imponibile netto:** € {risultato['reddito_netto']:,.2f}")
        st.write("")
        st.write(f"**Imposta sostitutiva ({aliquota}%):** € {risultato['imposta']:,.2f}")

        if riduzione > 0:
            st.write(f"**Contributi INPS (riduzione {riduzione}%):** € {risultato['contributi']:,.2f}")
        else:
            st.write(f"**Contributi INPS:** € {risultato['contributi']:,.2f}")

        st.write(f"**TOTALE imposte + contributi:** € {risultato['totale']:,.2f}")

# --- RACCOLTA EMAIL CON GOOGLE SHEETS ---
st.markdown("---")
st.header("📬 Ricevi Aggiornamenti Fiscali")
st.write("Iscriviti alla newsletter per rimanere aggiornato su novità fiscali e contributive")

with st.form("newsletter_form"):
    col_email, col_btn = st.columns([3, 1])
    with col_email:
        email = st.text_input("Email", placeholder="tuaemail@esempio.it", label_visibility="collapsed")
    with col_btn:
        submitted = st.form_submit_button("Iscriviti", use_container_width=True)

    if submitted and email:
        try:
            # Connessione a Google Sheets
            conn = st.connection("gsheets", type=GSheetsConnection)

            # Leggi i dati esistenti
            try:
                df_esistente = conn.read(worksheet="Iscrizioni", ttl=0)
                # Se il foglio è vuoto, crea struttura
                if df_esistente.empty or 'Email' not in df_esistente.columns:
                    df_esistente = pd.DataFrame(columns=['Email', 'Data', 'Timestamp'])
            except:
                # Se il worksheet non esiste, crea DataFrame vuoto
                df_esistente = pd.DataFrame(columns=['Email', 'Data', 'Timestamp'])

            # Verifica email duplicata
            if email in df_esistente['Email'].values:
                st.warning("⚠️ Questa email è già iscritta!")
            else:
                # Crea nuova riga
                nuova_iscrizione = pd.DataFrame({
                    'Email': [email],
                    'Data': [datetime.now().strftime("%Y-%m-%d")],
                    'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                })

                # Concatena con dati esistenti
                df_aggiornato = pd.concat([df_esistente, nuova_iscrizione], ignore_index=True)

                # Scrivi su Google Sheets
                conn.update(worksheet="Iscrizioni", data=df_aggiornato)

                st.success("✅ Grazie per l'iscrizione!")
                st.balloons()

        except Exception as e:
            st.error(f"❌ Errore durante il salvataggio: {str(e)}")
            st.info("💡 Verifica che il foglio Google Sheets sia configurato correttamente")

# --- FOOTER ---
st.markdown("---")
st.info("""
**ℹ️ Note importanti:**
- **Aliquota 5%**: valida per 5 anni per nuove attività che non hanno esercitato attività analoghe nei 3 anni precedenti
- **Riduzione 35%**: riservata ad Artigiani/Commercianti forfettari, domanda entro 28 febbraio ogni anno
- **Riduzione 50%**: per nuove iscrizioni 2025 alla Gestione Artigiani/Commercianti, valida 36 mesi
- **Cumulabilità**: Aliquota 5% + Riduzione contributi sono cumulabili per il massimo risparmio fiscale
- **Codice ATECO**: Per verificare il tuo codice ATECO, consulta il sito dell'Agenzia delle Entrate o la tua Camera di Commercio
""")
st.markdown("---")
st.markdown("**Sviluppato da [Fisco Chiaro Consulting](https://fiscochiaroconsulting.it)** | © 2025")
st.markdown("📧 Per consulenze personalizzate: info@fiscochiaroconsulting.it")

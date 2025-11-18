import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

# Configurazione pagina
st.set_page_config(
    page_title="Simulatore Forfettario 2025",
    page_icon="📊",
    layout="wide"
)

# Database codici ATECO
COEFFICIENTI_ATECO = {
    "10": 40, "11": 40, "13": 67, "14": 67, "15": 67, "16": 67, "17": 67, "18": 67,
    "19": 40, "20": 67, "21": 67, "22": 67, "24": 67, "25": 67, "26": 67, "27": 67,
    "28": 67, "29": 67, "30": 67, "31": 67, "32": 67, "33": 67, "41": 86, "42": 86,
    "43": 86, "45": 40, "46": 40, "47": 40, "4781": 40, "4782": 54, "49": 67,
    "50": 67, "51": 67, "52": 67, "53": 67, "55": 40, "56": 40, "58": 67, "59": 67,
    "60": 67, "61": 67, "62": 67, "63": 67, "64": 67, "65": 67, "66": 67, "68": 86,
    "69": 78, "70": 78, "71": 78, "72": 78, "73": 78, "74": 78, "75": 78, "77": 67,
    "78": 67, "79": 67, "80": 67, "81": 67, "82": 67, "85": 78, "86": 78, "87": 78,
    "88": 78, "90": 67, "91": 67, "92": 67, "93": 67, "94": 67, "95": 67, "96": 67,
    "461": 62,
}

def get_coefficiente(codice_ateco):
    codice = str(codice_ateco).strip().replace(".", "")
    if codice in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice]
    if len(codice) >= 4 and codice[:4] in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice[:4]]
    if len(codice) >= 3 and codice[:3] in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice[:3]]
    if len(codice) >= 2 and codice[:2] in COEFFICIENTI_ATECO:
        return COEFFICIENTI_ATECO[codice[:2]]
    return None

def calcola_forfettario(ricavi, coefficiente, contributi_anno_prec, 
                        aliquota_imposta, tipo_cassa, riduzione_contrib=0):
    reddito_imponibile_lordo = ricavi * (coefficiente / 100)
    reddito_imponibile_netto = reddito_imponibile_lordo - contributi_anno_prec
    imposta_sostitutiva = reddito_imponibile_netto * (aliquota_imposta / 100)

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
    ricavi = st.number_input("Ricavi annui (€)", min_value=0, max_value=85000, value=50000, step=1000)
    metodo = st.radio("Come vuoi inserire l'attività?", ["Codice ATECO", "Settore generico"])

    if metodo == "Codice ATECO":
        st.info("💡 Inserisci il tuo codice ATECO")
        codice_ateco = st.text_input("Codice ATECO", value="", placeholder="es. 69.20.11")
        if codice_ateco:
            coefficiente = get_coefficiente(codice_ateco)
            if coefficiente:
                st.success(f"✅ Coefficiente: **{coefficiente}%**")
            else:
                st.warning("⚠️ Codice ATECO non trovato.")
                coefficiente = 67
        else:
            coefficiente = 67
    else:
        attivita = st.selectbox("Settore di attività", [
            "Attività professionali, scientifiche, tecniche (78%)",
            "Costruzioni e attività immobiliari (86%)",
            "Intermediari commercio (62%)",
            "Commercio all'ingrosso e dettaglio (40%)",
            "Servizi alloggio e ristorazione (40%)",
            "Altre attività economiche (67%)"
        ])
        coefficiente = int(attivita.split("(")[1].split("%")[0])

    contributi_prec = st.number_input("Contributi anno precedente (€)", min_value=0, max_value=30000, value=5000, step=500)
    aliquota = st.radio("Aliquota imposta sostitutiva", [5, 15], 
                       format_func=lambda x: f"{x}% - {'Startup' if x == 5 else 'Ordinaria'}")
    cassa = st.selectbox("Cassa previdenziale", ["Gestione Separata INPS", "Artigiani e Commercianti"])

    riduzione = 0
    if cassa == "Artigiani e Commercianti":
        riduzione = st.selectbox("Riduzione contributiva", [0, 35, 50],
            format_func=lambda x: {0: "Nessuna", 35: "35%", 50: "50%"}[x])

with col2:
    st.header("📊 Risultati")
    risultato = calcola_forfettario(ricavi, coefficiente, contributi_prec, aliquota, cassa, riduzione)

    st.metric("Tax Rate Effettivo", f"{risultato['tax_rate']:.2f}%")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Netto Annuo", f"€ {risultato['netto']:,.0f}")
    with col_b:
        st.metric("Netto Mensile", f"€ {risultato['netto']/12:,.0f}")

    st.markdown("---")
    st.subheader("Dettaglio Calcolo")
    st.write(f"**Coefficiente:** {coefficiente}%")
    st.write(f"**Reddito lordo:** € {risultato['reddito_lordo']:,.2f}")
    st.write(f"**Imposta ({aliquota}%):** € {risultato['imposta']:,.2f}")
    st.write(f"**Contributi INPS:** € {risultato['contributi']:,.2f}")
    st.write(f"**TOTALE:** € {risultato['totale']:,.2f}")

# ============================================================================
# RACCOLTA EMAIL CON PULIZIA AUTOMATICA URL
# ============================================================================
st.markdown("---")
st.header("📬 Ricevi Aggiornamenti Fiscali")

# DEBUG
with st.expander("🔍 DEBUG - Verifica Configurazione"):
    st.write("**Environment Variables:**")

    spreadsheet_raw = os.getenv("GSHEETS_SPREADSHEET", "")
    # PULIZIA AUTOMATICA URL
    spreadsheet_clean = spreadsheet_raw.strip().replace("\n", "").replace("\r", "").replace("\t", "")
    # Rimuovi anche ?usp=sharing se presente
    if "?usp=sharing" in spreadsheet_clean:
        spreadsheet_clean = spreadsheet_clean.split("?usp=sharing")[0]

    st.write(f"**URL RAW:** `{repr(spreadsheet_raw)}`")
    st.write(f"**URL PULITO:** `{spreadsheet_clean}`")
    st.write(f"**Lunghezza:** {len(spreadsheet_clean)} caratteri")

    if spreadsheet_clean:
        st.success(f"✅ GSHEETS_SPREADSHEET: {spreadsheet_clean[:60]}...")
    else:
        st.error("❌ GSHEETS_SPREADSHEET: MANCANTE!")

    client_email = os.getenv("GSHEETS_CLIENT_EMAIL")
    if client_email:
        st.success(f"✅ GSHEETS_CLIENT_EMAIL: {client_email}")
    else:
        st.error("❌ GSHEETS_CLIENT_EMAIL: MANCANTE!")

    private_key = os.getenv("GSHEETS_PRIVATE_KEY")
    if private_key and len(private_key) > 1000:
        st.success(f"✅ GSHEETS_PRIVATE_KEY: {len(private_key)} caratteri (OK)")
    elif private_key:
        st.warning(f"⚠️ GSHEETS_PRIVATE_KEY: {len(private_key)} caratteri (troppo corta!)")
    else:
        st.error("❌ GSHEETS_PRIVATE_KEY: MANCANTE!")

with st.form("newsletter_form"):
    col_email, col_btn = st.columns([3, 1])
    with col_email:
        email = st.text_input("Email", placeholder="tuaemail@esempio.it", label_visibility="collapsed")
    with col_btn:
        submitted = st.form_submit_button("Iscriviti", use_container_width=True)

    if submitted and email:
        try:
            st.info("🔄 Connessione a Google Sheets...")

            # Crea connessione
            conn = st.connection("gsheets", type=GSheetsConnection)
            st.success("✅ Connessione creata")

            # PULIZIA AUTOMATICA URL
            spreadsheet_raw = os.getenv("GSHEETS_SPREADSHEET", "")
            spreadsheet_url = spreadsheet_raw.strip().replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")

            # Rimuovi ?usp=sharing se presente
            if "?usp=sharing" in spreadsheet_url:
                spreadsheet_url = spreadsheet_url.split("?usp=sharing")[0]

            # Rimuovi eventuali virgolette
            spreadsheet_url = spreadsheet_url.strip('"').strip("'")

            st.info(f"📄 URL pulito: {spreadsheet_url[:60]}...")

            # Leggi dati
            try:
                st.info("🔄 Lettura dati...")
                df_esistente = conn.read(
                    spreadsheet=spreadsheet_url,
                    worksheet="Iscrizioni",
                    ttl=0
                )
                st.success(f"✅ Lettura OK - {len(df_esistente)} righe")

                if df_esistente.empty or 'Email' not in df_esistente.columns:
                    df_esistente = pd.DataFrame(columns=['Email', 'Data', 'Timestamp'])
            except Exception as e:
                st.warning(f"⚠️ Creo nuovo foglio: {str(e)}")
                df_esistente = pd.DataFrame(columns=['Email', 'Data', 'Timestamp'])

            # Verifica duplicati
            if email in df_esistente['Email'].values:
                st.warning("⚠️ Email già iscritta!")
            else:
                # Aggiungi email
                st.info("🔄 Salvataggio...")
                nuova_iscrizione = pd.DataFrame({
                    'Email': [email],
                    'Data': [datetime.now().strftime("%Y-%m-%d")],
                    'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                })

                df_aggiornato = pd.concat([df_esistente, nuova_iscrizione], ignore_index=True)

                # Scrivi
                conn.update(
                    spreadsheet=spreadsheet_url,
                    worksheet="Iscrizioni",
                    data=df_aggiornato
                )

                st.success("✅ Grazie per l'iscrizione!")
                st.balloons()

        except Exception as e:
            st.error(f"❌ ERRORE: {str(e)}")
            st.code(str(e))

            st.warning("**Verifica:**")
            st.write("1. Google Sheet condiviso con service account")
            st.write("2. URL corretto (espandi DEBUG)")
            st.write("3. API abilitate su Google Cloud")

# FOOTER
st.markdown("---")
st.info("**Note**: Aliquota 5% startup, 15% ordinaria. Riduzioni per Artigiani/Commercianti.")
st.markdown("**Fisco Chiaro Consulting** | © 2025")

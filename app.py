import streamlit as st
import pandas as pd
from datetime import datetime
import locale

# Prova a impostare locale italiano
try:
    locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'it_IT')
    except:
        pass

# Configurazione pagina
st.set_page_config(
    page_title="Simulatore Regime Forfettario 2025",
    page_icon="📊",
    layout="wide"
)

# Database completo codici ATECO con coefficienti
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

def formatta_euro(valore):
    """Formatta un numero in euro con separatori italiani"""
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatta_numero(valore, decimali=0):
    """Formatta un numero con separatori italiani"""
    if decimali == 0:
        return f"{valore:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{valore:,.{decimali}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatta_percentuale(valore, decimali=2):
    """Formatta una percentuale con virgola italiana"""
    return f"{valore:.{decimali}f}%".replace(".", ",")

def get_coefficiente(codice_ateco):
    """Cerca il coefficiente per un codice ATECO"""
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
    """Calcola imposte e contributi per regime forfettario"""
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

# ============================================================================
# HEADER
# ============================================================================
st.title("📊 Simulatore Regime Forfettario 2025")
st.markdown("**by Fisco Chiaro Consulting**")
st.markdown("---")

# ============================================================================
# LAYOUT A DUE COLONNE
# ============================================================================
col1, col2 = st.columns([1, 1])

# COLONNA SINISTRA - INPUT
with col1:
    st.header("📝 Parametri Input")

    # Ricavi annui
    ricavi = st.number_input(
        "Ricavi annui (€)", 
        min_value=0, 
        max_value=85000, 
        value=50000, 
        step=1000,
        help="Inserisci i ricavi annui previsti (max 85.000€ per forfettario)"
    )

    # Metodo inserimento attività
    metodo = st.radio(
        "Come vuoi inserire l'attività?", 
        ["Codice ATECO", "Settore generico"]
    )

    # Coefficiente di redditività
    if metodo == "Codice ATECO":
        st.info("💡 Inserisci il tuo codice ATECO (es. 69.20.11, 47.11.40, 86.90.29)")
        codice_ateco = st.text_input(
            "Codice ATECO", 
            value="", 
            placeholder="es. 69.20.11 o 692011"
        )
        if codice_ateco:
            coefficiente = get_coefficiente(codice_ateco)
            if coefficiente:
                st.success(f"✅ Coefficiente trovato: **{coefficiente}%**")
            else:
                st.warning("⚠️ Codice ATECO non trovato. Uso coefficiente standard 67%")
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

    # Contributi anno precedente
    contributi_prec = st.number_input(
        "Contributi versati anno precedente (€)", 
        min_value=0, 
        max_value=30000, 
        value=5000, 
        step=500,
        help="Inserisci i contributi INPS versati l'anno scorso (deducibili dal reddito)"
    )

    # Aliquota imposta sostitutiva
    aliquota = st.radio(
        "Aliquota imposta sostitutiva", 
        [5, 15], 
        format_func=lambda x: f"{x}% - {'Startup (primi 5 anni)' if x == 5 else 'Ordinaria'}"
    )

    # Cassa previdenziale
    cassa = st.selectbox(
        "Cassa previdenziale", 
        ["Gestione Separata INPS", "Artigiani e Commercianti"]
    )

    # Riduzione contributiva (solo per Artigiani/Commercianti)
    riduzione = 0
    if cassa == "Artigiani e Commercianti":
        riduzione = st.selectbox(
            "Riduzione contributiva", 
            [0, 35, 50],
            format_func=lambda x: {
                0: "Nessuna riduzione",
                35: "Riduzione 35% (da rinnovare annualmente)",
                50: "Riduzione 50% (nuove attività 2025, primi 36 mesi)"
            }[x]
        )

# COLONNA DESTRA - RISULTATI
with col2:
    st.header("📊 Risultati")

    # Calcola risultati
    risultato = calcola_forfettario(
        ricavi, 
        coefficiente, 
        contributi_prec, 
        aliquota, 
        cassa, 
        riduzione
    )

    # Metrica principale - CON FORMATTAZIONE ITALIANA
    st.metric(
        "Tax Rate Effettivo", 
        formatta_percentuale(risultato['tax_rate']),
        help="Percentuale totale di imposte e contributi sui ricavi"
    )

    # Metriche netto - CON FORMATTAZIONE ITALIANA
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(
            "Netto Annuo", 
            formatta_euro(risultato['netto']),
            help="Guadagno netto dopo imposte e contributi"
        )
    with col_b:
        st.metric(
            "Netto Mensile", 
            formatta_euro(risultato['netto']/12),
            help="Guadagno netto medio mensile"
        )

    # Dettaglio calcolo - CON FORMATTAZIONE ITALIANA
    st.markdown("---")
    st.subheader("Dettaglio Calcolo")

    st.write(f"**Coefficiente redditività:** {coefficiente}%")
    st.write(f"**Reddito imponibile lordo:** {formatta_euro(risultato['reddito_lordo'])}")
    st.write(f"**Contributi anno prec. dedotti:** {formatta_euro(contributi_prec)}")
    st.write(f"**Reddito imponibile netto:** {formatta_euro(risultato['reddito_netto'])}")

    st.markdown("---")

    st.write(f"**Imposta sostitutiva ({aliquota}%):** {formatta_euro(risultato['imposta'])}")
    st.write(f"**Contributi INPS:** {formatta_euro(risultato['contributi'])}")

    if risultato['riduzione'] > 0:
        st.info(f"✅ Applicata riduzione contributiva del {risultato['riduzione']}%")

    st.markdown("---")
    st.write(f"**TOTALE DA VERSARE:** {formatta_euro(risultato['totale'])}")

# ============================================================================
# FOOTER CON NOTE
# ============================================================================
st.markdown("---")
st.info("""
**ℹ️ Note importanti:**
- **Aliquota 5%**: valida per 5 anni per nuove attività (requisiti da verificare)
- **Riduzione 35%**: domanda entro 28 febbraio di ogni anno
- **Riduzione 50%**: solo per nuove iscrizioni 2025, valida per 36 mesi
- Questo simulatore è indicativo. Per un calcolo preciso consulta un commercialista.
""")

st.markdown("---")
st.markdown("**Fisco Chiaro Consulting** | © 2025")
st.markdown("📧 Per consulenze personalizzate: info@fiscochiaroconsulting.it")

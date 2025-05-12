import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
import requests
import numpy as np

# Import custom modules
from agents.agent_coordinator import AgentCoordinator
from voice_commands.voice_processor import VoiceProcessor

# Backend API URL
BACKEND_URL = "http://localhost:5000/api"

# Set page configuration
st.set_page_config(
    page_title="F-RISK TEAM- Valutazione Rischi Automotive",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    /* Main background */
    .main {
        background-color: #1a1a1a;
    }
    .stApp {
        background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%);
    }
    .css-1d391kg, .css-1siy2j7 {
        background-color: #1a1a1a;
    }
    .stButton>button {
        background-color: #e63946;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #c1121f;
        color: white;
    }
    .risk-matrix {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #404040;
    }
    .team-header {
        text-align: center;
        color: #e63946;
        font-size: 2.8em;
        font-weight: 800;
        margin: 20px 0 30px 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        background: linear-gradient(45deg, #e63946, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 10px;
        border-bottom: 3px solid #e63946;
        letter-spacing: 1px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    }
    .stMarkdown {
        color: #ffffff;
    }
    /* Metrics styling */
    div[data-testid="stMetric"] {
        background-color: #2d2d2d;
        border-radius: 10px;
        padding: 16px 0 8px 0;
        margin-bottom: 8px;
        border: 1px solid #404040;
        color: #fff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] > div {
        color: #fff !important;
    }
    /* Select boxes and inputs */
    .stSelectbox, .stTextInput, .stTextArea {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .stSelectbox > div {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .stInfo {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #404040;
    }
    .stSuccess {
        background-color: #2d2d2d;
        color: #00ff00;
        border: 1px solid #404040;
    }
    .stError {
        background-color: #2d2d2d;
        color: #ff4444;
        border: 1px solid #404040;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d2d2d;
        border: 1px solid #404040;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e63946;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'risk_data' not in st.session_state:
    st.session_state.risk_data = []
    
if 'current_view' not in st.session_state:
    st.session_state.current_view = "dashboard"
    
if 'selected_level' not in st.session_state:
    st.session_state.selected_level = "Tutti i Livelli"
    
if 'voice_processor' not in st.session_state:
    st.session_state.voice_processor = VoiceProcessor()

# Function to load initial data
def load_initial_data():
    try:
        with open('data/initial_data.json', 'r') as f:
            data = json.load(f)
            # Extract all risks into a flat list
            all_risks = []
            for range_item in data["product_range"]:
                # Add strategic risks
                if "rischi_strategici" in range_item:
                    all_risks.extend(range_item["rischi_strategici"])
                
                # Add project risks
                for project in range_item.get("projects", []):
                    if "rischi_progetto" in project:
                        all_risks.extend(project["rischi_progetto"])
                    
                    # Add operational risks
                    for component in project.get("components", []):
                        if "rischi_operativi" in component:
                            all_risks.extend(component["rischi_operativi"])
            
            # Set the risk data in session state
            st.session_state.risk_data = all_risks
            return data
    except FileNotFoundError:
        st.error("File dati iniziali non trovato")
        return {"product_range": []}
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati iniziali: {str(e)}")
        return {"product_range": []}

# Function to load risk data from backend
def load_risk_data():
    try:
        response = requests.get(f"{BACKEND_URL}/risks")
        if response.status_code == 200:
            data = response.json()
            # Ensure data is a list of dictionaries
            if isinstance(data, list):
                st.session_state.risk_data = data
            else:
                st.error("Formato dati non valido dal backend")
                st.session_state.risk_data = []
        else:
            st.error("Impossibile caricare i dati dal backend")
            st.session_state.risk_data = []
    except requests.exceptions.ConnectionError:
        st.error("Impossibile connettersi al backend. Assicurati che il server Flask sia in esecuzione.")
        st.session_state.risk_data = []
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati: {str(e)}")
        st.session_state.risk_data = []

# Function to save risk data to backend
def save_risk_data():
    try:
        # Ensure risk_data is a list of dictionaries
        if not isinstance(st.session_state.risk_data, list):
            st.error("Formato dati non valido per il salvataggio")
            return
            
        response = requests.post(f"{BACKEND_URL}/risks", json=st.session_state.risk_data)
        if response.status_code != 200:
            st.error("Impossibile salvare i dati nel backend")
    except requests.exceptions.ConnectionError:
        st.error("Impossibile connettersi al backend. Assicurati che il server Flask sia in esecuzione.")
    except Exception as e:
        st.error(f"Errore nel salvataggio dei dati: {str(e)}")

# Function to create dataframe from risk data
def create_risk_dataframe():
    if not st.session_state.risk_data:
        return pd.DataFrame()
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(st.session_state.risk_data)
        
        # Calculate risk indices if not already present
        if 'RI_Cost' not in df.columns and 'Risk_Probability' in df.columns and 'Cost_Impact' in df.columns:
            df['RI_Cost'] = df['Risk_Probability'] * df['Cost_Impact']
        
        if 'RI_Time' not in df.columns and 'Risk_Probability' in df.columns and 'Time_Impact' in df.columns:
            df['RI_Time'] = df['Risk_Probability'] * df['Time_Impact']
        
        return df
    except Exception as e:
        st.error(f"Errore nella creazione del dataframe: {str(e)}")
        return pd.DataFrame()

# Initialize Agent Coordinator
@st.cache_resource
def get_agent_coordinator():
    return AgentCoordinator()

# Main application layout
def main():
    # Load data
    load_risk_data()
    initial_data = load_initial_data()
    agent_coordinator = get_agent_coordinator()
    
    # Sidebar
    with st.sidebar:
        st.title("🚗 Valutazione Rischi Automotive")
        
        # Navigation
        st.subheader("Navigazione")
        view_options = ["Dashboard", "Gestione Rischi", "Configurazione Agenti", "Comandi Vocali"]
        
        # Map current view to view options
        view_mapping = {
            "dashboard": "Dashboard",
            "gestione rischi": "Gestione Rischi",
            "configurazione agenti": "Configurazione Agenti",
            "comandi vocali": "Comandi Vocali"
        }
        
        # Get the current view in the correct format
        current_view = view_mapping.get(st.session_state.current_view, "Dashboard")
        
        selected_view = st.selectbox("Seleziona Vista", view_options, 
                                    index=view_options.index(current_view))
        
        # Map selected view back to session state format
        reverse_mapping = {v.lower(): k for k, v in view_mapping.items()}
        st.session_state.current_view = reverse_mapping.get(selected_view.lower(), "dashboard")
        
        # Filters for risk data
        st.subheader("Filtri")
        level_options = ["Tutti i Livelli", "Strategico", "Progetto", "Operativo"]
        st.session_state.selected_level = st.selectbox("Livello Rischio", level_options)
        
        # Quick actions
        st.subheader("Azioni Rapide")
        if st.button("Genera Valutazione Rischi", use_container_width=True):
            with st.spinner("Gli agenti AI stanno generando la valutazione dei rischi..."):
                # Call the agent coordinator to generate risks
                new_risks = agent_coordinator.generate_risk_assessment(initial_data)
                
                # Add new risks to existing risk data
                st.session_state.risk_data.extend(new_risks)
                try:
                    # Save each new risk to the backend
                    for risk in new_risks:
                        response = requests.post(f"{BACKEND_URL}/risks", json=risk)
                        if response.status_code != 200:
                            st.error(f"Impossibile salvare il rischio {risk.get('Risk_ID')} nel backend")
                except requests.exceptions.ConnectionError:
                    st.error("Impossibile connettersi al backend. Assicurati che il server Flask sia in esecuzione.")
                
                st.sidebar.success("Valutazione dei rischi generata con successo!")
    
    # Main content based on selected view
    if st.session_state.current_view == "dashboard":
        display_dashboard()
    elif st.session_state.current_view == "gestione rischi":
        display_risk_management(initial_data)
    elif st.session_state.current_view == "configurazione agenti":
        display_agent_configuration()
    elif st.session_state.current_view == "comandi vocali":
        display_voice_commands()

# Dashboard view
def display_dashboard():
    st.markdown('''<div class="team-header">F-RISK TEAM: DEMO PIATTAFORMA GESTIONE DEI RISCHI</div>''', unsafe_allow_html=True)
    st.header("Dashboard Rischi")
    
    df = create_risk_dataframe()
    
    if df.empty:
        st.info("Nessun dato disponibile. Genera una valutazione dei rischi per visualizzare i dati.")
        return
    
    # Filter by level if needed
    if st.session_state.selected_level != "Tutti i Livelli":
        df = df[df['Level'] == st.session_state.selected_level.lower()]
    
    # Create dashboard metrics and visualizations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Totale Rischi", len(df))
    with col2:
        if 'RI_Cost' in df.columns:
            st.metric("Indice C x I", f"€{df['RI_Cost'].mean()/10:,.2f}")
    with col3:
        if 'RI_Time' in df.columns:
            st.metric("Indice T x I", f"{df['RI_Time'].mean()/10:.2f}")
    
    st.header("Matrici di Rischio")
    # Cost Impact vs Probability Matrix
    with st.container():
        st.subheader("Matrice Rischio: Impatto Costi vs Probabilità")
        st.markdown('<div class="risk-matrix">', unsafe_allow_html=True)
        if 'Risk_Probability' in df.columns and 'Cost_Impact' in df.columns:
            # Create heatmap background (X: 0-100, Y: min-max)
            x = np.linspace(0, 100, 100)
            y = np.linspace(df['Cost_Impact'].min(), df['Cost_Impact'].max(), 100)
            xx, yy = np.meshgrid(x, y)
            zz = xx * (yy / (df['Cost_Impact'].max() if df['Cost_Impact'].max() > 0 else 1))
            # Normalize zz for color mapping (equidistributed)
            zz_norm = (zz - zz.min()) / (zz.max() - zz.min() + 1e-9)
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Heatmap(
                x=x, y=y, z=zz_norm,
                colorscale=[
                    [0.0, '#00ff00'],
                    [0.25, '#ffff00'],
                    [0.6, '#ffff00'],
                    [1.0, '#ff0000']
                ],
                showscale=False,
                opacity=0.5,
                hoverinfo='skip',
                zmin=0, zmax=1
            ))
            # Overlay risk points (use Risk_Probability as is)
            fig.add_trace(go.Scatter(
                x=df['Risk_Probability'],
                y=df['Cost_Impact'],
                mode='markers+text',
                marker=dict(size=14, color='black', line=dict(width=2, color='white')),
                text=df['Risk_Title'],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>Probabilità: %{x}%<br>Impatto Costi: %{y}<extra></extra>'
            ))
            fig.update_layout(
                xaxis=dict(
                    title='Probabilità di accadimento (%)',
                    tickvals=[0, 20, 40, 60, 80, 100],
                    ticktext=['0', '20', '40', '60', '80', '100'],
                    range=[0, 100],
                    gridcolor='#404040',
                    zerolinecolor='#404040',
                    color='white',
                ),
                yaxis=dict(
                    title='Impatto sui costi',
                    gridcolor='#404040',
                    zerolinecolor='#404040',
                    color='white',
                ),
                plot_bgcolor='#2d2d2d',
                paper_bgcolor='#2d2d2d',
                font=dict(color="white", size=12),
                margin=dict(l=40, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    # Time Impact vs Probability Matrix
    with st.container():
        st.subheader("Matrice Rischio: Impatto Tempi vs Probabilità")
        st.markdown('<div class="risk-matrix">', unsafe_allow_html=True)
        if 'Risk_Probability' in df.columns and 'Time_Impact' in df.columns:
            x = np.linspace(0, 100, 100)
            y = np.linspace(df['Time_Impact'].min(), df['Time_Impact'].max(), 100)
            xx, yy = np.meshgrid(x, y)
            zz = xx * (yy / (df['Time_Impact'].max() if df['Time_Impact'].max() > 0 else 1))
            zz_norm = (zz - zz.min()) / (zz.max() - zz.min() + 1e-9)
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Heatmap(
                x=x, y=y, z=zz_norm,
                colorscale=[
                    [0.0, '#00ff00'],
                    [0.25, '#ffff00'],
                    [0.6, '#ffff00'],
                    [1.0, '#ff0000']
                ],
                showscale=False,
                opacity=0.5,
                hoverinfo='skip',
                zmin=0, zmax=1
            ))
            fig.add_trace(go.Scatter(
                x=df['Risk_Probability'],
                y=df['Time_Impact'],
                mode='markers+text',
                marker=dict(size=14, color='black', line=dict(width=2, color='white')),
                text=df['Risk_Title'],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>Probabilità: %{x}%<br>Impatto Tempi: %{y}<extra></extra>'
            ))
            fig.update_layout(
                xaxis=dict(
                    title='Probabilità di accadimento (%)',
                    tickvals=[0, 20, 40, 60, 80, 100],
                    ticktext=['0', '20', '40', '60', '80', '100'],
                    range=[0, 100],
                    gridcolor='#404040',
                    zerolinecolor='#404040',
                    color='white',
                ),
                yaxis=dict(
                    title='Impatto sui tempi',
                    gridcolor='#404040',
                    zerolinecolor='#404040',
                    color='white',
                ),
                plot_bgcolor='#2d2d2d',
                paper_bgcolor='#2d2d2d',
                font=dict(color="white", size=12),
                margin=dict(l=40, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    # Risk distribution by level
    st.header("Distribuzione Rischi per Livello")
    if 'Level' in df.columns:
        level_counts = df['Level'].value_counts().reset_index()
        level_counts.columns = ['Livello', 'Conteggio']
        fig = px.pie(level_counts, values='Conteggio', names='Livello', 
                    title='',
                    color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig, use_container_width=True)
    # Top risks by cost impact
    st.header("Top Rischi per Impatto Costo")
    if 'RI_Cost' in df.columns and 'Risk_Title' in df.columns:
        top_cost_risks = df.sort_values('RI_Cost', ascending=False).head(5)
        fig = px.bar(top_cost_risks, x='Risk_Title', y='RI_Cost', 
                    title='',
                    color='RI_Cost',
                    color_continuous_scale=px.colors.sequential.Reds)
        st.plotly_chart(fig, use_container_width=True)
    # Top risks by time impact
    st.header("Top Rischi per Impatto Tempo")
    if 'RI_Time' in df.columns and 'Risk_Title' in df.columns:
        top_time_risks = df.sort_values('RI_Time', ascending=False).head(5)
        fig = px.bar(top_time_risks, x='Risk_Title', y='RI_Time', 
                    title='',
                    color='RI_Time',
                    color_continuous_scale=px.colors.sequential.Blues)
        st.plotly_chart(fig, use_container_width=True)

# Risk Management view
def display_risk_management(initial_data):
    st.header("Gestione Rischi")
    
    tab1, tab2 = st.tabs(["Tabella Rischi", "Aggiungi/Modifica Rischio"])
    
    with tab1:
        df = create_risk_dataframe()
        
        if df.empty:
            st.info("Nessun dato disponibile. Genera una valutazione dei rischi o aggiungi rischi manualmente.")
        else:
            # Filter by level if needed
            if st.session_state.selected_level != "Tutti i Livelli":
                df = df[df['Level'] == st.session_state.selected_level.lower()]
            
            # Display the risk table
            st.dataframe(df, use_container_width=True)
            
            # Option to download as CSV
            st.download_button(
                label="Scarica come CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='valutazione_rischi.csv',
                mime='text/csv',
            )
    
    with tab2:
        st.subheader("Aggiungi o Modifica Rischio")
        
        # Form for adding/editing risks
        with st.form("risk_form"):
            # Basic risk information
            col1, col2 = st.columns(2)
            
            with col1:
                risk_id = st.text_input("ID Rischio", value=f"R{len(st.session_state.risk_data) + 1}")
                level = st.selectbox("Livello", ["strategico", "progetto", "operativo"])
                
                # Dynamically generate project options based on level
                project_options = []
                if level == "strategico":
                    project_options = [range_item["name"] for range_item in initial_data["product_range"]]
                elif level == "progetto":
                    project_options = [project["name"] for range_item in initial_data["product_range"] 
                                     for project in range_item["projects"]]
                elif level == "operativo":
                    project_options = [component["name"] for range_item in initial_data["product_range"] 
                                     for project in range_item["projects"]
                                     for component in project["components"]]
                
                project = st.selectbox("Progetto/Componente", project_options if project_options else ["Non Disponibile"])
                owner = st.text_input("Proprietario")
            
            with col2:
                risk_title = st.text_input("Titolo Rischio")
                risk_description = st.text_area("Descrizione Rischio")
            
            # Risk assessment
            st.subheader("Valutazione Rischio")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                risk_probability = st.slider("Probabilità Rischio (0-1)", 0.0, 1.0, 0.5, 0.01)
            
            with col2:
                cost_impact = st.number_input("Impatto Costo (€)", 0, 10000000, 100000, 10000)
            
            with col3:
                time_impact = st.slider("Impatto Tempo (settimane)", 0, 52, 4, 1)
            
            # Automatic calculation of risk indices
            ri_cost = risk_probability * cost_impact
            ri_time = risk_probability * time_impact
            
            st.metric("Indice Rischio - Costo", f"€{ri_cost:,.2f}")
            st.metric("Indice Rischio - Tempo", f"{ri_time:.2f} settimane")
            
            # Detection and mitigation
            detection = st.slider("Capacità di Rilevamento (0-1)", 0.0, 1.0, 0.5, 0.01, 
                                help="Quanto facilmente può essere rilevato questo rischio? 0 = Molto difficile, 1 = Molto facile")
            mitigation_plan = st.text_area("Piano di Mitigazione")
            
            submitted = st.form_submit_button("Salva Rischio")
            
            if submitted:
                # Create risk item
                risk_item = {
                    "Risk_ID": risk_id,
                    "Level": level,
                    "Project": project,
                    "Owner": owner,
                    "Risk_Title": risk_title,
                    "Risk_Description": risk_description,
                    "Risk_Probability": risk_probability,
                    "Cost_Impact": cost_impact,
                    "Time_Impact": time_impact,
                    "RI_Cost": ri_cost,
                    "RI_Time": ri_time,
                    "Detection": detection,
                    "Mitigation_Plan": mitigation_plan
                }
                
                # Check if risk ID already exists (for editing)
                existing_index = next((i for i, item in enumerate(st.session_state.risk_data) 
                                     if item.get("Risk_ID") == risk_id), None)
                
                if existing_index is not None:
                    st.session_state.risk_data[existing_index] = risk_item
                    st.success(f"Rischio {risk_id} aggiornato con successo!")
                else:
                    st.session_state.risk_data.append(risk_item)
                    st.success(f"Rischio {risk_id} aggiunto con successo!")
                
                save_risk_data()

# AI Agent Configuration view
def display_agent_configuration():
    st.header("Configurazione Agenti AI")
    
    st.info("""
    Configura gli agenti AI che aiutano a generare e analizzare la valutazione dei rischi.
    Ogni agente si specializza in un aspetto diverso della valutazione dei rischi.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agente Ricerca Web")
        st.write("Questo agente cerca sul web i rischi comuni nel settore automotive basati su componenti e progetti.")
        enable_web_search = st.toggle("Abilita Agente Ricerca Web", value=True)
        web_search_temperature = st.slider("Creatività (Temperatura)", 0.0, 1.0, 0.7, 0.1, 
                                          help="Valori più alti rendono l'output più creativo, valori più bassi più deterministici")
    
    with col2:
        st.subheader("Agente Valutazione Rischi")
        st.write("Questo agente valuta i rischi in termini di probabilità, costo e impatto temporale.")
        enable_risk_evaluation = st.toggle("Abilita Agente Valutazione Rischi", value=True)
        risk_eval_temperature = st.slider("Precisione (Temperatura)", 0.0, 1.0, 0.3, 0.1,
                                        help="Valori più bassi forniscono valutazioni dei rischi più consistenti")
    
    st.subheader("Agente Pianificazione Mitigazione")
    st.write("Questo agente suggerisce piani di mitigazione per i rischi identificati.")
    enable_mitigation = st.toggle("Abilita Agente Pianificazione Mitigazione", value=True)
    mitigation_temperature = st.slider("Creatività per Piani di Mitigazione (Temperatura)", 0.0, 1.0, 0.6, 0.1)
    
    st.subheader("Configurazione Avanzata")
    api_key = st.text_input("Chiave API OpenAI (opzionale, usa il file .env se non fornita)", 
                           type="password", help="La tua chiave API OpenAI per gli agenti")
    
    if st.button("Salva Configurazione"):
        # Save the configuration
        config = {
            "web_search_agent": {
                "enabled": enable_web_search,
                "temperature": web_search_temperature
            },
            "risk_evaluation_agent": {
                "enabled": enable_risk_evaluation,
                "temperature": risk_eval_temperature
            },
            "mitigation_agent": {
                "enabled": enable_mitigation,
                "temperature": mitigation_temperature
            },
            "api_key": api_key if api_key else None
        }
        
        Path("config").mkdir(exist_ok=True)
        with open('config/agent_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        st.success("Configurazione agenti salvata con successo!")

# Voice Commands view
def display_voice_commands():
    st.header("Comandi Vocali")
    
    st.info("""
    Usa i comandi vocali per controllare l'applicazione di valutazione dei rischi.
    Clicca il pulsante qui sotto e pronuncia il tuo comando.
    
    Esempi di comandi:
    - "Genera valutazione rischi"
    - "Mostra dashboard"
    - "Filtra per livello strategico"
    - "Mostra rischi principali"
    """)
    
    voice_processor = st.session_state.voice_processor
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Inizia Comando Vocale", use_container_width=True):
            with st.spinner("In ascolto..."):
                command = voice_processor.listen_for_command()
                if command:
                    st.success(f"Comando rilevato: {command}")
                    # Process the command
                    result = voice_processor.process_command(command)
                    st.write(f"Risultato: {result}")
                    
                    # Execute the command
                    if result["success"]:
                        action = result["action"]
                        if action == "show_dashboard":
                            st.session_state.current_view = "dashboard"
                            st.experimental_rerun()
                        elif action == "show_risk_management":
                            st.session_state.current_view = "gestione rischi"
                            st.experimental_rerun()
                        elif action == "show_agent_configuration":
                            st.session_state.current_view = "configurazione agenti"
                            st.experimental_rerun()
                        elif action == "show_voice_commands":
                            st.session_state.current_view = "comandi vocali"
                            st.experimental_rerun()
                        elif action == "filter_strategic":
                            st.session_state.selected_level = "Strategico"
                            st.experimental_rerun()
                        elif action == "filter_project":
                            st.session_state.selected_level = "Progetto"
                            st.experimental_rerun()
                        elif action == "filter_operational":
                            st.session_state.selected_level = "Operativo"
                            st.experimental_rerun()
                        elif action == "show_all_risks":
                            st.session_state.selected_level = "Tutti i Livelli"
                            st.experimental_rerun()
                        elif action == "save_data":
                            save_risk_data()
                            st.success("Dati salvati con successo!")
                        elif action == "generate_risk_assessment":
                            # Trigger the risk assessment generation
                            st.session_state.generate_risk = True
                            st.experimental_rerun()
                else:
                    st.error("Impossibile riconoscere il comando. Riprova.")
    
    with col2:
        st.subheader("Comandi Disponibili")
        st.write("""
        - "Genera valutazione rischi"
        - "Mostra dashboard"
        - "Mostra gestione rischi"
        - "Mostra configurazione agenti"
        - "Filtra per livello strategico"
        - "Filtra per livello progetto"
        - "Filtra per livello operativo"
        - "Mostra tutti i rischi"
        - "Salva i dati"
        """)
    
    st.subheader("Cronologia Comandi")
    if hasattr(voice_processor, 'command_history') and voice_processor.command_history:
        for i, (command, timestamp) in enumerate(voice_processor.command_history):
            st.text(f"{timestamp}: {command}")
    else:
        st.write("Nessun comando ancora. Prova a pronunciare un comando!")

if __name__ == "__main__":
    main() 
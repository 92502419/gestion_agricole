import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Configuration de la page
st.set_page_config(
    page_title="🌱 MonPlanting - Journal Agricole",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
def load_custom_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .alert-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .info-card {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196F3;
    }
    </style>
    """, unsafe_allow_html=True)

# Classe pour la gestion de la base de données
class DatabaseManager:
    def __init__(self, db_path: str = "monplanting.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des parcelles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcelles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                surface REAL,
                location TEXT,
                soil_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Table des activités
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcelle_id INTEGER,
                activity_type TEXT NOT NULL,
                date DATE NOT NULL,
                crop_type TEXT,
                variety TEXT,
                quantity REAL,
                unit TEXT,
                notes TEXT,
                cost REAL,
                weather_conditions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parcelle_id) REFERENCES parcelles (id)
            )
        """)
        
        # Table des rappels
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcelle_id INTEGER,
                activity_type TEXT NOT NULL,
                reminder_date DATE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parcelle_id) REFERENCES parcelles (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hache le mot de passe"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str) -> bool:
        """Crée un nouvel utilisateur"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authentifie un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute("""
            SELECT id, username, email FROM users 
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        return None
    
    def get_user_parcelles(self, user_id: int) -> List[Dict]:
        """Récupère les parcelles d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, surface, location, soil_type, description, created_at
            FROM parcelles WHERE user_id = ?
        """, (user_id,))
        
        parcelles = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': p[0],
                'name': p[1],
                'surface': p[2],
                'location': p[3],
                'soil_type': p[4],
                'description': p[5],
                'created_at': p[6]
            }
            for p in parcelles
        ]
    
    def create_parcelle(self, user_id: int, name: str, surface: float, 
                       location: str, soil_type: str, description: str) -> bool:
        """Crée une nouvelle parcelle"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO parcelles (user_id, name, surface, location, soil_type, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, name, surface, location, soil_type, description))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def get_parcelle_activities(self, parcelle_id: int) -> List[Dict]:
        """Récupère les activités d'une parcelle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, activity_type, date, crop_type, variety, quantity, 
                   unit, notes, cost, weather_conditions, created_at
            FROM activities WHERE parcelle_id = ?
            ORDER BY date DESC
        """, (parcelle_id,))
        
        activities = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': a[0],
                'activity_type': a[1],
                'date': a[2],
                'crop_type': a[3],
                'variety': a[4],
                'quantity': a[5],
                'unit': a[6],
                'notes': a[7],
                'cost': a[8],
                'weather_conditions': a[9],
                'created_at': a[10]
            }
            for a in activities
        ]
    
    def add_activity(self, parcelle_id: int, activity_type: str, date: str,
                    crop_type: str, variety: str, quantity: float, unit: str,
                    notes: str, cost: float, weather_conditions: str) -> bool:
        """Ajoute une nouvelle activité"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO activities (parcelle_id, activity_type, date, crop_type, 
                                     variety, quantity, unit, notes, cost, weather_conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (parcelle_id, activity_type, date, crop_type, variety, 
                  quantity, unit, notes, cost, weather_conditions))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def get_reminders(self, parcelle_id: int) -> List[Dict]:
        """Récupère les rappels d'une parcelle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, activity_type, reminder_date, title, description, is_completed
            FROM reminders WHERE parcelle_id = ?
            ORDER BY reminder_date ASC
        """, (parcelle_id,))
        
        reminders = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'activity_type': r[1],
                'reminder_date': r[2],
                'title': r[3],
                'description': r[4],
                'is_completed': bool(r[5])
            }
            for r in reminders
        ]
    
    def add_reminder(self, parcelle_id: int, activity_type: str, reminder_date: str,
                    title: str, description: str) -> bool:
        """Ajoute un nouveau rappel"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO reminders (parcelle_id, activity_type, reminder_date, title, description)
                VALUES (?, ?, ?, ?, ?)
            """, (parcelle_id, activity_type, reminder_date, title, description))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def complete_reminder(self, reminder_id: int) -> bool:
        """Marque un rappel comme terminé"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE reminders SET is_completed = TRUE WHERE id = ?
            """, (reminder_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

# Classe principale de l'application
class MonPlantingApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_session_state()
    
    def init_session_state(self):
        """Initialise les variables de session"""
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "dashboard"
    
    def login_page(self):
        """Page de connexion"""
        st.markdown("""
        <div class="main-header">
            <h1>🌱 MonPlanting</h1>
            <p>Votre journal personnel de plantation agricole</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab1:
            st.subheader("Connexion")
            with st.form("login_form"):
                username = st.text_input("Nom d'utilisateur")
                password = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button("Se connecter")
                
                if submitted:
                    user = self.db.authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success("Connexion réussie!")
                        st.rerun()
                    else:
                        st.error("Nom d'utilisateur ou mot de passe incorrect")
        
        with tab2:
            st.subheader("Inscription")
            with st.form("register_form"):
                new_username = st.text_input("Nom d'utilisateur*")
                new_email = st.text_input("Email*")
                new_password = st.text_input("Mot de passe*", type="password")
                confirm_password = st.text_input("Confirmer le mot de passe*", type="password")
                submitted = st.form_submit_button("S'inscrire")
                
                if submitted:
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.error("Tous les champs sont obligatoires")
                    elif new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas")
                    elif len(new_password) < 6:
                        st.error("Le mot de passe doit contenir au moins 6 caractères")
                    elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', new_email):
                        st.error("Format d'email invalide")
                    else:
                        if self.db.create_user(new_username, new_email, new_password):
                            st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")
                        else:
                            st.error("Nom d'utilisateur ou email déjà utilisé")
    
    def dashboard(self):
        """Tableau de bord principal"""
        st.markdown(f"""
        <div class="main-header">
            <h1>🌱 Tableau de Bord</h1>
            <p>Bienvenue {st.session_state.user['username']}!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistiques générales
        parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🏞️ Parcelles</h3>
                <h2>{}</h2>
            </div>
            """.format(len(parcelles)), unsafe_allow_html=True)
        
        with col2:
            total_surface = sum(p['surface'] for p in parcelles if p['surface'])
            st.markdown("""
            <div class="metric-card">
                <h3>📏 Surface Totale</h3>
                <h2>{:.1f} ha</h2>
            </div>
            """.format(total_surface), unsafe_allow_html=True)
        
        # Calculer les activités récentes
        recent_activities = 0
        for parcelle in parcelles:
            activities = self.db.get_parcelle_activities(parcelle['id'])
            recent_activities += len([a for a in activities if 
                                    datetime.strptime(a['date'], '%Y-%m-%d') >= datetime.now() - timedelta(days=7)])
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>📅 Activités (7j)</h3>
                <h2>{}</h2>
            </div>
            """.format(recent_activities), unsafe_allow_html=True)
        
        # Rappels en attente
        pending_reminders = 0
        for parcelle in parcelles:
            reminders = self.db.get_reminders(parcelle['id'])
            pending_reminders += len([r for r in reminders if not r['is_completed']])
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>🔔 Rappels</h3>
                <h2>{}</h2>
            </div>
            """.format(pending_reminders), unsafe_allow_html=True)
        
        # Graphiques
        if parcelles:
            st.subheader("📊 Analyse des Activités")
            
            # Collecte des données pour les graphiques
            all_activities = []
            for parcelle in parcelles:
                activities = self.db.get_parcelle_activities(parcelle['id'])
                for activity in activities:
                    activity['parcelle_name'] = parcelle['name']
                    all_activities.append(activity)
            
            if all_activities:
                df_activities = pd.DataFrame(all_activities)
                df_activities['date'] = pd.to_datetime(df_activities['date'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Graphique des activités par type
                    activity_counts = df_activities['activity_type'].value_counts()
                    fig_pie = px.pie(
                        values=activity_counts.values,
                        names=activity_counts.index,
                        title="Répartition des Types d'Activités"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Graphique temporel des activités
                    df_timeline = df_activities.groupby(df_activities['date'].dt.date).size().reset_index()
                    df_timeline.columns = ['date', 'count']
                    
                    fig_line = px.line(
                        df_timeline,
                        x='date',
                        y='count',
                        title="Évolution des Activités dans le Temps"
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
        
        # Rappels urgents
        if pending_reminders > 0:
            st.subheader("🚨 Rappels Urgents")
            urgent_reminders = []
            for parcelle in parcelles:
                reminders = self.db.get_reminders(parcelle['id'])
                for reminder in reminders:
                    if not reminder['is_completed']:
                        reminder_date = datetime.strptime(reminder['reminder_date'], '%Y-%m-%d')
                        if reminder_date <= datetime.now() + timedelta(days=3):
                            reminder['parcelle_name'] = parcelle['name']
                            urgent_reminders.append(reminder)
            
            if urgent_reminders:
                for reminder in urgent_reminders:
                    days_left = (datetime.strptime(reminder['reminder_date'], '%Y-%m-%d') - datetime.now()).days
                    if days_left <= 0:
                        urgency_class = "alert-message"
                        urgency_text = "⚠️ EN RETARD"
                    elif days_left <= 1:
                        urgency_class = "alert-message"
                        urgency_text = "🔴 URGENT"
                    else:
                        urgency_class = "info-card"
                        urgency_text = f"🟡 Dans {days_left} jours"
                    
                    st.markdown(f"""
                    <div class="{urgency_class}">
                        <strong>{urgency_text}</strong><br>
                        <strong>{reminder['title']}</strong> - {reminder['parcelle_name']}<br>
                        {reminder['description']}<br>
                        <em>Prévu le: {reminder['reminder_date']}</em>
                    </div>
                    """, unsafe_allow_html=True)
    
    def parcelles_page(self):
        """Page de gestion des parcelles"""
        st.markdown("""
        <div class="main-header">
            <h1>🏞️ Gestion des Parcelles</h1>
            <p>Gérez vos terrains agricoles</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 Mes Parcelles", "➕ Ajouter Parcelle"])
        
        with tab1:
            parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
            
            if parcelles:
                for parcelle in parcelles:
                    with st.expander(f"🏞️ {parcelle['name']} ({parcelle['surface']} ha)"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Localisation:** {parcelle['location']}")
                            st.write(f"**Type de sol:** {parcelle['soil_type']}")
                            st.write(f"**Surface:** {parcelle['surface']} hectares")
                        
                        with col2:
                            st.write(f"**Description:** {parcelle['description']}")
                            st.write(f"**Créée le:** {parcelle['created_at']}")
                        
                        if st.button(f"Voir les activités", key=f"view_{parcelle['id']}"):
                            st.session_state.current_page = "activities"
                            st.session_state.selected_parcelle = parcelle['id']
                            st.rerun()
            else:
                st.info("Aucune parcelle créée. Ajoutez votre première parcelle!")
        
        with tab2:
            st.subheader("Ajouter une nouvelle parcelle")
            
            with st.form("add_parcelle_form"):
                name = st.text_input("Nom de la parcelle*")
                surface = st.number_input("Surface (hectares)*", min_value=0.01, step=0.01)
                location = st.text_input("Localisation*")
                soil_type = st.selectbox("Type de sol*", [
                    "Argile", "Limon", "Sable", "Argilo-limoneux", 
                    "Argilo-sableux", "Limono-sableux", "Autre"
                ])
                description = st.text_area("Description")
                
                submitted = st.form_submit_button("Ajouter la parcelle")
                
                if submitted:
                    if not all([name, surface, location, soil_type]):
                        st.error("Tous les champs marqués d'un * sont obligatoires")
                    else:
                        if self.db.create_parcelle(
                            st.session_state.user['id'], name, surface, 
                            location, soil_type, description
                        ):
                            st.success("Parcelle ajoutée avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout de la parcelle")
    
    def activities_page(self):
        """Page de gestion des activités"""
        st.markdown("""
        <div class="main-header">
            <h1>📝 Gestion des Activités</h1>
            <p>Suivez vos activités agricoles</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sélection de parcelle
        parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
        
        if not parcelles:
            st.warning("Aucune parcelle disponible. Créez d'abord une parcelle.")
            return
        
        selected_parcelle_id = st.selectbox(
            "Sélectionnez une parcelle",
            options=[p['id'] for p in parcelles],
            format_func=lambda x: next(p['name'] for p in parcelles if p['id'] == x)
        )
        
        if 'selected_parcelle' in st.session_state:
            selected_parcelle_id = st.session_state.selected_parcelle
        
        tab1, tab2 = st.tabs(["📋 Historique", "➕ Ajouter Activité"])
        
        with tab1:
            activities = self.db.get_parcelle_activities(selected_parcelle_id)
            
            if activities:
                # Filtres
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    activity_types = list(set(a['activity_type'] for a in activities))
                    selected_type = st.selectbox("Filtrer par type", ["Tous"] + activity_types)
                
                with col2:
                    crop_types = list(set(a['crop_type'] for a in activities if a['crop_type']))
                    selected_crop = st.selectbox("Filtrer par culture", ["Tous"] + crop_types)
                
                with col3:
                    date_range = st.date_input("Période", value=[])
                
                # Filtrage des activités
                filtered_activities = activities
                if selected_type != "Tous":
                    filtered_activities = [a for a in filtered_activities if a['activity_type'] == selected_type]
                if selected_crop != "Tous":
                    filtered_activities = [a for a in filtered_activities if a['crop_type'] == selected_crop]
                
                # Affichage des activités
                for activity in filtered_activities:
                    with st.expander(f"{activity['activity_type']} - {activity['date']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Type:** {activity['activity_type']}")
                            st.write(f"**Date:** {activity['date']}")
                            if activity['crop_type']:
                                st.write(f"**Culture:** {activity['crop_type']}")
                            if activity['variety']:
                                st.write(f"**Variété:** {activity['variety']}")
                        
                        with col2:
                            if activity['quantity']:
                                st.write(f"**Quantité:** {activity['quantity']} {activity['unit']}")
                            if activity['cost']:
                                st.write(f"**Coût:** {activity['cost']} €")
                            if activity['weather_conditions']:
                                st.write(f"**Météo:** {activity['weather_conditions']}")
                        
                        if activity['notes']:
                            st.write(f"**Notes:** {activity['notes']}")
                
                # Graphiques d'analyse
                if len(filtered_activities) > 1:
                    st.subheader("📊 Analyse des Activités")
                    
                    df_activities = pd.DataFrame(filtered_activities)
                    
                    # Graphique des coûts par activité
                    if 'cost' in df_activities.columns:
                        cost_data = df_activities[df_activities['cost'].notna()]
                        if not cost_data.empty:
                            fig_costs = px.bar(
                                cost_data,
                                x='date',
                                y='cost',
                                color='activity_type',
                                title="Évolution des Coûts par Activité"
                            )
                            st.plotly_chart(fig_costs, use_container_width=True)
            else:
                st.info("Aucune activité enregistrée pour cette parcelle.")
        
        with tab2:
            st.subheader("Ajouter une nouvelle activité")
            
            with st.form("add_activity_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    activity_type = st.selectbox("Type d'activité*", [
                        "Semis", "Plantation", "Arrosage", "Fertilisation", 
                        "Traitement", "Désherbage", "Récolte", "Labour", 
                        "Binage", "Autre"
                    ])
                    date = st.date_input("Date*", value=datetime.now())
                    crop_type = st.text_input("Type de culture")
                    variety = st.text_input("Variété")
                    quantity = st.number_input("Quantité", min_value=0.0, step=0.1)
                
                with col2:
                    unit = st.selectbox("Unité", ["kg", "g", "L", "mL", "pièces", "m²", "ha"])
                    cost = st.number_input("Coût (€)", min_value=0.0, step=0.01)
                    weather_conditions = st.selectbox("Conditions météo", [
                        "Ensoleillé", "Nuageux", "Pluvieux", "Orageux", "Venteux", "Brumeux"
                    ])
                    notes = st.text_area("Notes")
                
                submitted = st.form_submit_button("Ajouter l'activité")
                
                if submitted:
                    if not all([activity_type, date]):
                        st.error("Les champs marqués d'un * sont obligatoires")
                    else:
                        if self.db.add_activity(
                            selected_parcelle_id, activity_type, str(date),
                            crop_type, variety, quantity, unit, notes, cost, weather_conditions
                        ):
                            st.success("Activité ajoutée avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout de l'activité")
    
    def reminders_page(self):
        """Page de gestion des rappels"""
        st.markdown("""
        <div class="main-header">
            <h1>🔔 Gestion des Rappels</h1>
            <p>Programmez vos tâches agricoles</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sélection de parcelle
        parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
        
        if not parcelles:
            st.warning("Aucune parcelle disponible. Créez d'abord une parcelle.")
            return
        
        selected_parcelle_id = st.selectbox(
            "Sélectionnez une parcelle",
            options=[p['id'] for p in parcelles],
            format_func=lambda x: next(p['name'] for p in parcelles if p['id'] == x)
        )
        
        tab1, tab2 = st.tabs(["📋 Mes Rappels", "➕ Ajouter Rappel"])
        
        with tab1:
            reminders = self.db.get_reminders(selected_parcelle_id)
            
            if reminders:
                # Séparer les rappels en attente et terminés
                pending_reminders = [r for r in reminders if not r['is_completed']]
                completed_reminders = [r for r in reminders if r['is_completed']]
                
                # Rappels en attente
                if pending_reminders:
                    st.subheader("⏳ Rappels en attente")
                    for reminder in pending_reminders:
                        reminder_date = datetime.strptime(reminder['reminder_date'], '%Y-%m-%d')
                        days_left = (reminder_date - datetime.now()).days
                        
                        if days_left < 0:
                            urgency_icon = "🔴"
                            urgency_text = f"EN RETARD ({abs(days_left)} jours)"
                        elif days_left == 0:
                            urgency_icon = "⚠️"
                            urgency_text = "AUJOURD'HUI"
                        elif days_left <= 3:
                            urgency_icon = "🟡"
                            urgency_text = f"Dans {days_left} jours"
                        else:
                            urgency_icon = "🟢"
                            urgency_text = f"Dans {days_left} jours"
                        
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"""
                            **{urgency_icon} {reminder['title']}**  
                            *{reminder['activity_type']}* - {reminder['reminder_date']}  
                            {reminder['description']}  
                            **{urgency_text}**
                            """)
                        
                        with col2:
                            if st.button("✅ Terminer", key=f"complete_{reminder['id']}"):
                                if self.db.complete_reminder(reminder['id']):
                                    st.success("Rappel marqué comme terminé!")
                                    st.rerun()
                        
                        st.divider()
                
                # Rappels terminés
                if completed_reminders:
                    with st.expander(f"✅ Rappels terminés ({len(completed_reminders)})"):
                        for reminder in completed_reminders:
                            st.markdown(f"""
                            **{reminder['title']}** ✅  
                            *{reminder['activity_type']}* - {reminder['reminder_date']}  
                            {reminder['description']}
                            """)
                            st.divider()
            else:
                st.info("Aucun rappel programmé pour cette parcelle.")
        
        with tab2:
            st.subheader("Programmer un nouveau rappel")
            
            with st.form("add_reminder_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    activity_type = st.selectbox("Type d'activité*", [
                        "Semis", "Plantation", "Arrosage", "Fertilisation", 
                        "Traitement", "Désherbage", "Récolte", "Labour", 
                        "Binage", "Inspection", "Autre"
                    ])
                    reminder_date = st.date_input("Date du rappel*", value=datetime.now() + timedelta(days=1))
                
                with col2:
                    title = st.text_input("Titre du rappel*")
                    description = st.text_area("Description")
                
                submitted = st.form_submit_button("Ajouter le rappel")
                
                if submitted:
                    if not all([activity_type, reminder_date, title]):
                        st.error("Les champs marqués d'un * sont obligatoires")
                    else:
                        if self.db.add_reminder(
                            selected_parcelle_id, activity_type, str(reminder_date),
                            title, description
                        ):
                            st.success("Rappel ajouté avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout du rappel")
    
    def calendar_page(self):
        """Page calendrier"""
        st.markdown("""
        <div class="main-header">
            <h1>📅 Calendrier Agricole</h1>
            <p>Vue d'ensemble de vos activités et rappels</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sélection du mois
        col1, col2 = st.columns(2)
        
        with col1:
            selected_month = st.selectbox("Mois", [
                "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
            ], index=datetime.now().month - 1)
        
        with col2:
            selected_year = st.selectbox("Année", 
                list(range(datetime.now().year - 2, datetime.now().year + 3)),
                index=2)
        
        # Récupération des données
        parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
        all_activities = []
        all_reminders = []
        
        for parcelle in parcelles:
            activities = self.db.get_parcelle_activities(parcelle['id'])
            reminders = self.db.get_reminders(parcelle['id'])
            
            for activity in activities:
                activity['parcelle_name'] = parcelle['name']
                activity['type'] = 'activité'
                all_activities.append(activity)
            
            for reminder in reminders:
                reminder['parcelle_name'] = parcelle['name']
                reminder['type'] = 'rappel'
                all_reminders.append(reminder)
        
        # Filtrage par mois
        month_num = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"].index(selected_month) + 1
        
        filtered_activities = []
        filtered_reminders = []
        
        for activity in all_activities:
            activity_date = datetime.strptime(activity['date'], '%Y-%m-%d')
            if activity_date.month == month_num and activity_date.year == selected_year:
                filtered_activities.append(activity)
        
        for reminder in all_reminders:
            reminder_date = datetime.strptime(reminder['reminder_date'], '%Y-%m-%d')
            if reminder_date.month == month_num and reminder_date.year == selected_year:
                filtered_reminders.append(reminder)
        
        # Affichage du calendrier
        if filtered_activities or filtered_reminders:
            # Créer un DataFrame pour le calendrier
            calendar_data = []
            
            for activity in filtered_activities:
                calendar_data.append({
                    'date': activity['date'],
                    'title': f"📝 {activity['activity_type']}",
                    'description': f"{activity['parcelle_name']} - {activity.get('crop_type', 'N/A')}",
                    'type': 'Activité',
                    'color': '#4CAF50'
                })
            
            for reminder in filtered_reminders:
                status = "✅" if reminder['is_completed'] else "⏳"
                calendar_data.append({
                    'date': reminder['reminder_date'],
                    'title': f"{status} {reminder['title']}",
                    'description': f"{reminder['parcelle_name']} - {reminder['activity_type']}",
                    'type': 'Rappel',
                    'color': '#FF9800' if not reminder['is_completed'] else '#4CAF50'
                })
            
            # Tri par date
            calendar_data.sort(key=lambda x: x['date'])
            
            # Affichage en liste
            for item in calendar_data:
                item_date = datetime.strptime(item['date'], '%Y-%m-%d')
                day_name = item_date.strftime('%A')
                day_names = {
                    'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
                    'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi',
                    'Sunday': 'Dimanche'
                }
                
                st.markdown(f"""
                <div style="background: {item['color']}20; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid {item['color']};">
                    <strong>{item['title']}</strong><br>
                    <em>{day_names[day_name]} {item_date.strftime('%d/%m/%Y')}</em><br>
                    {item['description']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"Aucune activité ou rappel pour {selected_month} {selected_year}")
    
    def analytics_page(self):
        """Page d'analyse et statistiques"""
        st.markdown("""
        <div class="main-header">
            <h1>📊 Analyses et Statistiques</h1>
            <p>Analysez vos données agricoles</p>
        </div>
        """, unsafe_allow_html=True)
        
        parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
        
        if not parcelles:
            st.warning("Aucune parcelle disponible pour l'analyse.")
            return
        
        # Collecte des données
        all_activities = []
        for parcelle in parcelles:
            activities = self.db.get_parcelle_activities(parcelle['id'])
            for activity in activities:
                activity['parcelle_name'] = parcelle['name']
                all_activities.append(activity)
        
        if not all_activities:
            st.info("Aucune activité enregistrée pour l'analyse.")
            return
        
        df_activities = pd.DataFrame(all_activities)
        df_activities['date'] = pd.to_datetime(df_activities['date'])
        df_activities['month'] = df_activities['date'].dt.month
        df_activities['year'] = df_activities['date'].dt.year
        
        # Métriques principales
        st.subheader("📈 Métriques Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_activities = len(df_activities)
            st.metric("Total Activités", total_activities)
        
        with col2:
            total_cost = df_activities['cost'].sum()
            st.metric("Coût Total", f"{total_cost:.2f} €")
        
        with col3:
            avg_cost = df_activities['cost'].mean()
            st.metric("Coût Moyen", f"{avg_cost:.2f} €")
        
        with col4:
            most_common_activity = df_activities['activity_type'].mode().iloc[0]
            st.metric("Activité Principale", most_common_activity)
        
        # Graphiques détaillés
        st.subheader("📊 Analyses Détaillées")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔄 Activités", "💰 Coûts", "📅 Temporel", "🏞️ Parcelles"])
        
        with tab1:
            # Répartition des activités
            activity_counts = df_activities['activity_type'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    values=activity_counts.values,
                    names=activity_counts.index,
                    title="Répartition des Types d'Activités"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                fig_bar = px.bar(
                    x=activity_counts.index,
                    y=activity_counts.values,
                    title="Nombre d'Activités par Type"
                )
                fig_bar.update_layout(xaxis_title="Type d'Activité", yaxis_title="Nombre")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab2:
            # Analyse des coûts
            cost_data = df_activities[df_activities['cost'] > 0]
            
            if not cost_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    cost_by_activity = cost_data.groupby('activity_type')['cost'].sum().sort_values(ascending=False)
                    fig_cost_bar = px.bar(
                        x=cost_by_activity.index,
                        y=cost_by_activity.values,
                        title="Coûts par Type d'Activité"
                    )
                    fig_cost_bar.update_layout(xaxis_title="Type d'Activité", yaxis_title="Coût (€)")
                    st.plotly_chart(fig_cost_bar, use_container_width=True)
                
                with col2:
                    monthly_costs = cost_data.groupby(['year', 'month'])['cost'].sum().reset_index()
                    monthly_costs['date'] = pd.to_datetime(monthly_costs[['year', 'month']].assign(day=1))
                    
                    fig_cost_line = px.line(
                        monthly_costs,
                        x='date',
                        y='cost',
                        title="Évolution des Coûts Mensuels"
                    )
                    fig_cost_line.update_layout(xaxis_title="Date", yaxis_title="Coût (€)")
                    st.plotly_chart(fig_cost_line, use_container_width=True)
            else:
                st.info("Aucune donnée de coût disponible pour l'analyse.")
        
        with tab3:
            # Analyse temporelle
            monthly_activities = df_activities.groupby(['year', 'month']).size().reset_index(name='count')
            monthly_activities['date'] = pd.to_datetime(monthly_activities[['year', 'month']].assign(day=1))
            
            fig_timeline = px.line(
                monthly_activities,
                x='date',
                y='count',
                title="Évolution du Nombre d'Activités"
            )
            fig_timeline.update_layout(xaxis_title="Date", yaxis_title="Nombre d'Activités")
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Heatmap des activités par mois
            activity_heatmap = df_activities.pivot_table(
                index='activity_type',
                columns='month',
                values='id',
                aggfunc='count',
                fill_value=0
            )
            
            fig_heatmap = px.imshow(
                activity_heatmap,
                title="Répartition des Activités par Mois",
                labels=dict(x="Mois", y="Type d'Activité", color="Nombre")
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with tab4:
            # Analyse par parcelle
            parcelle_activities = df_activities.groupby('parcelle_name').size().sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_parcelle_bar = px.bar(
                    x=parcelle_activities.index,
                    y=parcelle_activities.values,
                    title="Nombre d'Activités par Parcelle"
                )
                fig_parcelle_bar.update_layout(xaxis_title="Parcelle", yaxis_title="Nombre d'Activités")
                st.plotly_chart(fig_parcelle_bar, use_container_width=True)
            
            with col2:
                parcelle_costs = df_activities[df_activities['cost'] > 0].groupby('parcelle_name')['cost'].sum().sort_values(ascending=False)
                
                if not parcelle_costs.empty:
                    fig_parcelle_cost = px.bar(
                        x=parcelle_costs.index,
                        y=parcelle_costs.values,
                        title="Coûts par Parcelle"
                    )
                    fig_parcelle_cost.update_layout(xaxis_title="Parcelle", yaxis_title="Coût (€)")
                    st.plotly_chart(fig_parcelle_cost, use_container_width=True)
                else:
                    st.info("Aucune donnée de coût par parcelle disponible.")
    
    def run(self):
        """Fonction principale pour lancer l'application"""
        load_custom_css()
        
        if not st.session_state.logged_in:
            self.login_page()
            return
        
        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 1rem;">
                <h3>👋 Bienvenue</h3>
                <p><strong>{st.session_state.user['username']}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Menu de navigation
            pages = {
                "📊 Tableau de Bord": "dashboard",
                "🏞️ Parcelles": "parcelles",
                "📝 Activités": "activities",
                "🔔 Rappels": "reminders",
                "📅 Calendrier": "calendar",
                "📈 Analyses": "analytics"
            }
            
            selected_page = st.selectbox("Navigation", list(pages.keys()))
            st.session_state.current_page = pages[selected_page]
            
            st.divider()
            
            # Informations rapides
            parcelles = self.db.get_user_parcelles(st.session_state.user['id'])
            st.metric("Mes Parcelles", len(parcelles))
            
            total_surface = sum(p['surface'] for p in parcelles if p['surface'])
            st.metric("Surface Totale", f"{total_surface:.1f} ha")
            
            st.divider()
            
            if st.button("🚪 Déconnexion"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.rerun()
        
        # Contenu principal
        if st.session_state.current_page == "dashboard":
            self.dashboard()
        elif st.session_state.current_page == "parcelles":
            self.parcelles_page()
        elif st.session_state.current_page == "activities":
            self.activities_page()
        elif st.session_state.current_page == "reminders":
            self.reminders_page()
        elif st.session_state.current_page == "calendar":
            self.calendar_page()
        elif st.session_state.current_page == "analytics":
            self.analytics_page()

# Point d'entrée de l'application
if __name__ == "__main__":
    app = MonPlantingApp()
    app.run()

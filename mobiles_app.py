import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
import json
import os
import time
from datetime import datetime
from prediction_model import MobilePricePredictor
from database import db  # Import database module

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'predictor' not in st.session_state:
    st.session_state.predictor = MobilePricePredictor()
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False

def initialize_database():
    """Initialize database connection"""
    if not st.session_state.db_connected:
        if db.test_connection():
            st.session_state.db_connected = True
            return True
        else:
            st.error("Database connection failed.")
            return False
    return True

def register_user(username, password):
    """Register new user using database"""
    success, message = db.create_user(username, password)
    return success, message

def verify_user(username, password):
    """Verify user using database"""
    success, result = db.verify_user(username, password)
    if success:
        return True, result
    return False, result

def login_page():
    """Login page with database authentication"""
    st.set_page_config(page_title="Mobile Analytics - Login", layout="centered")
    
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 400px;
        }
        .title {
            text-align: center;
            color: #333;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<div class="title">Mobile Analytics Pro</div>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Login", type="primary", use_container_width=True):
                    success, result = verify_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_id = result['id']
                        st.session_state.user_role = result['role']
                        
                        # Log activity
                        db.log_activity(result['id'], 'login', 'User logged in')
                        
                        st.success(f"Welcome {username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result)
            
            with tab2:
                new_user = st.text_input("New Username", key="reg_user")
                new_pass = st.text_input("New Password", type="password", key="reg_pass")
                confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                if st.button("Register", use_container_width=True):
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters")
                    elif len(new_user) < 3:
                        st.error("Username must be at least 3 characters")
                    else:
                        success, message = register_user(new_user, new_pass)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
            # Default credentials reminder
            st.markdown("---")
            st.markdown("**Default Credentials:**")
            st.markdown("- Admin: `admin` / `admin123`")
            st.markdown("- Analyst: `analyst` / `analyst123`")
            st.markdown("- User: `user` / `user123`")
            
            st.markdown('</div>', unsafe_allow_html=True)

def load_data():
    """Load data from database"""
    return db.load_mobile_data()

def main_app():
    """Main application with database integration"""
    st.set_page_config(
        page_title="Mobile Analytics Dashboard",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            padding: 20px;
            background: linear-gradient(90deg, #1f77b4, #2ca02c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #1f77b4;
        }
        .predict-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
        }
        .prediction-result {
            background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .admin-panel {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown(f'<div class="main-header">Mobile Analytics Pro Dashboard</div>', unsafe_allow_html=True)
        st.caption(f"Logged in as: {st.session_state.username} ({st.session_state.user_role})")
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"**Welcome, {st.session_state.username}**")
        st.markdown(f"*Role: {st.session_state.user_role}*")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            db.log_activity(st.session_state.user_id, 'logout', 'User logged out')
            st.session_state.authenticated = False
            st.session_state.username = ''
            st.session_state.user_id = None
            st.session_state.user_role = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Filters")
        
        # Load data for filters
        df = load_data()
        
        # Company filter
        companies = sorted(df['Company Name'].unique()) if 'Company Name' in df.columns else []
        selected_companies = st.multiselect(
            "Select Companies",
            options=companies,
            default=companies[:3] if companies else []
        )
        
        # Year filter
        if 'Launched Year' in df.columns and not df.empty:
            min_year = int(df['Launched Year'].min())
            max_year = int(df['Launched Year'].max())
            selected_years = st.slider(
                "Launch Year",
                min_value=min_year,
                max_value=max_year,
                value=(max(min_year, 2020), max_year)
            )
        else:
            selected_years = (2020, 2024)
        
        # Price filter
        if 'Launched Price (Pakistan)' in df.columns and not df.empty:
            min_price = float(df['Launched Price (Pakistan)'].min())
            max_price = float(df['Launched Price (Pakistan)'].max())
            price_range = st.slider(
                "Price Range (PKR)",
                min_value=int(min_price),
                max_value=int(max_price),
                value=(0, min(500000, int(max_price))),
                step=10000
            )
        else:
            price_range = (0, 500000)
        
        # Get filtered data
        filtered_df = db.get_filtered_data(
            companies=selected_companies if selected_companies else None,
            years=selected_years,
            price_range=price_range
        )
        
        # Data stats in sidebar
        st.markdown("---")
        st.markdown("### Data Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", len(filtered_df))
        with col2:
            st.metric("Companies", filtered_df['company_name'].nunique() if not filtered_df.empty else 0)
    
    # Main tabs
    if st.session_state.user_role == 'admin':
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Overview", "Company Analysis", "Price Trends", "Specifications", "Price Predictor", "Admin Panel"])
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Company Analysis", "Price Trends", "Specifications", "Price Predictor"])
    
    # Tab 1: Overview
    with tab1:
        display_overview_tab(filtered_df)
    
    # Tab 2: Company Analysis
    with tab2:
        display_company_analysis_tab(filtered_df)
    
    # Tab 3: Price Trends
    with tab3:
        display_price_trends_tab(filtered_df)
    
    # Tab 4: Specifications
    with tab4:
        display_specifications_tab(filtered_df)
    
    # Tab 5: Price Predictor
    with tab5:
        display_price_predictor_tab(df if not df.empty else filtered_df)
    
    # Tab 6: Admin Panel (Only for admins)
    if st.session_state.user_role == 'admin':
        with tab6:
            display_admin_panel()

def display_overview_tab(filtered_df):
    """Display overview tab"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Models", len(filtered_df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Companies", filtered_df['company_name'].nunique() if not filtered_df.empty else 0)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        avg_price = filtered_df['price_pakistan'].mean() if not filtered_df.empty else 0
        st.metric("Avg Price", f"PKR {avg_price:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        latest_year = filtered_df['launched_year'].max() if not filtered_df.empty else 2024
        st.metric("Latest Year", int(latest_year))
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Top expensive models
    st.subheader("Top 10 Most Expensive Models")
    if not filtered_df.empty:
        top_expensive = filtered_df.nlargest(10, 'price_pakistan')[['company_name', 'model_name', 'price_pakistan', 'launched_year']]
        top_expensive = top_expensive.rename(columns={'price_pakistan': 'Price (PKR)'})
        st.dataframe(top_expensive, use_container_width=True)
    else:
        st.info("No data available")
    
    # Visualizations
    col1, col2 = st.columns(2)
    with col1:
        if not filtered_df.empty and 'price_pakistan' in filtered_df.columns:
            fig = px.histogram(filtered_df, x='price_pakistan', nbins=30,
                             title='Price Distribution',
                             labels={'price_pakistan': 'Price (PKR)'},
                             color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not filtered_df.empty and 'company_name' in filtered_df.columns:
            fig = px.box(filtered_df, x='company_name', y='price_pakistan',
                        title='Price Comparison by Company',
                        labels={'price_pakistan': 'Price (PKR)', 'company_name': 'Company'})
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def display_company_analysis_tab(filtered_df):
    """Display company analysis tab"""
    company_stats = db.get_company_stats()
    
    if not company_stats.empty:
        st.subheader("Company Statistics")
        st.dataframe(company_stats, use_container_width=True)
        
        # Visualization
        fig = px.bar(company_stats.head(10), x='company_name', y='model_count',
                    title='Top 10 Companies by Model Count',
                    color='avg_price',
                    color_continuous_scale='Viridis',
                    labels={'company_name': 'Company', 'model_count': 'Model Count', 'avg_price': 'Avg Price'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No company statistics available")

def display_price_trends_tab(filtered_df):
    """Display price trends tab"""
    yearly_stats = db.get_yearly_stats()
    
    if not yearly_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(yearly_stats, x='launched_year', y='avg_price',
                         title='Average Price Trend Over Years',
                         markers=True,
                         labels={'launched_year': 'Year', 'avg_price': 'Avg Price (PKR)'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(yearly_stats, x='launched_year', y='model_count',
                        title='Number of Models Launched Each Year',
                        labels={'launched_year': 'Year', 'model_count': 'Model Count'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No yearly statistics available")

def display_specifications_tab(filtered_df):
    """Display specifications tab"""
    if filtered_df.empty:
        st.info("No data available for specifications analysis")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'ram' in filtered_df.columns:
            ram_dist = filtered_df['ram'].value_counts().head(10)
            if not ram_dist.empty:
                fig = px.pie(values=ram_dist.values, names=ram_dist.index,
                            title='Top 10 RAM Configurations')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'battery_capacity' in filtered_df.columns:
            battery_series = filtered_df['battery_capacity'].astype(str).str.extract('(\d+)')[0].astype(float)
            battery_series = battery_series.dropna()
            if not battery_series.empty:
                fig = px.histogram(x=battery_series, nbins=20,
                                 title='Battery Capacity Distribution (mAh)',
                                 labels={'x': 'Battery Capacity (mAh)'},
                                 color_discrete_sequence=['#2ca02c'])
                st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'processor' in filtered_df.columns:
            processor_dist = filtered_df['processor'].value_counts().head(10)
            if not processor_dist.empty:
                fig = px.bar(x=processor_dist.index, y=processor_dist.values,
                           title='Top 10 Processors',
                           labels={'x': 'Processor', 'y': 'Count'},
                           color=processor_dist.values,
                           color_continuous_scale='Viridis')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'screen_size' in filtered_df.columns:
            screen_series = filtered_df['screen_size'].astype(str).str.extract('(\d+\.?\d*)')[0].astype(float)
            screen_series = screen_series.dropna()
            if not screen_series.empty:
                fig = px.histogram(x=screen_series, nbins=15,
                                 title='Screen Size Distribution (inches)',
                                 labels={'x': 'Screen Size (inches)'},
                                 color_discrete_sequence=['#ff7f0e'])
                st.plotly_chart(fig, use_container_width=True)

def display_price_predictor_tab(df):
    """Display price predictor tab"""
    st.markdown('<div class="predict-card">', unsafe_allow_html=True)
    st.markdown("### Advanced Mobile Price Predictor")
    st.markdown("Predict mobile prices based on complete specifications")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Load or train model
    if not st.session_state.predictor.is_trained:
        st.session_state.predictor.load_saved_model()
    
    # Model training section
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Train Prediction Model", type="primary", use_container_width=True):
            with st.spinner("Training model with database data..."):
                success, message, feature_importance = st.session_state.predictor.train_model()
                if success:
                    model_info = st.session_state.predictor.get_model_info()
                    
                    st.success("Model trained successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("R² Score", f"{model_info['r2']:.2%}")
                    with col2:
                        st.metric("MAE", f"PKR {model_info['mae']:,.0f}")
                    with col3:
                        st.metric("RMSE", f"PKR {model_info['rmse']:,.0f}")
                    
                    if feature_importance is not None:
                        st.subheader("Feature Importance")
                        fig = px.bar(feature_importance.head(10), x='importance', y='feature',
                                    orientation='h', title='Top 10 Most Important Features',
                                    color='importance', color_continuous_scale='Viridis')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Training failed: {message}")
    
    with col2:
        if st.button("📊 View My Predictions", use_container_width=True):
            predictions = db.get_user_predictions(st.session_state.user_id)
            if not predictions.empty:
                st.subheader("My Prediction History")
                st.dataframe(predictions, use_container_width=True)
            else:
                st.info("No prediction history found")
    
    # Prediction form
    st.markdown("### Enter Mobile Specifications")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company = st.selectbox("Company/Brand", 
                              options=sorted(df['Company Name'].unique()) if 'Company Name' in df.columns else [])
        model_name = st.text_input("Model Name", placeholder="e.g., iPhone 16 Pro Max")
        launch_year = st.slider("Launch Year", 2010, 2025, 2024)
        
        ram_options = [4, 6, 8, 12, 16, 18, 24]
        ram = st.selectbox("RAM (GB)", options=ram_options, index=2)
        
        storage_input = st.text_input("Storage", placeholder="e.g., 256GB or 1TB", value="256GB")
    
    with col2:
        battery = st.slider("Battery (mAh)", 2000, 10000, 5000, step=100)
        screen_size = st.slider("Screen Size (inches)", 5.0, 7.5, 6.5, step=0.1)
        front_camera = st.slider("Front Camera (MP)", 5, 50, 12, step=1)
        back_camera = st.slider("Back Camera (MP)", 8, 200, 50, step=1)
        weight = st.slider("Weight (grams)", 100, 300, 180, step=5)
    
    # Get processors from database
    if 'Processor' in df.columns and not df.empty:
        processors = df['Processor'].value_counts().head(20).index.tolist()
    else:
        processors = [
            "Snapdragon 8 Gen 3", "Snapdragon 8 Gen 2", "A17 Bionic", "A16 Bionic",
            "Exynos 2400", "Exynos 2200", "Dimensity 9300", "Dimensity 9200"
        ]
    
    processor = st.selectbox("Processor", options=processors)
    
    # Prediction button
    if st.button("🔮 Predict Price", type="primary", use_container_width=True):
        if not st.session_state.predictor.is_trained:
            st.error("Please train the model first!")
        else:
            with st.spinner("Predicting price..."):
                result, message = st.session_state.predictor.predict_price(
                    company=company,
                    model_name=model_name,
                    launch_year=launch_year,
                    ram=ram,
                    storage=storage_input,
                    battery=battery,
                    screen_size=screen_size,
                    front_camera=front_camera,
                    back_camera=back_camera,
                    processor=processor,
                    weight=weight
                )
                
                if result:
                    predicted_price = result['predicted_price']
                    confidence = result['confidence']
                    lower_bound, upper_bound = result['price_range']
                    storage_used = result['storage_used']
                    
                    # Save prediction to database
                    prediction_data = {
                        'company': company,
                        'model_name': model_name,
                        'launch_year': launch_year,
                        'ram': ram,
                        'storage_used': storage_used,
                        'battery': battery,
                        'screen_size': screen_size,
                        'front_camera': front_camera,
                        'back_camera': back_camera,
                        'processor': processor,
                        'weight': weight,
                        'predicted_price': predicted_price,
                        'confidence': confidence,
                        'price_range': (lower_bound, upper_bound)
                    }
                    
                    db.save_prediction(st.session_state.user_id, prediction_data)
                    db.log_activity(st.session_state.user_id, 'prediction', f'Predicted price for {company} {model_name}')
                    
                    # Display result
                    st.markdown(f"""
                    <div class="prediction-result">
                        <h2>Predicted Price: PKR {predicted_price:,.0f}</h2>
                        <h4>Confidence: {confidence*100:.1f}%</h4>
                        <p>Price Range: PKR {lower_bound:,.0f} - PKR {upper_bound:,.0f}</p>
                        <p>{company} | {launch_year} | {ram}GB RAM | {storage_used}GB</p>
                        <p>{battery}mAh | {screen_size}" | {front_camera}MP+{back_camera}MP</p>
                        <p>Processor: {processor}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Similar models comparison
                    st.subheader("Similar Models Comparison")
                    similar_models = df[
                        (df['Company Name'] == company) & 
                        (df['Launched Year'].between(launch_year-1, launch_year+1))
                    ].sort_values('Launched Price (Pakistan)')
                    
                    if not similar_models.empty:
                        st.dataframe(similar_models[['Model Name', 'Launched Price (Pakistan)', 'Launched Year', 'RAM']].head(10), use_container_width=True)
                    else:
                        st.info("No similar models found in database")
                else:
                    st.error(f"Prediction failed: {message}")

def display_admin_panel():
    """Display admin panel (only for admin users)"""
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    st.markdown("### Administrator Panel")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("Admin features will be available in next update")
    st.write("Currently viewing as:", st.session_state.user_role)

if __name__ == "__main__":
    if not st.session_state.authenticated:
        login_page()
    else:
        if initialize_database():
            main_app()
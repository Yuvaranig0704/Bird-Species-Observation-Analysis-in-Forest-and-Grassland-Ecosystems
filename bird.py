import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------------------
# Data Loading
# ---------------------------
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="NanDha@12345",
        database="bird",
        auth_plugin='mysql_native_password'
    )

@st.cache_data
def load_data():
    conn = get_connection()
    query = "SELECT * FROM BirdObservations;"
    df = pd.read_sql(query, con=conn)
    conn.close()
    
    # Enhanced data cleaning
    df['ObservationCount'] = pd.to_numeric(df['Initial_Three_Min_Cnt'], errors='coerce')
    df = df.dropna(subset=['ObservationCount'])  
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['Date'].notna()]  
    df['Year'] = df['Date'].dt.year.astype(int)
    df['Month'] = df['Date'].dt.month.astype(int)
    df['Scientific_Name'] = df['Scientific_Name'].fillna('Unknown')  
    
    return df

# ---------------------------
# Load Verified Data
# ---------------------------
df = load_data()
st.title("🦜 Bird Species Observation And Analysis")	

# Show data summary for debugging
st.sidebar.subheader("Data Summary")
st.sidebar.write(f"Total Records: {len(df)}")
st.sidebar.write(f"Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}")
st.sidebar.write(f"Total Observations: {df['ObservationCount'].sum():,}")
st.sidebar.write(f"Unique Species: {df['Scientific_Name'].nunique()}")

# ---------------------------
#  Main Tabs
# ---------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", 
    "📈 Trends",
    "🌿 Environment",
    "🚨 Conservation"
])

# ---------------------------
# 📊 Tab 1: Overview
# ---------------------------
with tab1:
    st.subheader("Core Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Observations", f"{df['ObservationCount'].sum():,}")
    col2.metric("Unique Species", df['Scientific_Name'].nunique())
    col3.metric("Data Years", f"{df['Year'].min()} - {df['Year'].max()}")
    
    st.subheader("Species Distribution")
    species_counts = df['Scientific_Name'].value_counts().nlargest(10)
    fig = px.pie(species_counts, names=species_counts.index, values=species_counts.values)
    st.plotly_chart(fig)

# ---------------------------
# 📈 Tab 2: Trends
# ---------------------------
with tab2:
    st.subheader("Temporal Analysis")
    
    # Heatmap with data validation

    heatmap_data = df.groupby(['Year', 'Month'])['ObservationCount'].sum().unstack(fill_value=0)
        
    plt.figure(figsize=(12, 6))
    sns.heatmap(
            heatmap_data, 
            annot=True, 
            fmt="d", 
            cmap="YlGnBu",
            linewidths=.5,
            cbar_kws={'label': 'Observations'}
        )
    plt.title("Monthly Observation Patterns")
    plt.xlabel("Month")
    plt.ylabel("Year")
    st.pyplot(plt.gcf())
    plt.close()
       
    st.header("Species Observation Comparison by Year")
    
    top_n = st.slider("Select number of top species", 1, 20, 50)
    top_species = df['Scientific_Name'].value_counts().head(top_n).index.tolist()
    
    trend_data = df[df['Scientific_Name'].isin(top_species)]
    grouped = trend_data.groupby(['Year', 'Scientific_Name'])['ObservationCount'].sum().reset_index()
    
    fig = px.bar(
        grouped,
        x="Year",
        y="ObservationCount",
        color="Scientific_Name",
        barmode="group",
        title=f"Top {top_n} Species Observation Comparison by Year"
    )
    st.plotly_chart(fig)


# ---------------------------
# 🌿 Tab 3: Environment 
# ---------------------------
with tab3:
    st.subheader("Environmental Impact Analysis")
    
    # Check for environmental columns
    env_cols = ['Temperature', 'Humidity', 'Wind']
    available_env = [col for col in env_cols if col in df.columns]
    
    if available_env:
        # Correlation matrix
        st.subheader("Environmental Correlations")
        corr_data = df[available_env + ['ObservationCount']].corr()
        fig = px.imshow(corr_data, text_auto=True, aspect="auto")
        st.plotly_chart(fig)
        
        # Environmental factor analysis
        st.subheader("Factor Analysis")
        selected_factor = st.selectbox("Choose Environmental Factor", available_env)
        
        fig = px.scatter(
            df,
            x=selected_factor,
            y='ObservationCount',
            color='Scientific_Name',
            trendline='ols',
            title=f"{selected_factor} vs Observations"
        )
        st.plotly_chart(fig)
    
# ---------------------------
# 🚨 Tab 4: Conservation 
# ---------------------------
with tab4:
    
    st.header("Observation Hotspots")
    loc_group = df.groupby('Admin_Unit_Code')['ObservationCount'].sum().reset_index().sort_values(by='ObservationCount', ascending=False).head(10)
    fig = px.bar(loc_group, x='Admin_Unit_Code', y='ObservationCount', title="Top Observation Areas")
    st.plotly_chart(fig)

    st.header("PIF Watchlist Status")
    
    if 'PIF_Watchlist_Status' in df.columns:
        fig = px.pie(
            df['PIF_Watchlist_Status'].value_counts(), 
            names=df['PIF_Watchlist_Status'].value_counts().index,
            values=df['PIF_Watchlist_Status'].value_counts().values,
            title="Distribution of Species by PIF Watchlist Status",
        )
        st.plotly_chart(fig,color=['red','y'])

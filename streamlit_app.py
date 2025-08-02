import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from urllib.parse import urlparse
import re
from yc_scraper import YCScraperUniversal
import time

# Page config
st.set_page_config(
    page_title="YC 2025 Companies Directory",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #ff6b35, #f7931e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .company-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    @media (prefers-color-scheme: dark) {
        .company-card {
            background: rgba(50, 50, 50, 0.9);
            border: 1px solid #555;
            color: #fff;
        }
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .batch-badge {
        background: #ff6b35;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .batch-overview {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 2rem 0;
    }
    
    .batch-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        min-width: 200px;
    }
    
    .company-profile {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .profile-section {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load YC companies data"""
    try:
        # Load existing data
        df = pd.read_csv('data.csv')
        return df
    except FileNotFoundError:
        st.error("data.csv not found. Please run the scrapers first.")
        return pd.DataFrame()

def get_domain_from_url(url):
    """Extract domain from URL"""
    if not url or pd.isna(url):
        return "Unknown"
    try:
        domain = urlparse(url).netloc
        return domain.replace('www.', '') if domain else "Unknown"
    except:
        return "Unknown"

def get_company_link(company):
    """Get the appropriate link for a company (website first, then LinkedIn)"""
    # First try company website
    if company['Company Link'] and pd.notna(company['Company Link']) and str(company['Company Link']).strip():
        return str(company['Company Link']).strip()
    
    # Fallback to LinkedIn
    if company['Linkedin Link'] and pd.notna(company['Linkedin Link']) and str(company['Linkedin Link']).strip():
        return str(company['Linkedin Link']).strip()
    
    # No link available
    return None

def make_company_name_clickable(company_name, company):
    """Create a clickable company name with appropriate styling"""
    link = get_company_link(company)
    
    if link:
        # Create clickable markdown link with custom styling
        return f'<a href="{link}" target="_blank" style="color: #1f77b4; text-decoration: none; font-weight: bold; border-bottom: 1px solid #1f77b4;">{company_name}</a>'
    else:
        # No link available, return plain text
        return f'<span style="font-weight: bold;">{company_name}</span>'

def create_analytics_charts(df):
    """Create analytics charts"""
    # Row 1: Pie charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Companies by batch
        batch_counts = df['Batch'].value_counts()
        fig_batch = px.pie(
            values=batch_counts.values,
            names=batch_counts.index,
            title="Companies by YC Batch",
            color_discrete_sequence=['#ff6b35', '#f7931e', '#ffd23f']
        )
        fig_batch.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_batch, use_container_width=True)
    
    with col2:
        # Companies by location with "Others" for small percentages
        location_counts = df['Location'].value_counts()
        total_companies = len(df)
        
        # Separate locations with >= 5% and < 5%
        major_locations = location_counts[location_counts / total_companies >= 0.05]
        minor_locations = location_counts[location_counts / total_companies < 0.05]
        
        # Create final data
        if len(minor_locations) > 0:
            pie_data = major_locations.copy()
            pie_data['Others'] = minor_locations.sum()
        else:
            pie_data = major_locations
        
        fig_location = px.pie(
            values=pie_data.values,
            names=pie_data.index,
            title="Companies by Location",
            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
        )
        fig_location.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_location, use_container_width=True)
    
    # Row 2: Bar charts
    col3, col4 = st.columns(2)
    
    with col3:
        # Top tags/categories
        all_tags = []
        for tags in df['Tags']:
            if isinstance(tags, str) and tags.strip():
                # Split by comma for the actual data format
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                all_tags.extend(tag_list)
        
        if all_tags:
            tag_counts = pd.Series(all_tags).value_counts().head(10)
            fig_tags = px.bar(
                x=tag_counts.values,
                y=tag_counts.index,
                orientation='h',
                title="Top Company Categories/Tags",
                color=tag_counts.values,
                color_continuous_scale='Plasma'
            )
            fig_tags.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Number of Companies",
                yaxis_title="Category/Tag"
            )
            st.plotly_chart(fig_tags, use_container_width=True)
        else:
            st.info("No tags data available for visualization")
    
    with col4:
        # Team size distribution
        team_size_counts = df['Team Size'].value_counts().head(8)
        fig_team = px.bar(
            x=team_size_counts.index,
            y=team_size_counts.values,
            title="Team Size Distribution",
            color=team_size_counts.values,
            color_continuous_scale='Viridis'
        )
        fig_team.update_layout(xaxis_title="Team Size", yaxis_title="Number of Companies")
        st.plotly_chart(fig_team, use_container_width=True)
    
    # Row 3: Additional metrics
    col5, col6, col7 = st.columns(3)
    
    with col5:
        hiring_count = len(df[df['Jobs'] > 0])
        total_count = len(df)
        st.markdown(f"""
        <div class="metric-card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 150px; padding: 1rem;">
            <div style="text-align: center; width: 100%;">
                <h2 style="margin: 0.5rem 0; font-size: 2.5rem; text-align: center; display: block;">{hiring_count}</h2>
                <p style="margin: 0.5rem 0; font-size: 1.1rem; font-weight: bold; text-align: center; display: block;">Companies Hiring</p>
                <small style="margin: 0.5rem 0; opacity: 0.8; text-align: center; display: block;">{hiring_count/total_count*100:.1f}% of total</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        avg_team_size = df['Team Size'].mean()
        st.markdown(f"""
        <div class="metric-card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 150px; padding: 1rem;">
            <div style="text-align: center; width: 100%;">
                <h2 style="margin: 0.5rem 0; font-size: 2.5rem; text-align: center; display: block;">{avg_team_size:.1f}</h2>
                <p style="margin: 0.5rem 0; font-size: 1.1rem; font-weight: bold; text-align: center; display: block;">Avg Team Size</p>
                <small style="margin: 0.5rem 0; opacity: 0.8; text-align: center; display: block;">Across all companies</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col7:
        unique_locations = df['Location'].nunique()
        st.markdown(f"""
        <div class="metric-card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 150px; padding: 1rem;">
            <div style="text-align: center; width: 100%;">
                <h2 style="margin: 0.5rem 0; font-size: 2.5rem; text-align: center; display: block;">{unique_locations}</h2>
                <p style="margin: 0.5rem 0; font-size: 1.1rem; font-weight: bold; text-align: center; display: block;">Unique Locations</p>
                <small style="margin: 0.5rem 0; opacity: 0.8; text-align: center; display: block;">Global presence</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_company_profile(company):
    """Display detailed company profile/passport"""
    # Company header with clickable name
    clickable_name = make_company_name_clickable(company['Title'], company)
    st.markdown(f"## 🏢 {clickable_name}", unsafe_allow_html=True)
    
    # Company Overview section
    with st.container():
        st.markdown("### 📋 Company Overview")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Batch:** {company['Batch']}")
            founded_year = int(company['Founded']) if pd.notna(company['Founded']) else 'N/A'
            st.write(f"**Founded:** {founded_year}")
            team_size = int(company['Team Size']) if pd.notna(company['Team Size']) else 'N/A'
            st.write(f"**Team Size:** {team_size} employees")
        
        with col2:
            st.write(f"**Location:** {company['Location'] if pd.notna(company['Location']) else 'N/A'}")
            jobs_count = int(company['Jobs']) if pd.notna(company['Jobs']) else 'N/A'
            st.write(f"**Jobs Available:** {jobs_count}")
    
    st.divider()
    
    # Links section
    st.markdown("### 🔗 Links")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if company['Company Link'] and pd.notna(company['Company Link']):
            st.link_button("🌐 Website", company['Company Link'])
        else:
            st.write("🌐 Website: Not available")
    
    with col2:
        if company['Linkedin Link'] and pd.notna(company['Linkedin Link']):
            st.link_button("💼 LinkedIn", company['Linkedin Link'])
        else:
            st.write("💼 LinkedIn: Not available")
    
    with col3:
        if company['YC Page'] and pd.notna(company['YC Page']):
            st.link_button("🚀 YC Profile", company['YC Page'])
        else:
            st.write("🚀 YC Profile: Not available")
    
    st.divider()
    
    # Categories section
    st.markdown("### 🏷️ Categories")
    if company['Tags'] and pd.notna(company['Tags']):
        tags = [tag.strip() for tag in str(company['Tags']).split(',') if tag.strip()]
        if tags:
            # Display tags as badges
            cols = st.columns(min(len(tags), 4))
            for i, tag in enumerate(tags):
                with cols[i % 4]:
                    st.markdown(f"`{tag}`")
        else:
            st.write("No tags available")
    else:
        st.write("No tags available")
    
    st.divider()
    
    # Description section
    st.markdown("### 📝 Description")
    
    if company['Short Description'] and pd.notna(company['Short Description']):
        st.markdown("**Short Description:**")
        st.write(company['Short Description'])
    
    if company['Long Description'] and pd.notna(company['Long Description']):
        st.markdown("**Detailed Description:**")
        with st.expander("Read full description", expanded=False):
            st.write(company['Long Description'])

def display_company_card(company):
    """Display a company card"""
    with st.container():
        clickable_name = make_company_name_clickable(company['Title'], company)
        st.markdown(f"""
        <div class="company-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: inherit;">{clickable_name}</h3>
                <span class="batch-badge">{company['Batch']}</span>
            </div>
            <p style="color: inherit; opacity: 0.8; margin: 0.5rem 0;">{str(company['Short Description'])[:200] if pd.notna(company['Short Description']) else 'No description available'}{'...' if pd.notna(company['Short Description']) and len(str(company['Short Description'])) > 200 else ''}</p>
            
        """, unsafe_allow_html=True)
        
        # Tags section below the card
        if company['Tags'] and pd.notna(company['Tags']) and str(company['Tags']).strip():
            tags = [tag.strip() for tag in str(company['Tags']).split(',') if tag.strip()][:3]
            if tags:
                st.caption(f"🏷️ {', '.join(tags)}")
        
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Links section with 4 columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if company['Company Link'] and not pd.isna(company['Company Link']):
                st.markdown(f"🌐 [Website]({company['Company Link']})")
            else:
                st.markdown("🌐 Website: Not available")
        
        with col2:
            if company['YC Page'] and not pd.isna(company['YC Page']):
                st.markdown(f"🚀 [YC Profile]({company['YC Page']})")
            else:
                st.markdown("🚀 YC Profile: Not available")
        
        with col3:
            if company['Linkedin Link'] and not pd.isna(company['Linkedin Link']):
                st.markdown(f"💼 [LinkedIn]({company['Linkedin Link']})")
            else:
                st.markdown("💼 LinkedIn: Not available")
        
        with col4:
            # View Profile button
            if st.button(f"👁️ View Profile", key=f"profile_{company['Title']}", type="secondary"):
                st.session_state.selected_company = company['Title']
                st.session_state.view_mode = "Company Profile"
                st.rerun()

def get_company_link(row):
    """Get the best available link for a company with priority: website > LinkedIn > YC Page"""
    if pd.notna(row['Company Link']) and str(row['Company Link']).strip():
        return str(row['Company Link']).strip()
    elif pd.notna(row['Linkedin Link']) and str(row['Linkedin Link']).strip():
        return str(row['Linkedin Link']).strip()
    elif pd.notna(row['YC Page']) and str(row['YC Page']).strip():
        return str(row['YC Page']).strip()
    return None

def display_companies_table(df):
    """Display companies in a comprehensive table format for CEOs"""
    # Prepare data for table display
    table_df = df.copy()
    
    # Clean up description column
    table_df['Short Description'] = table_df['Short Description'].apply(
        lambda x: str(x).split('.')[0] + '.' if pd.notna(x) and '.' in str(x) else str(x)[:100] + '...' if pd.notna(x) and len(str(x)) > 100 else str(x) if pd.notna(x) else 'No description'
    )
    
    # Clean up tags column
    table_df['Tags'] = table_df['Tags'].apply(
        lambda x: ', '.join([tag.strip() for tag in str(x).split(',')[:3]]) if pd.notna(x) and str(x).strip() else 'No tags'
    )
    
    # Create clickable links for other columns
    def make_clickable(url):
        if pd.notna(url) and str(url).strip():
            return str(url).strip()
        return None
    
    # Create clickable company names with actual URLs for functionality
    table_df['Company_Link'] = table_df.apply(get_company_link, axis=1)
    
    # Create URLs with company names embedded in URL fragment (hash) for regex extraction
    def create_smart_company_link(row):
        link = get_company_link(row)
        if link:
            # Add company name as URL fragment/hash for regex extraction
            # Format: ACTUAL_URL#CompanyName
            company_name_clean = row['Title'].replace(' ', '_').replace('#', '').replace('&', 'and')
            return f"{link}#{company_name_clean}"
        else:
            return None
    
    table_df['Smart_Company_Link'] = table_df.apply(create_smart_company_link, axis=1)
    
    # Replace None values with company title for companies without links
    table_df['Smart_Company_Link'] = table_df.apply(
        lambda row: row['Smart_Company_Link'] if row['Smart_Company_Link'] is not None else row['Title'], 
        axis=1
    )
    
    table_df['Website'] = table_df['Company Link'].apply(make_clickable)
    table_df['YC Profile'] = table_df['YC Page'].apply(make_clickable)
    table_df['LinkedIn'] = table_df['Linkedin Link'].apply(make_clickable)
    
    # Select and rename columns for display
    display_columns = {
        'Smart_Company_Link': 'Company Name',
        'Batch': 'Batch',
        'Founded': 'Founded',
        'Team Size': 'Team Size',
        'Location': 'Location',
        'Jobs': 'Jobs',
        'Short Description': 'Short Description',
        'Tags': 'Categories',
        'Website': 'Website',
        'YC Profile': 'YC Profile',
        'LinkedIn': 'LinkedIn',
        'Has_YC_Batch_Indicator': 'YC Indicator'
    }
    
    table_display = table_df[list(display_columns.keys())].rename(columns=display_columns)
    
    # Display the table with selection
    st.caption("🔘 Click the small button on the left of any row to view company profile")
    
    event = st.dataframe(
        table_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Company Name": st.column_config.LinkColumn(
                "Company Name", 
                width="medium",
                display_text=r".*#(.+)",  # Extract company name from URL fragment after #
                help="Click to visit company website, LinkedIn, or YC profile"
            ),
            "Website": st.column_config.LinkColumn("Website"),
            "YC Profile": st.column_config.LinkColumn("YC Profile"),
            "LinkedIn": st.column_config.LinkColumn("LinkedIn"),
            "Short Description": st.column_config.TextColumn("Short Description", width="large"),
            "Categories": st.column_config.TextColumn("Categories", width="medium"),
            "YC Indicator": st.column_config.TextColumn("YC Indicator", width="small"),
        }
    )
    
    # Handle row selection
    if event.selection.rows:
        selected_row = event.selection.rows[0]
        selected_company = df.iloc[selected_row]
        st.session_state.selected_company = selected_company['Title']
        st.session_state.view_mode = "Company Profile"
        st.rerun()

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 YC 2025 Companies Directory</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading YC companies data..."):
        df = load_data()
    
    if df.empty:
        st.error("No data available. Please check the scraper.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Batch filter with radio buttons
    batches = ['All'] + sorted(list(df['Batch'].unique()))
    selected_batch = st.sidebar.radio(
        "Choose YC Batch:",
        batches
    )
    
    # Tag filter - moved up
    all_unique_tags = set()
    for tags in df['Tags']:
        if isinstance(tags, str) and tags.strip():
            # Split by comma for the actual data format
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            all_unique_tags.update(tag_list)
    
    if all_unique_tags:
        selected_tags = st.sidebar.multiselect("Filter by Tags", sorted(list(all_unique_tags)))
    else:
        selected_tags = []
    
    # Location filter using the Location column - multi-select
    location_counts = df['Location'].value_counts()
    unique_locations = location_counts.index.tolist()
    selected_locations = st.sidebar.multiselect("📍 Location", unique_locations)
    
    # Founded year filter - using actual data range
    min_founded = int(df['Founded'].min())
    max_founded = int(df['Founded'].max())
    founded_year = st.sidebar.slider("Founded Year", min_value=min_founded, max_value=max_founded, value=2023, step=1)
    founded_filter = st.sidebar.checkbox("Only companies founded in or after this year", value=True)
    
    # Team size filter - dynamic maximum based on actual data
    min_team_size = int(df['Team Size'].min())
    max_team_size = int(df['Team Size'].max())
    team_size_range = st.sidebar.slider("Team Size Range", min_value=min_team_size, max_value=max_team_size, value=(1, min(20, max_team_size)))
    
    # Search filter
    search_term = st.sidebar.text_input("🔎 Search companies", placeholder="Enter company name or keywords")
    
    # Is hiring filter
    is_hiring = st.sidebar.checkbox("Is hiring")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_batch != 'All':
        filtered_df = filtered_df[filtered_df['Batch'] == selected_batch]
    
    if selected_locations:
        filtered_df = filtered_df[filtered_df['Location'].isin(selected_locations)]
    
    if search_term:
        mask = (
            filtered_df['Title'].str.contains(search_term, case=False, na=False) |
            filtered_df['Short Description'].str.contains(search_term, case=False, na=False) |
            filtered_df['Long Description'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if founded_filter:
        filtered_df = filtered_df[filtered_df['Founded'] >= founded_year]
    
    # Team size filter
    filtered_df = filtered_df[
        (filtered_df['Team Size'] >= team_size_range[0]) & 
        (filtered_df['Team Size'] <= team_size_range[1])
    ]
    
    if is_hiring:
        filtered_df = filtered_df[filtered_df['Jobs'] > 0]
    
    if selected_tags:
        def has_selected_tags(tags_str):
            if not isinstance(tags_str, str) or not tags_str.strip():
                return False
            tag_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            return any(tag in tag_list for tag in selected_tags)
        
        tag_mask = filtered_df['Tags'].apply(has_selected_tags)
        filtered_df = filtered_df[tag_mask]
    
    # Batch overview and analytics section combined
    with st.expander("2025 YC Batches Overview and Analytics", expanded=False):
        # Batch overview with better symmetry
        st.subheader("YC 2025 Batch Overview")
        
        # Create symmetric batch cards
        batch_cols = st.columns(2)
        batch_data = [
            ('Spring 2025', len(df[df['Batch'] == 'Spring 2025']) if 'Spring 2025' in df['Batch'].values else 0),
            ('Summer 2025', len(df[df['Batch'] == 'Summer 2025']) if 'Summer 2025' in df['Batch'].values else 0)
        ]
        
        for i, (batch_name, actual) in enumerate(batch_data):
            with batch_cols[i]:
                st.markdown(f"""
                <div class="metric-card" style="margin: 1rem 0;">
                    <h3 style="margin-bottom: 1rem;">{batch_name}</h3>
                    <h1 style="font-size: 3rem; margin: 1rem 0;">{actual}</h1>
                    <p style="font-size: 1.2rem; margin-top: 1rem;">Companies</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Analytics section
        if len(filtered_df) > 0:
            st.subheader("Analytics Dashboard")
            create_analytics_charts(filtered_df)
    
    st.markdown("---")
    
    # Companies list with view options
    st.header("📋 Companies")
    
    # Initialize session state for selected company and view mode
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = None
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "Table View"
    
    # View and sorting options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Get current view mode from session state
        current_view_options = ["Table View", "Cards", "Company Profile"]
        current_index = 0
        if st.session_state.view_mode in current_view_options:
            current_index = current_view_options.index(st.session_state.view_mode)
        
        view_mode = st.radio("View Mode", current_view_options, 
                           index=current_index, horizontal=True, 
                           key="view_mode_radio")
        
        # Update session state when radio button changes
        if view_mode != st.session_state.view_mode:
            st.session_state.view_mode = view_mode
            st.rerun()
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Batch", "Founded", "Team Size"])
    with col3:
        if st.session_state.view_mode == "Table View":
            companies_per_page = st.selectbox("Per Page", [25, 50, 100], index=1)
        else:
            companies_per_page = st.selectbox("Per Page", [5, 10, 20], index=1)
    
    if sort_by == "Name":
        filtered_df = filtered_df.sort_values('Title')
    elif sort_by == "Batch":
        filtered_df = filtered_df.sort_values('Batch')
    elif sort_by == "Founded":
        filtered_df = filtered_df.sort_values('Founded', ascending=False)
    elif sort_by == "Team Size":
        filtered_df = filtered_df.sort_values('Team Size', ascending=False)
    
    # Display companies
    if len(filtered_df) > 0:
        # Pagination
        total_pages = (len(filtered_df) - 1) // companies_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1))
            start_idx = (page - 1) * companies_per_page
            end_idx = start_idx + companies_per_page
            page_df = filtered_df.iloc[start_idx:end_idx]
        else:
            page_df = filtered_df
        
        # Display based on view mode from session state
        if st.session_state.view_mode == "Table View":
            display_companies_table(page_df)
        elif st.session_state.view_mode == "Company Profile":
            # Show detailed profile for selected company
            if st.session_state.selected_company:
                # Pre-select the company from session state
                try:
                    company_index = filtered_df['Title'].tolist().index(st.session_state.selected_company)
                    company_data = filtered_df[filtered_df['Title'] == st.session_state.selected_company].iloc[0]
                except (ValueError, IndexError):
                    company_index = 0
                    company_data = filtered_df.iloc[0]
                    st.session_state.selected_company = filtered_df['Title'].iloc[0]
            else:
                company_index = 0
                company_data = filtered_df.iloc[0]
                st.session_state.selected_company = filtered_df['Title'].iloc[0]
            
            selected_company = st.selectbox("Select a company to view profile:", 
                                          filtered_df['Title'].tolist(),
                                          index=company_index)
            
            if selected_company != st.session_state.selected_company:
                st.session_state.selected_company = selected_company
                company_data = filtered_df[filtered_df['Title'] == selected_company].iloc[0]
            
            display_company_profile(company_data)
        else:  # Cards
            for _, company in page_df.iterrows():
                display_company_card(company)
                st.markdown("---")
    else:
        st.info("No companies found matching your criteria.")

if __name__ == "__main__":
    main()
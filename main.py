import streamlit as st
import folium
from streamlit_folium import st_folium
import osmnx as ox
from shapely.affinity import translate
from PIL import Image
import geopandas as gpd

# Custom page background and styling
st.markdown("""
<style>
.stApp {
    background-color: white;
    color: #333;
}

h1, h2, h3, h4, h5, h6 {
    color: #333;
}

.stTextInput>div>div>input {
    color: #333;
}
</style>
""", unsafe_allow_html=True)

# Display custom logo
logo = Image.open('images/city_size_comparison_header.png')
st.image(logo, use_container_width=True)

# Introductory text
st.markdown("""
Welcome to **City Size Comparison**. Enter two cities to visually compare their sizes:
""")

# Get city geometry (with caching)
@st.cache_data(show_spinner=True)
def get_city_shape(city):
    try:
        return ox.geocode_to_gdf(city)
    except:
        st.warning(f"⚠️ City '{city}' not found.")
        return None

# Calculate area in km²
def calculate_area(gdf):
    gdf_proj = gdf.to_crs(epsg=3857)
    return round(gdf_proj.geometry.area.iloc[0] / 1e6, 2)

# Initialize session state for swapping
if 'city1' not in st.session_state:
    st.session_state['city1'] = ""
if 'city2' not in st.session_state:
    st.session_state['city2'] = ""

# City inputs
col1, col2, col3 = st.columns([4,4,1])
with col1:
    city1 = st.text_input("Enter the first city:", value=st.session_state['city1'])
with col2:
    city2 = st.text_input("Enter the second city:", value=st.session_state['city2'])
with col3:
    if st.button("🔄"):
        st.session_state['city1'], st.session_state['city2'] = city2, city1
        st.rerun()

if city1:
    gdf1 = get_city_shape(city1)
    if gdf1 is not None:
        area1 = calculate_area(gdf1)
        centroid1 = gdf1.geometry.centroid.iloc[0]
        m = folium.Map(location=[centroid1.y, centroid1.x], zoom_start=10)

        # Add City 1 shape
        folium.GeoJson(gdf1,
                       name=f"{city1}",
                       style_function=lambda x: {'fillColor':'blue','color':'blue','weight':2,'fillOpacity':0.4},
                       tooltip=f"{city1}: {area1} km²").add_to(m)

        if city2:
            gdf2 = get_city_shape(city2)
            if gdf2 is not None:
                area2 = calculate_area(gdf2)
                centroid2 = gdf2.geometry.centroid.iloc[0]

                folium.GeoJson(gdf2,
                               name=f"{city2} (original)",
                               style_function=lambda x: {'fillColor':'gray','color':'gray','weight':1,'fillOpacity':0.2},
                               tooltip=f"{city2} (original): {area2} km²").add_to(m)

                offset_x, offset_y = centroid1.x - centroid2.x, centroid1.y - centroid2.y
                gdf2_translated = gdf2.copy()
                gdf2_translated['geometry'] = gdf2.geometry.apply(lambda geom: translate(geom, offset_x, offset_y))

                folium.GeoJson(gdf2_translated,
                               name=f"{city2} (translated)",
                               style_function=lambda x: {'fillColor':'red','color':'red','weight':2,'fillOpacity':0.4},
                               tooltip=f"{city2} (translated): {area2} km²").add_to(m)

                diff = ((area2 - area1)/area1)*100
                if diff > 0:
                    st.info(f"🌐 **{city2}** is **{diff:.1f}% larger** than **{city1}**.")
                else:
                    st.info(f"🌐 **{city2}** is **{abs(diff):.1f}% smaller** than **{city1}**.")

        folium.LayerControl('topright', collapsed=False).add_to(m)

        # Display map in Streamlit
        st_folium(m, width=700, height=500)

        # Download map as HTML
        map_html = m.get_root().render()
        st.download_button(label="🌍 Download map HTML",
                           data=map_html,
                           file_name='city_size_comparison.html',
                           mime='text/html')

# Disclaimer with data source and creator
st.markdown(
    """
    <hr>
    <div style="text-align:center;font-size:12px;color:gray;">
        The displayed areas have been calculated using data from
        <a href="https://www.openstreetmap.org/copyright" target="_blank">
        OpenStreetMap (Nominatim)</a>.
    </div>
    <br>
    <div style="text-align:center;">
        Website by: <a href="https://www.linkedin.com/in/mauricio-montilla-garc%C3%ADa-2953b1206/" target="_blank">Mauricio Montilla García</a>
    </div>
    """, unsafe_allow_html=True
)
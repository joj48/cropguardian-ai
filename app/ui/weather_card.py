# weather_card.py — CropGuardian AI Meteorological Renderer
import streamlit as st

def get_risk_colored_string(level: str) -> str:
    """Helper returning a standard color markdown string based on risk level."""
    l = level.lower()
    if "very high" in l or "high" in l:
        return f":red[{level}]"
    elif "medium" in l or "moderate" in l:
        return f":orange[{level}]"
    elif "low" in l or "healthy" in l:
        return f":green[{level}]"
    else:
        return f":grey[{level}]"

def render_weather_card(weather_data: dict, risk_data: dict = None):
    """Renders location-aware weather conditions and environmental risk assessments."""
    st.markdown("<div class='cg-section-label'>Environmental Intelligence</div>", unsafe_allow_html=True)
    
    if weather_data and "error" not in weather_data:
        w = weather_data.get("weather", {})
        st.caption(f"📍 Location Context: **{weather_data.get('location', 'Unknown')}**")
        
        # Grid layout for metrics
        wc1, wc2, wc3, wc4 = st.columns(4)
        with wc1:
            st.metric("🌡 Temperature", f"{w.get('temperature','—')}°C", delta=f"Feels like {w.get('feels_like','—')}°C", delta_color="off")
        with wc2:
            st.metric("💧 Humidity", f"{w.get('humidity','—')}%")
        with wc3:
            st.metric("🌧 Precipitation", f"{w.get('precipitation','—')} mm")
        with wc4:
            st.metric("💨 Wind Speed", f"{w.get('wind_speed','—')} km/h")
            
        if w.get("cloud_cover") is not None:
            st.caption(
                f"Cloud cover: {w.get('cloud_cover')}%  ·  "
                f"Gusts: {w.get('wind_gusts','—')} km/h  ·  "
                f"Pressure: {w.get('pressure','—')} hPa"
            )
    else:
        st.info("🌦 Weather data unavailable. Provide a farm location during analysis to enable environmental metrics.")

    # Risk Breakdown
    if risk_data and "error" not in risk_data:
        st.markdown("<div class='cg-section-label' style='margin-top:16px;'>Disease Risk Factors</div>", unsafe_allow_html=True)
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            with st.container(border=True):
                st.markdown(f"🍄 **Fungal Risk**")
                st.markdown(f"Level: {get_risk_colored_string(risk_data.get('fungal_risk', 'Unknown'))}")
        with rc2:
            with st.container(border=True):
                st.markdown(f"🦠 **Bacterial Risk**")
                st.markdown(f"Level: {get_risk_colored_string(risk_data.get('bacterial_risk', 'Unknown'))}")
        with rc3:
            with st.container(border=True):
                st.markdown(f"🌡️ **Heat Stress**")
                st.markdown(f"Level: {get_risk_colored_string(risk_data.get('heat_stress_risk', 'Unknown'))}")
                
        # Risk reasons
        reasons = risk_data.get("reasons", [])
        if reasons:
            st.markdown("")
            for reason in reasons:
                st.markdown(f"<div class='cg-reason'>• {reason}</div>", unsafe_allow_html=True)

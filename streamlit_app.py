"""Punto de entrada del dashboard (local y Streamlit Community Cloud).

Local:  streamlit run streamlit_app.py
Cloud:  Main file path = streamlit_app.py

Usamos st.navigation porque las páginas viven dentro del paquete
(src/marketpulse/dashboard/pages/) y no junto a este archivo.
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="MarketPulse", page_icon="📈", layout="wide")

PAGES = Path(__file__).parent / "src" / "marketpulse" / "dashboard"

nav = st.navigation(
    [
        st.Page(PAGES / "home.py", title="Inicio", icon="🏠", default=True),
        st.Page(PAGES / "pages" / "1_Mercado.py", title="Mercado", icon="📈"),
        st.Page(
            PAGES / "pages" / "2_Portafolio_simulado.py", title="Portafolio simulado", icon="💼"
        ),
        st.Page(PAGES / "pages" / "3_Salud_del_pipeline.py", title="Salud del pipeline", icon="🩺"),
        st.Page(
            PAGES / "pages" / "4_Pregunta_a_tus_datos.py", title="Pregunta a tus datos", icon="💬"
        ),
    ]
)
nav.run()

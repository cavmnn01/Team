import streamlit as st
st.sidebar.write("Sidebar")
st.markdown('''
<style>
header[data-testid="stHeader"]{background:transparent!important;box-shadow:none!important;pointer-events:none!important;}
[data-testid="collapsedControl"]{pointer-events:auto!important; background: red !important; display: flex !important;}
</style>
''', unsafe_allow_html=True)

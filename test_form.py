import streamlit as st
st.markdown('''
<style>
.mybtn { background: red; color: white; padding: 10px; cursor: pointer; }
</style>
<form action="" method="GET">
<input type="text" name="user" value="testuser">
<button type="submit" class="mybtn">Click Me</button>
</form>
'''
, unsafe_allow_html=True)
st.write(st.query_params)

import os

with open('ui/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will replace the pointer-events CSS logic to make the collapsed control explicitly visible
import re
old_css = '''header[data-testid="stHeader"]{background:transparent!important;box-shadow:none!important;pointer-events:none!important;}
header[data-testid="stHeader"] [data-testid="collapsedControl"]{pointer-events:auto!important;}
[data-testid="stToolbar"]{display:none!important;}'''

new_css = '''header[data-testid="stHeader"]{background:transparent!important;box-shadow:none!important;pointer-events:none!important;}
[data-testid="collapsedControl"]{
    pointer-events:auto!important;
    background:#0284c7!important;
    color:#ffffff!important;
    border-radius:8px!important;
    box-shadow:0 4px 14px rgba(2,132,199,0.3)!important;
    opacity:1!important;
    z-index:999999!important;
    display:flex!important;
}
[data-testid="stToolbar"]{display:none!important;}'''

if old_css in content:
    new_content = content.replace(old_css, new_css)
else:
    # Just in case it was formatted differently
    print("Could not find exact CSS string, doing a regex replace...")
    new_content = re.sub(
        r'header\[data-testid="stHeader"\].*?\[data-testid="stToolbar"\]\{display:none!important;\}',
        new_css, content, flags=re.DOTALL
    )

with open('ui/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Updated CSS for collapsedControl")

import sass
import os
import sys

try:
    print("🚀 Compiling SCSS...")
    css = sass.compile(filename='app/static/scss/main.scss', output_style='expanded')
    with open('app/static/css/main.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("✅ Successfully compiled app/static/scss/main.scss to app/static/css/main.css")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

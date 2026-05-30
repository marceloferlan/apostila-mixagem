import glob
import re
import os
import subprocess

def build_ebook():
    base_dir = "/Users/macbookpro/Documents/Produção Musical/Apostila Mixagem"
    docs_dir = "/Users/macbookpro/Documents/Produção Musical/docs"
    
    # Ensure docs dir exists
    os.makedirs(docs_dir, exist_ok=True)
    
    files = sorted(glob.glob(os.path.join(base_dir, "modulo-*.html")))
    if not files:
        print("Nenhum modulo encontrado.")
        return

    # Extract head and styles from the first file
    with open(files[0], 'r', encoding='utf-8') as f:
        first_content = f.read()

    head_match = re.search(r'(<!DOCTYPE html>.*?</head>)', first_content, re.DOTALL | re.IGNORECASE)
    if head_match:
        head_html = head_match.group(1)
    else:
        head_html = "<!DOCTYPE html><html><head><meta charset='UTF-8'></head>"
        
    # Inject print CSS before </head>
    print_css = """
    <style>
    @media print {
        .top-header, .sidebar, .sidebar-overlay, .next-module, .menu-toggle, .bg-ambient { display: none !important; }
        .app-layout { padding-top: 0 !important; display: block !important; }
        .main-content { margin-left: 0 !important; padding: 0 !important; display: block !important; }
        body { 
            background: #0a0a0f !important; 
            color: #f0f0f8 !important; 
            -webkit-print-color-adjust: exact !important; 
            print-color-adjust: exact !important; 
        }
        .module-hero { 
            page-break-before: always; 
            padding-top: 2cm !important; 
            border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        }
        /* Ensure first module doesn't add a blank page before it */
        main:first-of-type .module-hero { page-break-before: avoid; }
        
        .section-block { page-break-inside: avoid; }
        .callout { page-break-inside: avoid; }
        .param-table-wrapper { page-break-inside: avoid; }
        .compare-grid { page-break-inside: avoid; }
        .ps-grid { page-break-inside: avoid; }
        .checklist { page-break-inside: avoid; }
        
        /* Force background colors and gradients */
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    }
    </style>
    """
    head_html = head_html.replace("</head>", f"{print_css}\n</head>")

    combined_html = [head_html, "<body>"]

    for idx, filepath in enumerate(files):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract <main> content
        main_match = re.search(r'(<main[^>]*>.*?</main>)', content, re.DOTALL | re.IGNORECASE)
        if main_match:
            main_content = main_match.group(1)
            # Remove nav-buttons and next-module elements so they don't appear in the PDF
            main_content = re.sub(r'<div class="next-module[^>]*>.*?</div>\s*</div>', '', main_content, flags=re.DOTALL)
            main_content = re.sub(r'<div class="next-module.*?</section>', '</section>', main_content, flags=re.DOTALL) # Fallback
            
            # Make sure all animations are visible immediately for print
            main_content = main_content.replace('opacity:0', 'opacity:1')
            main_content = main_content.replace('class="section-block"', 'class="section-block visible"')
            main_content = main_content.replace('animate-in', '')
            
            combined_html.append(main_content)

    combined_html.append("</body></html>")

    out_html = "/tmp/ebook_combined.html"
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write("\n".join(combined_html))
        
    print(f"Generated {out_html}")
    
    # Render PDF
    out_pdf = os.path.join(docs_dir, "Apostila_Mixagem_Completa.pdf")
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf}",
        f"file://{out_html}"
    ]
    
    print(f"Running: {' '.join(chrome_cmd)}")
    subprocess.run(chrome_cmd, check=True)
    print(f"E-book gerado com sucesso em: {out_pdf}")

if __name__ == "__main__":
    build_ebook()

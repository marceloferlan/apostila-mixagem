import markdown
import os
import re
import subprocess
import urllib.request
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Dicionário estático com as descrições profissionais dos módulos para o sumário
MODULE_DESCRIPTIONS = {
    "01": "Estabelecer a fundação técnica e organizacional antes de iniciar a mixagem: gain staging correto, organização de sessões, color coding e a arquitetura ideal de buses e templates.",
    "02": "Calibrar os ouvidos para reconhecer desequilíbrios espectrais e posicionamento tridimensional: monitoração profissional, mono check, uso de faixas de referência e ear training.",
    "03": "Eliminar imperfeições e ruídos técnicos que degradam a clareza do mix: noise floor, eliminação de vazamentos (bleed), uso de gates e expanders, e técnicas de alinhamento de fase.",
    "04": "Construir um alicerce rítmico forte com punch e definição individual de peças: equalização e compressão cirúrgicas, controle de ambiências e o uso de compressão paralela.",
    "05": "Estabelecer uma base de graves robusta e focada, integrada ao bumbo: gerenciamento dinâmico de subgraves, saturação harmônica, sidechain inteligente e separação de frequências (low-end split).",
    "06": "Posicionar as guitarras de forma ampla e aberta, liberando espaço central para a voz e a caixa: abertura estéreo (double tracks), equalização midrange e controle de palm mutes.",
    "07": "Preservar a organicidade, o brilho natural e o dinamismo rítmico do violão: blend acústico ideal (Mic vs. DI), compressão óptica transparente e espacialização tridimensional.",
    "08": "Gerenciar teclados, pianos e sintetizadores que competem na faixa de médios: prevenção de mascaramento harmônico, processamento Mid/Side e controle estéreo de modulações.",
    "09": "Capturar o calor de peito, domar a dinâmica e dar autoridade à voz principal masculina: compressão em série (1176 + LA-2A), controle de sibilâncias e Abbey Road reverb.",
    "10": "Preservar a delicadeza de vocais femininos, domar frequências duras em belting e injetar um brilho aéreo superior: controle dinâmico da zona áspera e a técnica do shimmer reverb.",
    "11": "Unificar as pistas e aplicar a 'cola' invisível que transforma faixas individuais em um mix comercial coeso: compressão e equalização de mix bus (SSL Glue, Smile EQ) e saturação.",
    "12": "Garantir a integridade matemática da exportação do áudio e preparar as entregas profissionais: exportação de stems, dithering e targets de loudness por plataforma."
}

def generate_pdf():
    docs_dir = "/Users/macbookpro/Documents/Produção Musical/docs"
    md_file = os.path.join(docs_dir, "Apostila_Mixagem_Livro.md")
    css_file = os.path.join(docs_dir, "pdf-style.css")
    
    # Arquivos temporários e finais
    temp_html = os.path.join(docs_dir, "ebook_temp.html")
    temp_unpaginated_pdf = os.path.join(docs_dir, "temp_unpaginated.pdf")
    temp_official_pdf = os.path.join(docs_dir, "temp_unpaginated_official.pdf")
    temp_footers_pdf = os.path.join(docs_dir, "temp_footers.pdf")
    temp_paginated_book = os.path.join(docs_dir, "temp_paginated_book.pdf")
    
    cover_pdf_path = os.path.join(docs_dir, "Capa_Ebook_Apostila_Mixagem.pdf")
    final_output_pdf = os.path.join(docs_dir, "Apostila_Mixagem_Ebook.pdf")

    # 1. Carregar Markdown original
    print("Carregando arquivo Markdown original...")
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Converter para HTML básico
    html_content = markdown.markdown(md_text, extensions=['tables'])

    # Encontrar todos os módulos no HTML para estruturar o Sumário
    # Regex para capturar tags H1 como <h1>Módulo 01: Título</h1>
    modules = re.findall(r'<h1>(Módulo (\d+)):?\s*(.*?)</h1>', html_content)
    
    # 2. Injetar IDs previsíveis e classes especiais nos cabeçalhos de módulo H1
    def replacer(match):
        modulo_str = match.group(1) # "Módulo XX"
        num_str = match.group(2)    # "XX"
        titulo = match.group(3)     # "Título"
        return f'<h1 id="modulo-{num_str}" class="module-header">{modulo_str}: {titulo}</h1>'
        
    html_content = re.sub(r'<h1>(Módulo (\d+)):?\s*(.*?)</h1>', replacer, html_content)

    # 3. Ler arquivo CSS
    with open(css_file, "r", encoding="utf-8") as f:
        css_text = f.read()

    # ==========================================
    # PASSO A: Geração Temporária para Mapeamento
    # ==========================================
    print("\n[Passo A] Gerando Sumário temporário para mapeamento de páginas...")
    
    # Sumário temporário contendo placeholders nos números de páginas
    toc_items_temp = []
    for modulo_str, num_str, titulo in modules:
        desc = MODULE_DESCRIPTIONS.get(num_str, "")
        clean_titulo = re.sub(r'<[^>]*>', '', titulo)
        toc_items_temp.append(f"""
        <div class="toc-item">
            <div class="toc-header">
                <span class="toc-name"><a href="#modulo-{num_str}" class="toc-link">{modulo_str}: {clean_titulo}</a></span>
                <span class="toc-dots"></span>
                <span class="toc-page-num">999</span>
            </div>
            <p class="toc-description">{desc}</p>
        </div>
        """)
        
    toc_html_temp = f"""
    <div class="toc-page">
        <h1 class="toc-title">Sumário</h1>
        <div class="toc-list">
            {"".join(toc_items_temp)}
        </div>
    </div>
    """

    full_html_temp = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Apostila de Mixagem Profissional</title>
    <style>
        {css_text}
    </style>
</head>
<body>
    {toc_html_temp}
    <div class="book-content">
        {html_content}
    </div>
</body>
</html>
"""

    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html_temp)

    # Compilar temporariamente via Chrome Headless
    print("Compilando PDF temporário de mapeamento...")
    file_url = "file:" + urllib.request.pathname2url(temp_html)
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-web-security",
        "--no-pdf-header-footer",
        "--allow-file-access-from-files",
        f"--print-to-pdf={temp_unpaginated_pdf}",
        file_url
    ]
    subprocess.run(chrome_cmd, check=True)

    # ==========================================
    # PASSO B: Escaneamento Físico de Páginas
    # ==========================================
    print("\n[Passo B] Escaneando PDF temporário para encontrar inícios de módulos...")
    reader = PdfReader(temp_unpaginated_pdf)
    module_pages = {}
    
    # Escaneia a partir da página física 3 (índice 2) para evitar o Sumário (que pode ocupar págs 1 e 2)
    last_found_page = 2  # Página física 3 (0-indexed index 2)
    for i in range(1, 13):
        term1 = f"Módulo {i:02d}"
        term2 = f"Modulo {i:02d}"
        found = False
        for idx in range(last_found_page, len(reader.pages)):
            page_text = reader.pages[idx].extract_text()
            if term1 in page_text or term2 in page_text:
                module_pages[i] = idx + 1  # 1-indexed página física do Chrome
                last_found_page = idx  # A partir daqui para os próximos módulos
                found = True
                break
        
        # Fallback de segurança se algum módulo não for localizado textualmente
        if not found:
            prev_page = module_pages.get(i - 1, 1)
            module_pages[i] = prev_page + 6
            print(f"  [Aviso] Módulo {i:02d} não encontrado textualmente. Usando estimativa: pág {module_pages[i]}")
        else:
            print(f"  Módulo {i:02d} mapeado com sucesso para a página física {module_pages[i]} do Chrome.")

    # Calcular o offset para que a primeira página do Módulo 01 seja a Página 1 do livro
    # O Sumário ocupa a página física 1. O Módulo 01 costuma começar na página física 2.
    m1_phys_page = module_pages.get(1, 2)
    offset = m1_phys_page - 1
    print(f"Página física de início do Módulo 01: {m1_phys_page}. Offset de paginação calculado: {offset}")

    # ==========================================
    # PASSO C: Geração Oficial do Sumário Real
    # ==========================================
    print("\n[Passo C] Reconstruindo HTML oficial com sumário paginado...")
    
    toc_items_official = []
    for modulo_str, num_str, titulo in modules:
        m_num = int(num_str)
        phys_page = module_pages.get(m_num, m1_phys_page)
        book_page = phys_page - offset
        if book_page < 1:
            book_page = 1
            
        desc = MODULE_DESCRIPTIONS.get(num_str, "")
        clean_titulo = re.sub(r'<[^>]*>', '', titulo)
        toc_items_official.append(f"""
        <div class="toc-item">
            <div class="toc-header">
                <span class="toc-name"><a href="#modulo-{num_str}" class="toc-link">{modulo_str}: {clean_titulo}</a></span>
                <span class="toc-dots"></span>
                <span class="toc-page-num">{book_page}</span>
            </div>
            <p class="toc-description">{desc}</p>
        </div>
        """)
        
    toc_html_official = f"""
    <div class="toc-page">
        <h1 class="toc-title">Sumário</h1>
        <div class="toc-list">
            {"".join(toc_items_official)}
        </div>
    </div>
    """

    full_html_official = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Apostila de Mixagem Profissional</title>
    <style>
        {css_text}
    </style>
</head>
<body>
    {toc_html_official}
    <div class="book-content">
        {html_content}
    </div>
</body>
</html>
"""

    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html_official)

    # Compilar o PDF Oficial (limpo, sem rodapés)
    print("Compilando PDF oficial nativo do Chrome...")
    chrome_cmd_official = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-web-security",
        "--no-pdf-header-footer",
        "--allow-file-access-from-files",
        f"--print-to-pdf={temp_official_pdf}",
        file_url
    ]
    subprocess.run(chrome_cmd_official, check=True)

    # ==========================================
    # PASSO D: Estamparia Programática do Rodapé
    # ==========================================
    print("\n[Passo D] Gerando e estampando rodapés elegantes...")
    
    reader_official = PdfReader(temp_official_pdf)
    num_pages = len(reader_official.pages)
    
    # Gerar PDF de rodapés usando reportlab
    c = canvas.Canvas(temp_footers_pdf, pagesize=A4)
    width, height = A4 # 595.27 x 841.89
    
    for idx in range(num_pages):
        p_phys = idx + 1 # Página física do Chrome (1-based)
        
        # Omitir rodapé nas páginas que antecedem o Módulo 1 (ex: Sumário)
        if p_phys < m1_phys_page:
            c.showPage()
            continue
            
        book_page = p_phys - offset
        
        # Estilização profissional e minimalista (tons elegantes de cinza)
        c.setFont("Helvetica", 8.5)
        c.setFillColorRGB(0.392, 0.455, 0.545) # Cor #64748b
        
        # Rodapé Esquerdo: Título
        c.drawString(56.7, 40, "Apostila de Mixagem Profissional") # 56.7pt = 20mm
        
        # Rodapé Direito: Página X
        page_str = f"Página {book_page}"
        c.setFont("Helvetica-Bold", 8.5)
        text_width = c.stringWidth(page_str, "Helvetica-Bold", 8.5)
        c.drawString(width - 56.7 - text_width, 40, page_str)
        
        c.showPage()
        
    c.save()

    # Mesclar os rodapés por cima do PDF gerado pelo Chrome
    reader_book = PdfReader(temp_official_pdf)
    reader_footers = PdfReader(temp_footers_pdf)
    writer_paginated = PdfWriter()
    
    for i in range(len(reader_book.pages)):
        page = reader_book.pages[i]
        footer = reader_footers.pages[i]
        page.merge_page(footer)
        writer_paginated.add_page(page)
        
    with open(temp_paginated_book, "wb") as f:
        writer_paginated.write(f)

    # ==========================================
    # PASSO E: Anexar Capa Oficial & Salvar PDF Final
    # ==========================================
    print("\n[Passo E] Consolidando PDF com a Capa Oficial...")
    final_writer = PdfWriter()
    
    # 1. Tenta anexar a capa oficial em PDF do usuário
    cover_attached = False
    if os.path.exists(cover_pdf_path):
        cover_reader = PdfReader(cover_pdf_path)
        # Tamanho A4 padrão gerado pelas páginas do Chrome (aprox. 595.27 x 841.89 pt)
        target_width = 595.27
        target_height = 841.89
        
        for page in cover_reader.pages:
            # Redimensiona a capa para A4 físico uniforme de forma profissional
            page.scale_to(width=target_width, height=target_height)
            final_writer.add_page(page)
        cover_attached = True
        print(f"Capa oficial '{os.path.basename(cover_pdf_path)}' redimensionada para A4 e anexada com sucesso!")
    else:
        print(f"[Aviso] Capa oficial não encontrada em {cover_pdf_path}!")
        
    # 2. Anexa as páginas paginadas do livro (Sumário + Módulos)
    book_reader = PdfReader(temp_paginated_book)
    for page in book_reader.pages:
        final_writer.add_page(page)
        
    # Salva no arquivo final oficial
    with open(final_output_pdf, "wb") as f:
        final_writer.write(f)
        
    print(f"\n===========================================")
    print(f"APOSTILA GERADA COM SUCESSO!")
    print(f"Arquivo final: {final_output_pdf}")
    if cover_attached:
        print(f"Nota: Capa oficial anexada. A paginação começa no Módulo 01 (física {m1_phys_page + len(cover_reader.pages)}) como Página 1.")
    else:
        print(f"Nota: Capa oficial ausente. A paginação começa no Módulo 01 (física {m1_phys_page}) como Página 1.")
    print(f"===========================================")

    # ==========================================
    # Limpeza dos Arquivos Temporários
    # ==========================================
    print("\nLimpando arquivos temporários...")
    for path in [temp_html, temp_unpaginated_pdf, temp_official_pdf, temp_footers_pdf, temp_paginated_book]:
        if os.path.exists(path):
            os.remove(path)
    print("Limpeza concluída.")

if __name__ == "__main__":
    generate_pdf()

import glob
import os
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

def md(soup, **options):
    return MarkdownConverter(**options).convert(str(soup))

def build_md():
    base_dir = "/Users/macbookpro/Documents/Produção Musical/Apostila Mixagem"
    docs_dir = "/Users/macbookpro/Documents/Produção Musical/docs"
    
    os.makedirs(docs_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(base_dir, "modulo-*.html")))
    
    markdown_parts = []
    
    
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        main = soup.find('main', class_='main-content')
        
        if not main:
            continue
            
        # 1. Clean up elements we don't want in the ebook
        for el in main.select('.next-module, .nav-buttons, .progress-bar-container, script, style, .sidebar, .top-header, .dither-viz .dv-stage, .dither-viz .dv-controls, .gate-viz, .meter-container, .param-viz-container'):
            el.decompose()
            
        # 2. Convert Callouts
        for callout in main.select('.callout'):
            title_el = callout.find(class_='callout-title')
            body_el = callout.find(class_='callout-body') or callout.find(class_='callout-content')
            icon_el = callout.find(class_='callout-icon')
            
            icon = icon_el.get_text(strip=True) if icon_el else ''
            title = title_el.get_text(strip=True) if title_el else ''
            body = body_el.get_text(strip=True) if body_el and body_el != title_el else ''
            
            new_callout = soup.new_tag('blockquote')
            new_callout.append(BeautifulSoup(f"<p><strong>{icon} {title}</strong><br>{body}</p>", 'html.parser'))
            callout.replace_with(new_callout)

        # 2.5 Meter Demo (Modulo 01) → HTML table (not markdown inside div)
        for demo in main.select('.meter-demo'):
            t_el = demo.find(class_='meter-title')
            t_text = t_el.get_text(strip=True) if t_el else 'Gain Staging'
            
            table_html = f"<h4>{t_text}</h4><table><thead><tr><th>Status</th><th>Nível</th></tr></thead><tbody>"
            for ch in demo.select('.meter-channel'):
                lbl = ch.find(class_='meter-label')
                val = ch.find(class_='meter-value')
                if lbl and val:
                    table_html += f"<tr><td>{lbl.get_text(strip=True)}</td><td><strong>{val.get_text(strip=True)}</strong></td></tr>"
            table_html += "</tbody></table>"
            demo.replace_with(BeautifulSoup(table_html, 'html.parser'))

        # 2.55 Freq Cards (Modulo 02) → structured block with problems as sub-list
        for card in main.select('.freq-card'):
            badge   = card.find(class_='freq-badge')
            rng     = card.find(class_='freq-range')
            name    = card.find(class_='freq-name')
            desc    = card.find(class_='freq-desc')
            probs   = card.find(class_='freq-problems')
            
            badge_txt = badge.get_text(strip=True) if badge else ''
            rng_txt   = rng.get_text(strip=True)   if rng   else ''
            name_txt  = name.get_text(strip=True)  if name  else ''
            desc_txt  = desc.get_text(strip=True)  if desc  else ''
            
            new_html = f"<h4>{badge_txt} — {rng_txt}: {name_txt}</h4><p>{desc_txt}</p>"
            
            if probs:
                new_html += "<p><strong>⚠️ Problemas comuns:</strong></p><ul>"
                for li in probs.select('li'):
                    new_html += f"<li>{li.get_text(strip=True)}</li>"
                new_html += "</ul>"
            
            card.replace_with(BeautifulSoup(new_html, 'html.parser'))

        # 2.6 Workout Card (Modulo 02) → numbered list
        for wk in main.select('.workout-card'):
            hdr_text_el = wk.find(class_='workout-header-text')
            hdr_sub_el  = wk.find(class_='workout-header-sub')
            hdr_text = hdr_text_el.get_text(strip=True) if hdr_text_el else 'Rotina'
            hdr_sub  = hdr_sub_el.get_text(strip=True)  if hdr_sub_el  else ''
            
            new_ol = soup.new_tag('ol')
            for ex in wk.select('.workout-exercise'):
                name = ex.find(class_='exercise-name')
                desc = ex.find(class_='exercise-desc')
                tip  = ex.find(class_='exercise-tip')
                
                n_txt = name.get_text(strip=True) if name else ''
                d_txt = desc.get_text(strip=True) if desc else ''
                t_txt = tip.get_text(strip=True)  if tip  else ''
                
                li = soup.new_tag('li')
                li.append(BeautifulSoup(f"<strong>{n_txt}</strong><br>{d_txt}<br><em>{t_txt}</em>", 'html.parser'))
                new_ol.append(li)
            
            new_div = soup.new_tag('div')
            new_div.append(BeautifulSoup(f"<h4>🏋️ {hdr_text}</h4><p><em>{hdr_sub}</em></p>", 'html.parser'))
            new_div.append(new_ol)
            wk.replace_with(new_div)

        # 2.7 Color Grid (Modulo 01) → compact table
        for grid in main.select('.color-grid'):
            rows = []
            for chip in grid.select('.color-chip'):
                c_name = chip.find(class_='color-name')
                c_desc = chip.find(class_='color-desc')
                dot    = chip.find(class_='color-dot')
                
                color_hex = ''
                if dot and dot.get('style'):
                    import re as _re
                    m = _re.search(r'background:\s*(#[0-9a-fA-F]+)', dot.get('style', ''))
                    if m:
                        color_hex = m.group(1)
                
                name_txt = c_name.get_text(strip=True) if c_name else ''
                desc_txt = c_desc.get_text(strip=True) if c_desc else ''
                rows.append(f"| ● | **{name_txt}** | {desc_txt} |")
            
            table_html = "<table><thead><tr><th></th><th>Cor</th><th>Instrumento</th></tr></thead><tbody>"
            for chip in grid.select('.color-chip'):
                c_name = chip.find(class_='color-name')
                c_desc = chip.find(class_='color-desc')
                dot    = chip.find(class_='color-dot')
                
                color_hex = '#ccc'
                if dot and dot.get('style'):
                    import re as _re2
                    m2 = _re2.search(r'background:\s*(#[0-9a-fA-F]+)', dot.get('style', ''))
                    if m2:
                        color_hex = m2.group(1)
                
                name_txt = c_name.get_text(strip=True) if c_name else ''
                desc_txt = c_desc.get_text(strip=True) if c_desc else ''
                table_html += f"<tr><td style='color:{color_hex}'>●</td><td><strong>{name_txt}</strong></td><td>{desc_txt}</td></tr>"
            table_html += "</tbody></table>"
            grid.replace_with(BeautifulSoup(table_html, 'html.parser'))

        # 3. Trim Cards (Modulo 03)
        for card in main.select('.trim-card'):
            inst = card.find(class_='trim-instrument')
            name = card.find(class_='trim-name')
            t_text = f"{inst.get_text(strip=True)} — {name.get_text(strip=True)}" if inst and name else ""
            
            new_ul = soup.new_tag('ul')
            for row in card.select('.trim-row'):
                lbl = row.find(class_='trim-row-label')
                val = row.find(class_='trim-value')
                if lbl and val:
                    li = soup.new_tag('li')
                    li.append(BeautifulSoup(f"<strong>{lbl.get_text(strip=True)}</strong>: {val.get_text(strip=True)}", 'html.parser'))
                    new_ul.append(li)
                    
            new_card = soup.new_tag('div')
            if t_text:
                new_card.append(BeautifulSoup(f"<h4>{t_text}</h4>", 'html.parser'))
            new_card.append(new_ul)
            card.replace_with(new_card)

        # 4. Phase Cards
        for card in main.select('.phase-card'):
            lbl = card.find(class_='phase-label')
            status = card.find(class_='phase-status')
            desc = card.find(class_='phase-desc')
            
            t_text = lbl.get_text(strip=True) if lbl else ""
            s_text = status.get_text(strip=True) if status else ""
            d_text = desc.get_text(strip=True) if desc else ""
            
            new_card = soup.new_tag('div')
            new_card.append(BeautifulSoup(f"<h4>{t_text}</h4><p><strong>{s_text}</strong><br>{d_text}</p>", 'html.parser'))
            card.replace_with(new_card)

        # 5. Checklist Items (convert to list items)
        for item in main.select('.checklist-item'):
            title = item.find(class_='check-title')
            desc = item.find(class_='check-desc')
            
            t_text = title.get_text(strip=True) if title else ''
            d_text = desc.get_text(strip=True) if desc else ''
            
            new_item = soup.new_tag('li')
            new_item.append(BeautifulSoup(f"<strong>[ ] {t_text}</strong>: {d_text}", 'html.parser'))
            item.replace_with(new_item)

        # Replace checklist wrapper with ul so list items render correctly
        for chk in main.select('.checklist'):
            header = chk.find(class_='checklist-header')
            h_text = header.get_text(strip=True) if header else ''
            if header:
                header.decompose()
            chk.name = 'ul'
            if h_text:
                chk.insert_before(BeautifulSoup(f"<h4>{h_text}</h4>", 'html.parser'))

        # 5.5 Harmonic Viz
        for viz in main.select('.harmonic-viz'):
            title = viz.find(class_='hv-title')
            t_text = title.get_text(strip=True) if title else "Comparação"
            
            new_ul = soup.new_tag('ul')
            for panel in viz.select('.hv-panel'):
                p_title = panel.find(class_='hv-panel-title')
                p_note = panel.find(class_='hv-note')
                
                pt_text = p_title.get_text(strip=True) if p_title else ""
                pn_text = p_note.get_text(strip=True) if p_note else ""
                
                li = soup.new_tag('li')
                li.append(BeautifulSoup(f"<strong>{pt_text}</strong>: {pn_text}", 'html.parser'))
                new_ul.append(li)
                
            new_div = soup.new_tag('div')
            new_div.append(BeautifulSoup(f"<h4>{t_text}</h4>", 'html.parser'))
            new_div.append(new_ul)
            viz.replace_with(new_div)

        # 6. Generic Cards (Compare, Monitor, Step Content)
        for card in main.select('.card, .compare-card, .monitor-card, .color-chip, .step-content, .compare-row'):
            # Find Title
            title = card.find(class_=['card-title', 'compare-header', 'monitor-name', 'color-name', 'step-title', 'compare-label'])
            # Find Body
            body = card.find(class_=['card-body', 'compare-body', 'monitor-desc', 'color-desc', 'step-desc', 'compare-value'])
            
            # Find Extra
            extra = card.find(class_=['monitor-best'])
            
            t_text = title.get_text(separator=' ', strip=True) if title else ''
            b_text = body.get_text(separator=' ', strip=True) if body else ''
            
            if extra and extra != body:
                b_text += f" <br><em>{extra.get_text(separator=' ', strip=True)}</em>"
                
            if not t_text and not b_text:
                continue
                
            new_card = soup.new_tag('div')
            if t_text:
                new_card.append(BeautifulSoup(f"<h4>{t_text}</h4>", 'html.parser'))
            if b_text:
                new_card.append(BeautifulSoup(f"<p>{b_text}</p>", 'html.parser'))
            
            card.replace_with(new_card)

        # 7. EQ Strips
        for strip in main.select('.eq-strip'):
            new_ul = soup.new_tag('ul')
            for band in strip.select('.eq-band'):
                freq = band.find(class_='eq-band-freq')
                typ = band.find(class_='eq-band-type')
                action = band.find(class_='eq-band-action')
                val = band.find(class_='eq-band-value')
                
                f_txt = freq.get_text(strip=True) if freq else ""
                t_txt = typ.get_text(strip=True) if typ else ""
                a_txt = action.get_text(strip=True) if action else ""
                v_txt = val.get_text(strip=True) if val else ""
                
                li = soup.new_tag('li')
                li.append(BeautifulSoup(f"<strong>{f_txt} {t_txt}</strong>: {a_txt} (<em>{v_txt}</em>)", 'html.parser'))
                new_ul.append(li)
            strip.replace_with(new_ul)

        # 8. Compressor Strips and Grids
        for strip in main.select('.comp-strip, .comp-grid'):
            new_ul = soup.new_tag('ul')
            for param in strip.select('.comp-param'):
                lbl = param.find(class_='comp-param-label')
                val = param.find(class_='comp-param-value')
                note = param.find(class_='comp-param-note')
                
                l_txt = lbl.get_text(strip=True) if lbl else ""
                v_txt = val.get_text(strip=True) if val else ""
                n_txt = note.get_text(strip=True) if note else ""
                
                li = soup.new_tag('li')
                li.append(BeautifulSoup(f"<strong>{l_txt}</strong>: {v_txt} (<em>{n_txt}</em>)", 'html.parser'))
                new_ul.append(li)
            strip.replace_with(new_ul)

        # 9. Fix Drum Titles, Comp Titles, and Tips
        for title in main.select('.drum-col-title, .comp-card-title, .genre-panel-title'):
            title.name = 'h4'
            
        for tip in main.select('.drum-tip, .comp-tip'):
            new_tip = soup.new_tag('blockquote')
            new_tip.append(BeautifulSoup(f"<p>{tip.get_text(strip=True)}</p>", 'html.parser'))
            tip.replace_with(new_tip)

        # 10. Genre Parameters (Modulo 05)
        for params in main.select('.genre-params'):
            new_ul = soup.new_tag('ul')
            for item in params.select('.gp-item'):
                lbl = item.find(class_='gp-label')
                val = item.find(class_='gp-value')
                note = item.find(class_='gp-note')
                
                l_txt = lbl.get_text(strip=True) if lbl else ""
                v_txt = val.get_text(strip=True) if val else ""
                n_txt = note.get_text(strip=True) if note else ""
                
                li = soup.new_tag('li')
                li.append(BeautifulSoup(f"<strong>{l_txt}</strong>: {v_txt} (<em>{n_txt}</em>)", 'html.parser'))
                new_ul.append(li)
            params.replace_with(new_ul)

        # 11. Sidechain/Parallel Diagrams
        for diagram in main.select('.sc-diagram, .parallel-diagram'):
            title = diagram.find(class_=['sc-title', 'pd-title'])
            t_text = title.get_text(strip=True) if title else "Diagrama de Fluxo"
            
            new_ul = soup.new_tag('ol')
            for node in diagram.select('.sc-node, .pd-node'):
                lbl = node.find(class_=['sc-node-label', 'pd-node-label'])
                sub = node.find(class_=['sc-node-sub', 'pd-node-sub'])
                
                l_txt = lbl.get_text(separator=' ', strip=True) if lbl else ""
                s_txt = sub.get_text(separator=' ', strip=True) if sub else ""
                
                li = soup.new_tag('li')
                li.append(BeautifulSoup(f"<strong>{l_txt}</strong> - {s_txt}", 'html.parser'))
                new_ul.append(li)
                
            new_div = soup.new_tag('div')
            new_div.append(BeautifulSoup(f"<h4>{t_text}</h4>", 'html.parser'))
            new_div.append(new_ul)
            diagram.replace_with(new_div)

        # 12. Fix subtitles (small tags in H2)
        for h2 in main.find_all('h2'):
            small = h2.find('small')
            if small:
                small_text = small.get_text(strip=True)
                small.extract()
                h2.string = h2.get_text(strip=True)
                h2.insert_after(BeautifulSoup(f"<p><em>{small_text}</em></p>", 'html.parser'))

        # 13. Fix Floating Icons (Section, Drum, Compare, Monitor)
        for header in main.select('.section-header'):
            icon = header.find(class_=lambda x: x and 'section-icon' in x)
            title = header.find(class_='section-title')
            if icon and title:
                i_txt = icon.get_text(strip=True)
                icon.decompose()
                title.insert(0, f"{i_txt} ")
                
        for header in main.select('.drum-piece-header'):
            icon = header.find(class_='drum-piece-icon')
            title = header.find(class_='drum-piece-name')
            if icon and title:
                i_txt = icon.get_text(strip=True)
                icon.decompose()
                title.insert(0, f"{i_txt} ")

        for card in main.select('.compare-card'):
            icon = card.find(class_='compare-icon')
            title = card.find(class_='compare-header')
            if icon and title:
                i_txt = icon.get_text(strip=True)
                icon.decompose()
                title.insert(0, f"{i_txt} ")
                
        for card in main.select('.monitor-card'):
            icon = card.find(class_='monitor-icon')
            title = card.find(class_='monitor-name')
            if icon and title:
                i_txt = icon.get_text(strip=True)
                icon.decompose()
                title.insert(0, f"{i_txt} ")

        # 14. Merge Module Badge into Main Title
        import re
        badge = main.find(class_='module-badge')
        title = main.find(class_='module-title')
        if badge and title:
            # Remove the emoji span inside the badge
            badge_span = badge.find('span')
            if badge_span:
                badge_span.decompose()
                
            b_txt = badge.get_text(strip=True)
            # Remove anything in parenthesis, e.g. "MÓDULO 11 (FINALIZAÇÃO)" -> "MÓDULO 11"
            b_txt = re.sub(r'\(.*?\)', '', b_txt).strip()
            
            # Format as "Módulo XX"
            b_txt = b_txt.title()
            
            badge.decompose()
            # Collect existing title text, strip whitespace, then prepend badge prefix
            title_text = title.get_text(separator=' ', strip=True)
            # Clear all children of the title and set clean content
            title.clear()
            title.append(f"{b_txt}: {title_text}")

        # 15. Convert to markdown
        # Only strip div and section, but leave semantics like strong, em, ul, li
        md_text = md(main, strip=['div', 'span', 'section', 'header', 'label'])
        
        # Cleanup extra newlines
        md_text = md_text.replace('\n\n\n', '\n\n')
        
        # Remove ### and #### markers anywhere in the line (including inside list items like "1. #### Title")
        import re as _re_h
        md_text = _re_h.sub(r'#{3,4} ', '', md_text)
        
        # Ensure blank line before each numbered list item N. (N >= 2) when it follows content
        # This prevents paragraph descriptions from gluing to the next item title in PDF
        md_text = _re_h.sub(r'([^\n])\n(\d+\. )', r'\1\n\n\2', md_text)

        
        markdown_parts.append(md_text)
        markdown_parts.append("\n\n<div style='page-break-before: always;'></div>\n\n")

    out_file = os.path.join(docs_dir, "Apostila_Mixagem_Livro.md")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_parts))
        
    print(f"Livro Markdown gerado com sucesso em: {out_file}")

if __name__ == "__main__":
    build_md()

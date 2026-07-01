import streamlit as st
import pandas as pd
import io
import urllib.parse

st.set_page_config(page_title="Content Gap - Ahrefs & Senuto", layout="wide")

st.title("Content Gap - Ahrefs & Senuto Analiza")

st.markdown("""
Aplikacja pozwala na wygenerowanie linków do Ahrefs i Senuto dla podanych adresów URL, 
a następnie wgranie eksportów z obu narzędzi i automatyczne utworzenie pliku XLSX łączącego te dane.
""")

st.header("1. Wprowadź listę adresów URL")
urls_input = st.text_area("Wklej adresy URL (jeden pod drugim):", height=150)

if urls_input.strip():
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    urls = list(dict.fromkeys(urls)) # Usunięcie duplikatów z zachowaniem kolejności
    
    st.header("2. Tabela linków do analizy")
    st.write("Kliknij w wygenerowane linki dla każdego adresu URL, aby przejść bezpośrednio do narzędzi, a następnie wyeksportuj dane i pobierz na dysk.")
    
    # Tworzenie tabeli z linkami
    links_data = []
    for url in urls:
        encoded_url = urllib.parse.quote(url)
        ahrefs_url = f"https://app.ahrefs.com/site-explorer/organic-keywords?brandedMode=all&chartGranularity=monthly&chartInterval=year2&chartMetric=Keywords&compareDate=dontCompare&country=pl&currentDate=today&dataMode=keywords&hiddenColumns=AllIntents%7C%7CCPC%7C%7CEntities%7C%7CKD%7C%7COtherIntents%7C%7CPaidTraffic%7C%7CPositionHistory%7C%7CSF%7C%7CUserIntents&intentsAttrs=&keywordRules=&limit=100&localMode=all&mainOnly=0&mode=exact&multipleUrlsOnly=0&offset=0&performanceChartTopPosition=top11_20%7C%7Ctop21_50%7C%7Ctop3%7C%7Ctop4_10&positionChanges=&sort=OrganicTrafficInitial&sortDirection=desc&target={encoded_url}&urlRules=&volume=10-&volume_type=average"
        senuto_url = f"https://app.senuto.com/visibility-analysis/positions?domain={encoded_url}&fetch_mode=url&country_id=200"
        
        links_data.append({
            "Adres URL": url,
            "Ahrefs Link": ahrefs_url,
            "Senuto Link": senuto_url
        })
        
    df_links = pd.DataFrame(links_data)
    
    import json
    import streamlit.components.v1 as components
    
    ahrefs_urls_list = [d["Ahrefs Link"] for d in links_data]
    senuto_urls_list = [d["Senuto Link"] for d in links_data]
    
    html_code = f"""
    <div style="display:flex; gap:10px; margin-bottom: 10px; font-family: sans-serif;">
        <button onclick='openAhrefs()' style='padding:10px 20px; background-color:#ff4b4b; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;'>Otwórz wszystkie linki (Ahrefs)</button>
        <button onclick='openSenuto()' style='padding:10px 20px; background-color:#1c83e1; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;'>Otwórz wszystkie linki (Senuto)</button>
    </div>
    <script>
        var ahrefs_links = {json.dumps(ahrefs_urls_list)};
        var senuto_links = {json.dumps(senuto_urls_list)};
        
        function openAhrefs() {{
            ahrefs_links.forEach(function(link) {{
                window.open(link, '_blank');
            }});
        }}
        
        function openSenuto() {{
            senuto_links.forEach(function(link) {{
                window.open(link, '_blank');
            }});
        }}
    </script>
    """
    components.html(html_code, height=60)
    
    # Używamy st.dataframe ze specjalną konfiguracją kolumn do klikania w linki
    st.dataframe(
        df_links,
        column_config={
            "Ahrefs Link": st.column_config.LinkColumn("🔗 Otwórz w Ahrefs", display_text="Przejdź do Ahrefs"),
            "Senuto Link": st.column_config.LinkColumn("🔗 Otwórz w Senuto", display_text="Przejdź do Senuto")
        },
        hide_index=True,
        use_container_width=True
    )

    st.header("3. Wgraj pliki z eksportami (Mass Import)")
    st.write("Możesz wgrać wszystkie pobrane pliki z Ahrefs (format .csv) i Senuto (format .xlsx) naraz. System automatycznie je dopasuje.")
    
    uploaded_files = st.file_uploader("Wgraj wszystkie pliki tutaj", accept_multiple_files=True, type=['csv', 'xlsx'])
    
    if uploaded_files:
        if st.button("Generuj wynikowy plik XLSX"):
            with st.spinner("Przetwarzanie danych..."):
                ahrefs_dfs = []
                senuto_dfs = []
                
                # Odczyt wgranych plików
                for file in uploaded_files:
                    try:
                        if file.name.endswith('.csv'):
                            # Ahrefs zazwyczaj wypuszcza UTF-16 z tabulatorem lub UTF-8
                            file.seek(0)
                            try:
                                df = pd.read_csv(file, sep='\t', encoding='utf-16')
                                if 'Keyword' not in df.columns:
                                    file.seek(0)
                                    df = pd.read_csv(file, sep=',', encoding='utf-8')
                            except:
                                file.seek(0)
                                df = pd.read_csv(file, sep=',', encoding='utf-8')
                                
                            if 'Keyword' in df.columns and 'Current URL' in df.columns:
                                ahrefs_dfs.append(df)
                        
                        elif file.name.endswith('.xlsx'):
                            file.seek(0)
                            df = pd.read_excel(file)
                            if 'Słowo kluczowe' in df.columns and 'Adres URL' in df.columns:
                                senuto_dfs.append(df)
                    except Exception as e:
                        st.warning(f"Nie udało się odczytać pliku {file.name}: {e}")
                
                import re
                def clean_url(u):
                    if pd.isna(u): return ""
                    u = str(u).strip()
                    u = re.sub(r'^https?://', '', u)
                    u = re.sub(r'^www\.', '', u)
                    u = u.rstrip('/')
                    return u

                # Łączenie w jeden DataFrame dla Ahrefs i jeden dla Senuto
                df_ahrefs_all = pd.concat(ahrefs_dfs, ignore_index=True) if ahrefs_dfs else pd.DataFrame()
                df_senuto_all = pd.concat(senuto_dfs, ignore_index=True) if senuto_dfs else pd.DataFrame()
                
                if not df_ahrefs_all.empty:
                    df_ahrefs_all['Clean_URL'] = df_ahrefs_all['Current URL'].apply(clean_url)
                if not df_senuto_all.empty:
                    df_senuto_all['Clean_URL'] = df_senuto_all['Adres URL'].apply(clean_url)
                
                final_results = []
                
                # Złączenie danych dla każdego adresu URL
                for url in urls:
                    clean_target = clean_url(url)
                    
                    # Filtrujemy dane dla danego URL
                    df_a = pd.DataFrame()
                    df_s = pd.DataFrame()
                    
                    if not df_ahrefs_all.empty:
                        df_a = df_ahrefs_all[df_ahrefs_all['Clean_URL'] == clean_target].copy()
                    
                    if not df_senuto_all.empty:
                        df_s = df_senuto_all[df_senuto_all['Clean_URL'] == clean_target].copy()
                    
                    # Wymagane kolumny
                    if not df_a.empty:
                        cols_a = ['Current URL', 'Keyword', 'Volume', 'Current position']
                        if 'Organic traffic' in df_a.columns:
                            cols_a.append('Organic traffic')
                        df_a = df_a[cols_a]
                        
                        rename_a = {
                            'Keyword': 'Fraza (Ahrefs)',
                            'Volume': 'Wolumen (Ahrefs)',
                            'Current position': 'Pozycja (Ahrefs)'
                        }
                        if 'Organic traffic' in df_a.columns:
                            rename_a['Organic traffic'] = 'Szacowany ruch (Ahrefs)'
                            
                        df_a = df_a.rename(columns=rename_a)
                        df_a['Merge_Key'] = df_a['Fraza (Ahrefs)'].str.lower().str.strip()
                    else:
                        df_a = pd.DataFrame(columns=['Fraza (Ahrefs)', 'Szacowany ruch (Ahrefs)', 'Wolumen (Ahrefs)', 'Pozycja (Ahrefs)', 'Merge_Key'])
                        
                    if not df_s.empty:
                        cols_s = ['Adres URL', 'Słowo kluczowe', 'Śr. mies. liczba wyszukiwań', 'Pozycja']
                        if 'Szacowany ruch' in df_s.columns:
                            cols_s.append('Szacowany ruch')
                        df_s = df_s[cols_s]
                        
                        rename_s = {
                            'Słowo kluczowe': 'Fraza (Senuto)',
                            'Śr. mies. liczba wyszukiwań': 'Wolumen (Senuto)',
                            'Pozycja': 'Pozycje (Senuto)'
                        }
                        if 'Szacowany ruch' in df_s.columns:
                            rename_s['Szacowany ruch'] = 'Szacowany ruch (Senuto)'
                            
                        df_s = df_s.rename(columns=rename_s)
                        df_s['Merge_Key'] = df_s['Fraza (Senuto)'].str.lower().str.strip()
                    else:
                        df_s = pd.DataFrame(columns=['Fraza (Senuto)', 'Szacowany ruch (Senuto)', 'Wolumen (Senuto)', 'Pozycje (Senuto)', 'Merge_Key'])
                        
                    # Outer Join po 'Merge_Key' (czyli tej samej frazie)
                    if not df_a.empty and not df_s.empty:
                        df_merged = pd.merge(df_s, df_a, on='Merge_Key', how='outer')
                    elif not df_s.empty:
                        df_merged = df_s
                        df_merged['Fraza (Ahrefs)'] = ""
                        df_merged['Szacowany ruch (Ahrefs)'] = pd.NA
                        df_merged['Wolumen (Ahrefs)'] = ""
                        df_merged['Pozycja (Ahrefs)'] = ""
                    elif not df_a.empty:
                        df_merged = df_a
                        df_merged['Fraza (Senuto)'] = ""
                        df_merged['Szacowany ruch (Senuto)'] = pd.NA
                        df_merged['Wolumen (Senuto)'] = ""
                        df_merged['Pozycje (Senuto)'] = ""
                    else:
                        continue
                        
                    df_merged['URL'] = url
                    
                    # Sortowanie
                    if 'Szacowany ruch (Senuto)' not in df_merged.columns:
                        df_merged['Szacowany ruch (Senuto)'] = pd.NA
                    if 'Szacowany ruch (Ahrefs)' not in df_merged.columns:
                        df_merged['Szacowany ruch (Ahrefs)'] = pd.NA
                        
                    df_merged['Szacowany ruch (Senuto)'] = pd.to_numeric(df_merged['Szacowany ruch (Senuto)'], errors='coerce')
                    df_merged['Szacowany ruch (Ahrefs)'] = pd.to_numeric(df_merged['Szacowany ruch (Ahrefs)'], errors='coerce')
                    
                    def round_traffic(x):
                        if pd.isna(x):
                            return pd.NA
                        if x < 1:
                            return 0
                        return int(round(x))
                        
                    df_merged['Szacowany ruch (Senuto)'] = df_merged['Szacowany ruch (Senuto)'].apply(round_traffic)
                    
                    df_merged = df_merged.sort_values(
                        by=['Szacowany ruch (Senuto)', 'Szacowany ruch (Ahrefs)'], 
                        ascending=[False, False], 
                        na_position='last'
                    )
                    
                    # Wypełnienie NaN pustym ciągiem jeśli chcemy ładnie w Excelu
                    df_merged['Szacowany ruch (Senuto)'] = df_merged['Szacowany ruch (Senuto)'].fillna("")
                    df_merged['Szacowany ruch (Ahrefs)'] = df_merged['Szacowany ruch (Ahrefs)'].fillna("")
                    
                    # Selekcja i zmiana kolejności finałowych kolumn
                    df_final_url = df_merged[['URL', 'Fraza (Senuto)', 'Szacowany ruch (Senuto)', 'Wolumen (Senuto)', 'Pozycje (Senuto)', 'Fraza (Ahrefs)', 'Szacowany ruch (Ahrefs)', 'Wolumen (Ahrefs)', 'Pozycja (Ahrefs)']]
                    final_results.append(df_final_url)
                    
                if final_results:
                    df_final = pd.concat(final_results, ignore_index=True)
                    
                    # Generowanie pliku XLSX do pobrania
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_final.to_excel(writer, index=False, sheet_name='Content Gap')
                    
                    st.success("Zakończono generowanie raportu!")
                    
                    st.download_button(
                        label="📥 Pobierz wynikowy plik XLSX",
                        data=output.getvalue(),
                        file_name="content_gap_raport.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("Nie znaleziono pasujących danych dla podanych adresów URL w wgranych plikach.")

import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 语言配置字典 ---
# 顺序已调整：PT (葡语) 设为默认索引 0
LANG_DICT = {
    "PT": {
        "title": "Painel de Monitoramento MDC",
        "total_usage": "Taxa de Ocupação Total",
        "used": "Usado",
        "total_avail": "Capacidade Total",
        "ctrl_panel": "⚙️ Painel de Controlo",
        "lang_sel": "Escolher Língua / 语言选择",
        "wh_sel": "Selecionar Armazém",
        "stats_title": "Estatísticas em Tempo Real",
        "bin_total": "Total de Locais Disponíveis",
        "bin_used": "Locais Ocupados",
        "bin_free": "Locais Livres",
        "export_title": "📥 Exportação de Relatórios",
        "export_btn": "Exportar Locais Vazios - {}",
        "no_empty": "Não há locais vazios no momento",
        "legend_empty": "Local Disponível",
        "legend_used": "Local Ocupado",
        "legend_disabled": "Local Indisponível",
        "legend_beam": "Viga Laranja",
        "legend_pillar": "Pilar Azul",
        "aisle": "Corredor",
        "data_error": "Erro ao carregar dados. Verifique o arquivo SGF.csv.",
        "error_check": "⚠️ Verificação de Erros de Dados",
        "error_btn": "Exportar Locais Inválidos com Carga (Excel)",
        "error_msg": "Encontrados {} locais desativados com carga"
    },
    "CN": {
        "title": "MDC 仓库实时监控看板",
        "total_usage": "全库容积利用率",
        "used": "已用",
        "total_avail": "总可用",
        "ctrl_panel": "⚙️ 控制面板",
        "lang_sel": "语言选择 / Língua",
        "wh_sel": "选择库房视图",
        "stats_title": "实时状态统计",
        "bin_total": "可用库位总数",
        "bin_used": "当前已用库位",
        "bin_free": "当前剩余空闲",
        "export_title": "📥 报表导出",
        "export_btn": "导出 {} 库空库位清单",
        "no_empty": "目前没有空闲库位",
        "legend_empty": "可用空位",
        "legend_used": "有货占用",
        "legend_disabled": "不可用库位",
        "legend_beam": "橙色横梁",
        "legend_pillar": "蓝色立柱",
        "aisle": "货道",
        "data_error": "无法加载数据，请确保 SGF.csv 文件正确。",
        "error_check": "⚠️ 系统数据异常核查",
        "error_btn": "导出禁用库位有货清单 (Excel)",
        "error_msg": "发现 {} 个库位状态禁用但仍有货物"
    }
}

# --- 2. 页面配置与 UI 样式 ---
st.set_page_config(page_title="MDC WMS Monitor", layout="wide")

st.markdown("""
    <style>
    .total-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 15px; border-radius: 10px; color: white; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .wh-stat-card {
        background: white; padding: 10px; border-radius: 8px;
        border: 1px solid #e0e0e0; text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .wh-stat-title { font-weight: bold; color: #1e3c72; font-size: 16px; }
    .wh-stat-val { color: #2ecc71; font-weight: bold; font-size: 18px; }
    .legend-container {
        display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;
        background: white; padding: 12px; border-radius: 8px;
        border: 1px solid #eee; margin-bottom: 20px; font-size: 13px;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .shelf-container {
        display: flex; flex-wrap: nowrap; justify-content: flex-start;
        gap: 0px; padding: 15px; overflow-x: auto; background: white;
        border-radius: 10px; border: 1px solid #eee; margin-bottom: 30px;
    }
    .bay-unit { display: flex; flex-direction: row; align-items: flex-start; }
    .bin-column { display: flex; flex-direction: column; align-items: center; width: 42px; flex-shrink: 0; }
    .bin-box {
        width: 36px; height: 30px; margin: 0px 0;
        display: flex; align-items: center; justify-content: center;
        border-radius: 2px; font-size: 10px; font-weight: bold;
        border: 1px solid #eee; z-index: 2; background-color: white;
    }
    .orange-beam-row { width: 100%; height: 4px; background-color: #ff9800; margin: 2px 0; z-index: 5; }
    .pillar-tech-blue {
        width: 0; height: 210px; border-left: 4px dotted #3498db; 
        margin: 0 10px; opacity: 0.9; align-self: flex-start; margin-top: 5px;
    }
    .status-used { background-color: #3498db !important; color: white; border: none; }
    .status-empty { background-color: #2ecc71 !important; color: white; border: none; }
    .status-disabled { background-color: #95a5a6 !important; color: white; border: none; }
    .status-aisle { background-color: #f1c40f !important; color: #333; border: none; }
    .status-pillar { background-color: #7f8c8d !important; color: white; border: none; }
    .aisle-title { 
        background: #e9ecef; padding: 5px 15px; border-radius: 5px; 
        font-weight: bold; color: #495057; margin-top: 15px; margin-bottom: 8px; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据引擎 ---
@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists("SGF.csv"): return None, None
    try:
        raw_df = pd.read_csv("SGF.csv", low_memory=False)
        df = raw_df.iloc[:, [0, 6, 9, 11, 12, 13, 14]].copy()
        df.columns = ['SKU', 'Loc', 'Qty', 'L', 'W', 'H', 'Status']
        df['Loc'] = df['Loc'].astype(str).str.strip()
        df['Status'] = df['Status'].astype(str).str.strip()
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        for c in ['L','W','H']: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df['Vol'] = (df['L'] * df['W'] * df['H']) / 1000000
        m_mask = (~df['Loc'].str.contains('-', na=False)) & (df['Loc'].str.startswith(('A','B','C','D','E'))) & (df['L']>0)
        master = df[m_mask].drop_duplicates('Loc')
        l_map, stats = {}, {wh: {'t_v':0.0, 'u_v':0.0, 'total_bins':0, 'used_bins':0} for wh in 'ABCDE'}
        for _, r in master.iterrows():
            wh = r['Loc'][0].upper()
            l_map[r['Loc']] = {'Items':[], 'Status':r['Status'], 'Vol':r['Vol'], 'WH':wh, 'Aisle':r['Loc'][0:3], 'Col':r['Loc'][3:5], 'Lvl':r['Loc'][5:7]}
            if r['Status'] == "可用": 
                stats[wh]['t_v'] += r['Vol']; stats[wh]['total_bins'] += 1
        inv = df[df['Qty'] > 0]
        for _, r in inv.iterrows():
            if r['Loc'] in l_map: l_map[r['Loc']]['Items'].append(f"{r['SKU']}:{int(r['Qty'])}")
        for k, v in l_map.items():
            if len(v['Items']) > 0 and v['Status'] == "可用": 
                stats[v['WH']]['u_v'] += v['Vol']; stats[v['WH']]['used_bins'] += 1
        return l_map, stats
    except: return None, None

l_map, wh_stats = load_data()

# --- 4. 界面渲染 ---
if l_map:
    # 侧边栏控制 - 默认葡语
    if "lang" not in st.session_state:
        st.session_state.lang = "PT"
    
    # 切换选项顺序：葡语在前
    lang_choice = st.sidebar.radio("Escolher Língua / 语言", ["Português", "中文"])
    st.session_state.lang = "PT" if lang_choice == "Português" else "CN"
    L = LANG_DICT[st.session_state.lang]

    st.sidebar.header(L["ctrl_panel"])
    st.markdown(f'<h2 style="text-align:center; color:#1e3c72;">{L["title"]}</h2>', unsafe_allow_html=True)
    
    # 顶部汇总
    t_all, u_all = sum(s['t_v'] for s in wh_stats.values()), sum(s['u_v'] for s in wh_stats.values())
    r_all = (u_all/t_all*100) if t_all>0 else 0
    st.markdown(f'<div class="total-card">{L["total_usage"]}: <b>{r_all:.1f}%</b> &nbsp;&nbsp; | &nbsp;&nbsp; {L["used"]}: {u_all:.1f} m³ / {L["total_avail"]}: {t_all:.1f} m³</div>', unsafe_allow_html=True)

    # 侧边栏库房选择
    wh_sel = st.sidebar.selectbox(L["wh_sel"], ['A','B','C','D','E'])
    curr = wh_stats[wh_sel]
    st.sidebar.divider()
    st.sidebar.subheader(f"📊 {wh_sel} {L['stats_title']}")
    st.sidebar.markdown(f"{L['bin_total']}: **{curr['total_bins']}**")
    st.sidebar.markdown(f"{L['bin_used']}: **{curr['used_bins']}**")
    st.sidebar.markdown(f"{L['bin_free']}: **{curr['total_bins'] - curr['used_bins']}**")
    
    # --- 异常库位核查逻辑 ---
    st.sidebar.divider()
    st.sidebar.subheader(L["error_check"])
    
    error_list = []
    for loc, info in l_map.items():
        if info['Status'] == "不可用" and len(info['Items']) > 0:
            error_list.append({
                "Location": loc,
                "Status": info['Status'],
                "Items_Stocked": " | ".join(info['Items'])
            })
    
    if error_list:
        st.sidebar.warning(L["error_msg"].format(len(error_list)))
        error_df = pd.DataFrame(error_list)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            error_df.to_excel(writer, index=False, sheet_name='System_Errors')
        
        st.sidebar.download_button(
            label=L["error_btn"],
            data=output.getvalue(),
            file_name="MDC_System_Error_Bins.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.sidebar.success("OK: No Status Conflicts")

    # 导出空库位
    st.sidebar.divider()
    st.sidebar.subheader(L["export_title"])
    empty_locs = [k for k, v in l_map.items() if v['WH'] == wh_sel and v['Status'] == "可用" and len(v['Items']) == 0]
    if empty_locs:
        csv = pd.DataFrame(empty_locs, columns=['Loc_ID']).to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button(L["export_btn"].format(wh_sel), csv, f"MDC_{wh_sel}.csv", "text/csv")
    else: st.sidebar.warning(L["no_empty"])

    # 库房卡片
    cols_stats = st.columns(5)
    for i, wh_key in enumerate(['A', 'B', 'C', 'D', 'E']):
        s, r = wh_stats[wh_key], (wh_stats[wh_key]['u_v']/wh_stats[wh_key]['t_v']*100 if wh_stats[wh_key]['t_v']>0 else 0)
        with cols_stats[i]:
            st.markdown(f'<div class="wh-stat-card"><div class="wh-stat-title">{wh_key}</div><div class="wh-stat-val">{r:.1f}%</div><div style="font-size:11px; color:#888;">{s["u_v"]:.1f}/{s["t_v"]:.1f} m³</div></div>', unsafe_allow_html=True)

    # 图例
    st.markdown(f"""
        <div class="legend-container">
            <div class="legend-item"><div class="bin-box status-empty">L</div> {L['legend_empty']}</div>
            <div class="legend-item"><div class="bin-box status-used">L</div> {L['legend_used']}</div>
            <div class="legend-item"><div class="bin-box status-disabled">❌</div> {L['legend_disabled']}</div>
            <div class="legend-item" style="color:#ff9800; font-weight:bold;">━ {L['legend_beam']}</div>
            <div class="legend-item" style="color:#3498db; font-weight:bold;">⫶ {L['legend_pillar']}</div>
        </div>
    """, unsafe_allow_html=True)

    # 渲染
    levels = ["50","40","30","20","10","00"] if wh_sel=='A' else ["40","30","20","10","00"]
    split = 3 if wh_sel=='A' else 2
    aisles = sorted(list(set(v['Aisle'] for v in l_map.values() if v['WH']==wh_sel)))
    for a_id in aisles:
        st.markdown(f'<div class="aisle-title">📍 {L["aisle"]}: {a_id}</div>', unsafe_allow_html=True)
        all_cols = sorted(list(set(v['Col'] for v in l_map.values() if v['Aisle']==a_id)), reverse=True)
        h_str = '<div class="shelf-container"><div class="pillar-tech-blue"></div>'
        for i in range(0, len(all_cols), split):
            bay_cols = all_cols[i : i + split]
            h_str += '<div class="bay-unit">'
            col_htmls = ["" for _ in bay_cols]
            for l_idx, lvl in enumerate(levels):
                for c_idx, cid in enumerate(bay_cols):
                    f_id = f"{a_id}{cid}{lvl}"
                    d = l_map.get(f_id)
                    cls, sym = "status-unknown", lvl
                    if d:
                        if len(d['Items']) > 0: cls = "status-used"
                        elif d['Status'] == "可用": cls = "status-empty"
                        elif d['Status'] == "不可用": cls, sym = "status-disabled", "❌"
                        elif d['Status'] == "通道": cls, sym = "status-aisle", "↔️"
                        elif d['Status'] == "柱子": cls, sym = "status-pillar", "█"
                    col_htmls[c_idx] += f'<div class="bin-box {cls}" title="{d["Items"] if d else ""}">{sym}</div>'
                if l_idx < len(levels) - 1:
                    for c_idx in range(len(bay_cols)): col_htmls[c_idx] += '<div class="orange-beam-row"></div>'
            for idx, c_html in enumerate(col_htmls):
                h_str += f'<div class="bin-column">{c_html}<div style="font-size:10px;color:#888;">{bay_cols[idx]}</div></div>'
            h_str += '</div><div class="pillar-tech-blue"></div>'
        st.markdown(h_str + '</div>', unsafe_allow_html=True)
else: st.error("Erro / 错误: SGF.csv")
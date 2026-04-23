#!/usr/bin/env python3
"""
æºå½±AIè§è²åº Dashboard â è§è² IP æ¡£æ¡ + ä¸æ¡è¿åº¦
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="æºå½±AIè§è²åº",
    page_icon="ð­",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #1a1a1a; }
[data-testid="stHeader"] { background: #1a1a1a; }
section[data-testid="stSidebar"] { background: #141414; }

[data-testid="stTabs"] button {
    font-size: 15px !important;
    color: #888 !important;
    padding: 10px 20px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #fff !important;
    border-bottom: 2px solid #E879A0 !important;
}

.card {
    background: #242424;
    border: 1px solid #3a3a3a;
    border-radius: 10px;
    padding: 20px 22px;
    margin-bottom: 16px;
}
.card-title {
    font-size: 13px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
}
.kpi-wrap { display: flex; gap: 16px; margin-bottom: 20px; }
.kpi-card {
    flex: 1;
    background: #242424;
    border: 1px solid #3a3a3a;
    border-radius: 10px;
    padding: 18px 20px;
}
.kpi-label { font-size: 12px; color: #888; margin-bottom: 6px; }
.kpi-value { font-size: 34px; font-weight: 700; color: #fff; line-height: 1.1; }
.kpi-sub { font-size: 12px; color: #666; margin-top: 4px; }

.tag {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    margin: 3px;
    border: 1px solid;
}
.tag-pink   { border-color: #E879A0; color: #E879A0; }
.tag-purple { border-color: #7C6BDB; color: #7C6BDB; }
.tag-green  { border-color: #4CAF50; color: #4CAF50; }
.tag-cyan   { border-color: #26C6DA; color: #26C6DA; }
.tag-amber  { border-color: #FFB300; color: #FFB300; }
.tag-gray   { border-color: #666;    color: #aaa;    }

.char-section {
    border: 1px solid #3a3a3a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 28px;
    background: #1e1e1e;
}
h3 { color: #eee !important; font-size: 16px !important; margin-top: 28px !important; }
</style>
""", unsafe_allow_html=True)


# ââ é¡µé¦ âââââââââââââââââââââââââââââââââââââââââââââââââ
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
  <div>
    <span style="font-size:24px;font-weight:700;color:#fff;">ð­ æºå½±AIè§è²åº</span>
  </div>
  <div style="font-size:13px;color:#555;">èµææ´æ°ï¼{datetime.now().strftime('%Y/%m/%d %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["ð­ è§è² IP æ¡£æ¡", "ð ä¸æ¡è¿åº¦", "ð ç¤¾ç¾¤æ¸æ", "ðï¸ ç¸½æ§å°"])


# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TAB 1ï¼è§è² IP æ¡£æ¡
# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab1:
    from characters import CHARACTERS as ALL_CHARS

    def section_table(rows):
        rows_html = "".join(
            f'<tr><td style="padding:7px 12px;color:#888;font-size:12px;white-space:nowrap;width:140px;">{k}</td>'
            f'<td style="padding:7px 12px;color:#ccc;font-size:13px;">{v}</td></tr>'
            for k, v in rows
        )
        return f'<table style="width:100%;border-collapse:collapse;">{rows_html}</table>'

    SECTION_LABELS = [
        ("basic",      "â åºæ¬ä¿¡æ¯"),
        ("appearance", "ä¸ãåºç¡å¤è²"),
        ("persona",    "äºãæ°è´¨ / äººè®¾"),
        ("content",    "ä¸ãåå®¹å±æ§"),
        ("world",      "åãä¸çè§ / èæ¯"),
        ("voice",      "äºãå£°é³ / è¡¨æ¼"),
        ("business",   "å­ãåä¸ / è¿è¥"),
    ]

    CHAR_TAGS = {
        "ææµæµ":     [("é»å®¶æ","tag-pink"),("æ±æ","tag-pink"),("å²å¨","tag-pink"),("é·éª","tag-gray"),("SwitchåM","tag-gray")],
        "åªå¦®":       [("è¿å¨ç³»","tag-green"),("ä¸­å½åæ¹","tag-green"),("ç­åæ´»å","tag-cyan"),("SwitchåS","tag-gray"),("åå·®æ","tag-gray")],
        "çè·æ¶µ":[("æ³å¼","tag-purple"),("æ··è¡","tag-purple"),("åºç","tag-purple"),("çç¦»æ","tag-gray"),("æèº","tag-gray")],
        "é¡¾æ":       [("é©ç³»å·è³","tag-amber"),("å¤åºå¥³ç","tag-amber"),("å±é©å¦©åª","tag-pink"),("å¼ºS","tag-gray"),("æ§å¶ç","tag-gray")],
        "è¡èç":     [("æçäººå¦»","tag-cyan"),("ä¸­å¼å¤å¤","tag-cyan"),("æ¸©æé£éª","tag-pink"),("åM","tag-gray"),("å°æ¹¾å¤å¤","tag-gray")],
    }

    char_names = [c["name"] for c in ALL_CHARS]
    selected = st.radio(
        "éæ©è§è²",
        char_names,
        horizontal=True,
        label_visibility="collapsed",
    )

    char = next(c for c in ALL_CHARS if c["name"] == selected)

    ig_badge = f'<a href="{char["ig_url"]}" target="_blank" style="font-size:12px;color:#555;text-decoration:none;">{char["ig"]} â</a>' if char["ig"] else '<span style="font-size:12px;color:#444;">IG å¾å»ºç«</span>'
    rank_label = "S çº§" if char["rank"] == "S" else "A çº§"
    tags_html = "".join(f'<span class="tag {cls}">{t}</span>' for t, cls in CHAR_TAGS.get(char["name"], []))

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:20px 0 14px 0;">
      <span style="font-size:24px;font-weight:700;color:#fff;">{char['name']}</span>
      <span style="font-size:14px;color:#888;">{char['en_name']}</span>
      <span style="background:{char['rank_color']}22;border:1px solid {char['rank_color']};color:{char['rank_color']};
            border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600;">{rank_label}</span>
      {ig_badge}
    </div>
    <div style="margin-bottom:18px;">{tags_html}</div>
    """, unsafe_allow_html=True)

    col_imgs, col_info = st.columns([2, 3])

    with col_imgs:
        if char["images"]:
            imgs = char["images"]
            num_cols = min(len(imgs), 2)
            img_cols = st.columns(num_cols)
            for i, img_path in enumerate(imgs):
                full_path = os.path.join(os.path.dirname(__file__), img_path)
                if os.path.exists(full_path):
                    img_cols[i % num_cols].image(full_path, use_container_width=True)
        else:
            st.markdown("""
            <div style="background:#1e1e1e;border:1px dashed #333;border-radius:10px;
                        height:220px;display:flex;align-items:center;justify-content:center;">
              <span style="color:#444;font-size:13px;">åºå¾å¾è¡¥å</span>
            </div>
            """, unsafe_allow_html=True)

        # ææµæµä¸å±ï¼ä¸è§å¾ + å¨æ¼«å¾
        if char["name"] == "ææµæµ":
            sv_paths = [f"assets/characters/linqianqian_sv_{i}.jpg" for i in range(1,3)]
            sv_exists = [p for p in sv_paths if os.path.exists(os.path.join(os.path.dirname(__file__), p))]
            if sv_exists:
                st.markdown('<div style="font-size:12px;color:#E879A0;font-weight:600;margin:14px 0 6px 0;">â ä¸è§å¾</div>', unsafe_allow_html=True)
                sv_cols = st.columns(len(sv_exists))
                for i, p in enumerate(sv_exists):
                    full_p = os.path.join(os.path.dirname(__file__), p)
                    sv_cols[i].image(full_p, use_container_width=True)

            anime_paths = [f"assets/characters/linqianqian_anime_{i}.jpg" for i in range(1,3)]
            anime_exists = [p for p in anime_paths if os.path.exists(os.path.join(os.path.dirname(__file__), p))]
            if anime_exists:
                st.markdown('<div style="font-size:12px;color:#7C6BDB;font-weight:600;margin:14px 0 6px 0;">â å¨æ¼«å½¢è±¡</div>', unsafe_allow_html=True)
                an_cols = st.columns(len(anime_exists))
                for i, p in enumerate(anime_exists):
                    full_p = os.path.join(os.path.dirname(__file__), p)
                    an_cols[i].image(full_p, use_container_width=True)

        st.markdown(f"""
        <div class="card" style="margin-top:12px;">
          <div class="card-title">AI çå¾ Prompt</div>
          <div style="font-size:12px;color:#aaa;margin-bottom:8px;line-height:1.6;"><b style="color:#666;">ä¸­æï¼</b>{char['prompt_cn']}</div>
          <div style="font-size:12px;color:#aaa;line-height:1.6;"><b style="color:#666;">ENï¼</b>{char['prompt_en']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        for key, label in SECTION_LABELS:
            if key not in char: continue
            table_html = section_table(char[key])
            st.markdown(f"""
            <div style="margin-bottom:10px;">
              <div style="font-size:12px;color:#E879A0;font-weight:600;margin-bottom:4px;letter-spacing:0.05em;">{label}</div>
              <div class="card" style="padding:4px 0;">{table_html}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>æºå½±AIè§è²åº IP èµäº§ç³»ç»</div>", unsafe_allow_html=True)


# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TAB 2ï¼ä¸æ¡è¿åº¦
# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab2:

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ââ æ´ä½è¿åº¦ KPI âââââââââââââââââââââââââââââââââââââ
    st.markdown("""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">æ´ä½å®æåº¦</div>
        <div class="kpi-value" style="color:#4CAF50;">50%</div>
        <div class="kpi-sub">è§è²å¼åé¶æ®µ</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">è§è²å·²å»ºæ¡£</div>
        <div class="kpi-value" style="color:#FFB300;">5 / 5</div>
        <div class="kpi-sub">ææµæµã»CÃ©lineã»è¡èçã»é¡¾æã»åªå¦®</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">ç¤¾ç¾¤å·²å¼è®¾</div>
        <div class="kpi-value" style="color:#E879A0;">3 / 5</div>
        <div class="kpi-sub">ææµæµã»CÃ©lineã»è¡èç</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">ç®æ  Deadline</div>
        <div class="kpi-value" style="font-size:22px;color:#7C6BDB;">Q2 2026</div>
        <div class="kpi-sub">é¦æ¹åå®¹ä¸çº¿</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ââ çç¹å¾ âââââââââââââââââââââââââââââââââââââââââââ
    st.markdown("### ð ä¸æ¡çç¹å¾")

    gantt_data = [
        dict(Task="è§è²æ¡£æ¡å»ºç«ï¼5ä½ï¼", Start="2026-03-01", Finish="2026-03-31", Stage="Phase 1 è§è²èµäº§", Status="å·²å®æ"),
        dict(Task="é¢é¨éç¹ç¡®è®¤", Start="2026-03-10", Finish="2026-03-31", Stage="Phase 1 è§è²èµäº§", Status="å·²å®æ"),
        dict(Task="åºå¾çæï¼åªå¦®å®æï¼", Start="2026-03-15", Finish="2026-03-31", Stage="Phase 1 è§è²èµäº§", Status="å·²å®æ"),
        dict(Task="åæ ç³è¯·ï¼é+å°ï¼", Start="2026-03-15", Finish="2026-04-30", Stage="Phase 1 è§è²èµäº§", Status="å¾ç¡®è®¤"),
        dict(Task="ç¬¬ä¸æ¬¡è§è²èµäº§ä¼è®®", Start="2026-03-11", Finish="2026-03-12", Stage="Phase 1 è§è²èµäº§", Status="å·²å®æ"),
        dict(Task="IG èªå¨åå·¥ä½æµå»ºç«", Start="2026-03-10", Finish="2026-03-18", Stage="Phase 2 AIçäº§", Status="å·²å®æ"),
        dict(Task="é¦æ¹æ¦å¿µå¾çæï¼åè§è²Ã20å¼ ï¼", Start="2026-03-19", Finish="2026-04-10", Stage="Phase 2 AIçäº§", Status="è¿è¡ä¸­"),
        dict(Task="AI çæ¬¾åå®¹ææ¥", Start="2026-03-31", Finish="2026-04-05", Stage="Phase 2 AIçäº§", Status="è¿è¡ä¸­"),
        dict(Task="ææµæµ IG æç»­è¿è¥ï¼ç ´ä¸ï¼", Start="2026-03-01", Finish="2026-04-30", Stage="Phase 3 ç¤¾ç¾¤å¸å±", Status="è¿è¡ä¸­"),
        dict(Task="CÃ©line @celine_iso é¦æ¹åå®¹", Start="2026-03-20", Finish="2026-03-31", Stage="Phase 3 ç¤¾ç¾¤å¸å±", Status="å·²å®æ"),
        dict(Task="è¡èç @hu_maturemommy é¦æ¹åå®¹", Start="2026-03-20", Finish="2026-03-31", Stage="Phase 3 ç¤¾ç¾¤å¸å±", Status="å·²å®æ"),
        dict(Task="é¡¾æç¤¾ç¾¤å¸å·å¼è®¾", Start="2026-04-01", Finish="2026-04-07", Stage="Phase 3 ç¤¾ç¾¤å¸å±", Status="å¾ç¡®è®¤"),
        dict(Task="åªå¦®ç¤¾ç¾¤å¸å·å¼è®¾", Start="2026-04-01", Finish="2026-04-07", Stage="Phase 3 ç¤¾ç¾¤å¸å±", Status="å¾ç¡®è®¤"),
        dict(Task="é»çå¨å¹³å°å¼è®¾ï¼ææµæµï¼", Start="2026-03-16", Finish="2026-03-31", Stage="Phase 4 éå", Status="å·²å®æ"),
        dict(Task="IG èªå¨ç¬è«æ¥å¥ Dashboard", Start="2026-04-01", Finish="2026-04-20", Stage="Phase 4 éå", Status="å¾å¼å§"),
    ]

    df_gantt = pd.DataFrame(gantt_data)
    df_gantt["Start"] = pd.to_datetime(df_gantt["Start"])
    df_gantt["Finish"] = pd.to_datetime(df_gantt["Finish"])

    color_map = {
        "å®æ": "#4CAF50",
        "è¿è¡ä¸­": "#FFB300",
        "å¾ç¡®è®¤": "#7C6BDB",
        "å¾å¼å§": "#444",
    }

    fig_gantt = px.timeline(
        df_gantt, x_start="Start", x_end="Finish",
        y="Task", color="Status",
        color_discrete_map=color_map,
        hover_data=["Stage", "Status"],
    )
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="#242424", paper_bgcolor="#242424",
        font=dict(color="#aaa", size=12),
        xaxis=dict(gridcolor="#333", linecolor="#333"),
        yaxis=dict(gridcolor="#333", linecolor="#333"),
        legend=dict(bgcolor="#2d2d2d", bordercolor="#444", title="ç¶æ"),
        showlegend=True,
    )
    fig_gantt.add_vline(
        x=datetime.now().timestamp() * 1000,
        line_dash="dash", line_color="#E879A0", line_width=1.5,
        annotation_text="ä»å¤©", annotation_font_color="#E879A0",
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

    # ââ çæ¿ âââââââââââââââââââââââââââââââââââââââââââââ
    st.markdown("### ð ä»»å¡çæ¿")

    KANBAN = {
        "ð´ å¾ç¡®è®¤": [
            "åæ ç³è¯·ç­ç¥ç¡®è®¤ï¼é+å°ï¼",
            "é¡¾æç¤¾ç¾¤å¸å·å¼è®¾",
            "åªå¦®ç¤¾ç¾¤å¸å·å¼è®¾",
        ],
        "ð¡ è¿è¡ä¸­": [
            "ææµæµ IG åå®¹æç»­åå¸ï¼ç ´ä¸ðï¼",
            "CÃ©line IG æ°å¸å· @celine_iso ç»è¥",
            "è¡èç IG @hu_maturemommy åå®¹å»ºç«",
            "3/31 AI çæ¬¾åå®¹ææ¥",
            "é¦æ¹æ¦å¿µå¾çæï¼åè§è²Ã20å¼ ï¼",
        ],
        "ðµ å¾å¼å§": [
            "é¡¾æç¤¾ç¾¤å¸å·å¼è®¾",
            "åªå¦®ç¤¾ç¾¤å¸å·å¼è®¾",
            "IG èªå¨ç¬è«æ¥å¥ Dashboard",
        ],
        "â å·²å®æ": [
            "åå¤§è§è² IP æ¹åç¡®å®",
            "è§è²æ¡£æ¡å»ºç«ï¼5ä½ï¼",
            "KPI è¯åè¡¨å»ºç«",
            "å¨æ¥èªå¨åç³»ç» v3",
            "IG èªå¨åå·¥ä½æµå»ºç«",
            "AI åå®¹ IP åä¸è®¡åä¹¦ï¼13é¡µï¼",
            "ç¬¬ä¸æ¬¡è§è²èµäº§ä¼è®® 3/11",
            "æºå½±AIè§è²åº Dashboard å»ºç½®",
            "é»çæµç¨å¼æå®æ 3/23",
            "ææµæµé»çå¨å¹³å°å¼è®¾å®æ",
            "ææµæµ IG ç ´ä¸ 3/31",
            "è¡èç IG å¸å·å¼è®¾ @hu_maturemommy",
            "çè·æ¶µ IG æ°å¸å· @celine_isoï¼åå¸è¢«banï¼",
            "çè·æ¶µé¦æ¹åå®¹ä¸çº¿",
            "è¡èçé¦æ¹åå®¹ä¸çº¿",
            "åªå¦®é¢é¨éç¹ & åºå¾å®æ",
            "Dashboard ç¤¾ç¾¤æ°æ®é¡µç­¾ä¸çº¿",
        ],
    }

    col_colors = {
        "ð´ å¾ç¡®è®¤": "#c0392b22",
        "ð¡ è¿è¡ä¸­": "#FFB30022",
        "ðµ å¾å¼å§": "#7C6BDB22",
        "â å·²å®æ": "#4CAF5022",
    }
    border_colors = {
        "ð´ å¾ç¡®è®¤": "#c0392b",
        "ð¡ è¿è¡ä¸­": "#FFB300",
        "ðµ å¾å¼å§": "#7C6BDB",
        "â å·²å®æ": "#4CAF50",
    }

    cols = st.columns(4)
    for col, (status, tasks) in zip(cols, KANBAN.items()):
        bg = col_colors[status]
        border = border_colors[status]
        items_html = "".join(
            f'<div style="background:#2a2a2a;border-radius:6px;padding:10px 12px;'
            f'margin-bottom:8px;font-size:13px;color:#ccc;line-height:1.4;">{t}</div>'
            for t in tasks
        )
        col.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:10px;padding:16px;min-height:300px;">
          <div style="font-size:13px;font-weight:600;color:#eee;margin-bottom:12px;">{status}
            <span style="font-size:11px;color:#888;margin-left:6px;">({len(tasks)})</span>
          </div>
          {items_html}
        </div>
        """, unsafe_allow_html=True)

    # ââ è§è²è¿åº¦ç©éµ âââââââââââââââââââââââââââââââââââââ
    st.markdown("### ð¤ è§è²å¼åè¿åº¦")

    char_progress = [
        {"è§è²": "ææµæµ",  "æ¡£æ¡å»ºç«": "â", "é¢é¨éç¹": "â", "åºå¾çæ": "â", "ç¤¾ç¾¤å¼è®¾": "â", "é¦æ¹åå®¹": "â", "ç­çº§": "S"},
        {"è§è²": "çè·æ¶µ",  "æ¡£æ¡å»ºç«": "â", "é¢é¨éç¹": "â", "åºå¾çæ": "â", "ç¤¾ç¾¤å¼è®¾": "â", "é¦æ¹åå®¹": "â", "ç­çº§": "S"},
        {"è§è²": "è¡èç",  "æ¡£æ¡å»ºç«": "â", "é¢é¨éç¹": "â", "åºå¾çæ": "â", "ç¤¾ç¾¤å¼è®¾": "â", "é¦æ¹åå®¹": "â", "ç­çº§": "S"},
        {"è§è²": "é¡¾æ",    "æ¡£æ¡å»ºç«": "â", "é¢é¨éç¹": "â", "åºå¾çæ": "â³", "ç¤¾ç¾¤å¼è®¾": "â³", "é¦æ¹åå®¹": "â³", "ç­çº§": "S"},
        {"è§è²": "åªå¦®",    "æ¡£æ¡å»ºç«": "â", "é¢é¨éç¹": "â", "åºå¾çæ": "â", "ç¤¾ç¾¤å¼è®¾": "â³", "é¦æ¹åå®¹": "â³", "ç­çº§": "S"},
    ]

    header = ["è§è²", "ç­çº§", "æ¡£æ¡å»ºç«", "é¢é¨éç¹", "åºå¾çæ", "ç¤¾ç¾¤å¼è®¾", "é¦æ¹åå®¹"]
    header_html = "".join(f'<th style="padding:10px 16px;color:#888;font-size:12px;font-weight:500;text-align:center;">{h}</th>' for h in header)

    rows_html = ""
    for c in char_progress:
        lvl_color = "#FFB300" if c["ç­çº§"] == "S" else "#7C6BDB"
        rows_html += f"""<tr style="border-top:1px solid #2a2a2a;">
          <td style="padding:10px 16px;color:#fff;font-weight:600;">{c['è§è²']}</td>
          <td style="padding:10px 16px;text-align:center;"><span style="color:{lvl_color};font-weight:700;">{c['ç­çº§']}</span></td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['æ¡£æ¡å»ºç«']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['é¢é¨éç¹']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['åºå¾çæ']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['ç¤¾ç¾¤å¼è®¾']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['é¦æ¹åå®¹']}</td>
        </tr>"""

    st.markdown(f"""
    <div class="card" style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
      <div style="margin-top:12px;font-size:12px;color:#555;">â å®æ &nbsp; â³ è¿è¡ä¸­/å¾å¼å§</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>æºå½±AIè§è²åº Â· ä¸æ¡è¿åº¦è¿½è¸ª</div>", unsafe_allow_html=True)


# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TAB 3ï¼IG æ°æ®
# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab3:

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ââ æ°æ®è¯´æ âââââââââââââââââââââââââââââââââââââââââ
    st.markdown("""
    <div style="background:#242424;border:1px solid #3a3a3a;border-radius:8px;padding:12px 18px;margin-bottom:20px;font-size:12px;color:#666;">
      â ï¸ ç®åä¸ºæå¨å¡«åæ°æ®ï¼å°æªæ¥èªå¨ç¬è«ãæ°æ®ä»¥æåäººå·¥æ ¸å¯¹æ¶é´ä¸ºåã
    </div>
    """, unsafe_allow_html=True)

    # ââ IG æ°æ®ï¼æå¨ç»´æ¤ï¼ ââââââââââââââââââââââââââââââ
    IG_DATA = [
        {
            "name": "ææµæµ",
            "en_name": "Lin Qianqian",
            "ig": "@qianqian.hanfu",
            "ig_url": "https://www.instagram.com/qianqian.hanfu/",
            "color": "#FFB300",
            "status": "active",
            "followers": 15000,
            "following": 13,
            "posts": 21,
            "avg_likes": 1767,
            "avg_comments": 22,
            "last_post": "2026-03-27",
            "note": "ä¸»å¸³èï¼ç®åææ´»èºï¼4/13 ç ´1.5è¬",
            "updated": "2026-04-13",
            "platforms": [
                ("ð¸ IG",      "https://www.instagram.com/qianqian.hanfu/"),
                ("ð§µ Threads", "https://www.threads.com/@qianqian.hanfu"),
                ("ðµ TikTok",  "https://www.tiktok.com/@qianqian.hanfu"),
                ("â¶ï¸ YouTube", "https://www.youtube.com/@qianqian_hanfu"),
                ("ð Linktree","https://linktr.ee/qianqian_hanfu"),
                ("ð FansOne", "https://fansone.co/lazypiggy520"),
                ("ð Patreon", "https://www.patreon.com/cw/qianqian_haofu"),
            ],
            "highlights": [
                {
                    "date": "2026-03-11",
                    "content": "ä¹æ¯æ¢æchaäºï¼ï¼ðð\n#nobatidÃ£o #JennieNoBatidÃ£o #DanceCover #funkdance #nobatidaochallenge",
                    "likes": 14000,
                    "comments": 77,
                    "views": 224000,
                },
            ],
        },
        {
            "name": "çè·æ¶µ",
            "en_name": "CÃ©line Wang",
            "ig": "@celine.w_iso",
            "ig_url": "https://www.instagram.com/celine.w_iso/",
            "color": "#7C6BDB",
            "status": "new",
            "followers": 24,
            "following": 0,
            "posts": 0,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "å¨æ°å¸³èï¼èå¸³ @celine_iso å·²æ£ç¨",
            "updated": "2026-04-09",
            "platforms": [
                ("ð¸ IG",      "https://www.instagram.com/celine.w_iso/"),
                ("ð§µ Threads", "https://www.threads.com/@celine_iso"),
                ("ð¦ X",       "https://x.com/celineparisasia"),
                ("ð Linktree","https://linktr.ee/celineiso"),
                ("ð FansOne", "https://fansone.co/candykissvip520"),
                ("ð Patreon", "https://www.patreon.com/cw/CelineLin"),
            ],
        },
        {
            "name": "顾染",
            "en_name": "Gu Ran",
            "ig": "@good_ran__",
            "ig_url": "https://www.instagram.com/good_ran__/",
            "color": "#E05A5A",
            "status": "active",
            "followers": 168,
            "following": 25,
            "posts": 13,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "部落客，今天想當誰？來許願",
            "updated": "2026-04-23",
            "platforms": [
                ("📸 IG", "https://www.instagram.com/good_ran__/"),
            ],
        },
        {
            "name": "倪妮",
            "en_name": "Ni Ni",
            "ig": "@nini_power99",
            "ig_url": "https://www.instagram.com/nini_power99/",
            "color": "#4AABDB",
            "status": "active",
            "followers": 896,
            "following": 12,
            "posts": 5,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "我是Nini，本人經營，ENFP｜愛運動",
            "updated": "2026-04-23",
            "platforms": [
                ("📸 IG", "https://www.instagram.com/nini_power99/"),
            ],
        },
        {
            "name": "è¡èç",
            "en_name": "Hu Qianlu",
            "ig": "@hu_maturemommy",
            "ig_url": "https://www.instagram.com/hu_maturemommy/",
            "color": "#26C6DA",
            "status": "active",
            "followers": 995,
            "following": None,
            "posts": None,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "IG ç©©å®æé·ä¸­",
            "updated": "2026-04-13",
            "posts": 2,
            "following": 2,
            "platforms": [
                ("ð¸ IG",     "https://www.instagram.com/hu_maturemommy/"),
                ("ðµ TikTok", "https://www.tiktok.com/@hu_maturemommy"),
            ],
        },
        {
            "name": "é¡§æ",
            "en_name": "Gu Ran",
            "ig": None,
            "ig_url": None,
            "color": "#E879A0",
            "status": "pending",
            "followers": None,
            "following": None,
            "posts": None,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "å¸³èå¾å»ºç«",
            "updated": None,
        },

        {
            "name": "åªå¦®",
            "en_name": "Ni Ni",
            "ig": None,
            "ig_url": None,
            "color": "#4CAF50",
            "status": "pending",
            "followers": None,
            "following": None,
            "posts": None,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "å¸³èå¾å»ºç«",
            "updated": None,
        },
    ]

    STATUS_LABEL = {
        "active":  ("â æ´»èº", "#4CAF50"),
        "new":     ("ð æ°å¸³è", "#7C6BDB"),
        "pending": ("â³ å¾å»ºç«", "#555"),
    }

    # ââ KPI å¡ç âââââââââââââââââââââââââââââââââââââââââ
    total_followers = sum(d["followers"] for d in IG_DATA if d["followers"])
    active_names = "ã»".join(d["name"] for d in IG_DATA if d["status"] in ("active", "new"))
    active_count = sum(1 for d in IG_DATA if d["status"] in ("active", "new"))
    pending_names = "ã»".join(d["name"] for d in IG_DATA if d["status"] == "pending")
    pending_count = sum(1 for d in IG_DATA if d["status"] == "pending")

    st.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">ç¸½è¿½è¹¤äººæ¸</div>
        <div class="kpi-value" style="color:#E879A0;">{total_followers:,}</div>
        <div class="kpi-sub">ææè§è²åè¨</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">å·²éè¨­å¸³è</div>
        <div class="kpi-value" style="color:#FFB300;">{active_count} / 5</div>
        <div class="kpi-sub">{active_names}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">å¾å»ºç«å¸³è</div>
        <div class="kpi-value" style="color:#555;">{pending_count} / 5</div>
        <div class="kpi-sub">{pending_names}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">æ¸ææ´æ°æ¹å¼</div>
        <div class="kpi-value" style="font-size:18px;color:#444;">æå</div>
        <div class="kpi-sub">ç¬è²æ¥å¥å¾èªåæ´æ°</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ââ åè§è²æç´°å¡ç ââââââââââââââââââââââââââââââââââââ
    st.markdown("### ð¤ åè§è²ç¤¾ç¾¤æç´°")

    def fmt_metric(val):
        return f"{val:,}" if val is not None else "â"

    for d in IG_DATA:
        status_text, status_color = STATUS_LABEL[d["status"]]
        ig_link = (f'<a href="{d["ig_url"]}" target="_blank" style="color:#888;font-size:12px;">'
                   f'{d["ig"]} â</a>') if d["ig"] else '<span style="color:#444;font-size:12px;">â</span>'
        followers_str = f'{d["followers"]:,}' if d["followers"] is not None else "â"
        updated_str = d["updated"] or "â"

        # å¹³å°é£çµï¼æ¾å¨å¡çä¸æ¹ï¼
        if d.get("platforms"):
            links_html = "".join(
                f'<a href="{url}" target="_blank" style="display:inline-block;margin:0 6px 6px 0;'
                f'padding:3px 10px;background:#2a2a2a;border:1px solid #444;border-radius:12px;'
                f'font-size:11px;color:#aaa;text-decoration:none;">{label}</a>'
                for label, url in d["platforms"]
            )
            st.markdown(f'<div style="margin-bottom:4px;">{links_html}</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card" style="border-left:3px solid {d['color']};">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:12px;">
              <span style="font-size:18px;font-weight:700;color:#fff;">{d['name']}</span>
              <span style="font-size:13px;color:#888;">{d['en_name']}</span>
              {ig_link}
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
              <span style="background:{status_color}22;border:1px solid {status_color};color:{status_color};
                    border-radius:6px;padding:2px 10px;font-size:12px;">{status_text}</span>
              <span style="font-size:11px;color:#444;">æ´æ°ï¼{updated_str}</span>
            </div>
          </div>
          <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">è¿½è¹¤æ¸</div>
              <div style="font-size:22px;font-weight:700;color:{d['color']};">{followers_str}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">è¿½è¹¤ä¸­</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['following'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">è²¼ææ¸</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['posts'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">å¹³åè®æ¸</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['avg_likes'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">å¹³åçè¨</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['avg_comments'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">æå¾è²¼æ</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{d['last_post'] or 'â'}</div></div>
          </div>
          {f'<div style="margin-top:10px;font-size:12px;color:#555;">åè¨»ï¼{d["note"]}</div>' if d["note"] else ""}
        </div>
        """, unsafe_allow_html=True)

        if d.get("highlights"):
            import streamlit.components.v1 as components
            items_html = ""
            for h in d["highlights"]:
                likes_str = f'{h["likes"] // 10000}è¬+' if h["likes"] >= 10000 else str(h["likes"])
                views_str = f'{h["views"] // 10000}è¬+' if h["views"] >= 10000 else str(h["views"])
                content_html = h["content"].replace("\n", "<br>")
                items_html += (
                    '<div style="background:#1a1a1a;border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
                    '<div style="flex:1;">'
                    f'<div style="font-size:11px;color:#666;margin-bottom:4px;">{h["date"]}</div>'
                    f'<div style="font-size:12px;color:#aaa;line-height:1.5;">{content_html}</div>'
                    '</div>'
                    '<div style="display:flex;gap:16px;flex-shrink:0;margin-left:12px;">'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">â¤ï¸ è®</div><div style="font-size:15px;font-weight:700;color:#E879A0;">{likes_str}</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">ð¬ çè¨</div><div style="font-size:15px;font-weight:700;color:#aaa;">{h["comments"]}</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">â¶ï¸ è§ç</div><div style="font-size:15px;font-weight:700;color:#FFB300;">{views_str}</div></div>'
                    '</div></div></div>'
                )
            highlight_html = (
                f'<div style="font-family:sans-serif;background:#242424;border:1px solid #3a3a3a;border-radius:10px;'
                f'padding:16px 20px;margin-bottom:8px;border-left:3px solid {d["color"]};">'
                '<div style="font-size:11px;color:#E879A0;font-weight:600;margin-bottom:10px;">ð¥ äº®é»è²¼æ</div>'
                + items_html +
                '</div>'
            )
            components.html(highlight_html, height=len(d["highlights"]) * 100 + 60, scrolling=False)


    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>æºå½±AIè§è²åº Â· ç¤¾ç¾¤æ¸æç£æ§</div>", unsafe_allow_html=True)


with tab4:
    st.markdown("## \U0001f39b\ufe0f è§è²é²åº¦ç¸½æ§å°")
    st.caption("è³æä¾æºï¼Google Sheets èªååæ­¥")

    @st.cache_resource(ttl=60)
    def get_gsheet_connection():
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client

    try:
        client = get_gsheet_connection()
        sheet = client.open_by_key("1p5PkaYQQ8_g4iW9dRJlKucGG8o4kSKEZEBwEmknEV9k")
        ws = sheet.worksheet("\U0001f39b\ufe0f ç¸½æ§å°")

        all_data = ws.get_all_values()

        # ç¨æ¬ä½ç´¢å¼ (A=0, B=1, ... N=13)
        # A:åºè B:è§è²å C:å»ºç«è D:å»ºç«æ¥æ E:æäººå¬å¸ F:æäººçæ
        # G:æäººå®ææ¥ H:Mr.Båå¯© I:åå¯©æ¥æ J:æµ·å¥å¯©æ ¸ K:æµ·å¥å¯©æ ¸æ¥æ
        # L:ç®åçæ M:å¥åº«æ¥æ N:åè¨»
        COL_NAME = 1
        COL_CREATOR = 2
        COL_NIEN_STATUS = 5
        COL_MRB_REVIEW = 7
        COL_MRB_DATE = 8
        COL_BOSS_REVIEW = 9
        COL_BOSS_DATE = 10
        COL_STATUS = 11
        COL_STOCK_DATE = 12
        COL_NOTE = 13

        # æ¾è¡¨é ­è¡åæé å
        header_row_idx = None
        req_start_idx = None
        for i, row in enumerate(all_data):
            if len(row) > 1 and row[0].strip() == "åºè" and header_row_idx is None:
                header_row_idx = i
            if len(row) > 0 and "æé " in str(row[0]):
                req_start_idx = i

        if header_row_idx is not None:
            char_rows = []
            for i in range(header_row_idx + 1, len(all_data)):
                if req_start_idx and i >= req_start_idx:
                    break
                row = all_data[i]
                if len(row) > COL_NAME and row[COL_NAME].strip():
                    char_rows.append(row)

            if char_rows:
                total = len(char_rows)
                in_stock = sum(1 for r in char_rows if "å·²å¥åº«" in str(r[COL_STATUS]))
                in_review = sum(1 for r in char_rows if "å¾æµ·å¥å¯©" in str(r[COL_STATUS]))
                in_making = sum(1 for r in char_rows if "æäººä¸­" in str(r[COL_STATUS]))
                need_fix = sum(1 for r in char_rows if "é§å" in str(r[COL_STATUS]) or "éä¿®æ¹" in str(r[COL_STATUS]))

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("ç¸½è§è²æ¸", total)
                c2.metric("å·²å¥åº«", in_stock)
                c3.metric("å¾æµ·å¥å¯©", in_review)
                c4.metric("æäººä¸­", in_making)
                c5.metric("éä¿®æ¹", need_fix)

                st.markdown("---")
                st.markdown("### è§è²çæä¸è¦½")

                status_colors = {
                    "å·²å¥åº«": "#2ecc71",
                    "å¾æµ·å¥å¯©": "#9b59b6",
                    "æäººä¸­": "#f39c12",
                    "å¾åå¯©": "#3498db",
                    "é§å": "#e74c3c",
                    "éä¿®æ¹": "#e67e22",
                    "å»ºç«ä¸­": "#95a5a6",
                    "å·²ä¸æ¶": "#2c3e50",
                }

                for row in char_rows:
                    name = row[COL_NAME].strip()
                    status = str(row[COL_STATUS]) if len(row) > COL_STATUS else ""
                    note = str(row[COL_NOTE]) if len(row) > COL_NOTE else ""

                    color = "#95a5a6"
                    for key, clr in status_colors.items():
                        if key in status:
                            color = clr
                            break

                    st.markdown(
                        f'<div style="background:linear-gradient(135deg, {color}22, {color}11); '
                        f'border-left:4px solid {color}; border-radius:8px; padding:12px 16px; margin:8px 0;">'
                        f'<span style="font-size:1.2em; font-weight:bold;">{name}</span>'
                        f'&nbsp;&nbsp;<span style="background:{color}; color:white; padding:2px 10px; '
                        f'border-radius:12px; font-size:0.85em;">{status}</span>'
                        f'{"&nbsp;&nbsp; " + note if note else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("---")
                st.markdown("### æµ·å¥å¯©æ ¸å°å")

                pending = [r for r in char_rows if "å¾æµ·å¥å¯©" in str(r[COL_STATUS])]

                if not pending:
                    st.success("ç®åæ²æå¾å¯©æ ¸çè§è²")
                else:
                    boss_pwd = st.text_input("è«è¼¸å¥å¯©æ ¸å¯ç¢¼", type="password", key="boss_pwd")

                    if boss_pwd == "haige888":
                        st.success("èº«ä»½é©è­æå")

                        for row in pending:
                            name = row[COL_NAME].strip()
                            creator = row[COL_CREATOR] if len(row) > COL_CREATOR else ""
                            mrb = row[COL_MRB_REVIEW] if len(row) > COL_MRB_REVIEW else ""
                            note = row[COL_NOTE] if len(row) > COL_NOTE else ""

                            with st.expander(f"{name} â å¾å¯©æ ¸", expanded=True):
                                st.write(f"**å»ºç«èï¼** {creator}")
                                st.write(f"**åå¯©çµæï¼** {mrb}")
                                if note:
                                    st.write(f"**åè¨»ï¼** {note}")

                                b1, b2, b3 = st.columns(3)
                                approve = b1.button("â éé", key=f"ap_{name}")
                                reject = b2.button("é§å", key=f"rj_{name}")
                                adjust = b3.button("éèª¿æ´", key=f"ad_{name}")

                                if approve or reject or adjust:
                                    all_vals = ws.get_all_values()
                                    for si, sr in enumerate(all_vals):
                                        if len(sr) > COL_NAME and sr[COL_NAME].strip() == name:
                                            actual_row = si + 1
                                            today = datetime.now().strftime("%Y-%m-%d")

                                            if approve:
                                                ws.update_cell(actual_row, COL_BOSS_REVIEW + 1, "â éé")
                                                ws.update_cell(actual_row, COL_BOSS_DATE + 1, today)
                                                ws.update_cell(actual_row, COL_STATUS + 1, "ð¢ å·²å¥åº«")
                                                ws.update_cell(actual_row, COL_STOCK_DATE + 1, today)
                                                st.success(f"{name} å·²ééå¯©æ ¸ï¼")
                                            elif reject:
                                                ws.update_cell(actual_row, COL_BOSS_REVIEW + 1, "ð´ é§å")
                                                ws.update_cell(actual_row, COL_BOSS_DATE + 1, today)
                                                ws.update_cell(actual_row, COL_STATUS + 1, "ð´ æµ·å¥é§å")
                                                st.error(f"{name} å·²é§å")
                                            elif adjust:
                                                ws.update_cell(actual_row, COL_BOSS_REVIEW + 1, "â ï¸ éèª¿æ´")
                                                ws.update_cell(actual_row, COL_BOSS_DATE + 1, today)
                                                ws.update_cell(actual_row, COL_STATUS + 1, "ð  åå¯©éä¿®æ¹")
                                                st.warning(f"{name} éèª¿æ´")

                                            st.cache_resource.clear()
                                            st.rerun()
                                            break
                    elif boss_pwd:
                        st.error("å¯ç¢¼é¯èª¤")
            else:
                st.info("ç®åæ²æè§è²è³æ")
        else:
            st.warning("æ¾ä¸å°ç¸½æ§å°è¡¨é ­ï¼è«ç¢ºèª Google Sheets æ ¼å¼")

    except Exception as e:
        st.error(f"ç¡æ³é£æ¥ Google Sheetsï¼{str(e)}")
        st.info("è«ç¢ºèªï¼\n1. å·²å¨ Streamlit Secrets è¨­å® GCP æåå¸³èéé°\n2. Google Sheets å·²åäº«çµ¦æåå¸³è\n3. ç¸½æ§å°åé å·²å»ºç«")

#!/usr/bin/env python3
"""
MD AI角色库 Dashboard — 角色 IP 档案 + 专案进度
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(
    page_title="MD AI角色库",
    page_icon="🎭",
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


# ── 页首 ─────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
  <div>
    <span style="font-size:24px;font-weight:700;color:#fff;">🎭 MD AI角色库</span>
  </div>
  <div style="font-size:13px;color:#555;">资料更新：{datetime.now().strftime('%Y/%m/%d %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎭 角色 IP 档案", "📋 专案进度", "📊 IG 数据"])


# ════════════════════════════════════════════════════════
# TAB 1：角色 IP 档案
# ════════════════════════════════════════════════════════
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
        ("basic",      "▌ 基本信息"),
        ("appearance", "一、基础外貌"),
        ("persona",    "二、气质 / 人设"),
        ("content",    "三、内容属性"),
        ("world",      "四、世界观 / 背景"),
        ("voice",      "五、声音 / 表演"),
        ("business",   "六、商业 / 运营"),
    ]

    CHAR_TAGS = {
        "林浅浅":     [("邻家感","tag-pink"),("汉服","tag-pink"),("傲娇","tag-pink"),("闷骚","tag-gray"),("Switch偏M","tag-gray")],
        "倪妮":       [("运动系","tag-green"),("中国南方","tag-green"),("短发活力","tag-cyan"),("Switch偏S","tag-gray"),("反差感","tag-gray")],
        "王芷涵":[("法式","tag-purple"),("混血","tag-purple"),("底片","tag-purple"),("疏离感","tag-gray"),("文艺","tag-gray")],
        "顾染":       [("韩系冷艳","tag-amber"),("夜店女王","tag-amber"),("危险妩媚","tag-pink"),("强S","tag-gray"),("控制狂","tag-gray")],
        "胡芊璐":     [("成熟人妻","tag-cyan"),("中式复古","tag-cyan"),("温柔风骚","tag-pink"),("偏M","tag-gray"),("台湾复古","tag-gray")],
    }

    char_names = [c["name"] for c in ALL_CHARS]
    selected = st.radio(
        "选择角色",
        char_names,
        horizontal=True,
        label_visibility="collapsed",
    )

    char = next(c for c in ALL_CHARS if c["name"] == selected)

    ig_badge = f'<a href="{char["ig_url"]}" target="_blank" style="font-size:12px;color:#555;text-decoration:none;">{char["ig"]} ↗</a>' if char["ig"] else '<span style="font-size:12px;color:#444;">IG 待建立</span>'
    rank_label = "S 级" if char["rank"] == "S" else "A 级"
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
              <span style="color:#444;font-size:13px;">底图待补充</span>
            </div>
            """, unsafe_allow_html=True)

        # 林浅浅专属：三视图 + 动漫图
        if char["name"] == "林浅浅":
            sv_paths = [f"assets/characters/linqianqian_sv_{i}.jpg" for i in range(1,3)]
            sv_exists = [p for p in sv_paths if os.path.exists(os.path.join(os.path.dirname(__file__), p))]
            if sv_exists:
                st.markdown('<div style="font-size:12px;color:#E879A0;font-weight:600;margin:14px 0 6px 0;">▌ 三视图</div>', unsafe_allow_html=True)
                sv_cols = st.columns(len(sv_exists))
                for i, p in enumerate(sv_exists):
                    full_p = os.path.join(os.path.dirname(__file__), p)
                    sv_cols[i].image(full_p, use_container_width=True)

            anime_paths = [f"assets/characters/linqianqian_anime_{i}.jpg" for i in range(1,3)]
            anime_exists = [p for p in anime_paths if os.path.exists(os.path.join(os.path.dirname(__file__), p))]
            if anime_exists:
                st.markdown('<div style="font-size:12px;color:#7C6BDB;font-weight:600;margin:14px 0 6px 0;">▌ 动漫形象</div>', unsafe_allow_html=True)
                an_cols = st.columns(len(anime_exists))
                for i, p in enumerate(anime_exists):
                    full_p = os.path.join(os.path.dirname(__file__), p)
                    an_cols[i].image(full_p, use_container_width=True)

        st.markdown(f"""
        <div class="card" style="margin-top:12px;">
          <div class="card-title">AI 生图 Prompt</div>
          <div style="font-size:12px;color:#aaa;margin-bottom:8px;line-height:1.6;"><b style="color:#666;">中文：</b>{char['prompt_cn']}</div>
          <div style="font-size:12px;color:#aaa;line-height:1.6;"><b style="color:#666;">EN：</b>{char['prompt_en']}</div>
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

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>MD AI角色库 IP 资产系统</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 2：专案进度
# ════════════════════════════════════════════════════════
with tab2:

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ── 整体进度 KPI ─────────────────────────────────────
    st.markdown("""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">整体完成度</div>
        <div class="kpi-value" style="color:#4CAF50;">35%</div>
        <div class="kpi-sub">角色开发阶段</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">角色已建档</div>
        <div class="kpi-value" style="color:#FFB300;">4 / 4</div>
        <div class="kpi-sub">顾染・Céline・林浅浅・胡芊璐</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">社群已开设</div>
        <div class="kpi-value" style="color:#E879A0;">2 / 4</div>
        <div class="kpi-sub">林浅浅・Céline</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">目标 Deadline</div>
        <div class="kpi-value" style="font-size:22px;color:#7C6BDB;">Q2 2026</div>
        <div class="kpi-sub">首批内容上线</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 甘特图 ───────────────────────────────────────────
    st.markdown("### 📅 专案甘特图")

    gantt_data = [
        dict(Task="角色档案建立", Start="2026-03-01", Finish="2026-03-19", Stage="Phase 1 角色资产", Status="进行中"),
        dict(Task="面部锚点确认", Start="2026-03-10", Finish="2026-03-25", Stage="Phase 1 角色资产", Status="进行中"),
        dict(Task="商标申请（陆+台）", Start="2026-03-15", Finish="2026-04-30", Stage="Phase 1 角色资产", Status="待确认"),
        dict(Task="第一次角色资产会议", Start="2026-03-11", Finish="2026-03-12", Stage="Phase 1 角色资产", Status="已完成"),
        dict(Task="IG 自动化工作流建立", Start="2026-03-10", Finish="2026-03-18", Stage="Phase 2 AI生产", Status="已完成"),
        dict(Task="首批概念图生成（各角色×20张）", Start="2026-03-19", Finish="2026-03-31", Stage="Phase 2 AI生产", Status="待开始"),
        dict(Task="AI 影片脚本开发", Start="2026-04-01", Finish="2026-04-15", Stage="Phase 2 AI生产", Status="待开始"),
        dict(Task="林浅浅 IG 首批内容发布", Start="2026-03-01", Finish="2026-04-30", Stage="Phase 3 社群布局", Status="进行中"),
        dict(Task="Céline IG 首批内容发布", Start="2026-03-01", Finish="2026-04-30", Stage="Phase 3 社群布局", Status="进行中"),
        dict(Task="胡芊璐社群帐号开设", Start="2026-03-20", Finish="2026-03-21", Stage="Phase 3 社群布局", Status="待开始"),
        dict(Task="顾染社群帐号开设", Start="2026-03-25", Finish="2026-03-26", Stage="Phase 3 社群布局", Status="待开始"),
        dict(Task="黄版流程开拓", Start="2026-03-16", Finish="2026-03-23", Stage="Phase 4 量化", Status="进行中"),
        dict(Task="IP 授权框架建立", Start="2026-05-01", Finish="2026-05-31", Stage="Phase 4 量化", Status="待开始"),
    ]

    df_gantt = pd.DataFrame(gantt_data)
    df_gantt["Start"] = pd.to_datetime(df_gantt["Start"])
    df_gantt["Finish"] = pd.to_datetime(df_gantt["Finish"])

    color_map = {
        "完成": "#4CAF50",
        "进行中": "#FFB300",
        "待确认": "#7C6BDB",
        "待开始": "#444",
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
        legend=dict(bgcolor="#2d2d2d", bordercolor="#444", title="状态"),
        showlegend=True,
    )
    fig_gantt.add_vline(
        x=datetime.now().timestamp() * 1000,
        line_dash="dash", line_color="#E879A0", line_width=1.5,
        annotation_text="今天", annotation_font_color="#E879A0",
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

    # ── 看板 ─────────────────────────────────────────────
    st.markdown("### 📌 任务看板")

    KANBAN = {
        "🔴 待确认": [
            "第一次角色资产会议召开",
            "商标申请策略确认（陆+台）",
            "顾染面部锚点最终确认",
        ],
        "🟡 进行中": [
            "角色档案建立",
            "面部锚点确认",
            "林浅浅 IG 首批内容发布",
            "Céline IG 首批内容发布",
            "黄版流程开拓 3/16–3/23",
            "角色设定文件整理",
        ],
        "🔵 待开始": [
            "首批概念图生成（各角色×20张）3/19",
            "胡芊璐社群帐号开设 3/20",
            "顾染社群帐号开设 3/25",
            "AI 影片脚本开发 4/1",
            "对外合作洽谈 4/20",
            "IP 授权框架建立 5/1",
            "App 播放量 API 接入（技术待给）",
        ],
        "✅ 已完成": [
            "四大角色 IP 方向确定",
            "角色档案建立（4位）",
            "KPI 评分表建立",
            "周报自动化系统 v3",
            "IG 自动化工作流建立",
            "AI 内容 IP 商业计划书（13页）",
            "第一次角色资产会议 3/11",
            "MD AI角色库 Dashboard 建置",
        ],
    }

    col_colors = {
        "🔴 待确认": "#c0392b22",
        "🟡 进行中": "#FFB30022",
        "🔵 待开始": "#7C6BDB22",
        "✅ 已完成": "#4CAF5022",
    }
    border_colors = {
        "🔴 待确认": "#c0392b",
        "🟡 进行中": "#FFB300",
        "🔵 待开始": "#7C6BDB",
        "✅ 已完成": "#4CAF50",
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

    # ── 角色进度矩阵 ─────────────────────────────────────
    st.markdown("### 👤 角色开发进度")

    char_progress = [
        {"角色": "顾染",       "档案建立": "✅", "面部锚点": "✅", "底图生成": "⏳", "社群开设": "⏳", "首批内容": "⏳", "等级": "S"},
        {"角色": "林浅浅",     "档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "✅", "首批内容": "⏳", "等级": "S"},
        {"角色": "胡芊璐",     "档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "⏳", "首批内容": "⏳", "等级": "S"},
        {"角色": "王芷涵","档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "✅", "首批内容": "⏳", "等级": "A"},
    ]

    header = ["角色", "等级", "档案建立", "面部锚点", "底图生成", "社群开设", "首批内容"]
    header_html = "".join(f'<th style="padding:10px 16px;color:#888;font-size:12px;font-weight:500;text-align:center;">{h}</th>' for h in header)

    rows_html = ""
    for c in char_progress:
        lvl_color = "#FFB300" if c["等级"] == "S" else "#7C6BDB"
        rows_html += f"""<tr style="border-top:1px solid #2a2a2a;">
          <td style="padding:10px 16px;color:#fff;font-weight:600;">{c['角色']}</td>
          <td style="padding:10px 16px;text-align:center;"><span style="color:{lvl_color};font-weight:700;">{c['等级']}</span></td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['档案建立']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['面部锚点']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['底图生成']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['社群开设']}</td>
          <td style="padding:10px 16px;text-align:center;font-size:16px;">{c['首批内容']}</td>
        </tr>"""

    st.markdown(f"""
    <div class="card" style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
      <div style="margin-top:12px;font-size:12px;color:#555;">✅ 完成 &nbsp; ⏳ 进行中/待开始</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>MD AI角色库 · 专案进度追踪</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 3：IG 数据
# ════════════════════════════════════════════════════════
with tab3:

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ── 数据说明 ─────────────────────────────────────────
    st.markdown("""
    <div style="background:#242424;border:1px solid #3a3a3a;border-radius:8px;padding:12px 18px;margin-bottom:20px;font-size:12px;color:#666;">
      ⚠️ 目前为手动填写数据，尚未接自动爬虫。数据以最后人工核对时间为准。
    </div>
    """, unsafe_allow_html=True)

    # ── IG 数据（手动维护） ──────────────────────────────
    IG_DATA = [
        {
            "name": "林浅浅",
            "en_name": "Lin Qianqian",
            "ig": "@qianqian.hanfu",
            "ig_url": "https://www.instagram.com/qianqian.hanfu/",
            "color": "#FFB300",
            "status": "active",
            "followers": 9196,
            "following": 14,
            "posts": 16,
            "avg_likes": 1767,
            "avg_comments": 22,
            "last_post": "2026-03-27",
            "note": "主帳號，目前最活躍",
            "updated": "2026-03-27",
            "highlights": [
                {
                    "date": "2026-03-11",
                    "content": "也是换我cha了！！😁😁\n#nobatidão #JennieNoBatidão #DanceCover #funkdance #nobatidaochallenge",
                    "likes": 14000,
                    "comments": 77,
                    "views": 224000,
                },
            ],
        },
        {
            "name": "王芷涵",
            "en_name": "Céline Wang",
            "ig": "@celineparisasia",
            "ig_url": "https://www.instagram.com/celineparisasia/",
            "color": "#7C6BDB",
            "status": "new",
            "followers": 223,
            "following": None,
            "posts": None,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "新帳號，剛建立",
            "updated": "2026-03-25",
        },
        {
            "name": "顧染",
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
            "note": "帳號待建立",
            "updated": None,
        },
        {
            "name": "胡芊璐",
            "en_name": "Hu Qianlu",
            "ig": None,
            "ig_url": None,
            "color": "#26C6DA",
            "status": "pending",
            "followers": None,
            "following": None,
            "posts": None,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "帳號待建立",
            "updated": None,
        },
        {
            "name": "倪妮",
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
            "note": "帳號待建立",
            "updated": None,
        },
    ]

    STATUS_LABEL = {
        "active":  ("✅ 活躍", "#4CAF50"),
        "new":     ("🆕 新帳號", "#7C6BDB"),
        "pending": ("⏳ 待建立", "#555"),
    }

    # ── KPI 卡片：總追蹤數 ────────────────────────────────
    total_followers = sum(d["followers"] for d in IG_DATA if d["followers"])
    active_count = sum(1 for d in IG_DATA if d["status"] in ("active", "new"))

    st.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">總追蹤人數</div>
        <div class="kpi-value" style="color:#E879A0;">{total_followers:,}</div>
        <div class="kpi-sub">所有角色合計</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">已開設帳號</div>
        <div class="kpi-value" style="color:#FFB300;">{active_count} / 5</div>
        <div class="kpi-sub">林浅浅・Céline</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">待建立帳號</div>
        <div class="kpi-value" style="color:#555;">3 / 5</div>
        <div class="kpi-sub">顾染・胡芊璐・倪妮</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">數據更新方式</div>
        <div class="kpi-value" style="font-size:18px;color:#444;">手動</div>
        <div class="kpi-sub">爬蟲接入後自動更新</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 追蹤數長條圖 ─────────────────────────────────────
    active_data = [d for d in IG_DATA if d["followers"] is not None]
    if active_data:
        fig_bar = go.Figure(go.Bar(
            x=[d["name"] for d in active_data],
            y=[d["followers"] for d in active_data],
            marker_color=[d["color"] for d in active_data],
            text=[f'{d["followers"]:,}' for d in active_data],
            textposition="outside",
        ))
        fig_bar.update_layout(
            height=280,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="#242424",
            paper_bgcolor="#242424",
            font=dict(color="#aaa", size=13),
            xaxis=dict(gridcolor="#333", linecolor="#333"),
            yaxis=dict(gridcolor="#333", linecolor="#333", title="追蹤數"),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── 各角色明細卡片 ────────────────────────────────────
    st.markdown("### 👤 各角色 IG 明細")

    for d in IG_DATA:
        status_text, status_color = STATUS_LABEL[d["status"]]
        ig_link = f'<a href="{d["ig_url"]}" target="_blank" style="color:#888;font-size:12px;">{d["ig"]} ↗</a>' if d["ig"] else '<span style="color:#444;font-size:12px;">—</span>'
        followers_str = f'{d["followers"]:,}' if d["followers"] is not None else "—"
        updated_str = d["updated"] or "—"

        def fmt_metric(val, suffix=""):
            return f"{val:,}{suffix}" if val is not None else "—"

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
              <span style="font-size:11px;color:#444;">更新：{updated_str}</span>
            </div>
          </div>
          <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">追蹤數</div>
              <div style="font-size:22px;font-weight:700;color:{d['color']};">{followers_str}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">追蹤中</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['following'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">貼文數</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['posts'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">平均讚數</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['avg_likes'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">平均留言</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['avg_comments'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">最後貼文</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{d['last_post'] or '—'}</div></div>
          </div>
          {f'<div style="margin-top:10px;font-size:12px;color:#555;">備註：{d["note"]}</div>' if d["note"] else ""}
        </div>
        """, unsafe_allow_html=True)

        if d.get("highlights"):
            import streamlit.components.v1 as components
            items_html = ""
            for h in d["highlights"]:
                likes_str = f'{h["likes"] // 10000}萬+' if h["likes"] >= 10000 else str(h["likes"])
                views_str = f'{h["views"] // 10000}萬+' if h["views"] >= 10000 else str(h["views"])
                content_html = h["content"].replace("\n", "<br>")
                items_html += (
                    '<div style="background:#1a1a1a;border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
                    '<div style="flex:1;">'
                    f'<div style="font-size:11px;color:#666;margin-bottom:4px;">{h["date"]}</div>'
                    f'<div style="font-size:12px;color:#aaa;line-height:1.5;">{content_html}</div>'
                    '</div>'
                    '<div style="display:flex;gap:16px;flex-shrink:0;margin-left:12px;">'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">❤️ 讚</div><div style="font-size:15px;font-weight:700;color:#E879A0;">{likes_str}</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">💬 留言</div><div style="font-size:15px;font-weight:700;color:#aaa;">{h["comments"]}</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">▶️ 觀看</div><div style="font-size:15px;font-weight:700;color:#FFB300;">{views_str}</div></div>'
                    '</div></div></div>'
                )
            highlight_html = (
                f'<div style="font-family:sans-serif;background:#242424;border:1px solid #3a3a3a;border-radius:10px;'
                f'padding:16px 20px;margin-bottom:8px;border-left:3px solid {d["color"]};">'
                '<div style="font-size:11px;color:#E879A0;font-weight:600;margin-bottom:10px;">🔥 亮點貼文</div>'
                + items_html +
                '</div>'
            )
            components.html(highlight_html, height=len(d["highlights"]) * 100 + 60, scrolling=False)


    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>MD AI角色库 · IG 數據監控</div>", unsafe_allow_html=True)

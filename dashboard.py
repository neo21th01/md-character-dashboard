#!/usr/bin/env python3
"""
IG 社群监听 Dashboard — MD AI角色库
视觉风格参考：社群声量分析 Dark Mode
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

ACCOUNT_NAMES = {
    "qianqian.hanfu": "林浅浅",
    "celineparisasia": "Céline",
}
ACCOUNT_COLORS = {
    "qianqian.hanfu": "#E879A0",
    "celineparisasia": "#7C6BDB",
}

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

/* Tab 样式 */
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

.post-card {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.post-meta    { font-size: 12px; color: #888; margin-top: 8px; }
.post-caption { font-size: 14px; color: #ddd; margin: 8px 0; line-height: 1.5; }

.insight-item {
    background: #2d2d2d;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
    font-size: 14px;
    color: #ccc;
    line-height: 1.5;
}
.bar-row { display: flex; align-items: center; margin-bottom: 10px; }
.bar-label { width: 80px; font-size: 13px; color: #ccc; flex-shrink: 0; }
.bar-track { flex: 1; background: #333; border-radius: 4px; height: 8px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 4px; }
.bar-pct   { width: 40px; text-align: right; font-size: 12px; color: #888; }

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


# ── DB helpers ────────────────────────────────────────────
def get_conn():
    if not os.path.exists(DB_PATH): return None
    return sqlite3.connect(DB_PATH)

def load_profiles():
    conn = get_conn()
    if not conn: return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM profile_snapshots ORDER BY scraped_at DESC", conn)
    conn.close()
    return df

def load_posts(days=90):
    conn = get_conn()
    if not conn: return pd.DataFrame()
    since = (datetime.now() - timedelta(days=days)).isoformat()
    df = pd.read_sql(
        "SELECT * FROM posts WHERE post_date>=? ORDER BY post_date DESC",
        conn, params=(since,)
    )
    conn.close()
    return df

profiles_df = load_profiles()
posts_df    = load_posts()

if not posts_df.empty:
    posts_df["post_date"]    = pd.to_datetime(posts_df["post_date"])
    posts_df["date"]         = posts_df["post_date"].dt.date
    posts_df["account_name"] = posts_df["username"].map(ACCOUNT_NAMES)
    posts_df["engagement"]   = posts_df["likes"] + posts_df["comments"]

latest = pd.DataFrame()
if not profiles_df.empty:
    latest = profiles_df.drop_duplicates(subset=["username"], keep="first")


# ── 页首 ─────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
  <div>
    <span style="font-size:24px;font-weight:700;color:#fff;">🎭 MD AI角色库</span>
  </div>
  <div style="font-size:13px;color:#555;">资料更新：{datetime.now().strftime('%Y/%m/%d %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

tab2, tab1, tab3 = st.tabs(["🎭 角色 IP 档案", "📊 社群监听", "📋 专案进度"])


# ════════════════════════════════════════════════════════
# TAB 1：社群监听
# ════════════════════════════════════════════════════════
with tab1:

    if profiles_df.empty:
        st.info("📡 社群監聽數據每日09:00自動更新，目前展示角色IP檔案與專案進度。")
        st.markdown("### 📊 林淺淺 @qianqian.hanfu")
        st.markdown("**5,136 追蹤** · 每日自動抓取 IG 數據（本機運行）")
        st.markdown("### 📊 Céline @celineparisasia")
        st.markdown("**223 追蹤** · 成長中")
        return

    def get_val(username, field):
        row = latest[latest["username"] == username]
        if row.empty: return 0
        return int(row.iloc[0].get(field, 0))

    total_posts  = len(posts_df) if not posts_df.empty else 0
    total_eng    = int(posts_df["engagement"].sum()) if not posts_df.empty else 0
    ql_followers = get_val("qianqian.hanfu", "followers")
    ce_followers = get_val("celineparisasia", "followers")

    st.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">林浅浅 追踪者</div>
        <div class="kpi-value" style="color:#E879A0;">{ql_followers:,}</div>
        <div class="kpi-sub">@qianqian.hanfu</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Céline 追踪者</div>
        <div class="kpi-value" style="color:#7C6BDB;">{ce_followers:,}</div>
        <div class="kpi-sub">@celineparisasia</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">分析帖文总数</div>
        <div class="kpi-value">{total_posts}</div>
        <div class="kpi-sub">近 90 天</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">总互动数</div>
        <div class="kpi-value" style="color:#FFB300;">{total_eng:,}</div>
        <div class="kpi-sub">likes + 留言</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 追踪者趋势
    st.markdown("### 📈 追踪者趋势")
    if len(profiles_df["scraped_date"].unique()) > 1:
        fig = go.Figure()
        for username, name in ACCOUNT_NAMES.items():
            df_acc = profiles_df[profiles_df["username"] == username].sort_values("scraped_date")
            if not df_acc.empty:
                fig.add_trace(go.Scatter(
                    x=df_acc["scraped_date"], y=df_acc["followers"],
                    mode="lines+markers", name=name,
                    line=dict(color=ACCOUNT_COLORS[username], width=2),
                    marker=dict(size=6),
                ))
        fig.update_layout(
            height=260, margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="#242424", paper_bgcolor="#242424",
            font=dict(color="#aaa", size=12),
            xaxis=dict(gridcolor="#333", linecolor="#333"),
            yaxis=dict(gridcolor="#333", linecolor="#333"),
            legend=dict(bgcolor="#2d2d2d", bordercolor="#444"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="card"><div class="kpi-sub">追踪者趋势需要至少 2 天数据，明天再来 ✨</div></div>', unsafe_allow_html=True)

    if not posts_df.empty:
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("### 📊 各帐号互动占比")
            eng_by_acc = posts_df.groupby("account_name")["engagement"].sum().sort_values(ascending=True)
            total_e = eng_by_acc.sum() or 1
            bars = ""
            color_map = {"林浅浅": "#E879A0", "Céline": "#7C6BDB"}
            for acc, val in eng_by_acc.items():
                pct = val / total_e * 100
                bars += f"""<div class="bar-row">
                  <div class="bar-label">{acc}</div>
                  <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%;background:{color_map.get(acc,'#888')};"></div></div>
                  <div class="bar-pct">{pct:.0f}%</div></div>"""
            st.markdown(f'<div class="card"><div class="card-title">互动数占比</div>{bars}</div>', unsafe_allow_html=True)

        with col_r:
            st.markdown("### 🏷️ 贴文类型分布")
            type_map = {"image": "图片", "video": "影片", "carousel": "轮播"}
            type_colors = {"图片": "#7C6BDB", "影片": "#E879A0", "轮播": "#26C6DA"}
            type_counts = posts_df["post_type"].map(type_map).value_counts()
            total_t = type_counts.sum() or 1
            bars2 = ""
            for tp, cnt in type_counts.items():
                pct = cnt / total_t * 100
                bars2 += f"""<div class="bar-row">
                  <div class="bar-label">{tp}</div>
                  <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%;background:{type_colors.get(tp,'#888')};"></div></div>
                  <div class="bar-pct">{pct:.0f}%</div></div>"""
            st.markdown(f'<div class="card"><div class="card-title">类型分布（近 90 天）</div>{bars2}</div>', unsafe_allow_html=True)

        # 热门帖文
        st.markdown("### 🔥 热门帖文精选")
        filter_acc = st.radio("筛选", ["全部", "林浅浅", "Céline"], horizontal=True, label_visibility="collapsed")
        filtered = posts_df if filter_acc == "全部" else posts_df[posts_df["account_name"] == filter_acc]
        top10 = filtered.nlargest(10, "engagement")

        tag_color = {"qianqian.hanfu": "tag-pink", "celineparisasia": "tag-purple"}
        type_tag  = {"image": "tag-cyan", "video": "tag-green", "carousel": "tag-gray"}

        for _, row in top10.iterrows():
            cap = (row["caption"] or "")
            cap_short = cap[:80] + ("..." if len(cap) > 80 else "")
            st.markdown(f"""
            <div class="post-card">
              <span class="tag {tag_color.get(row['username'],'tag-gray')}">{row['account_name']}</span>
              <span class="tag {type_tag.get(row['post_type'],'tag-gray')}">{row['post_type']}</span>
              <div class="post-caption">{cap_short if cap_short else '（无 caption）'}</div>
              <div class="post-meta">❤️ {row['likes']:,} &nbsp; 💬 {row['comments']:,} &nbsp; ⚡ {row['engagement']:,} &nbsp; 📅 {row['date']}
              &nbsp; <a href="{row['url']}" target="_blank" style="color:#555;">查看 ↗</a></div>
            </div>""", unsafe_allow_html=True)

        # 洞察
        st.markdown("### 💡 关键洞察")
        c1, c2 = st.columns(2)
        avg_eng  = posts_df.groupby("account_name")["engagement"].mean()
        best_acc = avg_eng.idxmax() if not avg_eng.empty else "—"
        best_val = int(avg_eng.max()) if not avg_eng.empty else 0
        top_post = posts_df.nlargest(1, "engagement").iloc[0] if not posts_df.empty else None

        with c1:
            items = [
                f"🚀 <b>{best_acc}</b> 平均互动数最高（{best_val:,}），是目前主力帐号",
                f"📅 近 90 天共分析 <b>{total_posts}</b> 篇贴文，总互动 <b>{total_eng:,}</b>",
                f"🏆 最热贴文互动达 <b>{int(top_post['engagement']):,}</b>（{top_post['account_name']}）" if top_post is not None else "🏆 暂无贴文数据",
            ]
            html = "".join(f'<div class="insight-item">{i}</div>' for i in items)
            st.markdown(f'<div class="card"><div class="card-title">数据洞察</div>{html}</div>', unsafe_allow_html=True)
        with c2:
            items2 = [
                "📸 对比图片 vs 影片互动率，找出最适合的内容形式",
                "🔄 每天 09:00 自动更新数据，持续追踪帐号成长",
                "🎯 建议对比两帐号发文节奏，找出最佳发文时段",
            ]
            html2 = "".join(f'<div class="insight-item">{i}</div>' for i in items2)
            st.markdown(f'<div class="card"><div class="card-title">行动建议</div>{html2}</div>', unsafe_allow_html=True)

    else:
        st.info("📡 贴文互动数据等 IG 限速解除后自动补齐，Profile 基本数据已显示在上方 👆")

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>MD AI角色库 · IG 社群监听 · 每日 09:00 自动更新</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 2：角色 IP 档案
# ════════════════════════════════════════════════════════
with tab2:
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

    # 角色选择按钮列
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
            # 三视图
            sv_paths = [f"assets/characters/linqianqian_sv_{i}.jpg" for i in range(1,3)]
            sv_exists = [p for p in sv_paths if os.path.exists(os.path.join(os.path.dirname(__file__), p))]
            if sv_exists:
                st.markdown('<div style="font-size:12px;color:#E879A0;font-weight:600;margin:14px 0 6px 0;">▌ 三视图</div>', unsafe_allow_html=True)
                sv_cols = st.columns(len(sv_exists))
                for i, p in enumerate(sv_exists):
                    full_p = os.path.join(os.path.dirname(__file__), p)
                    sv_cols[i].image(full_p, use_container_width=True)

            # 动漫图（只显示前2张）
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
# TAB 3：专案进度
# ════════════════════════════════════════════════════════
with tab3:
    import plotly.express as px

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
        # Phase 1 角色资产
        dict(Task="角色档案建立", Start="2026-03-01", Finish="2026-03-19", Stage="Phase 1 角色资产", Status="进行中"),
        dict(Task="面部锚点确认", Start="2026-03-10", Finish="2026-03-25", Stage="Phase 1 角色资产", Status="进行中"),
        dict(Task="商标申请（陆+台）", Start="2026-03-15", Finish="2026-04-30", Stage="Phase 1 角色资产", Status="待确认"),
        dict(Task="第一次角色资产会议", Start="2026-03-11", Finish="2026-03-12", Stage="Phase 1 角色资产", Status="已完成"),
        # Phase 2 AI生产
        dict(Task="IG 自动化工作流建立", Start="2026-03-10", Finish="2026-03-18", Stage="Phase 2 AI生产", Status="已完成"),
        dict(Task="首批概念图生成（各角色×20张）", Start="2026-03-19", Finish="2026-03-31", Stage="Phase 2 AI生产", Status="待开始"),
        dict(Task="AI 影片脚本开发", Start="2026-04-01", Finish="2026-04-15", Stage="Phase 2 AI生产", Status="待开始"),
        # Phase 3 社群布局
        dict(Task="林浅浅 IG 首批内容发布", Start="2026-03-01", Finish="2026-04-30", Stage="Phase 3 社群布局", Status="进行中"),
        dict(Task="Céline IG 首批内容发布", Start="2026-03-01", Finish="2026-04-30", Stage="Phase 3 社群布局", Status="进行中"),
        dict(Task="胡芊璐社群帐号开设", Start="2026-03-20", Finish="2026-03-21", Stage="Phase 3 社群布局", Status="待开始"),
        dict(Task="顾染社群帐号开设", Start="2026-03-25", Finish="2026-03-26", Stage="Phase 3 社群布局", Status="待开始"),
        # Phase 4 量化
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
    # 今天标记线
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

#!/usr/bin/env python3
"""
智影AI角色库 Dashboard — 角色 IP 档案 + 专案进度
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
    page_title="智影AI角色库",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #1a1a1a; }
[data-testid="stHeader"] { background: #1a1a1a; }
section[data-testid="stSidebar"] { background: #141414; }

/* 主页签（🎭 角色 IP 档案 / 📋 专案进度 / 📊 社群数据 / 🎛️ 总控台） */
[data-testid="stTabs"] button {
    font-size: 14px !important;
    color: #888 !important;
    padding: 8px 18px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #fff !important;
    border-bottom: 2px solid #E879A0 !important;
}
/* 子分页（🟢 已入库 / ⏳ 待审核 / 🧊 开发中 / 📚 全部）— 更小、更低调 */
[data-testid="stTabs"] [data-testid="stTabs"] button {
    font-size: 12px !important;
    color: #666 !important;
    padding: 4px 10px !important;
    min-height: 28px !important;
}
[data-testid="stTabs"] [data-testid="stTabs"] button[aria-selected="true"] {
    color: #E879A0 !important;
    border-bottom: 1px solid #E879A0 !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid #2a2a2a;
}

/* Radio 改造：性别 filter 用的 pill button 样式 */
.stRadio [role="radiogroup"] {
    gap: 8px !important;
    flex-wrap: wrap;
}
.stRadio [role="radiogroup"] > label {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 999px;
    padding: 4px 14px !important;
    margin: 0 !important;
    cursor: pointer;
    transition: all 0.15s ease;
    font-size: 12px !important;
}
.stRadio [role="radiogroup"] > label:hover {
    border-color: #555;
    background: #222;
}
/* 隐藏 radio 圆点 */
.stRadio [role="radiogroup"] > label > div:first-child {
    display: none !important;
}
/* 预设选中状态：粉色 glow（gender 的 色 也会覆写于下方） */
.stRadio [role="radiogroup"] > label:has(input[type="radio"]:checked) {
    background: #E879A015 !important;
    border-color: #E879A0 !important;
    color: #E879A0 !important;
    box-shadow: 0 0 8px #E879A044;
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
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
  <div>
    <span style="font-size:20px;font-weight:700;color:#fff;letter-spacing:0.02em;">🎭 智影AI角色库</span>
  </div>
  <div style="font-size:11px;color:#555;">资料更新：{datetime.now().strftime('%Y/%m/%d %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# 总控台状态同步（让 Tab 1 显示海哥审核结果）
# ════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)
def _load_stock_status_from_sheet():
    """从总控台读取每位角色的状态。失败回传 {}。10 分钟快取，加 8 秒 socket timeout 避免卡住 UI。"""
    import socket
    _prev_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(8)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1p5PkaYQQ8_g4iW9dRJlKucGG8o4kSKEZEBwEmknEV9k")
        # Worksheet 名稱兼容繁簡：先試簡體，找不到再試繁體
        try:
            ws = sheet.worksheet("\U0001f39b\ufe0f 总控台")
        except Exception:
            ws = sheet.worksheet("\U0001f39b\ufe0f 總控台")
        # 只读名称 + 状态两栏，不整表拉
        names = ws.col_values(2)  # B 栏 = COL_NAME + 1
        statuses = ws.col_values(12)  # L 栏 = COL_STATUS + 1
        status_map = {}
        for i in range(2, min(len(names), len(statuses))):
            name = (names[i] or "").strip()
            status = (statuses[i] or "").strip()
            if not name:
                continue
            if status_map.get(name) == "已入库":
                continue
            # Sheet 状态已统一简体（user 2026-04-28 确认）
            # 比对顺序：先比对更具体的字串（含「初审」/「海哥」前缀），再比对一般字
            if "已入库" in status:
                status_map[name] = "已入库"
            elif "待海哥审" in status:
                status_map[name] = "待审"
            elif "初审需修改" in status:
                status_map[name] = "初审需修改"  # Mr.B 初审阶段的回稿，归开发中
            elif "海哥驳回" in status or "驳回" in status:
                status_map[name] = "驳回"
            elif "海哥需调整" in status or "需调整" in status or "需修改" in status:
                status_map[name] = "需调整"
            elif "捏人中" in status:
                status_map[name] = "捏人中"
        return status_map
    except Exception:
        return {}
    finally:
        socket.setdefaulttimeout(_prev_timeout)


_NAME_ALIASES = {
    "林浅浅": ["林淺淺"], "林淺淺": ["林浅浅"],
    "顾染":   ["顧染"],   "顧染":   ["顾染"],
    "欧晴":   ["歐晴"],   "歐晴":   ["欧晴"],
    "纪烟":   ["紀煙"],   "紀煙":   ["纪烟"],
    "白鹿鸣": ["白鹿鳴"], "白鹿鳴": ["白鹿鸣"],
    "云舒":   ["雲舒"],   "雲舒":   ["云舒"],
}


def get_char_stock_status(char_name, fallback_in_stock=False, fallback_review=False):
    """回传角色的总控台状态字串；找不到时若 fallback_in_stock=True 回『已入库』；fallback_review=True 回『待审』。"""
    status_map = _load_stock_status_from_sheet()
    for c in [char_name] + _NAME_ALIASES.get(char_name, []):
        if c in status_map:
            return status_map[c]
    if fallback_in_stock:
        return "已入库"
    if fallback_review:
        return "待审"
    return None


tab1, tab3, tab4 = st.tabs(["🎭 角色 IP 档案", "📊 社群数据", "🎛️ 总控台"])
tab2 = None  # 专案进度 暂时隐藏（2026-04-24），未来恢复：还原 tabs 清单 + 取消下方 `if False:` 即可


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

    _BADGE_STYLES = {
        "已入库":      ("#4CAF50", "✅ 已入库"),
        "待审":        ("#FFB300", "⏳ 待海哥审"),
        "驳回":        ("#F44336", "🔴 驳回"),
        "需调整":      ("#FF9800", "⚠️ 需调整"),
        "初审需修改":  ("#FF9800", "🟠 初审需修改"),
        "捏人中":      ("#7C6BDB", "🧊 捏人中"),
    }

    # ── 合并 sheet 角色名 + characters.py 详细资料 ──────────────
    sheet_status_map = _load_stock_status_from_sheet()  # {name: status}
    detailed_by_name = {c["name"]: c for c in ALL_CHARS}
    # 加入简繁体别名对应
    for c in ALL_CHARS:
        for alias in _NAME_ALIASES.get(c["name"], []):
            detailed_by_name[alias] = c

    # 搜集所有要显示的角色（sheet 有 + characters.py 有 的联集）
    all_names_set = set(sheet_status_map.keys()) | {c["name"] for c in ALL_CHARS}
    merged_chars = []
    for name in all_names_set:
        detail = detailed_by_name.get(name)
        # 简繁体 fallback：若 sheet 名字找不到 detail，找对应
        if not detail:
            for alias in _NAME_ALIASES.get(name, []):
                if alias in detailed_by_name:
                    detail = detailed_by_name[alias]
                    break
        status = get_char_stock_status(
            name,
            fallback_in_stock=(detail or {}).get("in_stock", False),
            fallback_review=(detail or {}).get("force_review_bucket", False),
        )
        gender = (detail or {}).get("gender", "女")  # 预设女（过渡期）
        merged_chars.append({
            "display_name": name,
            "detail": detail,
            "status": status,
            "gender": gender,
        })

    # 去重：如果 sheet 和 characters.py 都有，只保留一个（用 detail 的名字）
    seen_detail_ids = set()
    unique_chars = []
    for mc in merged_chars:
        if mc["detail"]:
            did = id(mc["detail"])
            if did in seen_detail_ids:
                continue
            seen_detail_ids.add(did)
            mc["display_name"] = mc["detail"]["name"]
        unique_chars.append(mc)

    # 排序：依 characters.py 原本顺序（有 detail 的），然后 sheet-only 的照名字
    _detail_order = {c["name"]: i for i, c in enumerate(ALL_CHARS)}
    def _sort_key(x):
        if x["detail"]:
            return (0, _detail_order.get(x["detail"]["name"], 9999))
        return (1, x["display_name"])
    unique_chars.sort(key=_sort_key)

    # ── 第一层：性别 filter（只有 女 / 男 两个 pill；预设女）──
    gender_filter = st.radio(
        "性别",
        ["👩 女角色", "👨 男角色"],
        horizontal=True,
        label_visibility="collapsed",
        key="tab1_gender_filter",
    )
    # 选中色：女=粉红 glow、男=蓝 glow
    if gender_filter == "👨 男角色":
        _g_color, _g_glow = "#4A9EE0", "#4A9EE088"
    else:
        _g_color, _g_glow = "#E879A0", "#E879A088"
    # 放宽选择器：applies to all st.radio selected state（character radio 也会跟随目前性别色，视觉一致）
    st.markdown(f"""
    <style>
    div[data-testid="stRadio"] [role="radiogroup"] > label:has(input[type="radio"]:checked) {{
        background: {_g_color}22 !important;
        border-color: {_g_color} !important;
        color: {_g_color} !important;
        box-shadow: 0 0 12px {_g_glow} !important;
        font-weight: 600 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    if gender_filter == "👨 男角色":
        filtered = [c for c in unique_chars if c["gender"] == "男"]
    else:
        filtered = [c for c in unique_chars if c["gender"] == "女"]

    # ── 第二层：按状态分桶 ──────────────
    # 角色 flag：dev_phase 強制歸 開發中、force_review_bucket 強制歸 待審核
    def _is_dev(c):
        return bool(c.get("detail") and c["detail"].get("dev_phase"))
    def _is_force_review(c):
        return bool(c.get("detail") and c["detail"].get("force_review_bucket"))

    bucket_in_stock = [c for c in filtered if c["status"] == "已入库" and not _is_dev(c) and not _is_force_review(c)]
    bucket_in_review = [
        c for c in filtered
        if (c["status"] in ("待审", "需调整", "驳回") or _is_force_review(c)) and not _is_dev(c)
    ]
    bucket_in_dev = [
        c for c in filtered
        if _is_dev(c)
        or ((c["status"] in ("捏人中", "初审需修改") or c["status"] is None) and not _is_force_review(c))
    ]

    # ── 角色详情渲染函式 ──────────────
    def render_character_detail(char):
        """完整渲染一个有 detail 资料的角色。"""
        ig_badge = (
            f'<a href="{char["ig_url"]}" target="_blank" style="font-size:12px;color:#555;text-decoration:none;">{char["ig"]} ↗</a>'
            if char.get("ig") else '<span style="font-size:12px;color:#444;">IG 待建立</span>'
        )
        rank_label = "S 级" if char["rank"] == "S" else "A 级"
        _sheet_status = get_char_stock_status(
            char["name"],
            fallback_in_stock=char.get("in_stock", False),
            fallback_review=char.get("force_review_bucket", False),
        )
        if _sheet_status and _sheet_status in _BADGE_STYLES:
            _c, _lbl = _BADGE_STYLES[_sheet_status]
            in_stock_badge = f'<span style="background:{_c}22;border:1px solid {_c};color:{_c};border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600;">{_lbl}</span>'
        else:
            in_stock_badge = ''
        tags_html = "".join(f'<span class="tag {cls}">{t}</span>' for t, cls in CHAR_TAGS.get(char["name"], []))

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin:20px 0 14px 0;">
          <span style="font-size:24px;font-weight:700;color:#fff;">{char['name']}</span>
          <span style="font-size:14px;color:#888;">{char['en_name']}</span>
          <span style="background:{char['rank_color']}22;border:1px solid {char['rank_color']};color:{char['rank_color']};
                border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600;">{rank_label}</span>
          {in_stock_badge}
          {ig_badge}
        </div>
        <div style="margin-bottom:18px;">{tags_html}</div>
        """, unsafe_allow_html=True)

        _char_placeholder = st.empty()
        with _char_placeholder.container():
            col_imgs, col_info = st.columns([2, 3])

            with col_imgs:
                if char.get("images"):
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

                tri_view_paths = char.get("tri_view_images", [])
                sv_exists = [p for p in tri_view_paths if os.path.exists(os.path.join(os.path.dirname(__file__), p))]
                if sv_exists:
                    st.markdown('<div style="font-size:12px;color:#E879A0;font-weight:600;margin:14px 0 6px 0;">▌ 三视图</div>', unsafe_allow_html=True)
                    sv_cols = st.columns(len(sv_exists))
                    for i, p in enumerate(sv_exists):
                        full_p = os.path.join(os.path.dirname(__file__), p)
                        sv_cols[i].image(full_p, use_container_width=True)

                anime_paths = char.get("anime_images", [])
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
                  <div style="font-size:12px;color:#aaa;margin-bottom:8px;line-height:1.6;"><b style="color:#666;">中文：</b>{char.get('prompt_cn','')}</div>
                  <div style="font-size:12px;color:#aaa;line-height:1.6;"><b style="color:#666;">EN：</b>{char.get('prompt_en','')}</div>
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

    def render_placeholder(name, status):
        """只在 sheet 有、characters.py 还没建档的角色 —— 显示占位卡片。"""
        badge_html = ""
        if status and status in _BADGE_STYLES:
            _c, _lbl = _BADGE_STYLES[status]
            badge_html = f'<span style="background:{_c}22;border:1px solid {_c};color:{_c};border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600;">{_lbl}</span>'
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin:20px 0 14px 0;">
          <span style="font-size:24px;font-weight:700;color:#fff;">{name}</span>
          <span style="background:#7C6BDB22;border:1px solid #7C6BDB;color:#7C6BDB;border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600;">📝 待建档</span>
          {badge_html}
        </div>
        <div style="background:#1e1e1e;border:1px dashed #333;border-radius:10px;padding:40px 20px;text-align:center;margin-top:12px;">
          <div style="color:#999;font-size:14px;margin-bottom:8px;">「{name}」已登记于总控台，但尚未在 characters.py 建立完整档案</div>
          <div style="color:#555;font-size:12px;">请通知开发者补建：面部锚点、外貌、气质、内容属性、世界观、声音、商业资料、AI prompt、照片等</div>
        </div>
        """, unsafe_allow_html=True)

    def render_bucket(chars_in_bucket, bucket_key):
        """渲染某一个桶子的 radio + 选中角色详情。"""
        if not chars_in_bucket:
            st.markdown(
                '<div style="color:#555;font-size:13px;padding:24px 8px;">此区块目前没有角色</div>',
                unsafe_allow_html=True,
            )
            return
        names = [c["display_name"] for c in chars_in_bucket]
        if len(names) <= 10:
            sel = st.radio(
                "选择角色",
                names,
                horizontal=True,
                label_visibility="collapsed",
                key=f"tab1_sel_{bucket_key}",
            )
        else:
            sel = st.selectbox(
                "选择角色",
                names,
                label_visibility="collapsed",
                key=f"tab1_sel_{bucket_key}",
            )
        mc = next(c for c in chars_in_bucket if c["display_name"] == sel)
        if mc["detail"]:
            render_character_detail(mc["detail"])
        else:
            render_placeholder(mc["display_name"], mc["status"])

    # ── 状态子分页 ──────────────
    sub_tabs = st.tabs([
        f"🟢 已入库 ({len(bucket_in_stock)})",
        f"⏳ 待审核 ({len(bucket_in_review)})",
        f"🧊 开发中 ({len(bucket_in_dev)})",
        f"📚 全部 ({len(filtered)})",
    ])
    with sub_tabs[0]: render_bucket(bucket_in_stock, "in_stock")
    with sub_tabs[1]: render_bucket(bucket_in_review, "in_review")
    with sub_tabs[2]: render_bucket(bucket_in_dev, "in_dev")
    with sub_tabs[3]: render_bucket(filtered, "all")

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>智影AI角色库 IP 资产系统</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 2：专案进度（暂时隐藏 2026-04-24，未来恢复：把 if False 改 if True）
# ════════════════════════════════════════════════════════
if False and tab2 is not None:
 with tab2:

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ── 整体进度 KPI ─────────────────────────────────────
    st.markdown("""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">整体完成度</div>
        <div class="kpi-value" style="color:#4CAF50;">50%</div>
        <div class="kpi-sub">角色开发阶段</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">角色已建档</div>
        <div class="kpi-value" style="color:#FFB300;">5 / 5</div>
        <div class="kpi-sub">林浅浅・Céline・胡芊璐・顾染・倪妮</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">社群已开设</div>
        <div class="kpi-value" style="color:#E879A0;">3 / 5</div>
        <div class="kpi-sub">林浅浅・Céline・胡芊璐</div>
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
        dict(Task="角色档案建立（5位）", Start="2026-03-01", Finish="2026-03-31", Stage="Phase 1 角色资产", Status="已完成"),
        dict(Task="面部锚点确认", Start="2026-03-10", Finish="2026-03-31", Stage="Phase 1 角色资产", Status="已完成"),
        dict(Task="底图生成（倪妮完成）", Start="2026-03-15", Finish="2026-03-31", Stage="Phase 1 角色资产", Status="已完成"),
        dict(Task="商标申请（陆+台）", Start="2026-03-15", Finish="2026-04-30", Stage="Phase 1 角色资产", Status="待确认"),
        dict(Task="第一次角色资产会议", Start="2026-03-11", Finish="2026-03-12", Stage="Phase 1 角色资产", Status="已完成"),
        dict(Task="IG 自动化工作流建立", Start="2026-03-10", Finish="2026-03-18", Stage="Phase 2 AI生产", Status="已完成"),
        dict(Task="首批概念图生成（各角色×20张）", Start="2026-03-19", Finish="2026-04-10", Stage="Phase 2 AI生产", Status="进行中"),
        dict(Task="AI 爆款内容提报", Start="2026-03-31", Finish="2026-04-05", Stage="Phase 2 AI生产", Status="进行中"),
        dict(Task="林浅浅 IG 持续运营（破万）", Start="2026-03-01", Finish="2026-04-30", Stage="Phase 3 社群布局", Status="进行中"),
        dict(Task="Céline @celine_iso 首批内容", Start="2026-03-20", Finish="2026-03-31", Stage="Phase 3 社群布局", Status="已完成"),
        dict(Task="胡芊璐 @hu_maturemommy 首批内容", Start="2026-03-20", Finish="2026-03-31", Stage="Phase 3 社群布局", Status="已完成"),
        dict(Task="顾染社群帐号开设", Start="2026-04-01", Finish="2026-04-07", Stage="Phase 3 社群布局", Status="待确认"),
        dict(Task="倪妮社群帐号开设", Start="2026-04-01", Finish="2026-04-07", Stage="Phase 3 社群布局", Status="待确认"),
        dict(Task="黄版全平台开设（林浅浅）", Start="2026-03-16", Finish="2026-03-31", Stage="Phase 4 量化", Status="已完成"),
        dict(Task="IG 自动爬虫接入 Dashboard", Start="2026-04-01", Finish="2026-04-20", Stage="Phase 4 量化", Status="待开始"),
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
            "商标申请策略确认（陆+台）",
            "顾染社群帐号开设",
            "倪妮社群帐号开设",
        ],
        "🟡 进行中": [
            "林浅浅 IG 内容持续发布（破万🎉）",
            "Céline IG 新帐号 @celine_iso 经营",
            "胡芊璐 IG @hu_maturemommy 内容建立",
            "3/31 AI 爆款内容提报",
            "首批概念图生成（各角色×20张）",
        ],
        "🔵 待开始": [
            "顾染社群帐号开设",
            "倪妮社群帐号开设",
            "IG 自动爬虫接入 Dashboard",
        ],
        "✅ 已完成": [
            "四大角色 IP 方向确定",
            "角色档案建立（5位）",
            "KPI 评分表建立",
            "周报自动化系统 v3",
            "IG 自动化工作流建立",
            "AI 内容 IP 商业计划书（13页）",
            "第一次角色资产会议 3/11",
            "智影AI角色库 Dashboard 建置",
            "黄版流程开拓完成 3/23",
            "林浅浅黄版全平台开设完成",
            "林浅浅 IG 破万 3/31",
            "胡芊璐 IG 帐号开设 @hu_maturemommy",
            "王芷涵 IG 新帐号 @celine_iso（原帐被ban）",
            "王芷涵首批内容上线",
            "胡芊璐首批内容上线",
            "倪妮面部锚点 & 底图完成",
            "Dashboard 社群数据页签上线",
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
        {"角色": "林浅浅",  "档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "✅", "首批内容": "✅", "等级": "S"},
        {"角色": "王芷涵",  "档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "✅", "首批内容": "✅", "等级": "S"},
        {"角色": "胡芊璐",  "档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "✅", "首批内容": "✅", "等级": "S"},
        {"角色": "顾染",    "档案建立": "✅", "面部锚点": "✅", "底图生成": "⏳", "社群开设": "⏳", "首批内容": "⏳", "等级": "S"},
        {"角色": "倪妮",    "档案建立": "✅", "面部锚点": "✅", "底图生成": "✅", "社群开设": "⏳", "首批内容": "⏳", "等级": "S"},
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

    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>智影AI角色库 · 专案进度追踪</div>", unsafe_allow_html=True)


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
            "ig": "@lqq.u_u",
            "ig_url": "https://www.instagram.com/lqq.u_u/",
            "color": "#FFB300",
            "status": "active",
            "followers": 62000,
            "following": 0,
            "posts": 0,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "新帐号 @lqq.u_u，2026-04-23 重新开始，快速破 6.2 万",
            "updated": "2026-04-23",
            "platforms": [
                ("📸 IG",      "https://www.instagram.com/lqq.u_u/"),
                ("🧵 Threads", "https://www.threads.com/@qianqian.hanfu"),
                ("🎵 TikTok",  "https://www.tiktok.com/@qianqian.hanfu"),
                ("▶️ YouTube", "https://www.youtube.com/@qianqian_hanfu"),
                ("🔗 Linktree","https://linktr.ee/qianqian_hanfu"),
                ("🔞 FansOne", "https://fansone.co/lazypiggy520"),
                ("🔞 Patreon", "https://www.patreon.com/cw/qianqian_haofu"),
            ],
        },
        {
            "name": "王芷涵",
            "en_name": "Céline Wang",
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
            "note": "全新帐号，旧帐 @celine_iso 已弃用",
            "updated": "2026-04-09",
            "platforms": [
                ("📸 IG",      "https://www.instagram.com/celine.w_iso/"),
                ("🧵 Threads", "https://www.threads.com/@celine_iso"),
                ("🐦 X",       "https://x.com/celineparisasia"),
                ("🔗 Linktree","https://linktr.ee/celineiso"),
                ("🔞 FansOne", "https://fansone.co/candykissvip520"),
                ("🔞 Patreon", "https://www.patreon.com/cw/CelineLin"),
            ],
        },
        {
            "name": "胡芊璐",
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
            "note": "IG 稳定成长中",
            "updated": "2026-04-13",
            "posts": 2,
            "following": 2,
            "platforms": [
                ("📸 IG",     "https://www.instagram.com/hu_maturemommy/"),
                ("🎵 TikTok", "https://www.tiktok.com/@hu_maturemommy"),
            ],
        },
        {
            "name": "顾染",
            "en_name": "Gu Ran",
            "ig": "@good_ran__",
            "ig_url": "https://www.instagram.com/good_ran__/",
            "color": "#E879A0",
            "status": "new",
            "followers": 168,
            "following": 25,
            "posts": 13,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "新帐号，韩系冷艳路线",
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
            "color": "#4CAF50",
            "status": "new",
            "followers": 896,
            "following": 12,
            "posts": 5,
            "avg_likes": None,
            "avg_comments": None,
            "last_post": None,
            "note": "新帐号，运动系活力风格",
            "updated": "2026-04-23",
            "platforms": [
                ("📸 IG", "https://www.instagram.com/nini_power99/"),
            ],
        },
    ]

    STATUS_LABEL = {
        "active":  ("✅ 活跃", "#4CAF50"),
        "new":     ("🆕 新帐号", "#7C6BDB"),
        "pending": ("⏳ 待建立", "#555"),
    }

    # ── KPI 卡片 ─────────────────────────────────────────
    total_followers = sum(d["followers"] for d in IG_DATA if d["followers"])
    active_names = "・".join(d["name"] for d in IG_DATA if d["status"] in ("active", "new"))
    active_count = sum(1 for d in IG_DATA if d["status"] in ("active", "new"))
    pending_names = "・".join(d["name"] for d in IG_DATA if d["status"] == "pending")
    pending_count = sum(1 for d in IG_DATA if d["status"] == "pending")

    st.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-label">总追踪人数</div>
        <div class="kpi-value" style="color:#E879A0;">{total_followers:,}</div>
        <div class="kpi-sub">所有角色合计</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">已开设帐号</div>
        <div class="kpi-value" style="color:#FFB300;">{active_count} / 5</div>
        <div class="kpi-sub">{active_names}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">待建立帐号</div>
        <div class="kpi-value" style="color:#555;">{pending_count} / 5</div>
        <div class="kpi-sub">{pending_names}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">数据更新方式</div>
        <div class="kpi-value" style="font-size:18px;color:#444;">手动</div>
        <div class="kpi-sub">爬虫接入后自动更新</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 各角色明细卡片 ────────────────────────────────────
    st.markdown("### 👤 各角色社群明细")

    def fmt_metric(val):
        return f"{val:,}" if val is not None else "—"

    for d in IG_DATA:
        status_text, status_color = STATUS_LABEL[d["status"]]
        ig_link = (f'<a href="{d["ig_url"]}" target="_blank" style="color:#888;font-size:12px;">'
                   f'{d["ig"]} ↗</a>') if d["ig"] else '<span style="color:#444;font-size:12px;">—</span>'
        followers_str = f'{d["followers"]:,}' if d["followers"] is not None else "—"
        updated_str = d["updated"] or "—"

        # 平台连结（放在卡片上方）
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
              <span style="font-size:11px;color:#444;">更新：{updated_str}</span>
            </div>
          </div>
          <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">追踪数</div>
              <div style="font-size:22px;font-weight:700;color:{d['color']};">{followers_str}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">追踪中</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['following'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">贴文数</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['posts'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">平均赞数</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['avg_likes'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">平均留言</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{fmt_metric(d['avg_comments'])}</div></div>
            <div><div style="font-size:11px;color:#666;margin-bottom:2px;">最后贴文</div>
              <div style="font-size:22px;font-weight:700;color:#aaa;">{d['last_post'] or '—'}</div></div>
          </div>
          {f'<div style="margin-top:10px;font-size:12px;color:#555;">备注：{d["note"]}</div>' if d["note"] else ""}
        </div>
        """, unsafe_allow_html=True)

        if d.get("highlights"):
            import streamlit.components.v1 as components
            items_html = ""
            for h in d["highlights"]:
                likes_str = f'{h["likes"] // 10000}万+' if h["likes"] >= 10000 else str(h["likes"])
                views_str = f'{h["views"] // 10000}万+' if h["views"] >= 10000 else str(h["views"])
                content_html = h["content"].replace("\n", "<br>")
                items_html += (
                    '<div style="background:#1a1a1a;border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
                    '<div style="flex:1;">'
                    f'<div style="font-size:11px;color:#666;margin-bottom:4px;">{h["date"]}</div>'
                    f'<div style="font-size:12px;color:#aaa;line-height:1.5;">{content_html}</div>'
                    '</div>'
                    '<div style="display:flex;gap:16px;flex-shrink:0;margin-left:12px;">'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">❤️ 赞</div><div style="font-size:15px;font-weight:700;color:#E879A0;">{likes_str}</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">💬 留言</div><div style="font-size:15px;font-weight:700;color:#aaa;">{h["comments"]}</div></div>'
                    f'<div style="text-align:center;"><div style="font-size:11px;color:#666;">▶️ 观看</div><div style="font-size:15px;font-weight:700;color:#FFB300;">{views_str}</div></div>'
                    '</div></div></div>'
                )
            highlight_html = (
                f'<div style="font-family:sans-serif;background:#242424;border:1px solid #3a3a3a;border-radius:10px;'
                f'padding:16px 20px;margin-bottom:8px;border-left:3px solid {d["color"]};">'
                '<div style="font-size:11px;color:#E879A0;font-weight:600;margin-bottom:10px;">🔥 亮点贴文</div>'
                + items_html +
                '</div>'
            )
            components.html(highlight_html, height=len(d["highlights"]) * 100 + 60, scrolling=False)


    st.markdown("<br><div style='text-align:center;color:#444;font-size:12px;'>智影AI角色库 · 社群数据监控</div>", unsafe_allow_html=True)


with tab4:
    st.markdown("## \U0001f39b\ufe0f 角色进度总控台")
    st.caption("资料来源：Google Sheets 自动同步")

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
        # Worksheet 名稱兼容繁簡：先試簡體，找不到再試繁體
        try:
            ws = sheet.worksheet("\U0001f39b\ufe0f 总控台")
        except Exception:
            ws = sheet.worksheet("\U0001f39b\ufe0f 總控台")

        all_data = ws.get_all_values()

        # 用栏位索引 (A=0, B=1, ... N=13)
        # A:序号 B:角色名 C:建立者 D:建立日期 E:捏人公司 F:捏人状态
        # G:捏人完成日 H:Mr.B初审 I:初审日期 J:海哥审核 K:海哥审核日期
        # L:目前状态 M:入库日期 N:备注
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

        # 找表头行和提领区
        header_row_idx = None
        req_start_idx = None
        for i, row in enumerate(all_data):
            if len(row) > 1 and row[0].strip() == "序号" and header_row_idx is None:
                header_row_idx = i
            if len(row) > 0 and "提领" in str(row[0]):
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
                in_stock = sum(1 for r in char_rows if "已入库" in str(r[COL_STATUS]))
                in_review = sum(1 for r in char_rows if "待海哥审" in str(r[COL_STATUS]))
                in_making = sum(1 for r in char_rows if "捏人中" in str(r[COL_STATUS]))
                need_fix = sum(1 for r in char_rows if "驳回" in str(r[COL_STATUS]) or "需修改" in str(r[COL_STATUS]))

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("总角色数", total)
                c2.metric("已入库", in_stock)
                c3.metric("待海哥审", in_review)
                c4.metric("捏人中", in_making)
                c5.metric("需修改", need_fix)

                st.markdown("---")
                st.markdown("### 海哥审核专区")

                # 标记为 dev_phase 的角色不出现在海哥审核区（即使 sheet 状态是「待海哥审」）
                from characters import CHARACTERS as _ALL_CHARS_FOR_FILTER
                _dev_names = {
                    n
                    for c in _ALL_CHARS_FOR_FILTER
                    if c.get("dev_phase")
                    for n in [c["name"]] + _NAME_ALIASES.get(c["name"], [])
                }
                pending = [
                    r for r in char_rows
                    if "待海哥审" in str(r[COL_STATUS])
                    if r[COL_NAME].strip() not in _dev_names
                ]

                if not pending:
                    st.success("目前没有待审核的角色")
                else:
                    boss_pwd = st.text_input("请输入审核密码", type="password", key="boss_pwd")

                    if boss_pwd == "haige888":
                        st.success("身份验证成功")

                        for row in pending:
                            name = row[COL_NAME].strip()
                            creator = row[COL_CREATOR] if len(row) > COL_CREATOR else ""
                            mrb = row[COL_MRB_REVIEW] if len(row) > COL_MRB_REVIEW else ""
                            note = row[COL_NOTE] if len(row) > COL_NOTE else ""

                            with st.expander(f"{name} — 待审核", expanded=True):
                                st.write(f"**建立者：** {creator}")
                                st.write(f"**初审结果：** {mrb}")
                                if note:
                                    st.write(f"**备注：** {note}")

                                b1, b2, b3 = st.columns(3)
                                approve = b1.button("✅ 通过", key=f"ap_{name}")
                                reject = b2.button("驳回", key=f"rj_{name}")
                                adjust = b3.button("需调整", key=f"ad_{name}")

                                if approve or reject or adjust:
                                    all_vals = ws.get_all_values()
                                    for si, sr in enumerate(all_vals):
                                        if len(sr) > COL_NAME and sr[COL_NAME].strip() == name:
                                            actual_row = si + 1
                                            today = datetime.now().strftime("%Y-%m-%d")

                                            if approve:
                                                ws.update_cell(actual_row, COL_BOSS_REVIEW + 1, "✅ 通过")
                                                ws.update_cell(actual_row, COL_BOSS_DATE + 1, today)
                                                ws.update_cell(actual_row, COL_STATUS + 1, "🟢 已入库")
                                                ws.update_cell(actual_row, COL_STOCK_DATE + 1, today)
                                                st.success(f"{name} 已通过审核！")
                                            elif reject:
                                                ws.update_cell(actual_row, COL_BOSS_REVIEW + 1, "🔴 驳回")
                                                ws.update_cell(actual_row, COL_BOSS_DATE + 1, today)
                                                ws.update_cell(actual_row, COL_STATUS + 1, "🔴 海哥驳回")
                                                st.error(f"{name} 已驳回")
                                            elif adjust:
                                                ws.update_cell(actual_row, COL_BOSS_REVIEW + 1, "⚠️ 需调整")
                                                ws.update_cell(actual_row, COL_BOSS_DATE + 1, today)
                                                ws.update_cell(actual_row, COL_STATUS + 1, "🟠 初审需修改")
                                                st.warning(f"{name} 需调整")

                                            st.cache_resource.clear()
                                            st.rerun()
                                            break
                    elif boss_pwd:
                        st.error("密码错误")

                st.markdown("---")
                st.markdown("### 角色状态一览")

                status_colors = {
                    "已入库": "#2ecc71",
                    "待海哥审": "#9b59b6",
                    "捏人中": "#f39c12",
                    "待初审": "#3498db",
                    "驳回": "#e74c3c",
                    "需修改": "#e67e22",
                    "建立中": "#95a5a6",
                    "已下架": "#2c3e50",
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
            else:
                st.info("目前没有角色资料")
        else:
            st.warning("找不到总控台表头，请确认 Google Sheets 格式")

    except Exception as e:
        st.error(f"无法连接 Google Sheets：{str(e)}")
        st.info("请确认：\n1. 已在 Streamlit Secrets 设定 GCP 服务帐号金钥\n2. Google Sheets 已分享给服务帐号\n3. 总控台分页已建立")

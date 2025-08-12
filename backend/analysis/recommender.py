# -*- coding: utf-8 -*-
"""
回答（強み/興味）から業界・職種を推定し、気づきにつながる説明を返すルールベース版。
- 日本語の表記ゆれを正規化
- 強み(現時点)と興味(将来軸)で重みを変える
- キーワードだけでなく「動機・価値観テーマ」を推定して説明を補強
- 掛け算提案 / 隣接フィールド / 最初の一歩 / 内省の問い を生成
"""

from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

# --------- 基本ユーティリティ ----------

def normalize(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"\s+", " ", t)
    return t

def rx(expr: str) -> re.Pattern:
    return re.compile(expr)

# --------- カテゴリ定義（業界） ----------

@dataclass
class Category:
    name: str
    patterns: List[re.Pattern]
    roles: List[str]
    typical_tasks: List[str]
    values_fit: List[str]

CATS: Dict[str, Category] = {}

def add_cat(cat: Category): CATS[cat.name] = cat

add_cat(Category(
    name="IT・ソフトウェア",
    patterns=[
        rx(r"it|ai|api|sql|web|db|データ|アプリ|システム|機械学習|可視化|ノーコード|内製化"),
        rx(r"python|java(script)?|gas|vba|プログラミング|コード|スクリプト|自動化|効率化|業務改善")
    ],
    roles=["業務改善・内製化推進","カスタマーサクセス（SaaS）","データアナリスト入門","Webエンジニア見習い"],
    typical_tasks=["要件ヒアリング","業務の自動化設計","ダッシュボード作成","運用改善"],
    values_fit=["論理性","改善志向","学習継続"]
))
add_cat(Category(
    name="教育・研修",
    patterns=[
        rx(r"教え|指導|育成|研修|講師|授業|ファシリテーション|伴走|学習会"),
        rx(r"キャリア(支援|相談)|面談|ワークショップ|教材|解説|わかりやす(く|い)|かみ砕")
    ],
    roles=["研修企画・運営","講師アシスタント","キャリア支援コーディネーター"],
    typical_tasks=["研修設計","教材作成","学習支援","進行/ファシリテート"],
    values_fit=["人の成長への関心","共感性","説明力"]
))
add_cat(Category(
    name="福祉・NPO・公的支援",
    patterns=[ rx(r"支援|相談|伴走|居場所|孤立|就労支援|地域|コミュニティ|npo|社会課題|行政") ],
    roles=["就労支援スタッフ","地域/コミュニティ運営","コーディネーター"],
    typical_tasks=["相談対応","関係機関連携","記録/報告","イベント運営"],
    values_fit=["公共性","傾聴","公平性"]
))
add_cat(Category(
    name="販売・サービス",
    patterns=[ rx(r"接客|販売|店舗|来客|受付|レジ|ホスピタリティ|お客様|電話対応|案内|調整|カフェ|飲食|ホテル|観光") ],
    roles=["カスタマーサポート","店舗運営（SV候補）","インサイドセールス"],
    typical_tasks=["顧客対応","問い合わせ対応","売場/在庫管理","オペレーション改善"],
    values_fit=["サービス精神","チームワーク","臨機応変"]
))
add_cat(Category(
    name="バックオフィス",
    patterns=[ rx(r"総務|庶務|備品|稟議|社内|手続|調達|契約"),
               rx(r"人事|採用|研修|評価|労務|勤怠|給与"),
               rx(r"経理|会計|請求|伝票|仕訳|月次|固定資産|予実") ],
    roles=["総務アシスタント","人事アシスタント","経理アシスタント"],
    typical_tasks=["文書/備品管理","勤怠/給与補助","請求/支払処理"],
    values_fit=["正確性","継続性","安心/安定"]
))
add_cat(Category(
    name="製造・ものづくり",
    patterns=[ rx(r"ものづくり|製造|加工|設備|現場|工場|試作|図面"),
               rx(r"品質|検査|工程|安全|5s|カイゼン|改善|段取り") ],
    roles=["品質管理/検査","生産管理アシスタント","製造オペレーター"],
    typical_tasks=["検査/測定","工程管理","安全衛生","改善提案"],
    values_fit=["着実さ","安全意識","観察力"]
))
add_cat(Category(
    name="クリエイティブ",
    patterns=[ rx(r"デザイン|イラスト|動画|写真|編集|撮影|コピー|ブランド|ディレクション|figma|canva") ],
    roles=["コンテンツ制作アシスタント","広報/SNS運用","デザイナー見習い"],
    typical_tasks=["素材作成","編集/校正","SNS運用","企画/構成"],
    values_fit=["審美性","表現","ユーザー視点"]
))

# --------- 動機・価値観テーマ ----------

@dataclass
class Theme:
    key: str
    patterns: List[re.Pattern]
    description: str
    suited_styles: List[str]      # 働き方の相性
    reflection: List[str]         # 内省の問い

THEMES: Dict[str, Theme] = {}

def add_theme(t: Theme): THEMES[t.key] = t

add_theme(Theme(
    key="改善・探究",
    patterns=[ rx(r"改善|効率|最適化|仕組|設計|分析|検証|試行|学習|探究|研究|自動化") ],
    description="問題を分解し、より良くすることに喜びを感じる傾向。",
    suited_styles=["課題解決型の業務","継続的改善の役割","裁量がある環境"],
    reflection=["どんな課題を解くと没頭できるか","成果を測る指標は何か"]
))
add_theme(Theme(
    key="支援・共感",
    patterns=[ rx(r"支援|相談|伴走|寄り添|傾聴|共感|コーチング|面談|サポート") ],
    description="人の成長や安心を支えることにやりがいを感じる傾向。",
    suited_styles=["対人支援","少人数の深い関わり","フィードバックがある環境"],
    reflection=["誰のどんな変化を支えたいか","境界線をどう守るか"]
))
add_theme(Theme(
    key="公共・社会貢献",
    patterns=[ rx(r"地域|コミュニティ|社会課題|公共|行政|公平|安心|孤立|居場所") ],
    description="社会的な意義や公平さを重視する傾向。",
    suited_styles=["公共性の高いプロジェクト","規範の明確な環境"],
    reflection=["自分にとっての『公益』とは何か","時間軸は短期/中長期どちらか"]
))
add_theme(Theme(
    key="表現・創造",
    patterns=[ rx(r"表現|創作|企画|構成|デザイン|編集|発信|魅せる|ストーリー") ],
    description="ゼロから形にし、伝わる形に磨くことに喜びを感じる傾向。",
    suited_styles=["コンテンツ制作","編集/広報","ユーザー体験設計"],
    reflection=["誰に何をどんなトーンで届けたいか","仕上げにこだわるポイントは何か"]
))
add_theme(Theme(
    key="堅実・正確",
    patterns=[ rx(r"正確|丁寧|期日|手順|ルール|品質|記録|安全|チェック|安定") ],
    description="正確さや継続性で価値を出す傾向。",
    suited_styles=["定型+改善のバランス","チェック体制のある環境"],
    reflection=["正確さを活かす場面はどこか","変化への耐性とその条件は何か"]
))
add_theme(Theme(
    key="対人フロント",
    patterns=[ rx(r"接客|顧客|お客様|提案|調整|折衝|関係構築|コミュニケーション|受付|窓口") ],
    description="人と直接関わり、期待を超えることを楽しめる傾向。",
    suited_styles=["顧客接点","CS/セールス/運営","チーム連携が密な場"],
    reflection=["嬉しかった顧客の反応は何か","疲れない関わり方の上限はどこか"]
))

# テーマ→業界の影響度（重み）
THEME_TO_INDUSTRY_WEIGHT: Dict[str, Dict[str, float]] = {
    "改善・探究": {"IT・ソフトウェア": 2.0, "製造・ものづくり": 1.2, "バックオフィス": 0.8},
    "支援・共感": {"教育・研修": 1.8, "福祉・NPO・公的支援": 1.6, "販売・サービス": 0.8},
    "公共・社会貢献": {"福祉・NPO・公的支援": 1.8, "教育・研修": 1.0},
    "表現・創造": {"クリエイティブ": 2.0, "教育・研修": 0.8, "IT・ソフトウェア": 0.6},
    "堅実・正確": {"バックオフィス": 1.8, "製造・ものづくり": 1.2},
    "対人フロント": {"販売・サービス": 1.8, "カスタマーサクセス": 1.2},
}

# 隣接フィールド（学びやすい近接領域）
ADJACENT: Dict[str, List[str]] = {
    "IT・ソフトウェア": ["CS/サクセス", "業務改革（BPR）", "データ可視化"],
    "教育・研修": ["人材開発/オンボーディング", "教材制作", "ラーニングデザイン"],
    "福祉・NPO・公的支援": ["地域連携", "行政委託事業運営", "コミュニティ拠点運営"],
    "販売・サービス": ["インサイドセールス", "CS改善", "店舗オペ改善"],
    "バックオフィス": ["人事/労務", "経理補助", "総務/情シス連携"],
    "製造・ものづくり": ["品質保証", "生産技術補助", "物流改善"],
    "クリエイティブ": ["広報/PR", "コンテンツ編集", "ブランド運用"],
}

FIRST_STEPS: Dict[str, List[str]] = {
    "IT・ソフトウェア": ["日常業務を1つ自動化（例:GASでテンプレ化）","業務要件→処理手順の文章化","可視化ダッシュボードの試作"],
    "教育・研修": ["10分のミニ勉強会を企画","教材テンプレを1枚作る","学習目標→評価指標の整理"],
    "福祉・NPO・公的支援": ["支援記録の型を作る","地域資源マップ化","関係者ミーティングの議事テンプレ作成"],
    "販売・サービス": ["よくある問合せFAQを作成","ピーク時動線の見直し","応対スクリプトの改善案"],
    "バックオフィス": ["請求/申請のチェックリスト化","月次ルーチンの標準化","RPA/スクリプトの小実験"],
    "製造・ものづくり": ["5Sチェック表の作成","不良の見える化","作業手順の写真付き標準化"],
    "クリエイティブ": ["1枚図解テンプレ作成","過去実績のミニポートフォリオ","SNSでの継続発信プラン"],
}

WEIGHT_STRENGTH = 1.2
WEIGHT_INTEREST = 1.5
THEME_INFLUENCE = 0.35  # テーマが最終スコアに乗る比率

def _score_patterns(pats: List[re.Pattern], text: str) -> Tuple[int, List[str]]:
    hits, ev = 0, []
    for p in pats:
        for m in p.findall(text):
            hits += 1
            ev.append(m)
    # 代表語だけ残す（重複削除）
    ev = list(dict.fromkeys(ev))
    return hits, ev

def analyze_text(q1: str, q2: str) -> Dict:
    s_text, i_text = normalize(q1), normalize(q2)

    # 1) カテゴリ（業界）スコア
    cat_scores: Dict[str, float] = {}
    cat_ev: Dict[str, List[str]] = {}
    details: Dict[str, Dict] = {}

    for name, cat in CATS.items():
        s_hit, s_ev = _score_patterns(cat.patterns, s_text)
        i_hit, i_ev = _score_patterns(cat.patterns, i_text)
        base = s_hit * WEIGHT_STRENGTH + i_hit * WEIGHT_INTEREST
        if base > 0:
            cat_scores[name] = base
            cat_ev[name] = list(dict.fromkeys(s_ev + i_ev))
            details[name] = {
                "strength_hits": s_hit, "interest_hits": i_hit,
                "strength_evidence": s_ev, "interest_evidence": i_ev,
                "base_score": base
            }

    # 2) テーマ推定
    theme_scores: Dict[str, float] = {}
    theme_ev: Dict[str, List[str]] = {}
    for key, theme in THEMES.items():
        s_hit, s_ev = _score_patterns(theme.patterns, s_text)
        i_hit, i_ev = _score_patterns(theme.patterns, i_text)
        score = s_hit * WEIGHT_STRENGTH + i_hit * WEIGHT_INTEREST
        if score > 0:
            theme_scores[key] = score
            theme_ev[key] = list(dict.fromkeys(s_ev + i_ev))

    # 3) テーマで業界スコアを補正
    if theme_scores:
        t_total = sum(theme_scores.values())
        for t_key, t_score in theme_scores.items():
            influence = (t_score / t_total) * THEME_INFLUENCE
            for ind, w in THEME_TO_INDUSTRY_WEIGHT.get(t_key, {}).items():
                cat_scores[ind] = cat_scores.get(ind, 0.0) + influence * w

    # スコア順
    ranked = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)
    if not ranked:  # 何もヒットしないときの安全網
        ranked = [("販売・サービス", 0.1)]
        cat_ev.setdefault("販売・サービス", [])

    # 4) 掛け算の提案
    combos = []
    names = [n for n,_ in ranked[:3]]
    if "IT・ソフトウェア" in names and "教育・研修" in names:
        combos.append({"label":"IT × 教育",
                       "roles":["社内ITトレーナー","デジタル推進の研修企画"],
                       "why":"改善・探究と支援・共感の両テーマが見られ、学習支援×業務改善の適性が示唆されます。"})
    if "IT・ソフトウェア" in names and "福祉・NPO・公的支援" in names:
        combos.append({"label":"ソーシャル × テック",
                       "roles":["支援現場のデータ/記録整備","業務の内製化支援"],
                       "why":"公共/支援語とIT語が併存し、現場の効率化に寄与できる可能性があります。"})
    if "クリエイティブ" in names and "教育・研修" in names:
        combos.append({"label":"教材制作 × 研修",
                       "roles":["教材/スライド制作","LMSコンテンツ運用"],
                       "why":"表現・創造の強みが学習支援に接続します。"})

    # 5) 推薦（上位2）
    recs = []
    for name, _ in ranked[:2]:
        cat = CATS[name]
        kws = cat_ev.get(name, [])[:8]
        themes_sorted = sorted(theme_scores.items(), key=lambda x:x[1], reverse=True)
        dom_themes = [t for t,_ in themes_sorted[:2]] if themes_sorted else []
        reason = build_reason(name, kws, dom_themes)
        recs.append({
            "industry": name,
            "roles": cat.roles[:3],
            "reason": reason,
            "evidence_keywords": kws,
            "typical_tasks": cat.typical_tasks[:3],
            "fit_values": cat.values_fit,
            "adjacent_fields": ADJACENT.get(name, [])[:3],
            "first_steps": FIRST_STEPS.get(name, [])[:3],
        })

    # 6) サマリー（気づきを促す）
    summary = build_summary(theme_scores, theme_ev)

    return {
        "summary": summary,
        "recommendations": recs,
        "combination_suggestions": combos,
        "raw_score": ranked,
        "details": {
            "categories": details,
            "themes": theme_scores
        }
    }

# --------- 説明生成 ---------

def build_reason(industry: str, kws: List[str], dom_themes: List[str]) -> str:
    parts = [f"{industry}を候補に挙げます。"]
    if kws:
        parts.append(f"回答に「{('、'.join(kws[:5]))}」といった語があり、仕事内容との接点が見られます。")
    if dom_themes:
        parts.append(f"特に「{('・'.join(dom_themes))}」の傾向が強く、活躍の土台になりやすいと考えられます。")
    return " ".join(parts)

def build_summary(theme_scores: Dict[str,float], theme_ev: Dict[str, List[str]]) -> Dict:
    if not theme_scores:
        return {
            "dominant_themes": [],
            "work_style": "文章量が少ないか、テーマの傾向が未検出でした。もう少し具体例を追加してください。",
            "reflection_questions": ["最近うまくいった/楽しかった活動は？ その中で何をしていたか。","これから伸ばしたい場面は？ 学び方は？"]
        }
    ts = sorted(theme_scores.items(), key=lambda x:x[1], reverse=True)
    top = [t for t,_ in ts[:2]]
    style = []
    rq = []
    for t in top:
        style.extend(THEMES[t].suited_styles[:2])
        rq.extend(THEMES[t].reflection[:1])
    return {
        "dominant_themes": top,
        "work_style": " / ".join(dict.fromkeys(style)),
        "reflection_questions": rq,
        "evidence": {k: theme_ev.get(k, []) for k in top}
    }

import streamlit as st
import anthropic

# ─── ページ設定 ───────────────────────────────────────────
st.set_page_config(page_title="カルテ変換ツール 🃏", page_icon="🃏", layout="centered")

# ─── パスワード認証 ───────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("🃏 カルテ変換ツール")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン", type="primary"):
        if pw == st.secrets.get("APP_PASSWORD", ""):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

if not check_password():
    st.stop()

st.title("🃏 カルテ変換ツール")
st.caption("NottaAIの要約をペーストして、カンペ形式に変換します")

# ─── システムプロンプト：カルテ ───────────────────────────
KARTE_PROMPT = """あなたは電話占い師のアシスタントです。
鑑定音声の文字起こし要約を受け取り、次回リピート時にひと目で読み返せる「カルテメモ（カンペ）」として整理してください。

【出力ルール】
- タイムスタンプ（00:00:00形式）はすべて除去する
- 情報は省略せず、元の内容をできるだけ保持する
- 体言止め・簡潔な文体に整える。話し言葉は書き言葉に直す
- そのままコピペして使えるプレーンテキストで出力する
- マークダウン記法（#・##・###・**・---・- など）は一切使わない
- 見出しは【】、小見出しは■、箇条書きは・を使う
- 出力全体は900文字以内に収める

【構成の目安】
【ご相談内容】
・相談テーマを箇条書き

【鑑定の核心】
■テーマ名
・占いで見えた事実・相性・時期を箇条書き
→ 重要ポイントにひとこと補足

【アドバイス】
・相談者への行動指針・心がけを箇条書き

【キーワード】
・重要な人物名・時期・固有名詞をコンパクトに

【次回フォロー】
・次回確認・引き継ぎ事項を箇条書き

構成はあくまで目安。内容に応じて項目を増減・統合してよい。
読んだ瞬間に鑑定の流れが思い出せるカンペを目指すこと。"""

# ─── システムプロンプト：フォローメール ─────────────────
MAIL_PROMPT = """あなたは電話占い師「おだんごめがね」のアシスタントです。
鑑定音声の文字起こし要約を受け取り、鑑定後にお客様へ送るフォローメールを仕上げてください。

【最優先ルール】
- 要約の末尾に「お客様へのフォローメールドラフト」がある場合は、それをベースとして使う
- ドラフトの文章・構成・トーンをできるだけ活かし、必要な修正のみ加える
- ドラフトがない場合は下記の構成で一から作成する

【修正・調整の方針】
- タイムスタンプは除去する
- 文体はですます調・温かみと親しみやすさのある雰囲気を維持
- 不自然な言い回しや冗長な部分があれば整える程度にとどめる
- 内容の追加・削除は最小限に

【ドラフトがない場合の構成】
1. 書き出し：鑑定のお礼と労い
2. 本文：鑑定の核心を1〜2段落でやさしくまとめる（箇条書きは使わない）
3. 締め：励ましの言葉＋また相談できることを伝える

【共通ルール】
- マークダウン記法は使わない
- 署名は「おだんごめがね」で統一
- 全体で300〜500文字程度"""

# ─── 入力エリア ───────────────────────────────────────────
input_text = st.text_area(
    "NottaAI 要約テキスト",
    height=200,
    placeholder="NottaAIの要約をここにペーストしてください…",
)

col1, col2 = st.columns([1, 5])
with col1:
    convert = st.button("変換する", type="primary", use_container_width=True)

# ─── 変換処理 ─────────────────────────────────────────────
if convert:
    if not input_text.strip():
        st.warning("テキストをペーストしてください")
    else:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

        # カルテ生成
        with st.spinner("カルテを生成中…"):
            try:
                karte_msg = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=2048,
                    system=KARTE_PROMPT,
                    messages=[{"role": "user", "content": input_text}],
                )
                karte_result = karte_msg.content[0].text.strip()
            except Exception as e:
                st.error(f"カルテ生成エラー: {e}")
                st.stop()

        # フォローメール生成
        with st.spinner("フォローメールを生成中…"):
            try:
                mail_msg = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=1024,
                    system=MAIL_PROMPT,
                    messages=[{"role": "user", "content": input_text}],
                )
                mail_result = mail_msg.content[0].text.strip()
            except Exception as e:
                st.error(f"メール生成エラー: {e}")
                st.stop()

        # ─── カルテ表示 ───────────────────────────────────
        st.divider()
        st.subheader("📋 カルテメモ")
        char_count = len(karte_result)
        color = "red" if char_count > 900 else "gray"
        st.markdown(
            f"<p style='color:{color}; font-size:13px; text-align:right;'>{char_count} 文字</p>",
            unsafe_allow_html=True,
        )
        st.text_area("", value=karte_result, height=400, key="karte_area")

        # ─── フォローメール表示 ───────────────────────────
        st.divider()
        st.subheader("✉️ フォローメール")
        mail_count = len(mail_result)
        st.markdown(
            f"<p style='color:gray; font-size:13px; text-align:right;'>{mail_count} 文字</p>",
            unsafe_allow_html=True,
        )
        st.text_area("", value=mail_result, height=300, key="mail_area")

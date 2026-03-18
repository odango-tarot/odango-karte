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

# ─── システムプロンプト ────────────────────────────────────
SYSTEM_PROMPT = """あなたは電話占い師のアシスタントです。
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
        with st.spinner("変換中…"):
            try:
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                message = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=2048,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": input_text}],
                )
                result = message.content[0].text.strip()

                # 文字数カウント
                char_count = len(result)
                color = "red" if char_count > 900 else "gray"
                st.divider()
                st.subheader("カルテメモ")
                st.markdown(
                    f"<p style='color:{color}; font-size:13px; text-align:right;'>{char_count} 文字</p>",
                    unsafe_allow_html=True,
                )

                # コピー用テキストエリア
                st.text_area("", value=result, height=500, key="copy_area")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

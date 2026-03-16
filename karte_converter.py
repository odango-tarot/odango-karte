import streamlit as st
import anthropic
import json

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
鑑定音声の文字起こし要約を受け取り、次回リピート時に見返す「カルテメモ（カンペ）」として整理してください。

以下のルールで整形してください：
- タイムスタンプ（00:00:00形式）はすべて除去する
- 情報は省略せず、元の内容をできるだけ保持する
- 各項目は体言止め・簡潔な文体に整える
- 話し言葉は書き言葉に直す
- 「鑑定結果」は占いで見えた事実・状況の分析のみ
- 「アドバイス」は相談者への行動指針・心がけのみ（両者を混在させない）

以下のJSON形式のみで返答してください（前後に説明文・マークダウン記号・バッククォートは一切不要）:
{
  "相談者情報": ["相談者名・属性・状況など"],
  "主な相談内容": ["相談テーマを簡潔に"],
  "鑑定結果": ["占いで見えた事実・相性・時期・環境の分析を漏れなく"],
  "アドバイス": ["相談者への行動指針・心がけを漏れなく"],
  "気になるキーワード": ["重要な人物名・時期・キーワード"],
  "次回への引き継ぎ": ["次回確認・フォローすべき点"]
}"""

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
                raw = message.content[0].text.strip()
                raw = raw.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw)

                # ─── 結果表示 ─────────────────────────────
                st.divider()
                st.subheader("カルテメモ")

                copy_text = ""
                for key, items in data.items():
                    if not items:
                        continue
                    st.markdown(f"**{key}**")
                    lines = []
                    for item in items:
                        st.markdown(f"- {item}")
                        lines.append(f"▸ {item}")
                    copy_text += f"【{key}】\n" + "\n".join(lines) + "\n\n"

                # 文字数カウント
                char_count = len(copy_text.strip())
                st.markdown(
                    f"<p style='color:gray; font-size:13px; text-align:right;'>{char_count} 文字</p>",
                    unsafe_allow_html=True,
                )

                # コピー用テキストエリア
                st.divider()
                st.caption("↓ コピー用（管理画面に貼り付け）")
                st.text_area("", value=copy_text.strip(), height=300, key="copy_area")

            except json.JSONDecodeError:
                st.error("変換結果のJSON解析に失敗しました。もう一度お試しください。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

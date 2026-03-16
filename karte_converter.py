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
st.caption("NottaAIの要約をペーストして、カンペ形式（900文字以内）に変換します")

# ─── システムプロンプト ────────────────────────────────────
SYSTEM_PROMPT = """あなたは電話占い師のアシスタントです。
鑑定音声の文字起こし要約を受け取り、次回リピート時に見返す「カルテメモ（カンペ）」として整理してください。

【重要】出力全体の文字数は必ず900文字以内に収めること。各項目は体言止め・簡潔に。

以下のJSON形式のみで返答してください（前後に説明文・マークダウン記号・バッククォートは一切不要）:
{
  "相談者情報": ["相談者の属性・状況（年齢・性別・仕事・恋愛状況等）。各項目15〜25字以内"],
  "主な相談内容": ["今回の相談テーマを簡潔に。各項目20字以内。最大3項目"],
  "鑑定結果・アドバイス": ["占い師が伝えた主な内容・アドバイス。各項目25字以内。最大4項目"],
  "気になるキーワード": ["重要な人物名・場所・日時・キーワード。各項目15字以内。最大4項目"],
  "次回への引き継ぎ": ["次回確認・フォローすべき点。各項目20字以内。最大3項目"]
}

タイムスタンプ不要。話し言葉不可。体言止めで簡潔に。全体で900文字を絶対に超えないこと。"""

LABELS = {
    "相談者情報": "👤 相談者",
    "主な相談内容": "💬 相談内容",
    "鑑定結果・アドバイス": "🔮 鑑定・アドバイス",
    "気になるキーワード": "🔑 キーワード",
    "次回への引き継ぎ": "📌 次回フォロー",
}

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
                    max_tokens=1024,
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
                    label = LABELS.get(key, key)
                    st.markdown(f"**{label}**")
                    lines = []
                    for item in items:
                        st.markdown(f"- {item}")
                        lines.append(f"▸ {item}")
                    copy_text += f"【{label}】\n" + "\n".join(lines) + "\n\n"

                # 文字数カウント
                char_count = len(copy_text.strip())
                color = "red" if char_count > 900 else "gray"
                st.markdown(
                    f"<p style='color:{color}; font-size:13px; text-align:right;'>{char_count} 文字</p>",
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

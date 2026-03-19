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

# ─── システムプロンプトテンプレート：フォローメール ────────
# ─── ラテン語フレーズ読み込み ────────────────────────────
@st.cache_data
def load_latin_phrases():
    try:
        with open("latin_phrases.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

latin_phrases = load_latin_phrases()

MAIL_PROMPT_TEMPLATE = """あなたは電話占い師「Shanti（シャンティ）」のクローンアシスタントです。
鑑定音声の文字起こし要約をもとに、Shantiとして鑑定後のフォローメールを書いてください。

【お客様の種別】
{client_type}

【種別ごとの冒頭文】
{opening_text}

【Shantiの文体・口癖】
- 「視えました」「視えます」（"見"ではなく必ず"視"を使う）
- 「〜ですよ」「〜ですね」「〜ましょうね」の柔らかい語尾
- 「焦らず」「急がず」「大丈夫ですよ」をよく使う
- お客様の感情・状況にまず寄り添ってから、鑑定内容に入る
- 箇条書きは避け、流れるような文章を好む
- 「〜と感じます」より「〜と視えます」を優先する
- 温かく、包み込むような雰囲気。押しつけがましくない
- 季節・体調への気遣いを自然に添えることがある
- 「でもね、」「〜ね。」「〜でしょう？」など馴れ馴れしい語尾・フレーズは使わない。自然な丁寧語を保つ
- 段落ごとに適切に改行し、読みやすくする

【必ず守る構造】
1. 書き出し：
「〇〇さん、こんばんは。
Shantiです。」

2. お礼・冒頭：上記【種別ごとの冒頭文】をそのまま使い、最後に以下を1行追加する
「ご相談内容を備忘録としておまとめいたしましたので、よろしければお読みくださいね。」

3. 区切り線：「- * - * - * - * - * - * -」

4. 本文：鑑定内容をShantiの文体で自然にまとめる
   - テーマごとに「◆テーマ名◆」の見出しを立てて整理する
   - 例：「◆振り返り◆」「◆〇〇さん（相手の名前）について◆」など
   - 各段落は短めに区切り、読みやすく改行する

5. 区切り線：「- * - * - * - * - * - * -」

6. 締め：
「もしまた何かあれば、ぜひぜひお気軽にお声がけくださいね。
不安な時、ちょっと気になってしまうことがある時、いつでもお待ちしております。」
＋状況に合わせた一言（例：「〇〇さんの幸せを、心より願っております！」）

7. おまじない：
「◆〇〇のフレーズ◆」（内容に合わせた見出しをつける。例：「◆お二人の周波数調整のフレーズ◆」）
ラテン語1文（下記【ラテン語フレーズ集】から相談内容・感情トーンに最も合うものを選ぶ）
おまじないの説明文1〜2文（例：「お読みいただいた瞬間から、〇〇さんを通して、お二人の波が整っていきます。音楽のように、少しずつ綺麗な和音にまとまっていきますよ。」）

【ラテン語フレーズ集】
{latin_phrases}

8. 署名：「＊Shanti＊」

【優先ルール】
- 要約の末尾に「お客様へのフォローメールドラフト」がある場合は、内容をベースにしつつShantiの文体・構造に書き直す
- ドラフトの内容は活かすが、文体は必ずShantiのトーンに統一する
- タイムスタンプは除去する
- マークダウン記法（#・**・---など）は使わない
- お客様の名前は要約から拾う"""

# ─── 冒頭文の定義 ────────────────────────────────────────
OPENING_TEXTS = {
    "新規のお客様": (
        "新規のお客様",
        "「先日はお電話をいただき、ありがとうございました。ご縁をいただけて、とても嬉しかったです。（フォローメール、遅くなってごめんなさい！）」"
    ),
    "リピーター（定期的にご利用）": (
        "定期リピーターのお客様",
        "「先日も、リピートでのお電話をいただき、ありがとうございました。こちらの都合で、メールまでのお時間が経ってしまってごめんなさい！」"
    ),
    "リピーター（久々のご利用）": (
        "久々にご利用いただいたリピーターのお客様",
        "「先日は久しぶりにお電話をいただけて、とても嬉しかったです。またお声がけいただけて、本当にありがとうございました。（フォローメール、遅くなってごめんなさい！）」"
    ),
}

# ─── 入力エリア ───────────────────────────────────────────
client_type_label = st.radio(
    "お客様の種別",
    options=list(OPENING_TEXTS.keys()),
    horizontal=True,
)

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

        # フォローメール用プロンプトを種別に応じて生成
        client_type_str, opening_text_str = OPENING_TEXTS[client_type_label]
        mail_prompt = MAIL_PROMPT_TEMPLATE.format(
            client_type=client_type_str,
            opening_text=opening_text_str,
            latin_phrases=latin_phrases,
        )

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
                    system=mail_prompt,
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
        st.text_area("", value=mail_result, height=400, key="mail_area")

"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
このファイルが実行されると、Streamlitを通じてWebアプリが起動します。
"""

############################################################
# 1. ライブラリの読み込み
############################################################
# 「.env」ファイルから環境変数を読み込むための関数
from dotenv import load_dotenv
# ログ出力を行うためのモジュール
import logging
# streamlitアプリの表示を担当するモジュール
import streamlit as st
# （自作）画面表示以外の様々な関数が定義されているモジュール
import utils
# （自作）アプリ起動時に実行される初期化処理が記述された関数
from initialize import initialize
# （自作）画面表示系の関数が定義されているモジュール
import components as cn
# （自作）変数（定数）がまとめて定義・管理されているモジュール
import constants as ct
# 

############################################################
# 2. 設定関連
############################################################
# ブラウザタブの表示文言を設定
st.set_page_config(
    page_title=ct.APP_NAME,
    layout="wide"
)

# ログ出力を行うためのロガーの設定
logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 3. 初期化処理
############################################################
try:
    # 初期化処理（「initialize.py」の「initialize」関数を実行）
    initialize()
except Exception as e:
    # エラーログの出力
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()

# アプリ起動時のログファイルへの出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)
    # セッション内の会話履歴を初期化し、初回起動時のみウェルカムメッセージを追加する
    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_text = (
            "こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。"
            "サイドメニューで利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。"
        )
        note_text = "具体的に入力した方が行きたい通りの回答を得られやすです。"
        st.session_state.messages.append({
            "role": "assistant",
            "content": {"mode": "system", "answer": welcome_text, "note": note_text}
        })
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []


############################################################
# 4. 初期表示
############################################################
# タイトルとモード表示を含む画面レイアウトを表示


# 右画面に表示されるチャット入力欄の値と会話コンテナとスピナープレースホルダを受け取る
chat_message, conv_container, spinner_placeholder = cn.display_app_layout()


############################################################
# 5-6. チャット送信時の処理（会話履歴へ追加し、会話コンテナが上部に表示される）
if chat_message:
    # ユーザーメッセージのログ出力
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    # LLMによる回答生成（できれば右カラムの会話コンテナ上にスピナーを表示、できない場合はglobal spinnerを使用）
    try:
        spinner_ctx = spinner_placeholder.spinner(ct.SPINNER_TEXT)
    except Exception:
        spinner_ctx = st.spinner(ct.SPINNER_TEXT)

    with spinner_ctx:
        try:
            llm_response = utils.get_llm_response(chat_message)
        except Exception as e:
            logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    # モードに応じて表示用の辞書データを作成（表示は conversation コンテナが行う）
    try:
        if st.session_state.mode == ct.ANSWER_MODE_1:
            content = cn.build_search_content(llm_response)
        elif st.session_state.mode == ct.ANSWER_MODE_2:
            content = cn.build_contact_content(llm_response)
        else:
            content = {"mode": st.session_state.mode, "answer": llm_response.get("answer", "")}
        logger.info({"message": content, "application_mode": st.session_state.mode})
    except Exception as e:
        logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
        st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
        st.stop()

    # 会話履歴へ追加（会話履歴は右上のコンテナに表示され、入力欄はその下に固定される）
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": content})

    # 生成した回答を即時表示するため、会話コンテナを再描画
    try:
        cn.display_conversation_log(container=conv_container)
    except Exception:
        # 再描画に失敗しても処理を継続（非致命）
        pass

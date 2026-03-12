"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import os
import csv
import constants as ct


############################################################
# 関数定義
############################################################

def display_left_panel():
    """
    左画面の表示
    """
    st.markdown("**利用目的**")

    st.session_state.mode = st.radio(
        label="利用目的を選択してください",
        options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
        label_visibility="collapsed"
    )
    # 「社内文書検索」の機能説明
    st.markdown("**【「社内文書検索」を選択した場合】**")
    # 「st.info()」を使うと青枠で表示される
    st.info("入力内容と関連性が高い社内文書のありかを検索できます。")
    # 「st.code()」を使うとコードブロックの装飾で表示される
    # 「wrap_lines=True」で折り返し設定、「language=None」で非装飾とする
    st.code(
        "【入力例】\n社員の育成方針に関するMTGの議事録",
        wrap_lines=True,
        language=None
    )

    # 「社内問い合わせ」の機能説明
    st.markdown("**【「社内問い合わせ」を選択した場合】**")
    # 「st.info()」を使うと青枠で表示される
    st.info("質問・要望に対して、社内文書の情報をもとに回答を得られます。")
    # 「st.code()」を使うとコードブロックの装飾で表示される
    # 「wrap_lines=True」で折り返し設定、「language=None」で非装飾とする
    st.code(
        "【入力例】\n人事部に所属している従業員情報を一覧化して",
        wrap_lines=True,
        language=None
    )

def display_right_panel(conv_container=None):
    """
    右画面の表示
    """
    # 会話描画先を決定
    target = conv_container if conv_container is not None else st

    # 初期メッセージ（会話履歴が空の場合）を会話コンテナに表示
    if not st.session_state.messages:
        with target.chat_message("assistant"):
            target.success(
                "こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。"
                "左側で利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。"
            )
            target.warning("具体的に入力した方が行きたい通りの回答を得られやすです。")

    # 会話履歴は conv_container に描画する（conv_container が指定されていればそちらへ）
    display_conversation_log(container=conv_container)

    # 右側に入力例（これからの会話）を追記（履歴の下、入力欄の上に表示）
    example_conversation = (
        "ユーザー: 社員の育成方針に関するMTGの議事録を探して\n"
        "アシスタント: 以下のファイルに該当する可能性があります。...\n"
        "ユーザー: その中で、評価基準に関する部分だけ抜粋して教えて。\n"
        "アシスタント: （該当ページの抜粋を提示）"
    )
    st.code(example_conversation, wrap_lines=True, language=None)

    # 右画面下部にチャット入力欄を表示して、入力値を呼び出し元に返す
    chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)
    return chat_message

def display_app_layout():
    """
    アプリのレイアウト表示
    """
    # 画面を左右2分割するレイアウトを作成
    left_column, right_column = st.columns([2, 8])
    
    # レイアウトの幅は、左画面が全体の2割、右画面が全体の8割になるように設定
    # 左画面の表示
    with left_column:
        display_left_panel()

    # 右側の表示
    with right_column:
        # 会話用のコンテナ（履歴をここに描画）を作成
        conv_container = right_column.container()
        # 入力欄の上に配置するスピナープレースホルダを用意
        # spinner_placeholder は input の上に表示する意図で使います
        spinner_placeholder = right_column.empty()
        chat_message = display_right_panel(conv_container=conv_container)

    return chat_message, conv_container, spinner_placeholder


def display_conversation_log(container=None):
    """
    会話ログの一覧表示
    """
    target = container if container is not None else st

    # 会話ログのループ処理（chat_message コンテナを使ってアイコンを表示）
    for message in st.session_state.messages:
        with target.chat_message(message["role"]):
            # ユーザー入力値の場合
            if message["role"] == "user":
                st.markdown(message["content"])
                continue

            # アシスタントの表示
            if message["content"]["mode"] == ct.ANSWER_MODE_1:
                if not "no_file_path_flg" in message["content"]:
                    st.markdown(message["content"]["main_message"])
                    icon = utils.get_source_icon(message['content']['main_file_path'])
                    if "main_page_number" in message["content"]:
                        st.success(f"{message['content']['main_file_path']} (p.{message['content']['main_page_number']})", icon=icon)
                    else:
                        st.success(f"{message['content']['main_file_path']}", icon=icon)

                    if "sub_message" in message["content"]:
                        st.markdown(message["content"]["sub_message"])
                        for sub_choice in message["content"]["sub_choices"]:
                            icon = utils.get_source_icon(sub_choice['source'])
                            if "page_number" in sub_choice:
                                st.info(f"{sub_choice['source']} (p.{sub_choice['page_number']})", icon=icon)
                            else:
                                st.info(f"{sub_choice['source']}", icon=icon)
                else:
                    st.markdown(message["content"]["answer"])            
            else:
                st.markdown(message["content"]["answer"])            
                if "file_info_list" in message["content"]:
                    st.divider()
                    st.markdown(f"##### {message['content']['message']}")
                    for file_info in message["content"]["file_info_list"]:
                        file_path_for_icon = file_info.split(" (p.")[0]
                        icon = utils.get_source_icon(file_path_for_icon)
                        st.info(file_info, icon=icon)


def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # LLMからのレスポンスに参照元情報が入っており、かつ「該当資料なし」が回答として返された場合
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:

        # ==========================================
        # ユーザー入力値と最も関連性が高いメインドキュメントのありかを表示
        # ==========================================
        # LLMからのレスポンス（辞書）の「context」属性の中の「0」に、最も関連性が高いドキュメント情報が入っている
        main_file_path = llm_response["context"][0].metadata["source"]

        # 補足メッセージの表示
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)
        
        # 参照元のありかに応じて、適したアイコンを取得
        icon = utils.get_source_icon(main_file_path)
        # ページ番号が取得できた場合のみ、ページ番号を表示（ドキュメントによっては取得できない場合がある）
        if "page" in llm_response["context"][0].metadata:
            # ページ番号を取得
            main_page_number = llm_response["context"][0].metadata["page"]
            # 「メインドキュメントのファイルパス」と「ページ番号」を表示
            st.success(f"{main_file_path} (p.{main_page_number})", icon=icon)
        else:
            # 「メインドキュメントのファイルパス」を表示
            st.success(f"{main_file_path}", icon=icon)

        # ==========================================
        # ユーザー入力値と関連性が高いサブドキュメントのありかを表示
        # ==========================================
        # メインドキュメント以外で、関連性が高いサブドキュメントを格納する用のリストを用意
        sub_choices = []
        # 重複チェック用のリストを用意
        duplicate_check_list = []

        # ドキュメントが2件以上検索できた場合（サブドキュメントが存在する場合）のみ、サブドキュメントのありかを一覧表示
        # 「source_documents」内のリストの2番目以降をスライスで参照（2番目以降がなければfor文内の処理は実行されない）
        for document in llm_response["context"][1:]:
            # ドキュメントのファイルパスを取得
            sub_file_path = document.metadata["source"]

            # メインドキュメントのファイルパスと重複している場合、処理をスキップ（表示しない）
            if sub_file_path == main_file_path:
                continue
            
            # 同じファイル内の異なる箇所を参照した場合、2件目以降のファイルパスに重複が発生する可能性があるため、重複を除去
            if sub_file_path in duplicate_check_list:
                continue

            # 重複チェック用のリストにファイルパスを順次追加
            duplicate_check_list.append(sub_file_path)
            
            # ページ番号が取得できない場合のための分岐処理
            if "page" in document.metadata:
                # ページ番号を取得
                sub_page_number = document.metadata["page"]
                # 「サブドキュメントのファイルパス」と「ページ番号」の辞書を作成
                sub_choice = {"source": sub_file_path, "page_number": sub_page_number}
            else:
                # 「サブドキュメントのファイルパス」の辞書を作成
                sub_choice = {"source": sub_file_path}
            
            # 後ほど一覧表示するため、サブドキュメントに関する情報を順次リストに追加
            sub_choices.append(sub_choice)
        
        # サブドキュメントが存在する場合のみの処理
        if sub_choices:
            # 補足メッセージの表示
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)

            # サブドキュメントに対してのループ処理
            for sub_choice in sub_choices:
                # 参照元のありかに応じて、適したアイコンを取得
                icon = utils.get_source_icon(sub_choice['source'])
                # ページ番号が取得できない場合のための分岐処理
                if "page_number" in sub_choice:
                    # 「サブドキュメントのファイルパス」と「ページ番号」を表示
                    st.info(f"{sub_choice['source']} (p.{sub_choice['page_number']})", icon=icon)
                else:
                    # 「サブドキュメントのファイルパス」を表示
                    st.info(f"{sub_choice['source']}", icon=icon)
        
        # 表示用の会話ログに格納するためのデータを用意
        # - 「mode」: モード（「社内文書検索」or「社内問い合わせ」）
        # - 「main_message」: メインドキュメントの補足メッセージ
        # - 「main_file_path」: メインドキュメントのファイルパス
        # - 「main_page_number」: メインドキュメントのページ番号
        # - 「sub_message」: サブドキュメントの補足メッセージ
        # - 「sub_choices」: サブドキュメントの情報リスト
        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["main_message"] = main_message
        content["main_file_path"] = main_file_path
        # メインドキュメントのページ番号は、取得できた場合にのみ追加
        if "page" in llm_response["context"][0].metadata:
            content["main_page_number"] = main_page_number
        # サブドキュメントの情報は、取得できた場合にのみ追加
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices
    
    # LLMからのレスポンスに、ユーザー入力値と関連性の高いドキュメント情報が入って「いない」場合
    else:
        # 関連ドキュメントが取得できなかった場合のメッセージ表示
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)

        # 表示用の会話ログに格納するためのデータを用意
        # - 「mode」: モード（「社内文書検索」or「社内問い合わせ」）
        # - 「answer」: LLMからの回答
        # - 「no_file_path_flg」: ファイルパスが取得できなかったことを示すフラグ（画面を再描画時の分岐に使用）
        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["answer"] = ct.NO_DOC_MATCH_MESSAGE
        content["no_file_path_flg"] = True
    
    return content


def build_search_content(llm_response):
    """LLMレスポンスから表示用の辞書データを作成（表示は行わない）"""
    # LLMからのレスポンスに参照元情報が入っており、かつ「該当資料なし」が回答として返された場合
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:
        main_file_path = llm_response["context"][0].metadata["source"]

        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"

        # ページ番号が取得できた場合のみ、ページ番号を保持
        if "page" in llm_response["context"][0].metadata:
            main_page_number = llm_response["context"][0].metadata["page"]

        sub_choices = []
        duplicate_check_list = []
        for document in llm_response["context"][1:]:
            sub_file_path = document.metadata["source"]
            if sub_file_path == main_file_path:
                continue
            if sub_file_path in duplicate_check_list:
                continue
            duplicate_check_list.append(sub_file_path)
            if "page" in document.metadata:
                sub_page_number = document.metadata["page"]
                sub_choice = {"source": sub_file_path, "page_number": sub_page_number}
            else:
                sub_choice = {"source": sub_file_path}
            sub_choices.append(sub_choice)

        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["main_message"] = main_message
        content["main_file_path"] = main_file_path
        if "page" in llm_response["context"][0].metadata:
            content["main_page_number"] = main_page_number
        if sub_choices:
            content["sub_message"] = "その他、ファイルありかの候補を提示します。"
            content["sub_choices"] = sub_choices
    else:
        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["answer"] = ct.NO_DOC_MATCH_MESSAGE
        content["no_file_path_flg"] = True

    return content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # LLMからの回答を表示
    st.markdown(llm_response["answer"])

    # ユーザーの質問・要望に適切な回答を行うための情報が、社内文書のデータベースに存在しなかった場合
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        # 区切り線を表示
        st.divider()

        # 補足メッセージを表示
        message = "情報源"
        st.markdown(f"##### {message}")

        # 参照元のファイルパスの一覧を格納するためのリストを用意
        file_path_list = []
        file_info_list = []

        # LLMが回答生成の参照元として使ったドキュメントの一覧が「context」内のリストの中に入っているため、ループ処理
        for document in llm_response["context"]:
            # ファイルパスを取得
            file_path = document.metadata["source"]
            # ファイルパスの重複は除去
            if file_path in file_path_list:
                continue

            # ページ番号が取得できた場合のみ、ページ番号を表示（ドキュメントによっては取得できない場合がある）
            if "page" in document.metadata:
                # ページ番号を取得
                page_number = document.metadata["page"]
                # 「ファイルパス」と「ページ番号」を組み合わせて表示用文字列を作成
                file_info = f"{file_path} (p.{page_number})"
            else:
                # 「ファイルパス」のみ
                file_info = f"{file_path}"

            # 参照元のありかに応じて、適したアイコンを取得
            icon = utils.get_source_icon(file_path)
            # ファイル情報を表示
            st.info(file_info, icon=icon)

            # 重複チェック用に、ファイルパスをリストに順次追加
            file_path_list.append(file_path)
            # ファイル情報をリストに順次追加
            file_info_list.append(file_info)

        # 参照元としてCSVファイルが含まれている場合、先頭の数行を表形式で表示する
        csv_files = [p for p in file_path_list if p.lower().endswith('.csv')]
        for csv_file in csv_files:
            try:
                with open(csv_file, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                if rows:
                    # 表示件数は最大10件（ただしCSVに4件以上存在すれば先頭4件以上を表示）
                    display_count = min(len(rows), 10)
                    st.markdown(f"##### {os.path.basename(csv_file)} の先頭 {display_count} 件")
                    st.table(rows[:display_count])
            except Exception:
                # CSVが読み込めない場合は細かいエラーを表示せず、処理を継続
                st.warning(f"{os.path.basename(csv_file)} の内容を表示できませんでした。")

    # 表示用の会話ログに格納するためのデータを用意
    # - 「mode」: モード（「社内文書検索」or「社内問い合わせ」）
    # - 「answer」: LLMからの回答
    # - 「message」: 補足メッセージ
    # - 「file_path_list」: ファイルパスの一覧リスト
    content = {}
    content["mode"] = ct.ANSWER_MODE_2
    content["answer"] = llm_response["answer"]
    # 参照元のドキュメントが取得できた場合のみ
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content


def build_contact_content(llm_response):
    """LLMレスポンスから表示用の辞書データを作成（表示は行わない）"""
    content = {}
    content["mode"] = ct.ANSWER_MODE_2
    content["answer"] = llm_response.get("answer", "")

    if llm_response.get("answer", "") != ct.INQUIRY_NO_MATCH_ANSWER:
        message = "情報源"
        file_path_list = []
        file_info_list = []
        for document in llm_response.get("context", []):
            file_path = document.metadata["source"]
            if file_path in file_path_list:
                continue
            if "page" in document.metadata:
                page_number = document.metadata["page"]
                file_info = f"{file_path} (p.{page_number})"
            else:
                file_info = f"{file_path}"
            file_path_list.append(file_path)
            file_info_list.append(file_info)
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content
import os
import json
import requests
from flask import Flask, request
from langchain_community.llms import Bedrock
from langchain.chains import RetrievalQA
from langchain_community.retrievers import AmazonKendraRetriever
from langchain.prompts import PromptTemplate

app = Flask(__name__)

@app.route('/endpoint', methods=['POST'])
def endPoint():
    
    if request.method == 'POST':
        
        if request.headers['Content-Type'] == 'application/json; charset=utf-8' :
            
            payload = request.json
            
            for event in payload['events']:
                
                if event['type'] == 'message':
                    
                    replyToken = event['replyToken']
                    receiveText = event['message']['text']
                    answer = send_prompt(receiveText)
                    replayMessage(replyToken, answer)
                    
            return "", 200
    
        else:
            return "Invalid Content Type", 400
    
    else:
        return "Method Not Allowed", 405
                    
def send_prompt(question):
    
    kendra_index_id=os.environ.get('AMAZON_KENDRA_INDEX_ID')
    attribute_filter = {"EqualsTo": {"Key": "_language_code","Value": {"StringValue": "ja"}}}
    retriever = AmazonKendraRetriever(index_id=kendra_index_id,attribute_filter=attribute_filter,top_k=20)

    llm =  Bedrock(
        model_id="anthropic.claude-v2:1",
        model_kwargs={"max_tokens_to_sample": 1000}
    )

    prompt_template = """

    <documents>{context}</documents>
    \n\nHuman: あなたはギークくんという名前の秋葉原のマスコットキャラクターです。
        <documents>タグに示されている情報を元に、<question>に対して説明してください。言語の指定が無い場合は日本語で答えてください。
        もし<question>タグの内容が参考文書に無かった場合は「文書にありません」と答えてください。回答に<documents>タグの内容や、<question>タグの内容を含めないでください。
        引用元はのURLは表示しないでください。「文書によると」などの表現を回答の始めに絶対に使用しないでください。なるべく親しげに、明るく元気な文体で答えるようにしてください。
    <question>{question}</question>
    \n\nAssistant:
"""

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain_type_kwargs = {"prompt": prompt}

    # Chainの定義
    qa = RetrievalQA.from_chain_type(retriever=retriever,llm=llm,chain_type_kwargs=chain_type_kwargs)

    # chainの実行
    answer = qa.invoke(question)
    
    return answer

def replayMessage(replyToken, answer):
    
    # LINE Messaging API のエンドポイント
    apiUrl = 'https://api.line.me/v2/bot/message/reply'
    
    # LINEのアクセストークン
    accessToken = os.environ.get('LINE_MESSAGEING_API_CHANEL_ACCESS_TOKEN')
    
    # 応答メッセージのレスポンスヘッダー
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + accessToken
    }
    
    # 応答メッセージの内容
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                'type': 'text',
                'text': answer['result'],
            }
        ]
    }
    
    # LINE Messaging API にPOSTリクエストを送信
    response = requests.post(apiUrl, data=json.dumps(data), headers=headers)
    
    if response.status_code == 200:
        return True
    else:
        return False
import streamlit as st
import pandas as pd
import pickle
import streamlit_authenticator as stauth
from pathlib import Path
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import urllib
import urllib.parse
from datetime import datetime, timedelta, timezone
import pytz

st.set_page_config(
            layout =  'wide',
            page_title = 'Ametista Store',
        )

file_path = Path(__file__).parent/"db"/"hashed_pw.pkl"

with file_path.open("rb") as file:
  hashed_passwords = pickle.load(file)

credentials = {
    "usernames": {
        "admin": {
            "email": 'admin@gmail.com',
            "name": "Admin",
            "password": hashed_passwords[0]
        }
    }
}

authenticator = stauth.Authenticate(credentials= credentials, cookie_name="st_session", cookie_key="key123", cookie_expiry_days= 2)
authenticator.login()

mongo_user = st.secrets['MONGO_USER']
mongo_pass = st.secrets["MONGO_PASS"]

username = urllib.parse.quote_plus(mongo_user)
password = urllib.parse.quote_plus(mongo_pass)
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password), ssl = True)
st.cache_resource = client
db = client.ametista
coll = db.estoque
coll2 = db.vendas
#coll3 = db.organizacao_dividas
#coll4 = db.historico_atendimento

fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")

if 'vendas' not in st.session_state:
	st.session_state['vendas'] = []

def increment_counter(venda):
	st.session_state['vendas'].append(venda)

def decrement_counter(venda):
	st.session_state['vendas'].remove(venda)

def estoque():
    estoque = coll.find({})
    estoquedf = []
    for item in estoque:
        estoquedf.append(item)
    df = pd.DataFrame(estoquedf, columns= ['_id', 'Categoria', 'Código','Descrição','Tamanho', 'Valor de compra', 'Valor de venda', 'Fornecedor'])
    df.drop(columns='_id', inplace=True)
    st.session_state['estoque'] = df
    g = df['Código'].value_counts()
    df_2 = pd.merge(df, g, on="Código")
    df_2.drop_duplicates(inplace= True)
    df_2.rename(columns={'count':'Quantidade'},inplace=True)
    st.session_state['estoque_2'] = df_2  

def adiciona_produto():
    select = st.selectbox('Selecione', ('Novo produto', 'Produto cadastrado'))
    if select == 'Novo produto':
        col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
        categoria = ['Blusa/Cropped', 'Calça/Shorts', 'Vestido/Conjunto', 'Acessórios']
        cat = col1.selectbox('Categoria', categoria)
        if cat == 'Blusa/Cropped':
            classe = 1
        if cat == 'Calça/Shorts':
            classe = 2
        if cat == 'Vestido/Conjunto':
            classe = 3
        if cat == 'Acessórios':
            classe = 4
        num = col2.number_input('Código', min_value= 0, max_value= 999, placeholder= 'Código do produto')
        cod = f'{classe}{num}'
        codigo = int(cod)   
        descricao = col3.text_input('Descrição do produto')
        tamanho = col4.text_input('Tamanho')
        valor_compra = col5.number_input('Valor de compra')
        valor_venda = col6.number_input('Valor de venda')
        fornecedor = col7.text_input('Fornecedor')
        
        produto = {'Categoria' : cat,
                   'Código' : codigo,
                   'Descrição' : descricao,
                   'Tamanho' : tamanho,
                   'Valor de compra': valor_compra,
                   'Valor de venda' : valor_venda,
                   'Fornecedor' : fornecedor}

    if select == 'Produto cadastrado':
        df = st.session_state['estoque']  
        col1,col2,col3,col4,col5,col6 = st.columns(6)
        codigo = col1.selectbox('Cód', df['Código'].value_counts().index)
        descricao = col2.selectbox('Produto', df[df['Código'] == codigo]['Descrição'])
        tamanho = col3.selectbox('Tam', df[df['Código'] == codigo]['Tamanho'])
        valor_compra = col4.number_input('Valor de compra')
        valor_venda = col5.number_input('Valor de venda')
        fornecedor = col6.text_input('Fornecedor')
 
        produto = {'Código' : codigo,
                   'Descrição' : descricao,
                   'Tamanho' : tamanho,
                   'Valor de compra': valor_compra,
                   'Valor de venda' : valor_venda,
                   'Fornecedor' : fornecedor}

        confirma = col6.button('Remover')
        if confirma:
            entry = [produto]
            coll.delete_one({'Código' : codigo})       

    confirma = st.button('Confirmar')
    if confirma:
        entry = [produto]
        coll.insert_many(entry)

def vendas():
    df = st.session_state['estoque']
    df_2 = st.session_state['estoque_2']
        
    col1,col2 = st.columns(2)
    col1.markdown('**Blusa/Cropped**')
    col1.dataframe(df_2[df_2['Categoria'] == 'Blusa/Cropped'][['Código','Descrição','Tamanho', 'Valor de venda', 'Quantidade']])
    col1.markdown('**Calça/Shorts**')
    col1.dataframe(df_2[df_2['Categoria'] == 'Calça/Shorts'][['Código','Descrição','Tamanho', 'Valor de venda', 'Quantidade']])
    col2.markdown('**Vestido/Conjunto**')
    col2.dataframe(df_2[df_2['Categoria'] == 'Vestido/Conjunto'][['Código','Descrição','Tamanho', 'Valor de venda', 'Quantidade']])
    col2.markdown('**Acessórios**')
    col2.dataframe(df_2[df_2['Categoria'] == 'Acessórios'][['Código','Descrição','Tamanho', 'Valor de venda', 'Quantidade']])

    st.divider()

    col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
    cat = df['Categoria'].value_counts().index
    cate = col1.selectbox('Categoria', cat)
    df_cat = df[df['Categoria'] == cate]
    cod = df_cat['Código'].value_counts().index
    codigo = col2.selectbox('Código', cod)
    desc = df_cat[df_cat['Código']==codigo]['Descrição']
    descricao = col3.selectbox('Descrição', desc)
    tam = df_cat[df_cat['Código']==codigo]['Tamanho']
    tamanho = col4.selectbox('Tamanho', tam)
    #val_com = df[df['Código']==codigo]['Valor de compra'].value_counts().index[0]
    #compra = col4.metric('Valor de compra', f'R$ {val_com:,.2f}')
    val_ven = df_cat[df_cat['Código']==codigo]['Valor de venda'].value_counts().index[0]
    valor_venda = col5.metric('Valor de venda', f'R$ {val_ven:,.2f}')
    desconto = col6.number_input('Desconto')
    soma_valor =  val_ven - desconto
    
    venda = {'Código' : codigo,
             'Descrição' : descricao,
             'Tamanho' : tamanho,
             'Valor' : val_ven,
             'Desconto' : desconto,
             'Final' : soma_valor}
    
    add = col7.button('Adicionar produto')
    if add:
        increment_counter(venda)
    
    vendas = st.session_state['vendas']

    add = col7.button('Remover produto')
    if add:
        decrement_counter(venda)

    df_venda = pd.DataFrame(vendas, columns = ['Código', 'Descrição', 'Tamanho', 'Valor', 'Desconto', 'Final'])
    col1,col2,col3,col4 = st.columns(4)
    col1.dataframe(df_venda)
    valor_total = df_venda['Final'].sum()
    col2.metric('Valor total', f'R$ {valor_total:,.2f}')
    cliente = col3.text_input('Cliente')
    taxa = col4.number_input('Taxa de entrega')
    forma_pgto = ['Pix','Dinheiro', 'Cartão de Crédito','Cartão de Débito', 'Parcelado']
    forma_pagamento = col2.selectbox('Forma de pagamento', forma_pgto)
    valor_fim = valor_total + taxa

    sell = {'Venda' : vendas,
            'Valor' : valor_total,
            'Entrega' : taxa,
            'Valor Final' : valor_fim,
            'Cliente' : cliente,
            'Forma de pagamento' : forma_pagamento}
    
    confirma = st.button('Confirmar venda')
    if confirma:
        tempo_agora = datetime.now(fuso_horario_brasilia)
        data_utc = tempo_agora
        if isinstance(data_utc, datetime):
            data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
            tempo_agora = data_brasilia.strftime('%d')
            mes_agora = data_brasilia.strftime('%m')
            ano_agora = data_brasilia.strftime('%Y')
        sell.update({'Data da venda' : tempo_agora,
                    'Mês da venda': mes_agora,
                    'Ano' : ano_agora})
        entry = [sell]
        coll2.insert_many(entry)
        codigos = df_venda['Código'].value_counts().index
        for codigo in codigos:
            coll.delete_one({'Código' : codigo})

def historico():
    hist = coll2.find({})
    histdf = []
    for item in hist:
        histdf.append(item)
    df = pd.DataFrame(histdf, columns= ['_id', 'Cliente', 'Forma de pagamento','Valor','Entrega', 'Valor Final', 'Data da venda','Mês da venda', 'Ano'])
    df.drop(columns='_id', inplace=True)
    df
    st.divider()
    st.session_state['df_vendas'] = df

def visualiza_dados():
    hist = coll2.find({})
    histdf = []
    for item in hist:
        histdf.append(item)
    df_vendas = pd.DataFrame(histdf, columns= ['_id', 'Cliente', 'Forma de pagamento','Valor','Entrega', 'Valor Final', 'Data da venda', 'Mês da venda', 'Ano'])
    df_vendas.drop(columns='_id', inplace=True)
    
    mes = {'1': 'Janeiro', '2' :'Fevereiro', '3': 'Março', '4': 'Abril', '5': 'Maio', '6' : 'Junho', '7' : 'Julho', '8' : 'Agosto', '9' : 'Setembro', '10' : 'Outubro', '11' : 'Novembro', '12' : 'Dezembro'}
    df_vendas['Mês da venda'] = df_vendas['Mês da venda'].map(mes)
    st.title('Financeiro')
    col1,col2 = st.columns(2)
    ano = df_vendas['Ano'].value_counts().index
    anos = col1.selectbox('Selecione um ano:', ano)
    df_ano = df_vendas[df_vendas['Ano'] == anos]
    mes = df_ano['Mês da venda'].value_counts().index
    mes_pesquisa = col2.selectbox('Selecione um Mês:', mes)
    df_mes_1 = df_ano[df_ano['Mês da venda'] == mes_pesquisa]
    df_mes = df_mes_1[['Cliente', 'Forma de pagamento', 'Valor', 'Entrega', 'Valor Final', 'Data da venda']]
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric('Numero de pedido no mês', df_mes['Cliente'].value_counts().values.sum())
    col2.metric('Cliente com mais pedidos', df_mes['Cliente'].value_counts().index[0])
    col3.markdown('Formas de pagamento mais utilizadas:')
    df_pagamento = pd.DataFrame(df_mes['Forma de pagamento'].value_counts())
    df_pagamento.rename(columns={'count':'Quantidade'}, inplace=True)
    col3.dataframe(df_pagamento)
    col4.metric('Valor vendido', f'R$ {df_mes['Valor Final'].sum():,.2f}')

def tabs():
    df = st.session_state['estoque']
    df_2 = st.session_state['estoque_2']
    tab1,tab2,tab3,tab4 = st.tabs(['Financeiro','Estoque', 'Vendas', 'Histórico de vendas'])

    with tab1:
        visualiza_dados()

    with tab2:
        st.title('Estoque')
        col1,col2 = st.columns(2)
        col1.markdown('**Blusa/Cropped**')
        col1.dataframe(df_2[df_2['Categoria'] == 'Blusa/Cropped'][['Código','Descrição','Tamanho', 'Valor de compra', 'Valor de venda', 'Fornecedor', 'Quantidade']])
        col1.markdown('**Calça/Shorts**')
        col1.dataframe(df_2[df_2['Categoria'] == 'Calça/Shorts'][['Código','Descrição','Tamanho', 'Valor de compra', 'Valor de venda', 'Fornecedor', 'Quantidade']])
        col2.markdown('**Vestido/Conjunto**')
        col2.dataframe(df_2[df_2['Categoria'] == 'Vestido/Conjunto'][['Código','Descrição','Tamanho', 'Valor de compra', 'Valor de venda', 'Fornecedor', 'Quantidade']])
        col2.markdown('**Acessórios**')
        col2.dataframe(df_2[df_2['Categoria'] == 'Acessórios'][['Código','Descrição','Tamanho', 'Valor de compra', 'Valor de venda', 'Fornecedor', 'Quantidade']])

        st.divider()
        st.markdown('**Adicionar e remover proutos**')
        adiciona_produto()       

    with tab3:
        st.title('Vendas')
        vendas()

    with tab4:
        st.title('Histórico de vendas')
        historico()

def pagina_principal():
    logo = "files/logo.png"
    st.title('Ametista Store')
    btn = authenticator.logout()
    if btn:
        st.session_state["authentication_status"] == None
    #visualiza_dados()
    st.divider()
    estoque()
    tabs()

def main():
    if st.session_state["authentication_status"]:
        pagina_principal()
    elif st.session_state["authentication_status"] == False:
        st.error("Username/password is incorrect.")

    elif st.session_state["authentication_status"] == None:
        st.warning("Please insert username and password")

if __name__ == '__main__':
    main()

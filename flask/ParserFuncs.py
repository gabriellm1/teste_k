# -*- coding: utf-8 -*-

# imports
from io import StringIO
from numpy import empty, object0
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import PyPDF2
import re
import spacy
from spacy.lang.pt import Portuguese
from spacy.matcher import Matcher, PhraseMatcher
import pandas as pd

################################################################################################

# Expressões regulares, delimitadores e palavras chaves para separar documento ou até encontrar alguma informação
clause_regex = r'(X|I|V)+(\s)*[–|\-]((\s)[A-ZÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ,/]+)+'
qr_topic_regex = r'(\w+)((\s)+(\w+))*\:'
location_date_regex = r'\w+(\s\w+)+,\s\d+\sde\s(?:\bjaneiro\b|\bfevereiro\b|\bmarço\b|\babril\b|\bmaio\b|\bjunho\b|\bjulho\b|\bagosto\b|\bsetembro\b|\boutubro\b|\bnovembro\b|\bdezembro\b)\sde\s\d+' # criar set de meses
extended_date_regex = r'\d+\sde\s\w+\sde\s\d+'
two_numbered_list_regex = '(\s\d+\.\d+\.\s)'
three_numbered_list_regex = '(\s\d+\.\d+\.\d+\.\s)'
roman_list_regex = '\((i|v)+(i|v)*\)'
abc_list_regex = r'[ˆa-z]\)(\s)+'

delimitador_contrato = 'CLÁUSULA '

keywords_contrato = ['resumo', 'multa','rescisão','benfeitorias','garantia']
keywords_quadroresumo = ['imóvel','prazo','valor','reajuste','forma','garantia','encargos','multa','rescisão','contatos','anexos']

################################################################################################

# Padrões Spacy
#  São utilizados para encontrar as informações desejadas
#  Cada dicionário representa a procura de um conjunto de informação Ex: valor_dict
#  Cada chave representa o padrão a ser procurado para encontrar uma informação específica Ex: 'data' : []
#  Padrão é representado por uma lista com varios dicionários que juntos formam um padrão Ex: [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS': 'PROPN'}], # 1º/12/2020
#  Se a lista de um padrão possuir mais que uma lista internamente é porque existem mais q 1 padrão para encontrar aquela informação
# Ex data': [
#                          [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS': 'PROPN'}], # 1º/12/2020
#                          [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS': 'ADJ'}, {'POS': 'ADP'}, {'POS': 'NOUN'}, {'POS': 'ADP'}, {'POS': 'NUM'}], # 1º de fevereiro de 2021
#                          [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS':'NUM'}] # Dezembro/2020                   
# ]
space = {'IS_SPACE': True, 'OP': '*'}


edificio_dict = {
    'area': [[{'POS': 'NUM'},{'ORTH': 'm²'}]],
    'pavimento/torre': [[{'POS': 'ADJ'},{'lower':'pavimento'}],[{'lower': 'torre'}]],
    'andar': [[{'POS': 'ADJ'},{'lower':'andar'}]],
    'vagas': [[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'lower':'vagas'}]],
    'nome': [[{'lower':'localizado'},{'lower':'no'}, {'IS_ALPHA':True,'OP': '+'}, {'IS_PUNCT': True}]]
    }

cd_dict = {
    'area': [[{'POS': 'NUM'},{'ORTH': 'm²'}]],
    'galpão': [[{'lower':'galpão'},{'POS':'PROPN'}]],
    'docas': [[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'ORTH': 'docas'}],
                [{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'ORTH': ')'},{'ORTH': 'doca'}]],
    'vagas': [[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'lower':'vagas'}]],
    'nome': [[{'lower':'todos'},{'lower':'situados'}, {'lower':'no'},{'IS_ALPHA':True,'OP': '+'}, {'IS_PUNCT': True}]]
    }

prazo_dict = {'prazo':[[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'ORTH': 'meses'}],
[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'ORTH': 'anos'}]],
'data':[[{'POS': 'NUM'}, {'POS': 'ADP'}, {'POS': 'NOUN'}, {'POS': 'ADP'}, {'POS': 'NUM'}],
[{'POS': 'ADJ'}, {'POS': 'ADP'}, {'POS': 'NOUN'}, {'POS': 'ADP'}, {'POS': 'NUM'}]]
}

valor_dict = { 'valor': [[{'ORTH': 'R$'}, {'POS': 'NUM'}]],
                'data': [
                         [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS': 'PROPN'}], # 1º/12/2020
                         [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS': 'ADJ'}, {'POS': 'ADP'}, {'POS': 'NOUN'}, {'POS': 'ADP'}, {'POS': 'NUM'}], # 1º de fevereiro de 2021
                         [{'lower':'base'},{'lower':'de'},{'lower':'reajuste'},{'POS':'NUM'}] # Dezembro/2020                   
]}

carencia_dict = {
    'periodo': [[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'}]],
    'data_inicio': [[{'POS': 'ADJ'}, {'ORTH': 'de'}, {'POS': 'NOUN'}, {'ORTH': 'de'}, {'POS': 'NUM'}]]
}

descontos_dict = {'periodo':[ [{'POS': 'ADJ'}, {'ORTH': 'de'}, {'POS': 'NOUN'}, {'ORTH': 'de'}, {'POS': 'NUM'}],
                              [{'POS': 'ADJ'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'IS_ALPHA': True},{'ORTH': 'de'},{'ORTH': 'locação'}] ],
                'valor_desconto_e_aluguel':[[{'ORTH': 'R$'}, {'POS': 'NUM'}],[{'ORTH': 'R$'}, {'POS': 'PROPN'}]]
                }

indice_reajuste_dict = {'indice':[[{'lower': 'igp-m','OP':'?'},{'lower': 'ipca','OP':'?'}]],'positivo':[ [{'lower':'positivo'}] , [{'lower':'positiva'}] ]}

forma_dict = {'dia': [[{'ORTH': 'dia'},{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'ORTH':'do'},{'ORTH':'mês'}],[{'ORTH': 'dia'},{'POS': 'ADJ'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'ORTH':'do'},{'ORTH':'mês'}]],
                'meio': [[{'ORTH':'por'},{'ORTH':'meio'},{'ORTH':'de'},{'IS_ALPHA': True,'OP':'+'},{'IS_PUNCT': True}]]}

garantia_dict = {'garantia':[[{'IS_ALPHA': True,'OP':'+'},{'ORTH':','}]]}

rescisao_antecipada_dict = {'aviso_previo':[[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'lower':'meses'}],
[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'lower':'dias'}],
[{'POS': 'NUM'},{'lower':'meses'}],[{'POS': 'NUM'},{'lower':'dias'}]],
'multa_rescisao_antecipada': [[{'POS': 'NUM'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'CCONJ','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'lower':'aluguéis'}],[{'POS': 'NUM'},{'lower':'aluguéis'}],],
'proporcional':[[{'lower':'proporcional'}],[{'lower':'proporcionais'}]]}

inadimplencia_dict = {'juros_ao_mes':[[{'lower':'razão'},{'POS': 'ADP'},{'POS': 'NUM'},{'ORTH':'%'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'ADP','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'},{'lower':'ao'},{'ORTH': 'mês'}]],
'multa_inadimplencia': [[{'lower':'multa'},{'lower':'equivalente'},{'lower':'a'},{'POS': 'NUM'},{'ORTH':'%'},{'ORTH': '('},{'IS_ALPHA': True},{'POS': 'ADP','OP':'*'},{'IS_ALPHA': True,'OP':'*'},{'ORTH': ')'}]], 
'prazos_multas':[[{'lower':'até'},{'POS':'NUM'},{"lower":'dias'},{'lower':'úteis'}]]}

################################################################################################

# Funções para estruturação do contrato

nlp = spacy.load('pt_core_news_md')

def pdf2string(path, remove_newline=True):
    '''
    Extrai conteúdo do PDF para uma única string Python
    '''
    output_string = StringIO()
    with open(path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    if remove_newline:
        return output_string.getvalue().replace('\n', '').encode().decode('utf-8')
    else:
        return output_string.getvalue()

def pdf2string2(path, remove_newline=True):
    # teste, não está sendo usada
    pdfFileObj = open('../contratos/foxconn.pdf', 'rb') 
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    n_pages = pdfReader.numPages
    content = ''
    for p in range(n_pages):
        content+= pdfReader.getPage(p).extractText()
    if remove_newline:  return content.replace('\n', '').encode().decode('utf-8')
    else:   return content


def split_regex_list(regex, conteudo):
    '''
    Divide o conteúdo usando um regex como delimitador
    '''
    meta = re.sub(regex, "_#DELIMITER#_", conteudo)

    return meta.split("_#DELIMITER#_")
    #posso usar depois para excluir o titulo na clausula tbm



def divide_contrato(delimitador, contrato):
    '''
    Divide contrato utilizando string como delimitador 
    '''
    return contrato.split(delimitador)

def extrai_titulo_clausulas(keywords, regex, conteudo):
    '''
    Extrai o Título das Cláusulas ou Sub-Cláusulas para uma lista
    '''
    titulos = []
    for t in conteudo:
        try:
            clausula = re.search(regex, t).group(0)
            clausula.replace(':','')
            pre_definido = False
            for kw in keywords:
                if kw in clausula.lower():  
                    titulos.append(kw)
                    pre_definido = True
                    break
            if not pre_definido:   titulos.append(clausula)
        except:
            titulos.append('None')
    # titulos.append('data_assinatura')
    return titulos

def extrai_subclausulas(regex, conteudo):
    '''
    Extrai conteúdo das subclausulas em uma lista para cada sessão
    '''
    clausulas = []
    for sessao_raw in conteudo:
        sessao = sessao_raw.replace('\n','').replace('  ',' ').strip()
        clausulas.append(split_regex_list(regex, sessao))
    return clausulas


def clausulas2dict(titulo_regex, conteudo_regex, keywords,conteudo, contrato, delimitador=delimitador_contrato):
    '''
    Separa partes do contrato ou quadro resumo em um dicionário
    '''
    dict_clausula = {}
    if contrato:    conteudo = divide_contrato(delimitador, conteudo)
    keys = extrai_titulo_clausulas(keywords, titulo_regex, conteudo)
    data = extrai_subclausulas(conteudo_regex, conteudo)

    if contrato: # Caso seja um contrato inteiro, tem suas peculiaridades
        keys[0] = 'intro' # Introdução do Contrato é importante guardar
        keys.append('data_assinatura') # Key para ter a data de assinatura no dict
        data_ass =  re.search(location_date_regex, conteudo[-1]).group(0) # Procura a data de assinatura
        data.append(data_ass) # Data de Assinatura no final
    else:
        # Se não for um contrato, a primeira chave e o primeiro conteúdo se tratam do título da clausula
        # Não é necessátio guarda-lo
        keys.pop(0)
        data.pop(0)
    if len(keys) != len(data): 
        print("Lengths {},{}".format(len(keys),len(data)))
        raise Exception("Keys and Data not the same length")
    else: tamanho = len(keys)
    for i in range(tamanho):
        dict_clausula[keys[i]] = data[i]
    return dict_clausula


def multa2dict(clausula):
    '''
    Separa a clausula de multa em um dicionário
    '''
    dict_multa = {'no_name': []}
    pre = extrai_subclausulas(three_numbered_list_regex,clausula)
    pre.pop(0) # Exclui texto inicial da clausula

    for sub in pre:  
        if 'MULTA POR RESCISÃO OU RESILIÇÃO ANTECIPADA' in sub[0]:
            dict_multa['rescisao_antecipada'] = sub[1:]
        elif 'MULTA POR INADIMPLÊNCIA CONTRATUAL' in sub[0]:
            dict_multa['inadimplencia'] = sub[1:]
        else:
            dict_multa['no_name']+=sub

    return dict_multa


def extrai_dado(padroes_dict, conteudo):
    '''
    Recebe padrões a ser procurados em determinado texto
    '''
    doc = nlp(conteudo)
    matcher = Matcher(nlp.vocab)
    for padrao in padroes_dict.keys():
        matcher.add(padrao,padroes_dict[padrao])
    matches = matcher(doc)

    extracted = {key:[] for key in padroes_dict}
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]
        span = doc[start : end]
        extracted[rule_id].append(span.text)
    return extracted

def extrai_imovel(conteudo):
    '''
    Extrai dados relacionados ao Imóvel do Quadro Resumo
    '''
    if 'CD' in conteudo[0]:
        cd = {'tipo_imovel': 'Galpão Logístico'}
        cd.update(extrai_CD(conteudo))
        return cd
    else:
        edificio = {'tipo_imovel': 'Escritório'}
        edificio.update(extrai_edificio(conteudo))
        return edificio

def extrai_CD(conteudo):
    '''
    Extrai dados relacionados ao CD do Quadro Resumo
    '''
    padroes_dict = cd_dict
    doc = nlp(conteudo[0])
    matcher = Matcher(nlp.vocab)
    for padrao in padroes_dict.keys():
        matcher.add(padrao,padroes_dict[padrao])
    matches = matcher(doc)

    extracted = {key:[] for key in padroes_dict}
    
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]
        span = doc[start : end]
        if rule_id == 'nome':
            span = doc[start+3:end-1] # pula o 'todos situados no'
        extracted[rule_id].append(span.text)
    # Tratar os dados para retornar de forma certa
    return {'area': extracted['area'],
            'galpao': extracted['galpão'],
            'docas': extracted['docas'],
            'vagas': extracted['vagas'],
            'nome': extracted['nome']}

def extrai_edificio(conteudo):
    '''
    Extrai dados relacionados ao Escritorio do Quadro Resumo
    '''
    padroes_dict = edificio_dict
    doc = nlp(conteudo[0])
    matcher = Matcher(nlp.vocab)
    for padrao in padroes_dict.keys():
        matcher.add(padrao,padroes_dict[padrao])
    matches = matcher(doc)

    extracted = {key:[] for key in padroes_dict}
    
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]
        if rule_id != 'pavimento/torre':
            span = doc[start : end]
        else:
            if doc[start : end].text.lower() == 'torre': span = doc[start : end+1]
            else:   span = doc[start : end]
        if rule_id == 'nome':
            span = doc[start+2:end-1] # pula o 'localizado no'
        extracted[rule_id].append(span.text)
    # Tratar os dados para retornar de forma certa
    return {'area': extracted['area'],
            'andar': extracted['andar'],
            'torre_docas': extracted['pavimento/torre'],
            'vagas': extracted['vagas'],
            'nome': extracted['nome']}


def extrai_prazo(conteudo):
    '''
    Extrai dados relacionados a prazo do Quadro Resumo
    '''
    extracted = extrai_dado(prazo_dict,conteudo[0])
    data_inicio = None
    if 'entrega das chaves' in conteudo[0].lower():
        data_inicio =  'entrega_chaves'
    else:   data_inicio = extracted['data'][0]
    # Tratar os dados para retornar de forma certa
    return {'prazo':extracted['prazo'], 'data_inicial': data_inicio}

def extrai_valores(conteudo):
    '''
    Extrai valores de alugel, carência e descontos do Quadro Resumo
    '''
    
    extracted_0 = extrai_dado(valor_dict,conteudo[0])
    if len(conteudo) == 1: # não possui carência nem desconto
        return {'valor_aluguel': extracted_0['valor'], 'data_reajuste': str(nlp(extracted_0['data'][0])[3:]),
                'periodo_carencia': None, 'data_inicio_carencia': None, 'descontos': []}
    
    extracted_1 = extrai_dado(carencia_dict,conteudo[1])
    extracted_2 = []

    if extracted_1['data_inicio']:
        inicio_carencia = extracted_1['data_inicio'][0] # pega primeira data
    else:
        inicio_carencia = 'entrega_chaves'
        
    descontos_raw = split_regex_list(roman_list_regex,conteudo[2])[1:] # exclui texto inicial da clausula
    for desconto in descontos_raw:
        desc = extrai_dado(descontos_dict,desconto)
        extracted_2.append({'periodo': desc['periodo'],'desconto': desc['valor_desconto_e_aluguel'][0],'aluguel':desc['valor_desconto_e_aluguel'][1]})

    #Tratar os dados para retornar de forma certa
    return {'valor_aluguel': extracted_0['valor'], 'data_reajuste': nlp(extracted_0['data'][0])[3:].text,
    'periodo_carencia': extracted_1['periodo'], 'data_inicio_carencia': inicio_carencia, 'descontos': extracted_2}

def extrai_indice_reajuste(conteudo):
    '''
    Extrai qual será o índice de reajuste do aluguel (IPCA ou IGP-M) do Quadro Resumo
    '''
    extracted = extrai_dado(indice_reajuste_dict,conteudo[0])
    if extracted['positivo']:   positivo = True
    return {'reajuste_positivo':positivo,'indice':extracted['indice'][0]}

def extrai_forma_pagamento(conteudo):
    '''
    Extrai a forma e local do pagamentos do aluguel e dos encargos mensais do Quadro Resumo
    '''

    cont_aluguel = conteudo[1] # Conteudo sobre aluguel
    cont_encargos = conteudo[2] # Conteudo sobre encargos

    extracted_aluguel = extrai_dado(forma_dict,cont_aluguel)
    extracted_encargos = extrai_dado(forma_dict,cont_encargos)

    return {'pagamento_aluguel': nlp(extracted_aluguel['meio'][0])[3:-1].text,
            'data_pagamento_aluguel': extracted_aluguel['dia'],
            'pagamento_encargos': nlp(extracted_encargos['meio'][0])[3:-1].text,
            'data_pagamento_encargos': extracted_encargos['dia']}

def extrai_garantia(conteudo,clausula_garantia):
    '''
    Extrai forma da garantia do Quadro Resumo e da Cláusula de Garantia
    (entende que a forma da garantia esta descrita até a ',')
    '''

    doc = nlp(conteudo[0])[2:]
    matcher = Matcher(nlp.vocab)
    for padrao in garantia_dict.keys():
        matcher.add(padrao,garantia_dict[padrao])
    matches = matcher(doc)

    extracted = []
    for match_id, start, end in matches:
        span = doc[start : end-1]
        extracted.append(span.text)

    extracted2 = extrai_dado({'valor_garantia':[[{'ORTH': 'R$'}, {'POS': 'NUM'}]]},clausula_garantia[0])
    return {'garantia': extracted[-1], 'valor_garantia':extracted2['valor_garantia']}

def extrai_inicio(conteudo):
    '''
    Extrai tipo do contrato, locataria, fiadores do Início do contrato
    '''
    ret_dict = {}
    struct = split_regex_list(abc_list_regex,conteudo[0])
    
    ret_dict['tipico'] = not ('atípico' in struct[0].lower()) # Checa se é típico ou atípico
    locataria = re.search(r'([A-ZÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ’]+(\s|\,|\.|\&)*)+', struct[2]).group(0).strip()
    if locataria[-1] == ',':    locataria = locataria[:-1]
    ret_dict['locataria'] = locataria

    # Puxar fiadores

    return ret_dict

def extrai_dados_multa(conteudo):
    '''
    Extrai dados da multa da cláusula de multa
    '''

    # rescisão antecipada
    res_ant = extrai_dado(rescisao_antecipada_dict,conteudo['rescisao_antecipada'][0])
    if res_ant['proporcional']: prop = True

    # rescisão inadimplência
    res_ina = extrai_dado(inadimplencia_dict,conteudo['inadimplencia'][0])
    
    return {'aviso_previo': res_ant['aviso_previo'],'multa_rescisao_antecipado':res_ant['multa_rescisao_antecipada'], 'proporcional': prop,
            'juros_ao_mes': res_ina['juros_ao_mes'],'multa_inadimplencia': res_ina['multa_inadimplencia'], 'prazos_multas': res_ina['prazos_multas']}


    
def extrai_tudo(intro ,qr, multa, garantia, data_assinatura):
    '''
    Responsável por chamar todas funções de estração de uma vez
    '''

    extracted_all = dict()

    extracted_all.update(extrai_inicio(intro))
    extracted_all.update(extrai_imovel(qr['imóvel']))
    extracted_all.update(extrai_prazo(qr['prazo']))
    extracted_all.update(extrai_valores(qr['valor']))
    extracted_all.update(extrai_indice_reajuste(qr['reajuste']))
    extracted_all.update(extrai_forma_pagamento(qr['forma']))
    extracted_all.update(extrai_garantia(qr['garantia'],garantia))
    extracted_all.update(extrai_dados_multa(multa))
    extracted_all.update({'data_assinatura': padroniza_data(data_assinatura.split(',')[1])})

    return extracted_all

def mostrar_dados_contrato(nome, dados):
    '''
    Mostra de maneira mais clara os dados extraidos da função extrai_tudo()
    Função para debug
    '''
    print('Contrato {}\n==================================\n'.format(nome))
    for key, value in dados.items():
        print('--------------------------------------------------------------------------')
        if isinstance(value, list) and value:
            if isinstance(value[0], dict):
                print('descontos:')
                for item in value:
                    print('                 ----------------------------------------------')
                    for key, value in item.items():
                        print('                 ',key,':   ',value)
                    print('                 ----------------------------------------------')
            else:
                print(key,':   ',value) 
        else:
            print(key,':   ',value)
        print('--------------------------------------------------------------------------\n')


##################################################################################

# Funções para tratar os dados

def padroniza_data(data):
    '''
    Padroniza datas em geral para o padrão dd/mm/aaaa
    '''
    meses = {'janeiro':'01','fevereiro':'02','março':'03','abril':'04','maio':'05','junho':'06','julho':'07','agosto':'08','  setembro':'09',         'outubro':'10','novembro':'11','dezembro':'12'}

    data = str(data).replace('º','')
    splitted = data.split()

    if len(splitted) == 1: # casos 01/01/2020, 1/02/2020, 1/1/2020, dezembro/2020
        bar_split = data.split('/')
        if len(bar_split) == 2:
            dia = '01'
            if bar_split[0].isalpha():  mes = meses[bar_split[0].lower()]
            if bar_split[0].isdigit():
                if len(bar_split[0]) == 1:  mes = '0' + bar_split[0]
                else:   mes = bar_split[0]
            if len(bar_split[1]) == 2:  ano = '20'+ bar_split[1]
            else:   ano = bar_split[1]
            p_data = dia+'/'+mes+'/'+ano
        if len(bar_split) == 3:
            if len(bar_split[0]) == 1:  dia = '0'+ bar_split[0]
            else:   dia = bar_split[0]
            if bar_split[1].isalpha():  mes = meses[bar_split[1].lower()]
            if bar_split[1].isdigit():
                if len(bar_split[1]) == 1:  mes = '0' + bar_split[1]
                else:   mes = bar_split[1]
            if len(bar_split[2]) == 2:  ano = '20'+ bar_split[2]
            else:   ano = bar_split[2]
            p_data = dia+'/'+mes+'/'+ano
    elif len(splitted) == 5:
        space_split = data.split()
        if len(space_split[0]) == 1:  dia = '0'+ space_split[0]
        else:   dia = space_split[0]
        if space_split[2].isalpha():  mes = meses[space_split[2].lower()]
        if space_split[2].isdigit():
            if len(space_split[2]) == 1:  mes = '0' + space_split[2]
            else:   mes = space_split[2]
        if len(space_split[4]) == 2:  ano = '20'+ space_split[4]
        else:   ano = space_split[4]
        p_data = dia+'/'+mes+'/'+ano

    return p_data


def soma_data(data, prazo):
    '''
    Soma uma data no formato padrão e soma com um prazo no formato exemplo: (8,'meses')
    '''
    # usar 31, 30 ou 28 fevereiro
    splitted_data = data.split('/')
    if prazo[1] == 'meses':
        if splitted_data[1] == '12':    years = prazo[0] // 12
        else:   years = (prazo[0] + int(splitted_data[1])) // 12
        months = (prazo[0]-(years*12))
        diff = months+int(splitted_data[1])
        if diff>12:
            months-=12
            years+=1

        if (int(splitted_data[1])+months) == 0:
            splitted_data[1] = '12'
            years-=1
            splitted_data[2] = str(int(splitted_data[2])+years)
            # data = splitted_data[0]+'/'+splitted_data[1]+'/'+str(int(splitted_data[2]))
        else:
            splitted_data[1] = str(int(splitted_data[1])+months)
            splitted_data[2] = str(int(splitted_data[2])+years)
            # data = splitted_data[0]+'/'+splitted[1]+'/'+str(int(splitted_data[2])+years)

        if int(splitted_data[0])>28 and int(splitted_data[1]) == 2:
            splitted_data[0] = '28'
        elif  int(splitted_data[0])==31 and (int(splitted_data[1]) in [4,6,9,11]):
            splitted_data[0] = '30'


        data =  splitted_data[0]+'/'+splitted_data[1]+'/'+splitted_data[2]
    if prazo[1] == 'anos':
        data = splitted_data[0]+'/'+splitted_data[1]+'/'+str(int(splitted_data[2])+prazo[0])
    return padroniza_data(data)

def tira_1_dia(data):
    '''
    Retira 1 dia da data
    Utilizada para cálculo das datas de desconto
    '''
    splitted_data = data.split('/')
    if splitted_data[0] == '01':
        splitted_data[1] = int(splitted_data[1])-1
        if splitted_data[1] == 2:
            splitted_data[0] = '28'
        elif splitted_data[1] == 0:
            splitted_data[0] = '31'
            splitted_data[1] = 12
            splitted_data[2] = str(int(splitted_data[2])-1)
        elif splitted_data[1] in [1,3,5,7,8,10,12]:
            splitted_data[0] = '31'
        else:
            splitted_data[0] = '30'
        return padroniza_data(splitted_data[0]+'/'+str(splitted_data[1])+'/'+splitted_data[2])
    else:
        splitted_data[0] = int(splitted_data[0])-1
        return padroniza_data(str(splitted_data[0])+'/'+splitted_data[1]+'/'+splitted_data[2])


def padroniza_imovel(imovel_dict):
    '''
    Padroniza os dados do imóvel para entrada do Salesforce
    '''

    t_imovel_dict = imovel_dict

    if imovel_dict['tipo_imovel'] == 'Escritório':

        # padronizando andar
        if imovel_dict['andar']:    t_imovel_dict['andar'] = int(t_imovel_dict['andar'][0].split()[0].replace('º',''))
        else:   t_imovel_dict['andar'] = 'Não encontrado'

        # padronizando pavimento ou torre
        if imovel_dict['torre_docas']:
            pav_tor_splitted = t_imovel_dict['torre_docas'][0].lower().split()
            if 'pavimento' in pav_tor_splitted:
                if pav_tor_splitted.index('pavimento') == 0:
                    t_imovel_dict['torre_docas'] = pav_tor_splitted[1].replace('º','')
                elif pav_tor_splitted.index('pavimento') == 1:
                    t_imovel_dict['torre_docas'] = pav_tor_splitted[0].replace('º','')

            if 'torre' in pav_tor_splitted:
                if pav_tor_splitted.index('torre') == 0:
                    t_imovel_dict['torre_docas'] = pav_tor_splitted[1].replace('º','')
                elif pav_tor_splitted.index('torre') == 1:
                    t_imovel_dict['torre_docas'] = pav_tor_splitted[0].replace('º','')
        else:   t_imovel_dict['torre_docas'] = 'Não encontrado'

    if imovel_dict['tipo_imovel'] == 'Galpão Logístico':

        # padronizando docas
        if imovel_dict['docas']:    t_imovel_dict['docas'] = int(t_imovel_dict['docas'][0].split()[0])
        else:   t_imovel_dict['docas'] = 'Não encontrado'

        # padronizando galpão (seria bom checar outros....)
        if imovel_dict['galpao']:    t_imovel_dict['galpao'] = int(t_imovel_dict['galpao'][0].split()[1])
        else:   t_imovel_dict['galpao'] = 'Não encontrado'



    # padronizando área
    if imovel_dict['area']: 
        meta  = t_imovel_dict['area'][0].replace('.','').replace('m²','').replace(' ','').replace(',','.')
        t_imovel_dict['area'] = float(meta)
    else:   t_imovel_dict['area'] = 'Não encontrado'

    # padronizando vagas
    if imovel_dict['vagas']:    t_imovel_dict['vagas'] = int(t_imovel_dict['vagas'][0].split()[0])
    else:   t_imovel_dict['vagas'] = 'Não encontrado'

    # pegando nome
    if imovel_dict['nome']:    t_imovel_dict['nome'] = t_imovel_dict['nome'][0]
    else:   t_imovel_dict['nome'] = 'Não encontrado'



    return t_imovel_dict


def padroniza_prazo(prazo_dict):
    '''
    Padroniza dados do prazo para entrada no Salesforce
    '''
    t_prazo_dict = {}
    meses = ['mes','mês','meses']
    anos = ['ano','anos']
    for txt in prazo_dict['prazo'][0].split():
        if txt.isdigit():   temp = int(txt)
        if txt in meses:    t_prazo_dict['prazo'] = (temp,'meses')
        if txt in anos: t_prazo_dict['prazo'] = (temp,'anos')
    if not (prazo_dict['data_inicial'] == 'entrega_chaves'):
        t_prazo_dict['inicio_vigencia'] = padroniza_data(prazo_dict['data_inicial'])
        t_prazo_dict['fim_vigencia'] = soma_data(t_prazo_dict['inicio_vigencia'],t_prazo_dict['prazo'])
    else:
        t_prazo_dict['inicio_vigencia'] = 'Entrega de Chaves'
        t_prazo_dict['fim_vigencia'] = None
    return t_prazo_dict


def padroniza_valores(valores_dict):
    '''
    Padroniza dados de valores para entrada no Salesforce
    '''
    escada_desconto = False
    t_valores_dict = valores_dict

    t_valores_dict['valor_aluguel'] = t_valores_dict['valor_aluguel'][0]
    t_valores_dict['data_reajuste'] = padroniza_data(t_valores_dict['data_reajuste'])
    if t_valores_dict['periodo_carencia']:
        t_valores_dict['periodo_carencia'] = int(t_valores_dict['periodo_carencia'][0].split()[0])
    if t_valores_dict['data_inicio_carencia'] and t_valores_dict['data_inicio_carencia'] != 'entrega_chaves':
        t_valores_dict['data_inicio_carencia'] = padroniza_data(t_valores_dict['data_inicio_carencia'])
    for desc_index in range(len(t_valores_dict['descontos'])):
        if len(t_valores_dict['descontos'][desc_index]['periodo']) == 1:
            escada_desconto = True # Considera escada de desconto sempre
        else:
            t_valores_dict['descontos'][desc_index]['data_inicio_desconto'] = padroniza_data(t_valores_dict['descontos'][desc_index]['periodo'][0])
            t_valores_dict['descontos'][desc_index]['data_final_desconto'] = padroniza_data(t_valores_dict['descontos'][desc_index]['periodo'][1])
    
    t_valores_dict['escada_desconto'] = escada_desconto

    return t_valores_dict


def padroniza_forma(forma_dict):
    '''
    Padroniza dados de forma de pagamento para entrada no Salesforce
    '''
    for i in forma_dict['data_pagamento_aluguel'][0].replace('º','').split():
        if i.isdigit():
            forma_dict['data_pagamento_aluguel'] = int(i)
    for i in forma_dict['data_pagamento_encargos'][0].replace('º','').split():
        if i.isdigit():
            forma_dict['data_pagamento_encargos'] = int(i)
    
    if 'boleto' in forma_dict['pagamento_aluguel'].lower():
        forma_dict['pagamento_aluguel'] = 'Boleto'

    if 'boleto' in forma_dict['pagamento_encargos'].lower():
        forma_dict['pagamento_encargos'] = 'Boleto'
 
    return forma_dict

def padroniza_garantia(garantia_dict):
    '''
    Padroniza dados da garantia para entrada no Salesforce
    '''
    if 'fiadores' in garantia_dict['garantia'].lower().split():
        garantia_dict['garantia'] = 'Fiador PF'
    elif 'bancária' in garantia_dict['garantia'].lower().split():
        garantia_dict['garantia'] = 'Fiança bancária'
    elif 'caução' in garantia_dict['garantia'].lower().split():
        garantia_dict['garantia'] = 'Depósito caução'

    if garantia_dict['valor_garantia']: garantia_dict['valor_garantia'] = garantia_dict['valor_garantia'][0]

    return garantia_dict

def padroniza_multa(multa_dict):
    '''
    Padroniza dados de multa para entrada no Salesforce
    '''
    for i in multa_dict['aviso_previo'][0].split():
        if i.isdigit():
            multa_dict['aviso_previo'] = int(i)
    for i in multa_dict['multa_rescisao_antecipado'][0].split():
        if i.isdigit():
            multa_dict['multa_rescisao_antecipado'] = int(i)
    for i in multa_dict['juros_ao_mes'][0].split():
        if i[-1] == '%':
            multa_dict['juros_ao_mes'] = i
    for mi in range(len(multa_dict['multa_inadimplencia'])):
        for i in multa_dict['multa_inadimplencia'][mi].split():
            if i[-1] == '%':
                multa_dict['multa_inadimplencia'][mi] = i
    return multa_dict  

def prazo_desconto(prazo_desconto):
    '''
    Caso desconto esteja em prazo, retorna no padrão de prazos
    Exemplo: 1 ano do aluguel ---> (1,'anos')
    '''
    splitted = prazo_desconto.split()
    if len(splitted) == 5:
        valor = int(prazo_desconto[0])
        if splitted[2] == 'ano':    return (valor,'anos')
        elif  splitted[2] == 'mês':   return (valor,'meses')
        else: return prazo_desconto
    else:
        return prazo_desconto

def extrai_tudo_padronizado(intro ,qr, multa, garantia, data_assinatura, data_entrega_de_chaves = None):
    '''
    Responsável por extrair e tratar todos os dados
    Não depende da função extrai_tudo()
    '''

    extracted_all = dict()

    extracted_all.update(extrai_inicio(intro))
    extracted_all.update(padroniza_imovel(extrai_imovel(qr['imóvel'])))
    extracted_all.update(padroniza_prazo(extrai_prazo(qr['prazo'])))
    extracted_all.update(padroniza_valores(extrai_valores(qr['valor'])))
    extracted_all.update(extrai_indice_reajuste(qr['reajuste']))
    extracted_all.update(padroniza_forma(extrai_forma_pagamento(qr['forma'])))
    extracted_all.update(padroniza_garantia(extrai_garantia(qr['garantia'],garantia)))
    extracted_all.update(padroniza_multa(extrai_dados_multa(multa)))
    extracted_all.update({'data_assinatura': padroniza_data(data_assinatura.split(',')[1])})

    # caso receba o input sobre a entrega de chaves
    if data_entrega_de_chaves is not None:
        if extracted_all['inicio_vigencia'] == 'Entrega de Chaves':
            extracted_all['inicio_vigencia'] = padroniza_data(data_entrega_de_chaves)
            extracted_all['fim_vigencia'] = soma_data(extracted_all['inicio_vigencia'],extracted_all['prazo'])
        if extracted_all['data_inicio_carencia'] == 'entrega_chaves':
            extracted_all['data_inicio_carencia'] = padroniza_data(data_entrega_de_chaves)
            extracted_all['data_fim_carencia'] = soma_data(extracted_all['data_inicio_carencia'],(extracted_all['periodo_carencia'],'meses'))

    if extracted_all['data_inicio_carencia'] != 'entrega_chaves' and extracted_all['data_inicio_carencia']:
        extracted_all['data_fim_carencia'] = soma_data(extracted_all['data_inicio_carencia'],(extracted_all['periodo_carencia'],'meses'))


    # cuidar do formato dos descontos
    is_good_format = True # checa se o formato do periodo de desconto é ex: '2º (segundo) ano de locação'
    # tratar descontos que não tenham data inicio e fim definidos
    if extracted_all['descontos']  and 'data_inicio_desconto' not in extracted_all['descontos'][0].keys() and extracted_all['inicio_vigencia'] != 'Entrega de Chaves':
        for i in range(len(extracted_all['descontos'])):
            if i == 0:
                extracted_all['descontos'][i]['data_inicio_desconto'] = extracted_all['inicio_vigencia']
                prazo  = prazo_desconto(extracted_all['descontos'][i]['periodo'][0])
                if type(prazo) is tuple:
                    extracted_all['descontos'][i]['data_final_desconto'] = soma_data(extracted_all['inicio_vigencia'],prazo)
                else:
                    is_good_format = False
            elif is_good_format:
                extracted_all['descontos'][i]['data_inicio_desconto'] = extracted_all['descontos'][i-1]['data_final_desconto']
                prazo  = prazo_desconto(extracted_all['descontos'][i]['periodo'][0])
                extracted_all['descontos'][i]['data_final_desconto'] = soma_data(extracted_all['descontos'][0]['data_inicio_desconto'],prazo)
    for i in range(len(extracted_all['descontos'])): # tira 1 dia da data final
        if 'data_inicio_desconto' in extracted_all['descontos'][i].keys() and i != len(extracted_all['descontos'])-1:
            extracted_all['descontos'][i]['data_final_desconto'] = tira_1_dia(extracted_all['descontos'][i]['data_final_desconto'])


    return extracted_all


def do_all(path_to_pdf, data=None):
    '''
    Função responsável por estruturar o contrato, extrair os dados e também trata-los
    '''

    structured = clausulas2dict(clause_regex, two_numbered_list_regex, keywords_contrato, pdf2string(path_to_pdf), True)
    qr = clausulas2dict(qr_topic_regex,three_numbered_list_regex,keywords_quadroresumo,structured['resumo'],False)
    multa = multa2dict(structured['multa'])
    text_intro = ''.join(structured['intro'])
    text_garantia = ''.join(structured['garantia'])
    text_inadimplencia = ''.join(multa['inadimplencia'])
    text_antecipada = ''.join(multa['rescisao_antecipada'])
    text_qr = ''
    for key in qr.keys():
        text_qr+=str(key).upper()
        text_qr+='\n\n'
        text_qr+=str(qr[key])
    # aqui se poderia formatar melhor para exibir de uma maneira mais bonita nos botões de consulta
    final = {
        'big_text': {
            'intro':text_intro,
            'qr': text_qr,
            'multa': 'INADIMPLÊNCIA:\n\n'+text_inadimplencia+'\n\nRESCISÃO-ANTECIPADA\n\n'+text_antecipada ,
            # 'multa' : multa,
            'garantia': text_garantia
        },
        'raw' : extrai_tudo(structured['intro'], qr, multa, structured['garantia'], structured['data_assinatura']),
        'tratado' : extrai_tudo_padronizado(structured['intro'], qr, multa, structured['garantia'], structured['data_assinatura'],data_entrega_de_chaves=data)
    }
    return final
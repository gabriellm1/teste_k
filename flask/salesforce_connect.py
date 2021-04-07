from simple_salesforce import Salesforce
from simple_salesforce import SFType
from simple_salesforce import *
from datetime import datetime
from dateutil.relativedelta import *
import time



# sf = Salesforce(instance=instance, session_id=session_id)

def get_locatario_id(sf,nome):
        '''
        Retorna o id do Locatário pelo nome
        '''
        try:
                locatario = sf.query("SELECT id from Account where Name ='"+nome+"'")
                return locatario['records'][0]['Id']
        except Exception:
                raise "Locatario não encontrado"

def get_imovel_id(sf,nome):
        '''
        Retorna o id do Imóvel pelo nome
        '''
        try:
                imovel = sf.query("SELECT id, Name from Imovel__c where Name ='"+nome+"'")
                return imovel['records'][0]['Id']
        except Exception:
                raise "Imóvel não encontrado"




# contratos_re__c = SFType('Contrato_RE__c',session_id,instance)
# desconto__c = SFType('Desconto__c',session_id,instance)

################ Checa colunas de um Objeto ###########################
# desc = sf.contratos_re__c.describe()  

# # Below is what you need
# field_names = [field['name'] for field in desc['fields']]
# soql = "SELECT {} FROM Contrato_RE__c".format(','.join(field_names))
# results = sf.query_all(soql)
# print(results)
# for col in results['records'][0].keys():
#         print(col)
#######################################################################


def adiciona_contrato(sf,contratos_re__c,desconto__c,dados):
        '''
        Adiciona contrato no Salesforce
        '''

        if dados['tipico']:
                dados['tipico'] = 'Típico'
        else:
                dados['tipico'] = 'Atípico'

        if dados['proporcional']:
                dados['proporcional'] = 'Proporcional'
        else:
                dados['proporcional'] = 'Não proporcional'

        imovel = get_imovel_id(sf,dados['nome'])
        time.sleep(3)
        locataria = get_locatario_id(sf,dados['locataria'])
        time.sleep(3)

        data = {
                'inicio_vigencia__c' : str(datetime.strptime(dados['inicio_vigencia'],'%d/%m/%Y'))[0:10],
                'termino_vigencia__c': str(datetime.strptime(dados['fim_vigencia'],'%d/%m/%Y'))[0:10],
                'Revisional__c': str((datetime.strptime(dados['inicio_vigencia'],'%d/%m/%Y') + relativedelta(years=+3)))[0:10],
                'Imovel__c': imovel,
                'locatario__c': locataria,
                'valor_aluguel__c': (dados['valor_aluguel'].replace('.','').replace('R$','').replace(' ',''))[:-3],
                'Data_Base_Reajuste__c': str(datetime.strptime(dados['data_reajuste'],'%d/%m/%Y'))[0:10],
                'Dia_do_pagamento__c': dados['data_pagamento_aluguel'],
                'multa_por_inadimplencia__c': dados['multa_inadimplencia'].replace('%',''),
                'juros_ao_mes__c':dados['juros_ao_mes'].replace('%',''),
                'Indice_de_Correcao__c': dados['indice'].replace('-',''),
                'Area__c': dados['area'],
                'Reajuste_Pro_rata__c': True, # padrão
                'Reajuste_positivo__c': dados['reajuste_positivo'],
                'Data_assinatura_do_contrato__c': str(datetime.strptime(dados['data_assinatura'],'%d/%m/%Y'))[0:10],
                'Aviso_previo_Recisao_antecipada__c': dados['aviso_previo'],
                'Tipo_de_contrato__c': dados['tipico'],
                'Forma_de_pagamento__c': dados['pagamento_aluguel'],
                'Multa_rescisao_antecipada__c': dados['multa_rescisao_antecipado'],
                'Tipo_multa_rescisao_antecipada__c': dados['proporcional']
                
        }
        
        if dados['data_inicio_carencia']:
                data['Inicio_da_Carencia__c'] = str(datetime.strptime(dados['data_inicio_carencia'],'%d/%m/%Y'))[0:10]
                data['Fim_da_Carencia__c'] = str(datetime.strptime(dados['data_fim_carencia'],'%d/%m/%Y'))[0:10]

        # Adiciona Contrato
        id = contratos_re__c.create(data)['id']
        time.sleep(3)
        first = True

        # Adiciona Descontos
        for desc in dados['descontos']:
                
                data_desconto = {}
                if first: 
                        first = False
                        data_desconto['Data_Base_Reajuste__c'] = str(datetime.strptime(desc['data_inicio_desconto'],'%d/%m/%Y'))[0:10]
                else:
                        data_desconto['Data_Base_Reajuste__c'] = str(datetime.strptime(dados['data_reajuste'],'%d/%m/%Y'))[0:10]

                data_desconto['inicio_vigencia__c'] = str(datetime.strptime(desc['data_inicio_desconto'],'%d/%m/%Y'))[0:10]
                data_desconto['termino_vigencia__c'] = str(datetime.strptime(desc['data_final_desconto'],'%d/%m/%Y'))[0:10]
                data_desconto['Contrato_RE__c'] = id
                data_desconto['Valor_do_desconto__c'] = desc['aluguel'].replace('.','').replace('R$','').replace(' ','')[:-3]
                data_desconto['Escada_de_Desconto__c'] = 'Sim' # padrão
                # data base usar normal nos outros
                desconto__c.create(data_desconto)
        
        return id



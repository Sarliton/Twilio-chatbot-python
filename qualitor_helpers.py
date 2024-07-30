import os
import zeep
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# URL do WSDL do serviço Qualitor
WSDL_URL = 'https://sac-nettelecom.com.br/qualitor_prd/ws/services/service.php?wsdl=WSTicket'

client = zeep.Client(wsdl=WSDL_URL)

def login():
    login = os.getenv('QUALITOR_LOGIN')
    password = os.getenv('QUALITOR_PASSWORD')
    company = os.getenv('QUALITOR_COMPANY')
    response = client.service.login(login=login, passwd=password, company=company)
    print(f"Token de autenticação: {response}")
    return response

def get_ticket_data(auth, ticket_id):
    xml_value = f'''<?xml version="1.0" encoding="ISO-8859-1"?>
    <wsqualitor>
      <contents>
        <data>
          <cdchamado>{ticket_id}</cdchamado>
          <campos>cdchamado,nmtitulochamado,dataultimoacompanhamento,nmsituacao</campos>
        </data>
      </contents>
    </wsqualitor>
    '''
    print(f"XML enviado para getTicketData: {xml_value}")
    response = client.service.getTicketData(auth=auth, xmlValue=xml_value)
    print(f"Resposta do getTicketData: {response}")
    return response

def get_tickets(auth, client_name):
    xml_value = f'''<?xml version="1.0" encoding="ISO-8859-1"?>
    <wsqualitor>
      <contents>
        <data>
          <cdcliente>{client_name}</cdcliente>
        </data>
      </contents>
    </wsqualitor>
    '''
    response = client.service.getTicket(auth=auth, xmlValue=xml_value)
    print(f"Resposta do getTickets: {response}")
    return response

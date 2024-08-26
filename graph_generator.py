import os
import openpyxl
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from qualitor_helpers import login, get_tickets
import xml.etree.ElementTree as ET

# Função principal para gerar relatório
def generate_report(client_code, report_type, month=None):
    auth_token = login()
    
    if report_type == 'mensal' and month:
        start_date = datetime(datetime.now().year, month, 1)
        end_date = datetime(datetime.now().year, month, 1).replace(day=28) + pd.offsets.MonthEnd(1)
        tickets = fetch_tickets(auth_token, client_code, start_date, end_date)
        excel_path = generate_excel(tickets, report_type, month)
        graph_path = generate_graph(tickets, report_type, month)
    elif report_type == 'anual':
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime(datetime.now().year, 12, 31)
        tickets = fetch_tickets(auth_token, client_code, start_date, end_date)
        excel_path = generate_excel(tickets, report_type)
        graph_path = generate_graph(tickets, report_type)
    else:
        raise ValueError('Parâmetros inválidos para geração de relatório.')
    
    return excel_path, graph_path

def fetch_tickets(auth_token, client_code, start_date, end_date):
    tickets_response = get_tickets(auth_token, client_code)
    root = ET.fromstring(tickets_response)
    items = root.findall('.//dataitem')
    
    tickets = []
    for item in items:
        dtchamado_text = item.find('dtchamado').text
        dtchamado = datetime.strptime(dtchamado_text, '%Y-%m-%d %H:%M')
        if start_date <= dtchamado <= end_date:
            tickets.append({
                'Código do Chamado': item.find('cdchamado').text,
                'Título do Chamado': item.find('nmtitulochamado').text,
                'Situação': item.find('nmsituacao').text,
                'Data de Criação': dtchamado
            })
    return tickets

def generate_excel(tickets, report_type, month=None):
    df = pd.DataFrame(tickets)
    if df.empty:
        raise ValueError('Nenhum chamado encontrado no período especificado.')
    
    file_name = f'relatorio_{report_type}'
    if month:
        file_name += f'_{month}'
    file_name += '.xlsx'
    excel_path = os.path.join('reports', file_name)
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    df.to_excel(excel_path, index=False)
    return excel_path

def generate_graph(tickets, report_type, month=None):
    df = pd.DataFrame(tickets)
    if df.empty:
        raise ValueError('Nenhum chamado encontrado no período especificado para gerar gráfico.')
    
    if report_type == 'mensal':
        df['Dia'] = df['Data de Criação'].dt.day
        summary = df.groupby('Dia').size()
        plt.figure(figsize=(10,6))
        summary.plot(kind='bar', color='skyblue')
        plt.title(f'Chamados por Dia - Mês {month}')
        plt.xlabel('Dia do Mês')
        plt.ylabel('Número de Chamados')
        plt.tight_layout()
        file_name = f'grafico_mensal_{month}.png'
    elif report_type == 'anual':
        df['Mês'] = df['Data de Criação'].dt.month
        summary = df.groupby('Mês').size()
        plt.figure(figsize=(10,6))
        summary.plot(kind='bar', color='skyblue')
        plt.title('Chamados por Mês - Ano Atual')
        plt.xlabel('Mês')
        plt.ylabel('Número de Chamados')
        plt.tight_layout()
        file_name = 'grafico_anual.png'
    else:
        raise ValueError('Tipo de relatório desconhecido para geração de gráfico.')
    
    graph_path = os.path.join('reports', file_name)
    plt.savefig(graph_path)
    plt.close()
    return graph_path

def send_report_via_twilio(to_phone_number, excel_path, graph_path):
    from twilio.rest import Client
    from dotenv import load_dotenv

    load_dotenv()
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
    client = Client(account_sid, auth_token)

    # Presume-se que os arquivos estão disponíveis em um servidor acessível
    base_url = os.getenv('BASE_URL')  # URL base onde os arquivos estão hospedados
    excel_url = f'{base_url}/{excel_path}'
    graph_url = f'{base_url}/{graph_path}'

    message = client.messages.create(
        body='Segue o relatório solicitado.',
        from_=twilio_number,
        to=to_phone_number,
        media_url=[excel_url, graph_url]
    )

    return message.sid

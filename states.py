from abc import ABC, abstractmethod
from context import ConversationContext
from qualitor_helpers import login, get_ticket_data, get_tickets
import xml.etree.ElementTree as ET
from datetime import datetime
from db import get_db  
from graph_generator import generate_report, send_report_via_twilio

class ChatBot:
    def __init__(self):
        self.conversation_state = {}

    def handle_message(self, phone_number, message):
        if phone_number not in self.conversation_state:
            self.conversation_state[phone_number] = ConversationContext(StartState, phone_number)
        response = self.conversation_state[phone_number].request(message)
        return response

class State(ABC):
    def __init__(self, context):
        self.context = context

    @abstractmethod
    def handle_request(self, message):
        pass

    def transition_to(self, new_state_class):
        self.context.state = new_state_class(self.context)
        if hasattr(self.context.state, 'auto_respond'):
            auto_response = self.context.state.auto_respond()
            if auto_response is None:
                auto_response = []
            return auto_response
        return []

class StartState(State):
    def handle_request(self, message):
        if message.lower() in ['ola', 'oi', 'oi, tudo bem?', 'ola, tudo bem?', "olá"]:
            return ['Olá! Bem-vindo à nossa empresa! Por favor, digite seu número de contrato.']
        else:
            client_info = self.verify_contract(message.strip())
            if client_info:
                client_name, client_code = client_info
                self.context.client_name = client_name
                self.context.client_code = client_code
                auto_responses = self.transition_to(SelectOptionState)
                return [
                    f'Contrato verificado para {self.context.client_name}! Por favor, escolha uma opção:\n1. Ver chamados\n2. Gerar relatório'
                ] + auto_responses
            else:
                return ['Contrato não encontrado. Por favor, verifique e digite novamente.']

    def verify_contract(self, contract_number):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT Nome, Cliente FROM clientes WHERE contrato=?", (contract_number,))
        result = cursor.fetchone()
        return (result[0], result[1]) if result else None

class SelectOptionState(State):
    def handle_request(self, message):
        option = message.strip()
        if option == '1':
            auto_responses = self.transition_to(GetCallsState)
            return auto_responses
        elif option == '2':
            auto_responses = self.transition_to(ChooseReportTypeState)
            return ['Você deseja um relatório mensal ou anual?\n1. Mensal\n2. Anual'] + auto_responses
        else:
            return ['Opção inválida. Por favor, escolha uma opção:\n1. Ver chamados\n2. Gerar relatório']

class GetCallsState(State):
    def handle_request(self, message):
        return self.auto_respond()

    def auto_respond(self):
        response_messages = ["Por favor, aguarde enquanto obtemos os chamados..."]

        auth_token = login()
        tickets_response = get_tickets(auth_token, self.context.client_code)
        root = ET.fromstring(tickets_response)
        items = root.findall('.//dataitem')

        if items:
            sorted_items = sorted(
                items,
                key=lambda x: datetime.strptime(
                    x.find('dtchamado').text if x.find('dtchamado') is not None else '1900-01-01 00:00',
                    '%Y-%m-%d %H:%M'
                ),
                reverse=True
            )[:10]
            chamados_msg = "\n".join([
                f"{item.find('cdchamado').text}: {item.find('nmtitulochamado').text}"
                for item in sorted_items
            ])
            response_messages.append(chamados_msg)
        else:
            response_messages.append("Não há chamados registrados.")

        response_messages.append("Por favor, digite o número do chamado desejado ou digite 'menu' para voltar ao menu principal.")
        self.transition_to(SelectCallState)
        return response_messages

class SelectCallState(State):
    def handle_request(self, message):
        if message.strip().lower() == 'menu':
            auto_responses = self.transition_to(SelectOptionState)
            return ['Retornando ao menu principal...'] + auto_responses
        try:
            call_number = int(message.strip())
            self.context.set_call_number(call_number)
            auto_response = self.transition_to(GetCallUpdatesState)
            return [
                'Número de chamado verificado!\nPor favor, aguarde enquanto obtemos as atualizações...'
            ] + auto_response
        except ValueError:
            return ['Número inválido. Por favor, digite um número de chamado válido ou digite "menu" para voltar ao menu principal.']

class GetCallUpdatesState(State):
    def handle_request(self, message):
        return self.auto_respond()

    def auto_respond(self):
        updates = self.get_call_updates(self.context.call_number)
        response_messages = []
        if updates:
            response_messages.append(f"Últimas atualizações do chamado {self.context.call_number}:\n{updates}")
        else:
            response_messages.append("Não há atualizações disponíveis para este chamado.")
        response_messages.append("Deseja:\n1. Ver outro chamado\n2. Voltar ao menu principal\n3. Encerrar a sessão")
        self.transition_to(PostCallOptionsState)
        return response_messages

    def get_call_updates(self, call_number):
        auth_token = login()
        updates_response = get_ticket_data(auth_token, call_number)
        root = ET.fromstring(updates_response)
        item = root.find('.//dataitem')

        if item:
            cdchamado = item.find('cdchamado').text or 'N/A'
            nmtitulochamado = item.find('nmtitulochamado').text or 'N/A'
            dataultimoacompanhamento = item.find('dataultimoacompanhamento').text or 'N/A'
            dsultimoacompanhamento = item.find('dsultimoacompanhamento').text or 'N/A'
            return (
                f"Chamado {cdchamado}: {nmtitulochamado}\n"
                f"Última atualização em {dataultimoacompanhamento}:\n{dsultimoacompanhamento}"
            )
        else:
            return None

class PostCallOptionsState(State):
    def handle_request(self, message):
        option = message.strip()
        if option == '1':
            auto_responses = self.transition_to(GetCallsState)
            return auto_responses
        elif option == '2':
            auto_responses = self.transition_to(SelectOptionState)
            return ['Retornando ao menu principal...'] + auto_responses
        elif option == '3':
            auto_responses = self.transition_to(EndState)
            return ['Encerrando a sessão. Obrigado!']
        else:
            return ['Opção inválida. Por favor, escolha uma das opções abaixo:\n1. Ver outro chamado\n2. Voltar ao menu principal\n3. Encerrar a sessão']

class ChooseReportTypeState(State):
    def handle_request(self, message):
        option = message.strip()
        if option == '1':
            auto_responses = self.transition_to(SelectMonthState)
            return ['Por favor, digite o mês desejado (1-12):'] + auto_responses
        elif option == '2':
            self.context.report_type = 'anual'
            auto_responses = self.transition_to(GenerateReportState)
            return ['Gerando relatório anual. Por favor, aguarde...'] + auto_responses
        else:
            return ['Opção inválida. Por favor, escolha uma opção:\n1. Mensal\n2. Anual']

class SelectMonthState(State):
    def handle_request(self, message):
        try:
            month = int(message.strip())
            if 1 <= month <= 12:
                self.context.report_type = 'mensal'
                self.context.report_month = month
                auto_responses = self.transition_to(GenerateReportState)
                return [f'Gerando relatório do mês {month}. Por favor, aguarde...'] + auto_responses
            else:
                return ['Mês inválido. Por favor, digite um número entre 1 e 12:']
        except ValueError:
            return ['Entrada inválida. Por favor, digite um número entre 1 e 12:']

class GenerateReportState(State):
    def handle_request(self, message):
        return self.auto_respond()

    def auto_respond(self):
        report_type = self.context.report_type
        client_code = self.context.client_code
        phone_number = self.context.phone_number

        try:
            if report_type == 'mensal':
                month = self.context.report_month
                excel_path, graph_path = generate_report(client_code, report_type='mensal', month=month)
                month_name = datetime(1900, month, 1).strftime('%B').capitalize()
                send_report_via_twilio(phone_number, excel_path, graph_path)
                response = f'Relatório mensal de {month_name} gerado e enviado com sucesso!'
            elif report_type == 'anual':
                excel_path, graph_path = generate_report(client_code, report_type='anual')
                send_report_via_twilio(phone_number, excel_path, graph_path)
                response = 'Relatório anual gerado e enviado com sucesso!'
            else:
                response = 'Tipo de relatório desconhecido.'
        except Exception as e:
            print(f"Erro ao gerar ou enviar relatório: {e}")
            response = 'Ocorreu um erro ao gerar o relatório. Por favor, tente novamente mais tarde.'

        self.transition_to(SelectOptionState)
        return [response, 'Deseja realizar outra operação?\n1. Sim\n2. Não']

class EndState(State):
    def handle_request(self, message):
        return ['Atendimento concluído. Obrigado por usar nossos serviços!']

    def auto_respond(self):
        self.context.state = StartState(self.context)
        return []

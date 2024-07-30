class ConversationContext:
    def __init__(self, state_cls, phone_number, my_twilio_number):
        self.state = state_cls(self)  # Inicializa o estado passando a si mesmo como contexto
        self.phone_number = phone_number
        self.my_twilio_number = my_twilio_number
        self.contract_id = None
        self.client_name = None
        self.client_code = None
        self.call_number = None

    def set_contract_id(self, contract_id):
        self.contract_id = contract_id

    def set_call_number(self, call_number):
        self.call_number = call_number

    def request(self, message):
        response = self.state.handle_request(message)
        # Supondo que auto_respond possa retornar mensagens adicionais para serem processadas
        auto_response = self.state.auto_respond() if hasattr(self.state, 'auto_respond') else []
        return [response] + auto_response if isinstance(auto_response, list) else response

/**
 * Trade-off 4.3.4: Tratamento de Erros e Loading
 *
 * Estratégia escolhida: Mensagens ESPECÍFICAS com fallback para genérica
 *
 * Justificativa:
 * - Mensagens específicas ajudam o usuário a entender o problema
 * - Fallback genérico previne UI quebrada com erros inesperados
 * - Loading states em cada componente (não global)
 * - Estados vazios com mensagens orientadas à ação
 */

import axios from "axios";

const API_BASE_URL = "/api";

const client = axios.create({
	baseURL: API_BASE_URL,
	timeout: 30000,
	headers: {
		"Content-Type": "application/json",
	},
});

client.interceptors.response.use(
	(response) => response.data,
	(error) => {
		let errorMessage = "Erro desconhecido. Tente novamente.";

		if (error.response) {
			const status = error.response.status;
			const detail = error.response.data?.detail;

			switch (status) {
				case 404:
					errorMessage = detail || "Recurso não encontrado";
					break;
				case 500:
					errorMessage =
						"Erro no servidor. Por favor, tente novamente mais tarde.";
					break;
				case 503:
					errorMessage = "Serviço temporariamente indisponível";
					break;
				default:
					errorMessage = detail || `Erro HTTP ${status}`;
			}
		} else if (error.request) {
			errorMessage = "Sem conexão com o servidor. Verifique sua internet.";
		} else {
			errorMessage = error.message || errorMessage;
		}

		return Promise.reject(new Error(errorMessage));
	},
);

/**
 * API Service
 *
 * Trade-off 4.3.1: Estratégia de Busca/Filtro
 * Escolha: Opção A - Busca no servidor
 *
 * Justificativa:
 * - Dataset grande (1.1k operadoras)
 * - Paginação server-side já implementada
 * - Reduz carga no cliente (não precisa carregar todas operadoras)
 * - Busca no servidor é mais eficiente (índices do PostgreSQL)
 * - Evita transferir 1.1k registros só para filtrar no cliente
 *
 * Alternativa rejeitada:
 * - Busca no cliente: Só faria sentido com <100 registros
 * - Híbrido: Complexidade desnecessária para este caso
 */

const api = {
	async getOperadoras(page = 1, limit = 10, search = "") {
		const params = { page, limit };
		if (search) params.search = search;
		return await client.get("/operadoras", { params });
	},

	async getOperadora(cnpj) {
		return await client.get(`/operadoras/${cnpj}`);
	},

	async getOperadoraDespesas(cnpj) {
		return await client.get(`/operadoras/${cnpj}/despesas`);
	},

	async getEstatisticas() {
		return await client.get("/estatisticas");
	},
};

export default api;

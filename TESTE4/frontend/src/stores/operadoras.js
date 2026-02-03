/**
 * Trade-off 4.3.2: Gerenciamento de Estado
 * Escolha: Opção B - Pinia
 *
 * Justificativa:
 * - Aplicação com múltiplas views compartilhando dados (operadoras, estatísticas)
 * - Evita prop drilling entre componentes profundos
 * - Facilita cache de dados já carregados (evita requests duplicados)
 * - API moderna e type-safe do Pinia (melhor que Vuex)
 * - Composables seria suficiente para app simples, mas Pinia escala melhor
 */

import { defineStore } from "pinia";
import api from "../services/api";

export const useOperadorasStore = defineStore("operadoras", {
	state: () => ({
		operadoras: [],
		currentPage: 1,
		limit: 10,
		total: 0,
		totalPages: 0,
		loading: false,
		error: null,
		searchQuery: "",
		estatisticas: null,
		estatisticasLoading: false,
	}),

	actions: {
		async fetchOperadoras(page = 1, search = "") {
			this.loading = true;
			this.error = null;

			try {
				const response = await api.getOperadoras(page, this.limit, search);
				this.operadoras = response.data;
				this.currentPage = response.page;
				this.total = response.total;
				this.totalPages = response.total_pages;
				this.searchQuery = search;
			} catch (error) {
				this.error = error.message;
				this.operadoras = [];
			} finally {
				this.loading = false;
			}
		},

		async fetchEstatisticas() {
			this.estatisticasLoading = true;

			try {
				this.estatisticas = await api.getEstatisticas();
			} catch (error) {
				console.error("Erro ao carregar estatísticas:", error);
			} finally {
				this.estatisticasLoading = false;
			}
		},

		setPage(page) {
			this.currentPage = page;
			this.fetchOperadoras(page, this.searchQuery);
		},

		nextPage() {
			if (this.currentPage < this.totalPages) {
				this.setPage(this.currentPage + 1);
			}
		},

		prevPage() {
			if (this.currentPage > 1) {
				this.setPage(this.currentPage - 1);
			}
		},
	},
});

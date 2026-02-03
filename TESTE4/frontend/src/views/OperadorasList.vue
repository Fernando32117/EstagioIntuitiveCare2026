<template>
  <div>
    <div class="card" v-if="estatisticas && !estatisticasLoading">
      <h2 style="margin-bottom: 20px;">📊 Distribuição de Despesas por UF</h2>
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div class="search-bar">
      <input
        type="text"
        v-model="searchInput"
        @input="onSearchInput"
        placeholder="🔍 Buscar por CNPJ, Razão Social, Registro ANS ou Modalidade..."
      />
    </div>

    <div v-if="loading" class="loading">
      Carregando operadoras...
    </div>

    <div v-else-if="error" class="error">
      <strong>❌ Erro ao carregar operadoras</strong>
      {{ error }}
      <button @click="recarregar" class="btn btn-primary" style="margin-top: 12px;">
        Tentar Novamente
      </button>
    </div>

    <div v-else-if="operadoras.length === 0" class="empty-state">
      <p>Nenhuma operadora encontrada.</p>
      <p v-if="searchQuery" style="margin-top: 12px;">
        <button @click="limparBusca" class="btn btn-primary">
          Limpar Busca
        </button>
      </p>
    </div>

    <div v-else class="card">
      <h2 style="margin-bottom: 20px;">Operadoras ({{ total }} registros)</h2>
      
      <table>
        <thead>
          <tr>
            <th>Registro ANS</th>
            <th>CNPJ</th>
            <th>Razão Social</th>
            <th>Modalidade</th>
            <th>UF</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="operadora in operadoras" :key="operadora.registro_ans">
            <td>{{ operadora.registro_ans }}</td>
            <td>{{ operadora.cnpj || '-' }}</td>
            <td>{{ operadora.razao_social }}</td>
            <td>{{ operadora.modalidade || '-' }}</td>
            <td>{{ operadora.uf || '-' }}</td>
            <td>
              <button
                @click="verDetalhes(operadora)"
                class="btn btn-primary"
              >
                Ver Detalhes
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button @click="prevPage" :disabled="currentPage === 1">
          ← Anterior
        </button>
        <span>Página {{ currentPage }} de {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage === totalPages">
          Próxima →
        </button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * Trade-off 4.3.3: Performance da Tabela
 * 
 * Estratégia escolhida: Paginação server-side
 * 
 * Justificativa:
 * - Com 1.1k operadoras, paginação server-side é mais eficiente
 * - Renderiza apenas 10-20 registros por vez
 * - Não precisa de virtual scroll (renderização simples é suficiente)
 * - Browser renderiza tabela pequena instantaneamente
 * 
 * Alternativas consideradas:
 * - Virtual scroll: Over-engineering (só necessário para 10k+ registros visíveis)
 * - Renderizar tudo: 1.1k linhas causaria lag perceptível
 * - Infinite scroll: Pior UX que paginação para dados tabulares
 */

import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useOperadorasStore } from '../stores/operadoras'
import { storeToRefs } from 'pinia'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'OperadorasList',
  
  setup() {
    const router = useRouter()
    const store = useOperadorasStore()
    const { operadoras, currentPage, totalPages, total, loading, error, searchQuery, estatisticas, estatisticasLoading } = storeToRefs(store)
    
    const searchInput = ref('')
    let searchTimeout = null
    const chartCanvas = ref(null)
    let chartInstance = null

    const onSearchInput = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        store.fetchOperadoras(1, searchInput.value)
      }, 500)
    }

    const limparBusca = () => {
      searchInput.value = ''
      store.fetchOperadoras(1, '')
    }

    const recarregar = () => {
      store.fetchOperadoras(currentPage.value, searchQuery.value)
    }

    const verDetalhes = (operadora) => {
      const cnpj = operadora.cnpj || operadora.registro_ans
      router.push(`/operadora/${cnpj}`)
    }

    const nextPage = () => store.nextPage()
    const prevPage = () => store.prevPage()

    const criarGrafico = () => {
      if (!estatisticas.value || !chartCanvas.value) return

      const ctx = chartCanvas.value.getContext('2d')      
      const topUFs = estatisticas.value.despesas_por_uf.slice(0, 10)
      
      if (chartInstance) {
        chartInstance.destroy()
      }

      chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: topUFs.map(item => item.uf),
          datasets: [{
            label: 'Despesas Totais (R$)',
            data: topUFs.map(item => item.total_despesas),
            backgroundColor: 'rgba(102, 126, 234, 0.7)',
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 2,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const valor = context.parsed.y
                  return `R$ ${valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => {
                  return 'R$ ' + (value / 1000000000).toFixed(1) + 'B'
                }
              }
            }
          }
        }
      })
    }

    onMounted(() => {
      store.fetchOperadoras(1)
      store.fetchEstatisticas()
    })

    watch(estatisticas, () => {
      if (estatisticas.value) {
        setTimeout(criarGrafico, 100)
      }
    })

    return {
      operadoras,
      currentPage,
      totalPages,
      total,
      loading,
      error,
      searchQuery,
      searchInput,
      estatisticas,
      estatisticasLoading,
      onSearchInput,
      limparBusca,
      recarregar,
      verDetalhes,
      nextPage,
      prevPage,
      chartCanvas
    }
  }
}
</script>

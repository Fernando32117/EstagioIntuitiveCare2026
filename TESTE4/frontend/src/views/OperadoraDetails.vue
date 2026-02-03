<template>
  <div>
    <button @click="voltar" class="btn btn-primary" style="margin-bottom: 20px;">
      ← Voltar
    </button>

    <div v-if="loading" class="loading">
      Carregando detalhes...
    </div>

    <div v-else-if="error" class="error">
      <strong>❌ Erro ao carregar detalhes da operadora</strong>
      {{ error }}
      <button @click="recarregar" class="btn btn-primary" style="margin-top: 12px;">
        Tentar Novamente
      </button>
    </div>

    <div v-else>
      <div class="card">
        <h2>{{ operadora?.razao_social }}</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 20px;">
          <div>
            <strong>Registro ANS:</strong>
            <p>{{ operadora?.registro_ans }}</p>
          </div>
          <div>
            <strong>CNPJ:</strong>
            <p>{{ operadora?.cnpj || '-' }}</p>
          </div>
          <div>
            <strong>Modalidade:</strong>
            <p>{{ operadora?.modalidade || '-' }}</p>
          </div>
          <div>
            <strong>UF:</strong>
            <p>{{ operadora?.uf || '-' }}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 style="margin-bottom: 20px;">📈 Histórico de Despesas</h2>
        
        <div v-if="despesas && despesas.length > 0">
          <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
            <strong>Total de Despesas:</strong> 
            R$ {{ totalDespesas.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}
            <br>
            <strong>Número de Trimestres:</strong> {{ numTrimestres }}
          </div>

          <table>
            <thead>
              <tr>
                <th>Ano</th>
                <th>Trimestre</th>
                <th>Valor das Despesas</th>
                <th>Data Importação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(despesa, index) in despesas" :key="index">
                <td>{{ despesa.ano }}</td>
                <td>{{ despesa.trimestre }}º Trimestre</td>
                <td>R$ {{ despesa.valor_despesas.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}</td>
                <td>{{ formatarData(despesa.data_importacao) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-state">
          Nenhuma despesa registrada para esta operadora.
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

export default {
  name: 'OperadoraDetails',
  
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    const loading = ref(true)
    const error = ref(null)
    const operadora = ref(null)
    const despesas = ref([])
    const totalDespesas = ref(0)
    const numTrimestres = ref(0)

    const cnpj = computed(() => route.params.cnpj)

    const carregar = async () => {
      loading.value = true
      error.value = null

      try {
        const [detalhesOp, historico] = await Promise.all([
          api.getOperadora(cnpj.value),
          api.getOperadoraDespesas(cnpj.value)
        ])

        operadora.value = detalhesOp
        despesas.value = historico.despesas
        totalDespesas.value = historico.total_despesas
        numTrimestres.value = historico.num_trimestres
      } catch (err) {
        error.value = err.message
      } finally {
        loading.value = false
      }
    }

    const recarregar = () => {
      carregar()
    }

    const voltar = () => {
      router.push('/')
    }

    const formatarData = (dataISO) => {
      if (!dataISO) return '-'
      const data = new Date(dataISO)
      return data.toLocaleDateString('pt-BR')
    }

    onMounted(() => {
      carregar()
    })

    return {
      loading,
      error,
      operadora,
      despesas,
      totalDespesas,
      numTrimestres,
      recarregar,
      voltar,
      formatarData
    }
  }
}
</script>

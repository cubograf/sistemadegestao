// Namespace para o dashboard
window.Dashboard = {
    // Função para verificar se o usuário é admin
    isAdmin: function() {
        return typeof USER_ROLE !== 'undefined' && USER_ROLE === 'admin';
    },

    // Função para excluir ordem
    deleteOrder: function(numero) {
        if (confirm('Tem certeza que deseja excluir a ordem ' + numero + '?')) {
            $.ajax({
                url: `/api/orders/${numero}`,
                method: 'DELETE',
                success: function(response) {
                    alert('Ordem excluída com sucesso!');
                    Dashboard.updateDashboard();
                    if (typeof updateAllOrdersTable === 'function') {
                        updateAllOrdersTable();
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Erro ao excluir ordem:', error);
                    alert('Erro ao excluir ordem: ' + error);
                }
            });
        }
    },

    // Função para formatar valores monetários
    formatMoney: function(value) {
        if (typeof value === 'string') {
            value = this.parseMoneyToNumber(value);
        }
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    },

    // Função para converter valor monetário em número
    parseMoneyToNumber: function(value) {
        if (typeof value === 'number') return value;
        if (!value) return 0;
        return Number(value.replace(/[^0-9,-]/g, '').replace('.', '').replace(',', '.'));
    },

    // Função para atualizar a lista de vendedores
    updateVendedoresList: function() {
        $.get('/api/orders')
            .done(function(orders) {
                const vendedores = new Set();
                orders.forEach(order => {
                    if (order.vendedor) {
                        vendedores.add(order.vendedor);
                    }
                });

                const vendedorSelect = $('#dashboardVendedorFilter');
                vendedorSelect.find('option:not(:first)').remove();

                Array.from(vendedores).sort().forEach(vendedor => {
                    vendedorSelect.append(`<option value="${vendedor}">${vendedor}</option>`);
                });
            });
    },

    // Função para atualizar a lista de fornecedores
    updateFornecedoresList: function() {
        $.get('/api/orders')
            .done(function(orders) {
                const fornecedores = new Set();
                orders.forEach(order => {
                    if (order.fornecedor) {
                        fornecedores.add(order.fornecedor);
                    }
                });

                const fornecedorSelect = $('#dashboardFornecedorFilter');
                fornecedorSelect.find('option:not(:first)').remove();

                Array.from(fornecedores).sort().forEach(fornecedor => {
                    fornecedorSelect.append(`<option value="${fornecedor}">${fornecedor}</option>`);
                });
            });
    },

    // Função para atualizar o dashboard
    updateDashboard: function() {
        try {
            const mes = parseInt($('#dashboardMesSelect').val());
            const ano = parseInt($('#dashboardAnoSelect').val());
            const status = $('#dashboardStatusFilter').val();
            const vendedor = $('#dashboardVendedorFilter').val();
            const fornecedor = $('#dashboardFornecedorFilter').val();

            console.log('Atualizando dashboard com:', { mes, ano, status, vendedor, fornecedor });

            if (isNaN(mes) || isNaN(ano)) {
                console.error('Mês ou ano inválidos:', { mes, ano });
                return;
            }

            $.get('/api/orders')
                .done(function(orders) {
                    if (!Array.isArray(orders)) {
                        console.error('Resposta inválida da API:', orders);
                        return;
                    }

                    // Filtrar as ordens
                    const filteredOrders = orders.filter(order => {
                        if (!order || !order.data) {
                            console.log('Ordem inválida ou sem data:', order);
                            return false;
                        }

                        try {
                            const orderDate = new Date(order.data);
                            if (isNaN(orderDate.getTime())) {
                                console.log('Data inválida:', order.data);
                                return false;
                            }

                            const orderMonth = orderDate.getMonth() + 1;
                            const orderYear = orderDate.getFullYear();

                            const matchesDate = orderMonth === mes && orderYear === ano;
                            const matchesStatus = !status || order.status === status;
                            const matchesVendedor = !vendedor || order.vendedor === vendedor;
                            const matchesFornecedor = !fornecedor || order.fornecedor === fornecedor;

                            return matchesDate && matchesStatus && matchesVendedor && matchesFornecedor;
                        } catch (error) {
                            console.error('Erro ao processar ordem:', error, order);
                            return false;
                        }
                    });

                    console.log('Ordens filtradas:', filteredOrders);

                    // Calcular estatísticas
                    const stats = {
                        orders_aguardando: filteredOrders.filter(o => ['Aguardando Aprovação', 'Aguardando Pagamento'].includes(o.status)).length,
                        orders_em_producao: filteredOrders.filter(o => o.status === 'Em Produção').length,
                        orders_retirada: filteredOrders.filter(o => o.status === 'Disponível para Retirada').length,
                        orders_finalizados: filteredOrders.filter(o => o.status === 'Finalizada').length,
                        receita_total: filteredOrders.filter(o => o.status === 'Finalizada').reduce((sum, o) => sum + Dashboard.parseMoneyToNumber(o.valor_total), 0),
                        custos_total: filteredOrders.filter(o => o.status === 'Finalizada').reduce((sum, o) => sum + Dashboard.parseMoneyToNumber(o.custo), 0),
                        valores_receber: filteredOrders.filter(o => o.status !== 'Finalizada' && o.status !== 'Cancelada').reduce((sum, o) => sum + Dashboard.parseMoneyToNumber(o.valor_total), 0)
                    };

                    stats.lucro_total = stats.receita_total - stats.custos_total;

                    // Atualizar cards de estatísticas
                    $('#kpiOrdensPendentes').text(stats.orders_aguardando);
                    $('#kpiOrdensAndamento').text(stats.orders_em_producao);
                    $('#kpiOrdensRetirada').text(stats.orders_retirada);
                    $('#kpiOrdensFinalizadas').text(stats.orders_finalizados);

                    // Atualizar cards financeiros
                    $('#kpiReceita').text(Dashboard.formatMoney(stats.receita_total));
                    $('#kpiCusto').text(Dashboard.formatMoney(stats.custos_total));
                    $('#kpiLucro').text(Dashboard.formatMoney(stats.lucro_total));
                    $('#kpiParaEntrar').text(Dashboard.formatMoney(stats.valores_receber));

                    // Atualizar cards financeiros visíveis apenas para Admin
                    if (Dashboard.isAdmin()) {
                        $('#financeReceita').text(Dashboard.formatMoney(stats.receita_total));
                        $('#financeCusto').text(Dashboard.formatMoney(stats.custos_total));
                        $('#financeLucro').text(Dashboard.formatMoney(stats.lucro_total));
                        $('#financeParaEntrar').text(Dashboard.formatMoney(stats.valores_receber));
                    }

                    // Atualizar tabela de ordens recentes
                    const tbody = $('#recentOrdersTable tbody');
                    tbody.empty();

                    // Ordenar por data mais recente
                    filteredOrders.sort((a, b) => new Date(b.data) - new Date(a.data));

                    // Pegar as 10 ordens mais recentes
                    const recentOrders = filteredOrders.slice(0, 10);

                    recentOrders.forEach(order => {
                        const row = `
                            <tr>
                                <td>${order.numero}</td>
                                <td>${order.cliente}</td>
                                <td>${order.vendedor}</td>
                                <td>${order.fornecedor || ''}</td>
                                <td>${new Date(order.data).toLocaleDateString('pt-BR')}</td>
                                <td class="${order.status_class || ''}">${order.status}</td>
                                <td>${Dashboard.formatMoney(order.valor_total)}</td>
                                <td>${order.forma_pagamento}</td>
                                <td>
                                    <button type="button" class="btn btn-sm btn-edit" onclick="Dashboard.editOrder('${order.numero}')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button type="button" class="btn btn-sm btn-print" onclick="Dashboard.printOrder('${order.numero}')">
                                        <i class="fas fa-print"></i>
                                    </button>
                                    <button type="button" class="btn btn-sm btn-delete" onclick="Dashboard.deleteOrder('${order.numero}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `;
                        tbody.append(row);
                    });
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
                    console.error('Erro ao atualizar dashboard:', {
                        status: textStatus,
                        error: errorThrown,
                        response: jqXHR.responseText
                    });
                });
        } catch (error) {
            console.error('Erro geral ao atualizar dashboard:', error);
        }
    },

    // Inicialização
    init: function() {
        console.log('Inicializando dashboard...');

        try {
            // Definir mês e ano atual
            const now = new Date();
            $('#dashboardMesSelect').val(now.getMonth() + 1);
            $('#dashboardAnoSelect').val(now.getFullYear());

            // Atualizar listas de filtros
            this.updateVendedoresList();
            this.updateFornecedoresList();

            // Atualizar dashboard com delay inicial
            setTimeout(() => this.updateDashboard(), 500);

            // Event listeners para os filtros
            $('#dashboardMesSelect, #dashboardAnoSelect, #dashboardStatusFilter, #dashboardVendedorFilter, #dashboardFornecedorFilter').on('change', () => {
                this.updateDashboard();
            });
        } catch (error) {
            console.error('Erro na inicialização do dashboard:', error);
        }
    }
};

// Inicializar quando o documento estiver pronto
$(document).ready(function() {
    Dashboard.init();
});
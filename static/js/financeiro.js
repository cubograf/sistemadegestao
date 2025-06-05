// Variáveis globais
let currentMonth = new Date().getMonth() + 1;
let currentYear = new Date().getFullYear();
let balanceChart = null;
let ordersStatusChart = null;

// Funções de formatação
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('pt-BR');
}

// Funções de carregamento de dados
async function loadFinancialData() {
    try {
        const response = await fetch(`/api/financeiro/dados?mes=${currentMonth}&ano=${currentYear}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao carregar dados financeiros');
        }
        
        const data = await response.json();
        updateDashboard(data);
        updateCharts(data);
        updateTables(data);
    } catch (error) {
        console.error('Erro:', error);
        showError('Erro ao carregar dados financeiros: ' + error.message);
    }
}

// Função para mostrar erros
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Funções de atualização da interface
function updateDashboard(data) {
    try {
        document.getElementById('totalRevenue').textContent = formatCurrency(data.receita_total || 0);
        document.getElementById('totalExpenses').textContent = formatCurrency(data.despesas_total || 0);
        document.getElementById('netProfit').textContent = formatCurrency(data.lucro_liquido || 0);
        document.getElementById('openOrders').textContent = data.pedidos_aberto || 0;
        
        document.getElementById('currentPeriod').textContent = 
            new Date(currentYear, currentMonth - 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
    } catch (error) {
        console.error('Erro ao atualizar dashboard:', error);
        showError('Erro ao atualizar dashboard');
    }
}

function updateCharts(data) {
    try {
        // Atualizar gráfico de balanço
        const ctx1 = document.getElementById('balanceChart').getContext('2d');
        if (balanceChart) balanceChart.destroy();
        
        balanceChart = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: ['Receita', 'Despesas', 'Lucro'],
                datasets: [{
                    data: [
                        data.receita_total || 0, 
                        data.despesas_total || 0, 
                        data.lucro_liquido || 0
                    ],
                    backgroundColor: ['#4CAF50', '#F44336', '#2196F3']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });
        
        // Atualizar gráfico de status dos pedidos
        const statusCount = {};
        (data.pedidos || []).forEach(order => {
            statusCount[order.status] = (statusCount[order.status] || 0) + 1;
        });
        
        const ctx2 = document.getElementById('ordersStatusChart').getContext('2d');
        if (ordersStatusChart) ordersStatusChart.destroy();
        
        ordersStatusChart = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: Object.keys(statusCount),
                datasets: [{
                    data: Object.values(statusCount),
                    backgroundColor: [
                        '#9b59b6', // Aguardando Aprovação
                        '#f39c12', // Aguardando Pagamento
                        '#3498db', // Em Produção
                        '#1abc9c', // Disponível para Retirada
                        '#2ecc71', // Finalizada
                        '#e74c3c'  // Cancelada
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    } catch (error) {
        console.error('Erro ao atualizar gráficos:', error);
        showError('Erro ao atualizar gráficos');
    }
}

function updateTables(data) {
    try {
        // Atualizar tabela de pedidos em aberto
        const openOrdersTable = document.getElementById('openOrdersTable');
        if (!openOrdersTable) return;
        
        openOrdersTable.innerHTML = '';
        
        const openOrders = (data.pedidos || []).filter(order => 
            !['Finalizada', 'Cancelada'].includes(order.status)
        );
        
        openOrders.forEach(order => {
            const row = openOrdersTable.insertRow();
            row.innerHTML = `
                <td>${order.numero}</td>
                <td>${order.cliente}</td>
                <td>${formatCurrency(order.valor_total)}</td>
                <td>${formatCurrency(order.valor_restante)}</td>
                <td><span class="status status-${order.status.toLowerCase().replace(' ', '-')}">${order.status}</span></td>
                <td>
                    <button class="btn-action edit-order" data-order="${order.numero}">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
            `;
        });
    } catch (error) {
        console.error('Erro ao atualizar tabelas:', error);
        showError('Erro ao atualizar tabelas');
    }
}

// Funções de navegação de período
function changeMonth(delta) {
    currentMonth += delta;
    
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    } else if (currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    
    loadFinancialData();
}

// Funções de transferência de pedidos
async function transferOrders() {
    if (!confirm('Deseja transferir todos os pedidos em aberto para o próximo mês?')) return;
    
    const nextMonth = currentMonth === 12 ? 1 : currentMonth + 1;
    const nextYear = currentMonth === 12 ? currentYear + 1 : currentYear;
    
    try {
        const response = await fetch('/api/financeiro/transferir', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                mes_origem: currentMonth,
                ano_origem: currentYear,
                mes_destino: nextMonth,
                ano_destino: nextYear
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao transferir pedidos');
        }
        
        const result = await response.json();
        showSuccess(result.message);
        loadFinancialData();
    } catch (error) {
        console.error('Erro:', error);
        showError('Erro ao transferir pedidos: ' + error.message);
    }
}

// Função para mostrar mensagens de sucesso
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    document.body.appendChild(successDiv);
    setTimeout(() => successDiv.remove(), 3000);
}

// Funções de gerenciamento de pagamentos
function openPaymentModal(paymentId = null) {
    const modal = document.getElementById('paymentModal');
    const form = document.getElementById('paymentForm');
    const title = document.getElementById('paymentModalTitle');
    
    form.reset();
    document.getElementById('paymentId').value = '';
    document.getElementById('paymentDate').valueAsDate = new Date();
    
    if (paymentId) {
        title.textContent = 'Editar Pagamento';
        // Carregar dados do pagamento
        loadPaymentData(paymentId);
    } else {
        title.textContent = 'Adicionar Pagamento';
    }
    
    modal.style.display = 'block';
}

async function loadPaymentData(paymentId) {
    try {
        const response = await fetch(`/api/financeiro/pagamentos/${paymentId}`);
        if (!response.ok) throw new Error('Erro ao carregar dados do pagamento');
        
        const payment = await response.json();
        
        document.getElementById('paymentId').value = payment.id;
        document.getElementById('paymentDate').value = payment.data;
        document.getElementById('paymentClient').value = payment.cliente;
        document.getElementById('paymentValue').value = payment.valor;
        document.getElementById('paymentStatus').value = payment.status;
        document.getElementById('paymentObservation').value = payment.observacao || '';
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao carregar dados do pagamento');
        closePaymentModal();
    }
}

function closePaymentModal() {
    document.getElementById('paymentModal').style.display = 'none';
}

async function savePayment(event) {
    event.preventDefault();
    
    const paymentId = document.getElementById('paymentId').value;
    const formData = {
        data: document.getElementById('paymentDate').value,
        cliente: document.getElementById('paymentClient').value,
        valor: parseFloat(document.getElementById('paymentValue').value),
        status: document.getElementById('paymentStatus').value,
        observacao: document.getElementById('paymentObservation').value
    };
    
    try {
        const url = paymentId ? 
            `/api/financeiro/pagamentos/${paymentId}` : 
            '/api/financeiro/pagamentos';
        
        const response = await fetch(url, {
            method: paymentId ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Erro ao salvar pagamento');
        
        const result = await response.json();
        alert(paymentId ? 'Pagamento atualizado com sucesso!' : 'Pagamento adicionado com sucesso!');
        closePaymentModal();
        loadFinancialData();
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar pagamento');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Carregar dados iniciais
    loadFinancialData();
    
    // Navegação de período
    document.getElementById('prevMonth')?.addEventListener('click', () => changeMonth(-1));
    document.getElementById('nextMonth')?.addEventListener('click', () => changeMonth(1));
    
    // Transferência de pedidos
    document.getElementById('transferNextMonth')?.addEventListener('click', transferOrders);
    
    // Modal de pagamento
    document.getElementById('addPaymentBtn').addEventListener('click', () => openPaymentModal());
    document.getElementById('paymentForm').addEventListener('submit', savePayment);
    
    // Fechar modal
    const closeButtons = document.querySelectorAll('.close-button');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
});

// Função para formatar valores monetários
function formatMoney(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Função para formatar datas
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('pt-BR');
}

// Função para atualizar os cards financeiros
function updateFinanceiroCards() {
    const mes = new Date().getMonth() + 1;
    const ano = new Date().getFullYear();

    // Primeiro, buscar dados financeiros gerais
    $.get(`/api/financeiro/dados?mes=${mes}&ano=${ano}`)
        .done(function(data) {
            // Agora buscar dados de compras
            $.get(`/api/compras?mes=${mes}&ano=${ano}`)
                .done(function(comprasData) {
                    // Buscar dados de contas a pagar
                    $.get(`/api/contas_pagar?mes=${mes}&ano=${ano}`)
                        .done(function(contasData) {
                            // Calcular total de saídas
                            const comprasTotal = comprasData.reduce((sum, compra) => sum + (compra.valor || 0), 0);
                            const contasTotal = contasData.reduce((sum, conta) => sum + (conta.valor || 0), 0);
                            const saidasTotal = (data.saidas_total || 0) + comprasTotal + contasTotal;

                            // Atualizar cards
                            $('#financeReceita').text(formatMoney(data.receita_total || 0));
                            $('#financeCusto').text(formatMoney(data.custos_total || 0));
                            $('#financeLucro').text(formatMoney((data.receita_total || 0) - saidasTotal));
                            $('#financeParaEntrar').text(formatMoney(data.valores_receber || 0));
                            $('#financeSaidas').text(formatMoney(saidasTotal));
                        })
                        .fail(function(jqXHR, textStatus, errorThrown) {
                            console.error('Erro ao carregar contas a pagar:', errorThrown);
                        });
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
                    console.error('Erro ao carregar compras:', errorThrown);
                });
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.error('Erro ao atualizar cards financeiros:', errorThrown);
        });
}

// Função para carregar contas a pagar
function loadContasPagar() {
    $.get('/api/contas_pagar')
        .done(function(contas) {
            const tbody = $('#contasPagarTable tbody');
            tbody.empty();

            contas.forEach(function(conta) {
                const row = $('<tr>');
                row.append(`<td>${conta.id}</td>`);
                row.append(`<td>${conta.descricao}</td>`);
                row.append(`<td>${formatMoney(conta.valor)}</td>`);
                row.append(`<td>${formatDate(conta.data_vencimento)}</td>`);
                row.append(`<td class="status-${conta.status.toLowerCase()}">${conta.status}</td>`);

                const actions = $('<td class="actions">');
                if (conta.status === 'Pendente') {
                    actions.append(`
                        <button onclick="pagarConta('${conta.id}')" class="btn-success">Pagar</button>
                        <button onclick="editarConta('${conta.id}')" class="btn-primary">Editar</button>
                    `);
                }
                row.append(actions);

                tbody.append(row);
            });
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.error('Erro ao carregar contas:', errorThrown);
        });
}

// Função para pagar uma conta
function pagarConta(id) {
    if (confirm('Confirma o pagamento desta conta?')) {
        $.post(`/api/contas_pagar/${id}/pagar`)
            .done(function(response) {
                alert('Conta paga com sucesso!');
                loadContasPagar();
                updateFinanceiroCards();
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                alert('Erro ao pagar conta: ' + errorThrown);
            });
    }
}

// Função para editar uma conta
function editarConta(id) {
    // Carregar dados da conta
    $.get(`/api/contas_pagar/${id}`)
        .done(function(conta) {
            // Preencher o formulário
            $('#contaId').val(conta.id);
            $('#contaDescricao').val(conta.descricao);
            $('#contaValor').val(conta.valor);
            $('#contaVencimento').val(conta.data_vencimento);
            $('#contaStatus').val(conta.status);

            // Mostrar modal
            $('#contaModal').show();
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            alert('Erro ao carregar dados da conta: ' + errorThrown);
        });
}

// Event listeners
$(document).ready(function() {
    // Atualizar cards financeiros a cada 30 segundos
    updateFinanceiroCards();
    setInterval(updateFinanceiroCards, 30000);

    // Carregar contas a pagar
    if ($('#contasPagarTable').length) {
        loadContasPagar();
    }

    // Form de nova conta
    $('#contaForm').on('submit', function(e) {
        e.preventDefault();

        const formData = {
            descricao: $('#contaDescricao').val(),
            fornecedor: $('#contaFornecedor').val(),
            valor: parseFloat($('#contaValor').val()),
            data_vencimento: $('#contaVencimento').val(),
            categoria: $('#contaCategoria').val(),
            forma_pagamento: $('#contaFormaPagamento').val(),
            observacao: $('#contaObservacao').val()
        };

        const contaId = $('#contaId').val();
        const url = contaId ? `/api/contas_pagar/${contaId}` : '/api/contas_pagar';
        const method = contaId ? 'PUT' : 'POST';

        $.ajax({
            url: url,
            method: method,
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                alert(contaId ? 'Conta atualizada com sucesso!' : 'Conta criada com sucesso!');
                $('#contaModal').hide();
                $('#contaForm')[0].reset();
                loadContasPagar();
                updateFinanceiroCards();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert('Erro ao salvar conta: ' + (jqXHR.responseJSON?.error || errorThrown));
            }
        });
    });

    // Fechar modal
    $('.close-button').click(function() {
        $(this).closest('.modal').hide();
    });

    // Abrir modal de nova conta
    $('#addContaBtn').click(function() {
        $('#contaForm')[0].reset();
        $('#contaId').val('');
        $('#contaModal').show();
    });
}); 
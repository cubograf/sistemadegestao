// Namespace para o módulo de Contas a Pagar
window.ContasPagar = {
    // Função para formatar valores monetários
    formatMoney: function(value) {
        if (typeof value === 'string') {
            value = this.parseMoneyToNumber(value);
        }
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    // Função para converter string monetária em número
    parseMoneyToNumber: function(value) {
        if (typeof value === 'number') return value;
        if (!value) return 0;
        return Number(value.replace(/[^0-9,-]/g, '').replace('.', '').replace(',', '.'));
    },

    // Função para formatar datas
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '-';
        return date.toLocaleDateString('pt-BR');
    },

    // Função para carregar a tabela de contas
    loadTable: function() {
        const mes = $('#mesFiltro').val() || (new Date().getMonth() + 1);
        const ano = $('#anoFiltro').val() || new Date().getFullYear();

        $.get(`/api/contas_pagar?mes=${mes}&ano=${ano}`)
            .done(function(contas) {
                const tbody = $('#contasPagarTable tbody');
                tbody.empty();

                let totalPendente = 0;
                let totalPago = 0;

                contas.forEach(function(conta) {
                    const row = $('<tr>');
                    row.append(`<td>${conta.id}</td>`);
                    row.append(`<td>${conta.descricao}</td>`);
                    row.append(`<td>${conta.fornecedor || '-'}</td>`);
                    row.append(`<td>${ContasPagar.formatMoney(conta.valor)}</td>`);
                    row.append(`<td>${ContasPagar.formatDate(conta.data_vencimento)}</td>`);
                    row.append(`<td>${conta.categoria || '-'}</td>`);
                    row.append(`<td>${conta.forma_pagamento || '-'}</td>`);
                    row.append(`<td class="status-${conta.status.toLowerCase()}">${conta.status}</td>`);

                    const actions = $('<td class="actions">');
                    if (conta.status === 'Pendente') {
                        actions.append(`
                            <button onclick="ContasPagar.pagar('${conta.id}')" class="btn btn-sm btn-success" title="Pagar">
                                <i class="fas fa-check"></i>
                            </button>
                            <button onclick="ContasPagar.edit('${conta.id}')" class="btn btn-sm btn-primary" title="Editar">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button onclick="ContasPagar.delete('${conta.id}')" class="btn btn-sm btn-danger" title="Excluir">
                                <i class="fas fa-trash"></i>
                            </button>
                        `);
                        totalPendente += ContasPagar.parseMoneyToNumber(conta.valor);
                    } else {
                        totalPago += ContasPagar.parseMoneyToNumber(conta.valor);
                    }
                    row.append(actions);

                    tbody.append(row);
                });

                // Atualizar totais
                $('#totalPendente').text(ContasPagar.formatMoney(totalPendente));
                $('#totalPago').text(ContasPagar.formatMoney(totalPago));
                $('#totalGeral').text(ContasPagar.formatMoney(totalPendente + totalPago));
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error('Erro ao carregar contas:', errorThrown);
                alert('Erro ao carregar contas: ' + errorThrown);
            });
    },

    // Função para pagar uma conta
    pagar: function(id) {
        if (confirm('Confirma o pagamento desta conta?')) {
            $.post(`/api/contas_pagar/${id}/pagar`)
                .done(function(response) {
                    alert('Conta paga com sucesso!');
                    ContasPagar.loadTable();
                    if (typeof updateFinanceiroCards === 'function') {
                        updateFinanceiroCards();
                    }
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
                    alert('Erro ao pagar conta: ' + errorThrown);
                });
        }
    },

    // Função para excluir uma conta
    delete: function(id) {
        if (confirm('Tem certeza que deseja excluir esta conta?')) {
            $.ajax({
                url: `/api/contas_pagar/${id}`,
                method: 'DELETE',
                success: function(response) {
                    alert('Conta excluída com sucesso!');
                    ContasPagar.loadTable();
                    if (typeof updateFinanceiroCards === 'function') {
                        updateFinanceiroCards();
                    }
                },
                error: function(xhr, status, error) {
                    alert('Erro ao excluir conta: ' + error);
                }
            });
        }
    },

    // Função para editar uma conta
    edit: function(id) {
        $.get(`/api/contas_pagar/${id}`)
            .done(function(conta) {
                $('#contaId').val(conta.id);
                $('#contaDescricao').val(conta.descricao);
                $('#contaFornecedor').val(conta.fornecedor);
                $('#contaValor').val(conta.valor);
                $('#contaVencimento').val(conta.data_vencimento);
                $('#contaCategoria').val(conta.categoria);
                $('#contaFormaPagamento').val(conta.forma_pagamento);
                $('#contaObservacao').val(conta.observacao);
                $('#contaStatus').val(conta.status);

                $('#contaModal').modal('show');
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                alert('Erro ao carregar dados da conta: ' + errorThrown);
            });
    },

    // Função para salvar uma conta (nova ou editada)
    save: function(formData) {
        const id = formData.id;
        const url = id ? `/api/contas_pagar/${id}` : '/api/contas_pagar';
        const method = id ? 'PUT' : 'POST';

        $.ajax({
            url: url,
            method: method,
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                alert(id ? 'Conta atualizada com sucesso!' : 'Conta criada com sucesso!');
                $('#contaModal').modal('hide');
                $('#contaForm')[0].reset();
                ContasPagar.loadTable();
                if (typeof updateFinanceiroCards === 'function') {
                    updateFinanceiroCards();
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert('Erro ao salvar conta: ' + (jqXHR.responseJSON?.error || errorThrown));
            }
        });
    },

    // Inicialização
    init: function() {
        console.log('Inicializando módulo Contas a Pagar...');

        // Configurar filtros de mês e ano
        const now = new Date();
        const currentMonth = now.getMonth() + 1;
        const currentYear = now.getFullYear();

        // Preencher select de mês
        const meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];
        const mesSelect = $('#mesFiltro');
        meses.forEach((mes, index) => {
            mesSelect.append(`<option value="${index + 1}">${mes}</option>`);
        });
        mesSelect.val(currentMonth);

        // Preencher select de ano
        const anoSelect = $('#anoFiltro');
        for (let ano = currentYear - 2; ano <= currentYear + 2; ano++) {
            anoSelect.append(`<option value="${ano}">${ano}</option>`);
        }
        anoSelect.val(currentYear);

        // Event listeners para filtros
        $('#mesFiltro, #anoFiltro').on('change', () => {
            this.loadTable();
        });

        // Event listener para o formulário
        $('#contaForm').on('submit', function(e) {
            e.preventDefault();

            const formData = {
                id: $('#contaId').val(),
                descricao: $('#contaDescricao').val(),
                fornecedor: $('#contaFornecedor').val(),
                valor: parseFloat($('#contaValor').val()),
                data_vencimento: $('#contaVencimento').val(),
                categoria: $('#contaCategoria').val(),
                forma_pagamento: $('#contaFormaPagamento').val(),
                observacao: $('#contaObservacao').val(),
                status: $('#contaStatus').val() || 'Pendente'
            };

            ContasPagar.save(formData);
        });

        // Event listener para o botão de nova conta
        $('#addContaBtn').click(function() {
            $('#contaForm')[0].reset();
            $('#contaId').val('');
            $('#contaStatus').val('Pendente');
            const hoje = new Date().toISOString().split('T')[0];
            $('#contaVencimento').val(hoje);
            $('#contaModal').modal('show');
        });

        // Carregar tabela inicial
        this.loadTable();
    }
};

// Inicializar quando o documento estiver pronto
$(document).ready(function() {
    ContasPagar.init();
});
document.addEventListener("DOMContentLoaded", function () {

    // Elementos do DOM
    const sections = document.querySelectorAll(".dashboard-section");
    const navLinks = document.querySelectorAll(".sidebar-nav .nav-item");
    const mainSearchInput = document.getElementById("mainSearchInput");
    const orderSearchInput = document.getElementById("orderSearchInput");
    const vendedorFilterInput = document.getElementById("vendedorFilterInput");
    const statusFilterSelect = document.getElementById("statusFilterSelect");

    // Elementos do Modal de Ordem
    const orderModal = document.getElementById("orderModal");
    const orderForm = document.getElementById("orderForm");
    const modalTitle = document.getElementById("modalTitle");
    const saveOrderBtn = document.getElementById("saveOrderBtn");
    const closeButton = orderModal.querySelector(".close-button");
    const addOrderBtn = document.getElementById("addOrderBtn");
    const addOrderBtnDashboard = document.getElementById("addOrderBtnDashboard");
    const printOrderBtn = document.getElementById("printOrderBtn");
    
    // Campos do formulário de ordem
    const valorTotalInput = document.getElementById("valor_total");
    const valorEntradaInput = document.getElementById("valor_entrada");
    const valorRestanteInput = document.getElementById("valor_restante");

    // Elementos do Modal de Compra
    const compraModal = document.getElementById("compraModal");
    const addCompraBtn = document.getElementById("addCompraBtn");
    const compraForm = document.getElementById("compraForm");
    const closeCompraButton = compraModal?.querySelector(".close-button");

    // Elementos do Modal de Conta a Pagar
    const contaModal = document.getElementById("contaModal");
    const addContaBtn = document.getElementById("addContaBtn");
    const contaForm = document.getElementById("contaForm");
    const closeContaButton = contaModal?.querySelector(".close-button");

    // Elementos do Balancete
    const balanceteMesSelect = document.getElementById("balanceteMesSelect");
    const balanceteAnoSelect = document.getElementById("balanceteAnoSelect");
    const atualizarBalanceteBtn = document.getElementById("atualizarBalanceteBtn");

    // Tabelas
    const recentOrdersTableBody = document.getElementById("recentOrdersTable")?.querySelector("tbody");
    const allOrdersTableBody = document.getElementById("allOrdersTable")?.querySelector("tbody");
    const producaoTableBody = document.getElementById("producaoTable")?.querySelector("tbody");
    const financeiroTableBody = document.getElementById("financeiroTable")?.querySelector("tbody");
    const comprasTableBody = document.getElementById("comprasTable")?.querySelector("tbody");
    const contasPagarTableBody = document.getElementById("contasPagarTable")?.querySelector("tbody");
    const entradasTableBody = document.getElementById("entradasTable")?.querySelector("tbody");
    const saidasTableBody = document.getElementById("saidasTable")?.querySelector("tbody");

    // Estado da aplicação
    let currentOrders = [];
    let currentCompras = [];
    let currentContasPagar = [];
    let currentBalancete = {
        entradas: [],
        saidas: []
    };

    // --- Funções de API ---
    async function fetchData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                if (response.status === 401) {
                    console.error("Unauthorized access. Redirecting to login.");
                    window.location.href = "/login";
                    return null;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${url}:`, error);
            return null;
        }
    }

    async function postData(url, data) {
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                if (response.status === 401) {
                    console.error("Unauthorized access. Redirecting to login.");
                    window.location.href = "/login";
                    return null;
                }
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error posting to ${url}:`, error);
            alert(`Erro ao salvar: ${error.message}`);
            return null;
        }
    }

    async function putData(url, data) {
        try {
            const response = await fetch(url, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                if (response.status === 401) {
                    console.error("Unauthorized access. Redirecting to login.");
                    window.location.href = "/login";
                    return null;
                }
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error putting to ${url}:`, error);
            alert(`Erro ao atualizar: ${error.message}`);
            return null;
        }
    }

    // --- Funções de Renderização ---
    function formatCurrency(value) {
        if (value === null || value === undefined || value === "") {
            return "-";
        }
        return parseFloat(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    }

    function formatDate(dateString) {
        if (!dateString) return "-";
        try {
            const date = new Date(dateString + "T00:00:00");
            return date.toLocaleDateString("pt-BR");
        } catch (e) {
            console.error("Error formatting date:", e);
            return dateString;
        }
    }

    function getStatusClass(status) {
        switch (status) {
            case "Aguardando Aprovação": return "status-aprovacao";
            case "Aguardando Pagamento": return "status-pagamento";
            case "Em Produção": return "status-producao";
            case "Disponível para Retirada": return "status-retirada";
            case "Finalizada": return "status-finalizada";
            case "Cancelada": return "status-cancelada";
            default: return "";
        }
    }

    function renderOrdersTable(tableBody, orders, limit = null) {
        if (!tableBody) return;
        tableBody.innerHTML = "";
        
        const ordersToRender = limit ? orders.slice(0, limit) : orders;

        if (ordersToRender.length === 0) {
            const row = tableBody.insertRow();
            const cell = row.insertCell();
            let colspan = 8; // Default
            
            if (tableBody.closest("#allOrdersTable")) {
                colspan = 13;
            } else if (tableBody.closest("#producaoTable")) {
                colspan = 8;
            } else if (tableBody.closest("#financeiroTable")) {
                colspan = 9;
            }
            
            cell.colSpan = colspan;
            cell.textContent = "Nenhuma ordem encontrada.";
            cell.style.textAlign = "center";
            return;
        }

        ordersToRender.forEach(order => {
            const row = tableBody.insertRow();
            const isAllOrdersTable = tableBody.closest("#allOrdersTable");
            const isProducaoTable = tableBody.closest("#producaoTable");
            const isFinanceiroTable = tableBody.closest("#financeiroTable");
            
            // Colunas comuns
            if (!isFinanceiroTable) {
                row.insertCell().textContent = order.numero;
                row.insertCell().textContent = order.cliente || "-";
                row.insertCell().textContent = order.vendedor || "-";
                row.insertCell().textContent = formatDate(order.data);
            }
            
            // Status (exceto para tabela financeiro)
            if (!isFinanceiroTable) {
                if (!isProducaoTable) {
                    const statusCell = row.insertCell();
                    const statusSpan = document.createElement("span");
                    statusSpan.className = `status ${getStatusClass(order.status)}`;
                    statusSpan.textContent = order.status || "-";
                    statusCell.appendChild(statusSpan);
                }
            }
            
            // Colunas específicas
            if (isAllOrdersTable) {
                // Material e Fornecedor
                const materialCell = row.insertCell();
                if (Array.isArray(order.material)) {
                    materialCell.textContent = order.material.join(", ");
                } else {
                    materialCell.textContent = order.material || "-";
                }
                row.insertCell().textContent = order.fornecedor || "-";
                
                // Valores
                row.insertCell().textContent = formatCurrency(order.custo);
                row.insertCell().textContent = formatCurrency(order.valor_total);
                row.insertCell().textContent = formatCurrency(order.valor_entrada);
                row.insertCell().textContent = formatCurrency(order.valor_restante);
                row.insertCell().textContent = order.forma_pagamento || "-";
            } 
            else if (isProducaoTable) {
                // Material e Fornecedor
                const materialCell = row.insertCell();
                if (Array.isArray(order.material)) {
                    materialCell.textContent = order.material.join(", ");
                } else {
                    materialCell.textContent = order.material || "-";
                }
                row.insertCell().textContent = order.fornecedor || "-";
                
                // Valor Total
                row.insertCell().textContent = formatCurrency(order.valor_total);
            }
            else if (isFinanceiroTable) {
                // Colunas específicas para financeiro
                row.insertCell().textContent = order.numero;
                row.insertCell().textContent = order.cliente || "-";
                row.insertCell().textContent = formatCurrency(order.valor_total);
                row.insertCell().textContent = formatCurrency(order.custo);
                row.insertCell().textContent = formatCurrency(order.valor_estimado_lucro);
                row.insertCell().textContent = formatCurrency(order.valor_entrada);
                row.insertCell().textContent = formatCurrency(order.valor_restante);
                row.insertCell().textContent = order.forma_pagamento || "-";
                
                const statusCell = row.insertCell();
                const statusSpan = document.createElement("span");
                statusSpan.className = `status ${getStatusClass(order.status)}`;
                statusSpan.textContent = order.status || "-";
                statusCell.appendChild(statusSpan);
            }
            else {
                // Para tabela de ordens recentes
                row.insertCell().textContent = formatCurrency(order.valor_total);
                row.insertCell().textContent = order.forma_pagamento || "-";
            }

            // Ações (exceto para tabela financeiro)
            if (!isFinanceiroTable) {
                const actionsCell = row.insertCell();
                
                // Botão de edição
                const editButton = document.createElement("button");
                editButton.className = "btn-action edit-order";
                editButton.innerHTML = '<i class="fas fa-pencil-alt"></i>';
                editButton.title = "Editar Ordem";
                editButton.dataset.orderNumber = order.numero;
                actionsCell.appendChild(editButton);
                
                // Botão de impressão
                const printButton = document.createElement("button");
                printButton.className = "btn-action print-order";
                printButton.innerHTML = '<i class="fas fa-print"></i>';
                printButton.title = "Imprimir Ordem";
                printButton.dataset.orderNumber = order.numero;
                actionsCell.appendChild(printButton);
                
                // Adicionar listeners
                editButton.addEventListener("click", () => openOrderModal(order.numero));
                printButton.addEventListener("click", () => printOrder(order.numero));
            }
        });
    }

    function renderComprasTable(tableBody, compras) {
        if (!tableBody) return;
        tableBody.innerHTML = "";
        
        if (compras.length === 0) {
            const row = tableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 7;
            cell.textContent = "Nenhuma compra registrada.";
            cell.style.textAlign = "center";
            return;
        }
        
        compras.forEach(compra => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = compra.id;
            row.insertCell().textContent = formatDate(compra.data);
            row.insertCell().textContent = compra.item || "-";
            row.insertCell().textContent = compra.fornecedor || "-";
            row.insertCell().textContent = formatCurrency(compra.valor);
            row.insertCell().textContent = compra.observacao || "-";
            
            // Ações
            const actionsCell = row.insertCell();
            
            // Botão de edição
            const editButton = document.createElement("button");
            editButton.className = "btn-action edit-compra";
            editButton.innerHTML = '<i class="fas fa-pencil-alt"></i>';
            editButton.title = "Editar Compra";
            editButton.dataset.compraId = compra.id;
            actionsCell.appendChild(editButton);
            
            // Adicionar listener
            editButton.addEventListener("click", () => openCompraModal(compra.id));
        });
    }

    function renderContasPagarTable(tableBody, contas) {
        if (!tableBody) return;
        tableBody.innerHTML = "";
        
        if (contas.length === 0) {
            const row = tableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 6;
            cell.textContent = "Nenhuma conta a pagar registrada.";
            cell.style.textAlign = "center";
            return;
        }
        
        contas.forEach(conta => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = conta.id;
            row.insertCell().textContent = conta.descricao || "-";
            row.insertCell().textContent = formatCurrency(conta.valor);
            row.insertCell().textContent = formatDate(conta.vencimento);
            row.insertCell().textContent = conta.status || "Pendente";
            
            // Ações
            const actionsCell = row.insertCell();
            
            // Botão de edição
            const editButton = document.createElement("button");
            editButton.className = "btn-action edit-conta";
            editButton.innerHTML = '<i class="fas fa-pencil-alt"></i>';
            editButton.title = "Editar Conta";
            editButton.dataset.contaId = conta.id;
            actionsCell.appendChild(editButton);
            
            // Botão de marcar como pago (apenas se estiver pendente)
            if (conta.status !== "Pago") {
                const pagarButton = document.createElement("button");
                pagarButton.className = "btn-action pagar-conta";
                pagarButton.innerHTML = '<i class="fas fa-check"></i>';
                pagarButton.title = "Marcar como Pago";
                pagarButton.dataset.contaId = conta.id;
                actionsCell.appendChild(pagarButton);
                
                // Adicionar listener
                pagarButton.addEventListener("click", () => marcarContaComoPaga(conta.id));
            }
            
            // Adicionar listener para edição
            editButton.addEventListener("click", () => openContaModal(conta.id));
        });
    }

    function renderBalanceteTables(entradas, saidas) {
        if (!entradasTableBody || !saidasTableBody) return;
        
        // Limpar tabelas
        entradasTableBody.innerHTML = "";
        saidasTableBody.innerHTML = "";
        
        // Renderizar entradas
        if (entradas.length === 0) {
            const row = entradasTableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 3;
            cell.textContent = "Nenhuma entrada registrada no período.";
            cell.style.textAlign = "center";
        } else {
            entradas.forEach(entrada => {
                const row = entradasTableBody.insertRow();
                row.insertCell().textContent = formatDate(entrada.data);
                row.insertCell().textContent = entrada.descricao;
                row.insertCell().textContent = formatCurrency(entrada.valor);
            });
        }
        
        // Renderizar saídas
        if (saidas.length === 0) {
            const row = saidasTableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 3;
            cell.textContent = "Nenhuma saída registrada no período.";
            cell.style.textAlign = "center";
        } else {
            saidas.forEach(saida => {
                const row = saidasTableBody.insertRow();
                row.insertCell().textContent = formatDate(saida.data);
                row.insertCell().textContent = saida.descricao;
                row.insertCell().textContent = formatCurrency(saida.valor);
            });
        }
    }

    function updateBalanceteKPIs(balancete) {
        if (!balancete) return;
        
        const totalEntradas = balancete.entradas.reduce((sum, entrada) => sum + parseFloat(entrada.valor || 0), 0);
        const totalSaidas = balancete.saidas.reduce((sum, saida) => sum + parseFloat(saida.valor || 0), 0);
        const saldo = totalEntradas - totalSaidas;
        
        if (document.getElementById("balanceteEntradas"))
            document.getElementById("balanceteEntradas").text(formatCurrency(totalEntradas));
        
        if (document.getElementById("balanceteSaidas"))
            document.getElementById("balanceteSaidas").text(formatCurrency(totalSaidas));
        
        if (document.getElementById("balanceteSaldo"))
            document.getElementById("balanceteSaldo").text(formatCurrency(saldo));
        
        // Atualizar gráfico do balancete
        updateBalanceteChart(totalEntradas, totalSaidas);
    }

    // --- Funções de Navegação ---
    function showSection(sectionId) {
        updateDashboard();
        sections.forEach(section => {
            section.classList.remove("active-section");
        });
        
        const targetSection = document.getElementById(sectionId + "Section");
        if (targetSection) {
            targetSection.classList.add("active-section");
        }
        
        navLinks.forEach(link => {
            link.classList.remove("active");
        });
        
        const activeLink = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
        if (activeLink) {
            activeLink.classList.add("active");
        }
        
        // Carregar dados específicos da seção
        if (sectionId === "dashboard") {
            loadDashboardData();
        } else if (sectionId === "ordens") {
            loadAllOrders();
        } else if (sectionId === "producao") {
            loadProducaoOrders();
        } else if (sectionId === "financeiro") {
            loadFinanceiroData();
        } else if (sectionId === "compras") {
            loadCompras();
        } else if (sectionId === "contas_pagar") {
            loadContasPagar();
        } else if (sectionId === "balancete") {
            loadBalancete();
        }
    }

    // --- Funções de Carregamento de Dados ---
    async function loadDashboardData() {
        const orders = await fetchData("/api/orders");
        if (!orders) return;
        
        currentOrders = orders;
        
        // Calcular KPIs
        calculateKPIs(orders);
        
        // Renderizar tabela de ordens recentes
        const recentOrders = [...orders].sort((a, b) => {
            const dateA = new Date(a.data + "T00:00:00");
            const dateB = new Date(b.data + "T00:00:00");
            return dateB - dateA;
        }).slice(0, 5);
        
        renderOrdersTable(recentOrdersTableBody, recentOrders);
    }

    async function loadAllOrders() {
        const orders = await fetchData("/api/orders");
        if (!orders) return;
        
        currentOrders = orders;
        
        // Aplicar filtros
        const filteredOrders = filterOrders(orders);
        
        // Renderizar tabela
        renderOrdersTable(allOrdersTableBody, filteredOrders);
    }

    async function loadProducaoOrders() {
        const orders = await fetchData("/api/orders");
        if (!orders) return;
        
        // Filtrar apenas ordens em produção
        const ordersEmProducao = orders.filter(order => order.status === "Em Produção");
        
        // Renderizar tabela
        renderOrdersTable(producaoTableBody, ordersEmProducao);
    }

    async function loadFinanceiroData() {
        const orders = await fetchData("/api/orders");
        if (!orders) return;
        
        currentOrders = orders;
        
        // Calcular KPIs
        const kpis = calculateKPIs(orders);
        updateKPIs(kpis);
        
        // Renderizar tabela financeira
        renderOrdersTable(financeiroTableBody, orders);
    }

    async function loadCompras() {
        const compras = await fetchData("/api/compras");
        if (!compras) return;
        
        currentCompras = compras;
        
        // Renderizar tabela
        renderComprasTable(comprasTableBody, compras);
    }

    async function loadContasPagar() {
        const contas = await fetchData("/api/contas_pagar");
        if (!contas) return;
        
        currentContasPagar = contas;
        
        // Renderizar tabela
        renderContasPagarTable(contasPagarTableBody, contas);
    }

    async function loadBalancete() {
        const mes = balanceteMesSelect.value;
        const ano = balanceteAnoSelect.value;
        
        // Simular dados de balancete (em produção, isso viria da API)
        const orders = await fetchData("/api/orders");
        const compras = await fetchData("/api/compras");
        const contas = await fetchData("/api/contas_pagar");
        
        if (!orders || !compras || !contas) return;
        
        // Filtrar por mês e ano
        const entradas = orders
            .filter(order => {
                if (!order.data) return false;
                const date = new Date(order.data + "T00:00:00");
                return date.getMonth() + 1 == mes && date.getFullYear() == ano && 
                       (order.status === "Finalizada" || order.status === "Disponível para Retirada");
            })
            .map(order => ({
                data: order.data,
                descricao: `Ordem #${order.numero} - ${order.cliente}`,
                valor: parseFloat(order.valor_entrada || 0)
            }));
        
        const saidas = [
            ...compras.filter(compra => {
                if (!compra.data) return false;
                const date = new Date(compra.data + "T00:00:00");
                return date.getMonth() + 1 == mes && date.getFullYear() == ano;
            }).map(compra => ({
                data: compra.data,
                descricao: `Compra #${compra.id} - ${compra.item}`,
                valor: parseFloat(compra.valor || 0)
            })),
            ...contas.filter(conta => {
                if (!conta.vencimento) return false;
                const date = new Date(conta.vencimento + "T00:00:00");
                return date.getMonth() + 1 == mes && date.getFullYear() == ano && conta.status === "Pago";
            }).map(conta => ({
                data: conta.vencimento,
                descricao: `Conta #${conta.id} - ${conta.descricao}`,
                valor: parseFloat(conta.valor || 0)
            }))
        ];
        
        currentBalancete = { entradas, saidas };
        
        // Atualizar KPIs e tabelas
        updateBalanceteKPIs(currentBalancete);
        renderBalanceteTables(entradas, saidas);
    }

    // --- Funções de Filtro ---
    function filterOrders(orders) {
        const searchTerm = orderSearchInput.value.toLowerCase();
        const vendedorFilter = vendedorFilterInput.value.toLowerCase();
        const statusFilter = statusFilterSelect.value;
        
        return orders.filter(order => {
            // Filtro de busca
            const matchesSearch = !searchTerm || 
                                 order.numero?.toLowerCase().includes(searchTerm) || 
                                 order.cliente?.toLowerCase().includes(searchTerm);
            
            // Filtro de vendedor
            const matchesVendedor = !vendedorFilter || 
                                   order.vendedor?.toLowerCase().includes(vendedorFilter);
            
            // Filtro de status
            const matchesStatus = !statusFilter || order.status === statusFilter;
            
            return matchesSearch && matchesVendedor && matchesStatus;
        });
    }

    // --- Funções de Cálculo ---
    async function calculateKPIs(orders, compras, contasPagar) {
        const kpis = {
            ordens_pendentes: 0,
            ordens_andamento: 0,
            ordens_retirada: 0,
            ordens_finalizadas: 0,
            receita: 0,
            custo_total_finalizadas: 0,
            lucro_bruto_finalizadas: 0,
            valor_para_entrar: 0,
            total_saidas: 0 // Novo KPI
        };
        
        // Calcular KPIs das Ordens
        orders.forEach(order => {
            // Contagem por status
            if (order.status === "Aguardando Aprovação" || order.status === "Aguardando Pagamento") {
                kpis.ordens_pendentes++;
            } else if (order.status === "Em Produção") {
                kpis.ordens_andamento++;
            } else if (order.status === "Disponível para Retirada") {
                kpis.ordens_retirada++;
            } else if (order.status === "Finalizada") {
                kpis.ordens_finalizadas++;
                
                // Valores financeiros (apenas ordens finalizadas)
                kpis.receita += parseFloat(order.valor_total || 0);
                kpis.custo_total_finalizadas += parseFloat(order.custo || 0);
            }
            
            // Valor para entrar (ordens não finalizadas)
            if (order.status !== "Finalizada" && order.status !== "Cancelada") {
                kpis.valor_para_entrar += parseFloat(order.valor_restante || 0);
            }
        });
        
        // Calcular lucro bruto
        kpis.lucro_bruto_finalizadas = kpis.receita - kpis.custo_total_finalizadas;

        // Calcular Total de Saídas (Compras + Contas Pagas)
        if (compras) {
            kpis.total_saidas += compras.reduce((sum, compra) => sum + parseFloat(compra.valor || 0), 0);
        }
        if (contasPagar) {
            kpis.total_saidas += contasPagar
                .filter(conta => conta.status === "Pago")
                .reduce((sum, conta) => sum + parseFloat(conta.valor || 0), 0);
        }
        
        return kpis;
    }

    // --- Funções de Modal ---
    function openOrderModal(orderNumber = null) {
        // Limpar formulário
        orderForm.reset();
        
        // Definir data atual como padrão
        document.getElementById("data").valueAsDate = new Date();
        
        if (orderNumber) {
            // Modo de edição
            modalTitle.textContent = `Editar Ordem #${orderNumber}`;
            
            // Buscar ordem pelo número
            const order = currentOrders.find(o => o.numero === orderNumber);
            if (!order) {
                alert("Ordem não encontrada!");
                return;
            }
            
            // Preencher formulário
            document.getElementById("orderNumero").value = order.numero;
            document.getElementById("cliente").value = order.cliente || "";
            document.getElementById("vendedor").value = order.vendedor || "";
            
            // Tratar material (pode ser array ou string)
            if (Array.isArray(order.material)) {
                document.getElementById("material").value = order.material.join(", ");
            } else {
                document.getElementById("material").value = order.material || "";
            }
            
            document.getElementById("fornecedor").value = order.fornecedor || "";
            document.getElementById("custo").value = order.custo || "";
            document.getElementById("valor_total").value = order.valor_total || "";
            document.getElementById("valor_entrada").value = order.valor_entrada || "";
            document.getElementById("valor_restante").value = order.valor_restante || "";
            document.getElementById("forma_pagamento").value = order.forma_pagamento || "PIX";
            
            if (order.data) {
                document.getElementById("data").value = order.data;
            }
            
            document.getElementById("status").value = order.status || "Aguardando Aprovação";
            
            // Mostrar botão de impressão
            printOrderBtn.style.display = "inline-block";
        } else {
            // Modo de adição
            modalTitle.textContent = "Adicionar Nova Ordem";
            document.getElementById("orderNumero").value = "";
            
            // Esconder botão de impressão
            printOrderBtn.style.display = "none";
        }
        
        // Exibir modal
        orderModal.style.display = "block";
    }

    function closeOrderModal() {
        orderModal.style.display = "none";
    }

    function openCompraModal(compraId = null) {
        // Limpar formulário
        compraForm.reset();
        
        // Definir data atual como padrão
        document.getElementById("compraData").valueAsDate = new Date();
        
        if (compraId) {
            // Modo de edição
            document.getElementById("compraModalTitle").textContent = `Editar Compra #${compraId}`;
            
            // Buscar compra pelo ID
            const compra = currentCompras.find(c => c.id === compraId);
            if (!compra) {
                alert("Compra não encontrada!");
                return;
            }
            
            // Preencher formulário
            document.getElementById("compraId").value = compra.id;
            document.getElementById("compraItem").value = compra.item || "";
            document.getElementById("compraFornecedor").value = compra.fornecedor || "";
            document.getElementById("compraValor").value = compra.valor || "";
            document.getElementById("compraObservacao").value = compra.observacao || "";
            
            if (compra.data) {
                document.getElementById("compraData").value = compra.data;
            }
        } else {
            // Modo de adição
            document.getElementById("compraModalTitle").textContent = "Adicionar Nova Compra";
            document.getElementById("compraId").value = "";
        }
        
        // Exibir modal
        compraModal.style.display = "block";
    }

    function closeCompraModal() {
        compraModal.style.display = "none";
    }

    function openContaModal(contaId = null) {
        // Limpar formulário
        contaForm.reset();
        
        // Definir data atual como padrão
        document.getElementById("contaVencimento").valueAsDate = new Date();
        
        if (contaId) {
            // Modo de edição
            document.getElementById("contaModalTitle").textContent = `Editar Conta #${contaId}`;
            
            // Buscar conta pelo ID
            const conta = currentContasPagar.find(c => c.id === contaId);
            if (!conta) {
                alert("Conta não encontrada!");
                return;
            }
            
            // Preencher formulário
            document.getElementById("contaId").value = conta.id;
            document.getElementById("contaDescricao").value = conta.descricao || "";
            document.getElementById("contaValor").value = conta.valor || "";
            document.getElementById("contaStatus").value = conta.status || "Pendente";
            
            if (conta.vencimento) {
                document.getElementById("contaVencimento").value = conta.vencimento;
            }
        } else {
            // Modo de adição
            document.getElementById("contaModalTitle").textContent = "Adicionar Nova Conta a Pagar";
            document.getElementById("contaId").value = "";
        }
        
        // Exibir modal
        contaModal.style.display = "block";
    }

    function closeContaModal() {
        contaModal.style.display = "none";
    }

    // --- Funções de Ação ---
    async function saveOrder(event) {
        event.preventDefault();
        
        // Função auxiliar para limpar valores monetários
        function cleanCurrencyValue(value) {
            if (typeof value !== 'string') {
                return value; // Retorna o valor original se não for string
            }
            // Remove "R$", espaços, pontos de milhar e substitui vírgula decimal por ponto
            return value.replace(/R\$\s?|\./g, '').replace(',', '.');
        }

        // Validar campos obrigatórios
        const cliente = document.getElementById("cliente").value;
        const vendedor = document.getElementById("vendedor").value;
        const material = document.getElementById("material").value;
        const valorTotalRaw = document.getElementById("valor_total").value;
        const custoRaw = document.getElementById("custo").value || "0";
        const data = document.getElementById("data").value;
        const status = document.getElementById("status").value;
        
        if (!cliente || !vendedor || !material || !valorTotalRaw || !data || !status) {
            alert("Por favor, preencha todos os campos obrigatórios!");
            return;
        }

        // Limpar e validar valores numéricos
        const valorTotalClean = cleanCurrencyValue(valorTotalRaw);
        const custoClean = cleanCurrencyValue(custoRaw);

        const valorTotal = parseFloat(valorTotalClean);
        const custo = parseFloat(custoClean);

        if (isNaN(valorTotal) || isNaN(custo)) {
            alert("Valores monetários inválidos. Use apenas números e vírgula/ponto decimal.");
            return;
        }
        
        // Preparar dados
        const orderData = {
            cliente: cliente,
            vendedor: vendedor,
            material: material, // O backend já trata a conversão para lista
            fornecedor: document.getElementById("fornecedor").value,
            valor_total: valorTotal, // Enviar valor numérico limpo
            custo: custo, // Enviar valor numérico limpo
            forma_pagamento: document.getElementById("forma_pagamento").value,
            data: data,
            status: status
        };
        
        // O backend calculará entrada e restante
        // delete orderData.valor_entrada;
        // delete orderData.valor_restante;
        
        const orderNumero = document.getElementById("orderNumero").value;
        let result;
        
        if (orderNumero) {
            // Atualizar ordem existente
            result = await putData(`/api/orders/${orderNumero}`, orderData);
        } else {
            // Criar nova ordem
            result = await postData("/api/orders", orderData);
        }
        
        if (result && result.success) {
            alert(orderNumero ? "Ordem atualizada com sucesso!" : "Ordem criada com sucesso!");
            closeOrderModal();
            
            // Recarregar dados da seção atual
            const activeSection = document.querySelector(".dashboard-section.active-section");
            if (activeSection) {
                const sectionId = activeSection.id.replace("Section", "");
                showSection(sectionId);
            }
        }
    }

    async function saveCompra(event) {
        event.preventDefault();
        
        // Validar campos obrigatórios
        const item = document.getElementById("compraItem").value;
        const fornecedor = document.getElementById("compraFornecedor").value;
        const valor = document.getElementById("compraValor").value;
        const data = document.getElementById("compraData").value;
        
        if (!item || !fornecedor || !valor || !data) {
            alert("Por favor, preencha todos os campos obrigatórios!");
            return;
        }
        
        // Preparar dados
        const compraData = {
            item: item,
            fornecedor: fornecedor,
            valor: parseFloat(valor),
            data: data,
            observacao: document.getElementById("compraObservacao").value
        };
        
        const compraId = document.getElementById("compraId").value;
        let result;
        
        if (compraId) {
            // Atualizar compra existente
            result = await putData(`/api/compras/${compraId}`, compraData);
        } else {
            // Criar nova compra
            result = await postData("/api/compras", compraData);
        }
        
        if (result && result.success) {
            alert(compraId ? "Compra atualizada com sucesso!" : "Compra registrada com sucesso!");
            closeCompraModal();
            
            // Recarregar dados
            loadCompras();
        }
    }

    async function saveConta(event) {
        event.preventDefault();
        
        // Validar campos obrigatórios
        const descricao = document.getElementById("contaDescricao").value;
        const valor = document.getElementById("contaValor").value;
        const vencimento = document.getElementById("contaVencimento").value;
        const status = document.getElementById("contaStatus").value;
        
        if (!descricao || !valor || !vencimento || !status) {
            alert("Por favor, preencha todos os campos obrigatórios!");
            return;
        }
        
        // Preparar dados
        const contaData = {
            descricao: descricao,
            valor: parseFloat(valor),
            vencimento: vencimento,
            status: status
        };
        
        const contaId = document.getElementById("contaId").value;
        let result;
        
        if (contaId) {
            // Atualizar conta existente
            result = await putData(`/api/contas_pagar/${contaId}`, contaData);
        } else {
            // Criar nova conta
            result = await postData("/api/contas_pagar", contaData);
        }
        
        if (result && result.success) {
            alert(contaId ? "Conta atualizada com sucesso!" : "Conta registrada com sucesso!");
            closeContaModal();
            
            // Recarregar dados
            loadContasPagar();
        }
    }

    async function marcarContaComoPaga(contaId) {
        if (!contaId) return;
        
        // Confirmar ação
        if (!confirm("Deseja marcar esta conta como paga?")) return;
        
        // Buscar conta pelo ID
        const conta = currentContasPagar.find(c => c.id === contaId);
        if (!conta) {
            alert("Conta não encontrada!");
            return;
        }
        
        // Atualizar status
        const contaData = { ...conta, status: "Pago" };
        
        const result = await putData(`/api/contas_pagar/${contaId}`, contaData);
        
        if (result && result.success) {
            alert("Conta marcada como paga com sucesso!");
            
            // Recarregar dados
            loadContasPagar();
        }
    }

    function printOrder(orderNumber) {
        if (!orderNumber) return;
        
        // Buscar ordem pelo número
        const order = currentOrders.find(o => o.numero === orderNumber);
        if (!order) {
            alert("Ordem não encontrada!");
            return;
        }
        
        // Criar conteúdo para impressão
        let printContent = `
            <div class="print-container" style="padding: 20px; font-family: Arial, sans-serif;">
                <h1 style="text-align: center; margin-bottom: 20px;">CUBOGRAF</h1>
                <h2 style="text-align: center; margin-bottom: 30px;">Ordem de Serviço #${order.numero}</h2>
                
                <div style="margin-bottom: 20px;">
                    <p><strong>Cliente:</strong> ${order.cliente || "-"}</p>
                    <p><strong>Vendedor:</strong> ${order.vendedor || "-"}</p>
                    <p><strong>Data:</strong> ${formatDate(order.data)}</p>
                    <p><strong>Status:</strong> ${order.status || "-"}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p><strong>Material:</strong> ${Array.isArray(order.material) ? order.material.join(", ") : order.material || "-"}</p>
                    <p><strong>Fornecedor:</strong> ${order.fornecedor || "-"}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p><strong>Valor Total:</strong> ${formatCurrency(order.valor_total)}</p>
                    <p><strong>Entrada (50%):</strong> ${formatCurrency(order.valor_entrada)}</p>
                    <p><strong>Restante a Pagar:</strong> ${formatCurrency(order.valor_restante)}</p>
                    <p><strong>Forma de Pagamento:</strong> ${order.forma_pagamento || "-"}</p>
                </div>
                
                <div style="margin-top: 50px; text-align: center;">
                    <p>_______________________________</p>
                    <p>Assinatura do Cliente</p>
                </div>
                
                <div style="margin-top: 30px; text-align: center;">
                    <p>_______________________________</p>
                    <p>Assinatura do Vendedor</p>
                </div>
            </div>
        `;
        
        // Criar janela de impressão
        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <html>
                <head>
                    <title>Ordem de Serviço #${order.numero} - CUBOGRAF</title>
                </head>
                <body>
                    ${printContent}
                    <script>
                        window.onload = function() {
                            window.print();
                            window.setTimeout(function() {
                                window.close();
                            }, 500);
                        };
                    </script>
                </body>
            </html>
        `);
        printWindow.document.close();
    }

    // --- Funções de Gráficos ---
    function updateBalanceteChart(entradas, saidas) {
        const ctx = document.getElementById("balanceteChart")?.getContext("2d");
        if (!ctx) return;
        
        // Destruir gráfico existente se houver
        if (window.balanceteChart) {
            Chart.getChart("balanceteChart")?.destroy();
        }
        
        // Criar novo gráfico
        window.balanceteChart = new Chart(ctx, {
            type: "pie",
            data: {
                labels: ["Entradas", "Saídas"],
                datasets: [{
                    data: [entradas, saidas],
                    backgroundColor: ["#4CAF50", "#F44336"],
                    borderColor: ["#388E3C", "#D32F2F"],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "right",
                        labels: {
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || "";
                                const value = context.raw;
                                return `${label}: ${formatCurrency(value)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // --- Event Listeners ---
    // Navegação
    navLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();
            const sectionId = this.getAttribute("data-section");
            showSection(sectionId);
        });
    });

    // Busca global
    if (mainSearchInput) {
        mainSearchInput.addEventListener("input", function() {
            const searchTerm = this.value.toLowerCase();
            
            // Se estiver na seção de ordens, aplicar filtro
            const activeSection = document.querySelector(".dashboard-section.active-section");
            if (activeSection && activeSection.id === "ordensSection") {
                orderSearchInput.value = searchTerm;
                const filteredOrders = filterOrders(currentOrders);
                renderOrdersTable(allOrdersTableBody, filteredOrders);
            }
        });
    }

    // Filtros de ordens
    if (orderSearchInput) {
        orderSearchInput.addEventListener("input", function() {
            const filteredOrders = filterOrders(currentOrders);
            renderOrdersTable(allOrdersTableBody, filteredOrders);
        });
    }

    if (vendedorFilterInput) {
        vendedorFilterInput.addEventListener("input", function() {
            const filteredOrders = filterOrders(currentOrders);
            renderOrdersTable(allOrdersTableBody, filteredOrders);
        });
    }

    if (statusFilterSelect) {
        statusFilterSelect.addEventListener("change", function() {
            const filteredOrders = filterOrders(currentOrders);
            renderOrdersTable(allOrdersTableBody, filteredOrders);
        });
    }

    // Modais
    if (addOrderBtn) {
        addOrderBtn.addEventListener("click", () => openOrderModal());
    }

    if (addOrderBtnDashboard) {
        addOrderBtnDashboard.addEventListener("click", () => openOrderModal());
    }

    if (closeButton) {
        closeButton.addEventListener("click", closeOrderModal);
    }

    if (addCompraBtn) {
        addCompraBtn.addEventListener("click", () => openCompraModal());
    }

    if (closeCompraButton) {
        closeCompraButton.addEventListener("click", closeCompraModal);
    }

    if (addContaBtn) {
        addContaBtn.addEventListener("click", () => openContaModal());
    }

    if (closeContaButton) {
        closeContaButton.addEventListener("click", closeContaModal);
    }

    // Formulários
    if (orderForm) {
        orderForm.addEventListener("submit", saveOrder);
    }

    if (compraForm) {
        compraForm.addEventListener("submit", saveCompra);
    }

    if (contaForm) {
        contaForm.addEventListener("submit", saveConta);
    }

    // Balancete
    if (atualizarBalanceteBtn) {
        atualizarBalanceteBtn.addEventListener("click", loadBalancete);
    }

    // Fechar modais ao clicar fora
    window.addEventListener("click", function(event) {
        if (event.target === orderModal) {
            closeOrderModal();
        } else if (event.target === compraModal) {
            closeCompraModal();
        } else if (event.target === contaModal) {
            closeContaModal();
        }
    });

    // Inicialização
    // Definir data atual nos selects do balancete
    if (balanceteMesSelect && balanceteAnoSelect) {
        const now = new Date();
        balanceteMesSelect.value = now.getMonth() + 1;
        
        // Verificar se o ano atual está nas opções
        const anoAtual = now.getFullYear().toString();
        let anoEncontrado = false;
        
        for (let i = 0; i < balanceteAnoSelect.options.length; i++) {
            if (balanceteAnoSelect.options[i].value === anoAtual) {
                anoEncontrado = true;
                balanceteAnoSelect.selectedIndex = i;
                break;
            }
        }
        
        // Se não encontrou, adicionar o ano atual
        if (!anoEncontrado) {
            const option = document.createElement("option");
            option.value = anoAtual;
            option.textContent = anoAtual;
            balanceteAnoSelect.appendChild(option);
            balanceteAnoSelect.value = anoAtual;
        }
    }

    // Carregar dados iniciais
    showSection("dashboard");

    // Função para atualizar o dashboard
    function updateDashboard() {
        $.get('/api/dashboard/stats')
            .done(function(data) {
                // Atualizar cards de estatísticas
                $('#kpiOrdensPendentes').text(data.orders_aguardando);
                $('#kpiOrdensAndamento').text(data.orders_em_producao);
                $('#kpiOrdensRetirada').text(data.orders_retirada);
                $('#kpiOrdensFinalizadas').text(data.orders_finalizados);

                // Atualizar cards financeiros (apenas para admin)
                if (USER_ROLE === 'admin') {
                    $('#kpiReceita').text(formatMoney(data.receita_total));
                    $('#kpiCusto').text(formatMoney(data.custos_total));
                    $('#kpiLucro').text(formatMoney(data.lucro_total));
                    $('#kpiParaEntrar').text(formatMoney(data.valores_receber));
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error('Erro ao atualizar dashboard:', errorThrown);
            });
    }

    // Atualizar dashboard a cada 30 segundos
    $(document).ready(function() {
        updateDashboard();
        setInterval(updateDashboard, 30000); 
    });
});

// Gráfico de vendedores
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se o elemento do gráfico existe
    const ctx = document.getElementById('vendedoresChart');
    if (!ctx) return;

    // Função para carregar dados e criar o gráfico
    async function loadVendedoresChart() {
        try {
            // Buscar dados das ordens
            const response = await fetch('/api/orders');
            if (!response.ok) {
                throw new Error('Erro ao buscar dados das ordens');
            }
            
            const orders = await response.json();
            
            // Processar dados para o gráfico
            const vendedoresCount = {};
            let totalVendas = 0;
            
            orders.forEach(order => {
                if (!order.vendedor || order.status === 'Cancelada') return;
                
                const vendedor = order.vendedor.trim();
                const valorTotal = parseFloat(order.valor_total || 0);
                
                if (!vendedoresCount[vendedor]) {
                    vendedoresCount[vendedor] = 0;
                }
                
                vendedoresCount[vendedor] += valorTotal;
                totalVendas += valorTotal;
            });
            
            // Ordenar vendedores por valor total (do maior para o menor)
            const sortedVendedores = Object.entries(vendedoresCount)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8); // Limitar aos 8 vendedores com mais vendas
            
            const labels = sortedVendedores.map(item => item[0]);
            const data = sortedVendedores.map(item => item[1]);
            
            // Cores para o gráfico
            const backgroundColors = [
                '#212121', // Preto (cor secundária)
                '#424242', // Cinza escuro
                '#616161', // Cinza médio
                '#757575', // Cinza claro
                '#9E9E9E', // Cinza mais claro
                '#FFC107', // Amarelo ouro (cor primária)
                '#FFD54F', // Amarelo claro
                '#FFE082'  // Amarelo mais claro
            ];
            
            // Criar o gráfico
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: backgroundColors,
                        borderColor: '#ffffff',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                font: {
                                    size: 12
                                },
                                padding: 15
                            }
                        },
                        title: {
                            display: false,
                            text: 'Vendas por Vendedor'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw;
                                    const percentage = Math.round((value / totalVendas) * 100);
                                    return `${label}: ${value.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Erro ao carregar gráfico de vendedores:', error);
        }
    }
    
    // Carregar o gráfico
    loadVendedoresChart();
});

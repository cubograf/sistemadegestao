// Gráfico de materiais
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se o elemento do gráfico existe
    const ctx = document.getElementById('materialsChart');
    if (!ctx) return;

        
    
    // Função para carregar dados e criar o gráfico
    async function loadMaterialsChart() {
        try {

            Chart.getChart("materialsChart")?.destroy()
            
            // Buscar dados das ordens
            const response = await fetch('/api/orders');
            if (!response.ok) {
                throw new Error('Erro ao buscar dados das ordens');
            }
            
            const orders = await response.json();
            
            // Processar dados para o gráfico
            const materialsCount = {};
            
            orders.forEach(order => {
                if (!order.material) return;
                
                // Tratar material como array ou string
                let materials = [];
                if (Array.isArray(order.material)) {
                    materials = order.material;
                } else if (typeof order.material === 'string') {
                    materials = [order.material];
                }
                
                materials.forEach(material => {
                    if (material && material.trim()) {
                        const trimmedMaterial = material.trim();
                        materialsCount[trimmedMaterial] = (materialsCount[trimmedMaterial] || 0) + 1;
                    }
                });
            });
            
            // Ordenar materiais por contagem (do maior para o menor)
            const sortedMaterials = Object.entries(materialsCount)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8); // Limitar aos 8 materiais mais comuns
            
            const labels = sortedMaterials.map(item => item[0]);
            const data = sortedMaterials.map(item => item[1]);
            
            // Cores para o gráfico
            const backgroundColors = [
                '#FFC107', // Amarelo ouro (cor primária)
                '#FFD54F', // Amarelo claro
                '#FFE082', // Amarelo mais claro
                '#FFECB3', // Amarelo muito claro
                '#FFF8E1', // Amarelo quase branco
                '#212121', // Preto (cor secundária)
                '#424242', // Cinza escuro
                '#616161'  // Cinza médio
            ];
            
            // Criar o gráfico
            new Chart(ctx, {
                type: 'pie',
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
                            text: 'Materiais Mais Utilizados'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Erro ao carregar gráfico de materiais:', error);
        }
    }
    
    // Carregar o gráfico
    loadMaterialsChart();
});

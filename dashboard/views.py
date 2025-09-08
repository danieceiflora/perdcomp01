from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, F, Q, Func, FloatField
from django.db.models.functions import Trunc, Abs
from django.utils import timezone
import json

from clientes_parceiros.models import ClientesParceiros
from adesao.models import Adesao
from lancamentos.models import Lancamentos
from empresas.models import Empresa

def is_admin_or_staff(user):
    """Verificar se o usuário é admin ou staff"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin_or_staff)
def dashboard_view(request):
    """
    View para o dashboard administrativo.
    Exibe métricas e gráficos sobre parceiros, clientes e créditos recuperados.
    """
    # Contagem correta de parceiros (registros com tipo_parceria='parceiro')
    parceiros = ClientesParceiros.objects.filter(
        tipo_parceria='parceiro',
        ativo=True
    ).values('id_company_vinculada').distinct().count()
    
    # Contagem correta de clientes (registros com tipo_parceria='cliente')
    clientes = ClientesParceiros.objects.filter(
        tipo_parceria='cliente',
        ativo=True
    ).values('id_company_vinculada').distinct().count()
    
    # Crédito recuperado por parceiro
    credito_por_parceiro = []
    parceiros_ativos = ClientesParceiros.objects.filter(
        tipo_parceria='parceiro',
        ativo=True
    ).select_related('id_company_vinculada').distinct()
    
    for parceiro in parceiros_ativos:
        # Encontra todos os clientes deste parceiro
        # Os clientes são empresas onde id_company_base é a empresa do parceiro
        clientes_do_parceiro = ClientesParceiros.objects.filter(
            id_company_base=parceiro.id_company_vinculada,
            tipo_parceria='cliente',
            ativo=True
        ).values_list('id_company_vinculada', flat=True)
        
        # Calcula o crédito total recuperado para estes clientes
        # Considerando lançamentos de débito (sinal='-') que representam créditos utilizados
        total_credito = Lancamentos.objects.filter(
            id_adesao__cliente__id_company_vinculada__in=clientes_do_parceiro,
            sinal='-'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        # Nome do parceiro
        nome_parceiro = parceiro.id_company_vinculada.razao_social
        
        credito_por_parceiro.append({
            'parceiro': nome_parceiro,
            'total_credito': total_credito
        })
    
    # Convertendo valores negativos para positivos e ordenando pela magnitude
    for item in credito_por_parceiro:
        item['total_credito'] = abs(item['total_credito'])
        
    # Ordenando a lista por valor de crédito
    credito_por_parceiro = sorted(
        credito_por_parceiro, 
        key=lambda x: x['total_credito'], 
        reverse=True
    )[:5]
    
    # Clientes com mais crédito recuperado
    # Usamos o valor absoluto da soma para ordenar corretamente
    top_clientes = Lancamentos.objects.filter(
        sinal='-'  # Sinal negativo representa crédito recuperado/utilizado
    ).values(
        'id_adesao__cliente__id_company_vinculada__razao_social'
    ).annotate(
        total_credito=Sum('valor')
    ).order_by('total_credito')[:5]  # Ordem ascendente, pois os valores são negativos
    
    # Dados para o gráfico de crédito recuperado por mês
    # Últimos 12 meses
    hoje = timezone.now()
    doze_meses_atras = hoje - timezone.timedelta(days=365)
    
    credito_por_mes = Lancamentos.objects.filter(
        data_lancamento__gte=doze_meses_atras,
        sinal='-'  # Sinal negativo representa crédito recuperado/utilizado
    ).annotate(
        mes=Trunc('data_lancamento', 'month')
    ).values(
        'mes'
    ).annotate(
        total=Sum('valor')
    ).order_by('mes')
    
    # Formatando dados para o gráfico
    labels = []
    valores = []
    total_credito = 0
    
    try:
        print("Dados do crédito por mês:", list(credito_por_mes))
        
        if not credito_por_mes:
            # Se não há dados mensais, vamos calcular o total a partir dos lançamentos
            total_credito_recuperado = Lancamentos.objects.filter(
                sinal='-'  # Sinal negativo representa crédito recuperado/utilizado
            ).aggregate(
                total=Sum('valor')
            )['total'] or 0
            # Usamos o valor absoluto do total
            total_credito = abs(float(total_credito_recuperado))
            print("Total de crédito calculado diretamente:", total_credito)
        else:
            for item in credito_por_mes:
                mes_formatado = item['mes'].strftime('%b/%Y') if hasattr(item['mes'], 'strftime') else str(item['mes'])
                labels.append(mes_formatado)
                # Usamos o valor absoluto já que estamos lidando com valores negativos
                valor_item = abs(float(item['total'])) if item['total'] else 0
                valores.append(valor_item)
                total_credito += valor_item
                print(f"Mês: {mes_formatado}, Valor: {valor_item}")
        
        # Convertendo para JSON
        labels_json = json.dumps(labels)
        valores_json = json.dumps(valores)
        print(f"Total calculado: {total_credito}")
        print(f"Labels JSON: {labels_json}")
        print(f"Valores JSON: {valores_json}")
        
    except Exception as e:
        print(f"Erro ao processar dados do gráfico: {str(e)}")
        import traceback
        traceback.print_exc()
        labels_json = json.dumps([])
        valores_json = json.dumps([])
        total_credito = 0
    
    # Cálculo de Crédito Compensado/Utilizado e Saldo de Crédito para o cliente logado
    credito_compensado = 0
    saldo_credito = 0
    if hasattr(request.user, 'profile') and request.user.profile.empresa_vinculada:
        empresa_cliente = request.user.profile.empresa_vinculada
        # Adesões relacionadas ao cliente
        adesoes_cliente = Adesao.objects.filter(cliente__id_company_vinculada=empresa_cliente)
        for adesao in adesoes_cliente:
            # Saldo inicial da adesão
            saldo_inicial = adesao.saldo_inicial if hasattr(adesao, 'saldo_inicial') else 0
            # Total de lançamentos realizados para a adesão
            total_lancamentos = Lancamentos.objects.filter(id_adesao=adesao).aggregate(total=Sum('valor'))['total'] or 0
            # Crédito compensado: saldo inicial - total de lançamentos
            credito_compensado += saldo_inicial - total_lancamentos
            # Saldo de crédito: soma dos saldos atuais das adesões
            saldo_credito += adesao.saldo_restante if hasattr(adesao, 'saldo_restante') and adesao.saldo_restante is not None else 0
    
    # Contexto para o template
    context = {
        'total_parceiros': parceiros,
        'total_clientes': clientes,
        'credito_por_parceiro': credito_por_parceiro,
        'top_clientes': top_clientes,
        'labels_grafico': labels_json,
        'valores_grafico': valores_json,
        'total_credito': total_credito,
        'credito_compensado': credito_compensado,
        'saldo_credito': saldo_credito,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

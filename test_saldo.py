#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perdcomp.settings')
django.setup()

from adesao.models import Adesao
from lancamentos.models import Lancamentos
from datetime import datetime
from django.utils import timezone

def test_saldo_logic():
    """
    Testa a lógica de atualização de saldo dos lançamentos
    """
    print("=== Teste de Lógica de Saldo ===")
    
    # Busca uma adesão existente
    adesao = Adesao.objects.first()
    if not adesao:
        print("❌ Nenhuma adesão encontrada no banco de dados")
        return
    
    print(f"📋 Adesão: {adesao.perdcomp}")
    print(f"💰 Saldo inicial: R$ {adesao.saldo or 0:.2f}")
    print(f"💰 Saldo atual: R$ {adesao.saldo_atual or 0:.2f}")
    
    # Se saldo_atual está None, inicializa
    if adesao.saldo_atual is None:
        adesao.saldo_atual = adesao.saldo or 0
        adesao.save(update_fields=['saldo_atual'])
        print(f"💰 Saldo atual inicializado: R$ {adesao.saldo_atual:.2f}")
    
    # Teste 1: Crédito (deve aumentar o saldo)
    print("\n🔍 Teste 1: Lançamento de Crédito (+100)")
    saldo_antes = adesao.saldo_atual
    
    lancamento_credito = Lancamentos(
        id_adesao=adesao,
        data_lancamento=timezone.now(),
        valor=100.0,
        sinal='+',
        tipo='Gerado',
        descricao='Teste de crédito'
    )
    
    try:
        lancamento_credito.save()
        adesao.refresh_from_db()
        print(f"✅ Saldo antes: R$ {saldo_antes:.2f}")
        print(f"✅ Saldo depois: R$ {adesao.saldo_atual:.2f}")
        print(f"✅ Diferença: R$ {adesao.saldo_atual - saldo_antes:.2f}")
        
        # Teste 2: Débito (deve diminuir o saldo)
        print("\n🔍 Teste 2: Lançamento de Débito (-50)")
        saldo_antes = adesao.saldo_atual
        
        lancamento_debito = Lancamentos(
            id_adesao=adesao,
            data_lancamento=timezone.now(),
            valor=50.0,
            sinal='-',
            tipo='Gerado',
            descricao='Teste de débito'
        )
        
        lancamento_debito.save()
        adesao.refresh_from_db()
        print(f"✅ Saldo antes: R$ {saldo_antes:.2f}")
        print(f"✅ Saldo depois: R$ {adesao.saldo_atual:.2f}")
        print(f"✅ Diferença: R$ {adesao.saldo_atual - saldo_antes:.2f}")
        
        # Teste 3: Débito que excede saldo (deve falhar)
        print(f"\n🔍 Teste 3: Débito maior que saldo atual (-{adesao.saldo_atual + 100})")
        
        lancamento_invalido = Lancamentos(
            id_adesao=adesao,
            data_lancamento=timezone.now(),
            valor=adesao.saldo_atual + 100,
            sinal='-',
            tipo='Gerado',
            descricao='Teste de débito inválido'
        )
        
        try:
            lancamento_invalido.clean()
            lancamento_invalido.save()
            print("❌ ERRO: Lançamento inválido foi salvo!")
        except Exception as e:
            print(f"✅ Validação funcionou: {str(e)}")
        
        print(f"\n📊 Saldo final: R$ {adesao.saldo_atual:.2f}")
        
        # Listar últimos lançamentos
        print("\n📋 Últimos lançamentos:")
        ultimos = Lancamentos.objects.filter(id_adesao=adesao).order_by('-data_criacao')[:5]
        for lanc in ultimos:
            print(f"  {lanc.data_lancamento.strftime('%d/%m/%Y %H:%M')} | {lanc.sinal}R$ {lanc.valor:.2f} | Saldo: R$ {lanc.saldo_restante or 0:.2f}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")

if __name__ == "__main__":
    test_saldo_logic()

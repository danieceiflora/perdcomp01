# PERDCOMP - Sistema de Gestão de Créditos e Relacionamentos Empresariais

## Objetivo
O PERDCOMP é um sistema web desenvolvido em Django para gerenciar relacionamentos empresariais, adesões a teses de crédito, lançamentos financeiros e o acompanhamento de créditos recuperados. O sistema visa facilitar o controle de vínculos entre empresas, gestão de clientes/parceiros, adesões a oportunidades de crédito e o monitoramento de resultados financeiros.

## Funcionalidades Principais
- **Gestão de Empresas**: Cadastro e administração de empresas, com dados como CNPJ, razão social, nome fantasia e logomarca.
- **Relacionamentos Empresariais**: Registro de vínculos entre empresas (clientes e parceiros), com tipos de relacionamento personalizados.
- **Gestão de Contatos**: Cadastro de contatos comerciais, pessoais e celulares vinculados às empresas.
- **Adesão a Teses de Crédito**: Controle de adesões de empresas a diferentes teses de crédito, com saldo inicial, saldo atual e status.
- **Lançamentos Financeiros**: Registro de lançamentos de crédito e débito relacionados às adesões, com histórico detalhado e cálculo automático de saldos.
- **Gestão de Teses e Correções**: Cadastro de teses de crédito, índices de correção e tipos de documentos relacionados.
- **Dashboard Gerencial**: Visualização de métricas, gráficos e relatórios sobre parceiros, clientes, créditos recuperados e desempenho financeiro.
- **Administração Personalizada**: Interface administrativa customizada com Django Jazzmin, incluindo navegação facilitada e visual moderno.
- **Autenticação e Segurança**: Controle de acesso por usuários, autenticação JWT e permissões diferenciadas para administradores e clientes.

## Tecnologias Utilizadas
- Python 3
- Django 5
- Django REST Framework
- SQLite (padrão, pode ser adaptado para outros bancos)
- Jazzmin (admin customizado)
- Bootstrap (frontend)

## Estrutura de Pastas
- `accounts/` - Usuários e perfis
- `clientes_parceiros/` - Relacionamentos entre empresas
- `empresas/` - Cadastro de empresas
- `contatos/` - Contatos empresariais
- `adesao/` - Adesões a teses de crédito
- `lancamentos/` - Lançamentos financeiros
- `correcao/` - Teses, índices e correções
- `dashboard/` - Visão gerencial e relatórios
- `utils/` - Utilitários e filtros customizados

## Como rodar o projeto
1. Instale as dependências: `pip install -r requirements.txt`
2. Execute as migrações: `python manage.py migrate`
3. Crie um superusuário: `python manage.py createsuperuser`
4. Inicie o servidor: `python manage.py runserver`
5. Acesse o sistema em `http://localhost:8000/`

## Observações
- O sistema está preparado para customizações e integrações futuras.
- O painel administrativo é acessível apenas para usuários autorizados.
- O sistema utiliza autenticação JWT para APIs.

---
Desenvolvido por danieceiflora

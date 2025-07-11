from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .models import ClientesParceiros, TipoRelacionamento
from .forms import TipoRelacionamentoForm, EmpresaClienteParceiroForm, ClientesParceirosForm
from contatos.models import Contatos
from django.contrib import messages
class NewTipoRelacionamentoView(CreateView):
    model = TipoRelacionamento
    template_name = 'cadastrar_tipo_relacionamento.html'
    form_class = TipoRelacionamentoForm
    success_url = '/clientes-parceiros/tipo-relacionamento/'
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_relacionamento'] = TipoRelacionamento.objects.all()
        return context
class TipoRelacionamentoListView(ListView):
    model = TipoRelacionamento
    template_name = 'cadastrar_tipo_relacionamento.html'
    context_object_name = 'tipos_relacionamento'

class TipoRelacionamentoUpdateView(UpdateView):
    model = TipoRelacionamento
    template_name = 'cadastrar_tipo_relacionamento.html'
    form_class = TipoRelacionamentoForm
    success_url = '/clientes-parceiros/tipo-relacionamento/'

class TipoRelacionamentoDeleteView(DeleteView):
    model = TipoRelacionamento
    template_name = 'excluir_tipo_relacionamento.html'
    success_url = reverse_lazy('lista_tipos_relacionamento')

class NewClienteParceiroView(CreateView):
    template_name = 'cadastrar_cliente_parceiro.html'
    form_class = EmpresaClienteParceiroForm
    success_url = reverse_lazy('lista_clientes_parceiros')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_contato_options'] = Contatos.tipo_contato_options
        return context
        
    def form_valid(self, form):
        from empresas.models import Empresa
        from contatos.models import Contatos
        
        # Pegar a empresa base selecionada (já existente no sistema)
        empresa_base = form.cleaned_data.get('empresa_base')
        if not empresa_base:
            form.add_error('empresa_base', 'É necessário selecionar uma empresa base.')
            return self.form_invalid(form)
            
        # Criar uma nova empresa vinculada
        empresa_vinculada = Empresa.objects.create(
            cnpj=form.cleaned_data['cnpj'],
            razao_social=form.cleaned_data['razao_social'],
            nome_fantasia=form.cleaned_data['nome_fantasia'],
            codigo_origem=form.cleaned_data['codigo_origem'],
            logomarca=form.cleaned_data.get('logomarca')
        )
        
        # Não salvar o formulário diretamente, pois precisamos configurar os campos do modelo
        cliente_parceiro = form.instance
        cliente_parceiro.id_company_base = empresa_base
        cliente_parceiro.id_company_vinculada = empresa_vinculada
        # Verificar se a data de início foi fornecida e processá-la corretamente
        data_inicio = form.cleaned_data.get('data_inicio_parceria')
        if data_inicio:
            cliente_parceiro.data_inicio_parceria = data_inicio
        cliente_parceiro.save()
        
        # Processar os contatos (obrigatório)
        contact_count = int(self.request.POST.get('contact_count', 0))
        
        # Verificar se pelo menos um contato foi adicionado
        if contact_count == 0:
            form.add_error(None, "É obrigatório adicionar pelo menos um contato.")
            return self.form_invalid(form)
            
        # Processar cada formulário de contato
        contato_adicionado = False
        for i in range(1, contact_count + 1):
            tipo_contato = self.request.POST.get(f'tipo_contato_{i}')
            telefone = self.request.POST.get(f'telefone_{i}')
            email = self.request.POST.get(f'email_{i}')
            site = self.request.POST.get(f'site_{i}')
            
            # Criar um novo registro de contato se os dados forem fornecidos
            if telefone or email or site:
                Contatos.objects.create(
                    tipo_contato=tipo_contato,
                    empresa_base=empresa_base,
                    empresa_vinculada=empresa_vinculada,
                    telefone=telefone or "",
                    email=email or "",
                    site=site or ""
                )
                contato_adicionado = True
                
        # Se nenhum contato foi adicionado (campos vazios), retornar um erro
        if not contato_adicionado:
            # Remover registros criados anteriormente para evitar dados orfãos
            cliente_parceiro.delete()
            empresa_vinculada.delete()  # Só excluímos a empresa vinculada, não a empresa base
            form.add_error(None, "É obrigatório preencher pelo menos um contato com telefone, email ou site.")
            return self.form_invalid(form)
        
        messages.success(self.request, 'Cliente/Parceiro cadastrado com sucesso!')
        return super().form_valid(form)

class ListClienteParceiroView(ListView):
    model = ClientesParceiros
    template_name = 'lista_clientes_parceiros.html'
    context_object_name = 'clientes_parceiros'

class ClienteParceiroUpdateView(UpdateView):
    model = ClientesParceiros
    template_name = 'editar_cliente_parceiro.html'
    fields = ['id_tipo_relacionamento', 'nome_referencia', 'cargo_referencia', 'data_inicio_parceria', 'ativo']
    success_url = reverse_lazy('lista_clientes_parceiros')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adicionar informações das empresas para exibição
        cliente_parceiro = self.object
        context['empresa_base'] = cliente_parceiro.id_company_base
        context['empresa_vinculada'] = cliente_parceiro.id_company_vinculada
        
        # Buscar contatos relacionados
        contatos = Contatos.objects.filter(
            empresa_base=cliente_parceiro.id_company_base,
            empresa_vinculada=cliente_parceiro.id_company_vinculada
        )
        context['contatos'] = contatos
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente/Parceiro atualizado com sucesso!')
        return super().form_valid(form)

class ClienteParceiroDeleteView(DeleteView):
    model = ClientesParceiros
    template_name = 'excluir_cliente_parceiro.html'
    success_url = reverse_lazy('lista_clientes_parceiros')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cliente/Parceiro excluído com sucesso!')
        return super().delete(request, *args, **kwargs)
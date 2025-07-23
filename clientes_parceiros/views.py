from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from .models import ClientesParceiros, TipoRelacionamento
from .forms import TipoRelacionamentoForm, EmpresaClienteParceiroForm, ClientesParceirosForm, ClienteParceiroUpdateForm
from contatos.models import Contatos
from empresas.models import Empresa
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

# Classe de exclusão removida conforme solicitado

class NewClienteParceiroView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'cadastrar_cliente_parceiro.html'
    form_class = EmpresaClienteParceiroForm
    success_url = reverse_lazy('lista_clientes_parceiros')
    
    def test_func(self):
        # Permite acesso para administradores, staff e usuários do tipo parceiro
        return (self.request.user.is_superuser or 
                self.request.user.is_staff or 
                (hasattr(self.request.user, 'profile') and 
                 getattr(self.request.user.profile, 'eh_parceiro', False)))

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Filtra para mostrar apenas o vínculo do tipo "Cliente"
        if 'id_tipo_relacionamento' in form.fields:
            # Tenta encontrar o tipo de relacionamento "Cliente"
            try:
                tipo_cliente = TipoRelacionamento.objects.filter(tipo_relacionamento__icontains='cliente').first()
                if tipo_cliente:
                    # Se encontrou, limita o queryset apenas a esse tipo
                    form.fields['id_tipo_relacionamento'].queryset = TipoRelacionamento.objects.filter(id=tipo_cliente.id)
                    form.fields['id_tipo_relacionamento'].initial = tipo_cliente
                    # Mantém o campo ativo (removendo readonly e disabled)
                    
                    # Campo escondido para garantir que o valor seja enviado
                    form.fields['id_tipo_relacionamento_hidden'] = forms.ModelChoiceField(
                        queryset=TipoRelacionamento.objects.filter(id=tipo_cliente.id),
                        initial=tipo_cliente,
                        widget=forms.HiddenInput()
                    )
            except Exception as e:
                # Se não encontrar, não faz nada
                pass
        
        # Se for parceiro, pré-seleciona a empresa base e vinculada como a do parceiro
        if hasattr(self.request.user, 'profile') and not (self.request.user.is_superuser or self.request.user.is_staff):
            if self.request.user.profile.relacionamento:
                # Define a empresa vinculada como a do parceiro logado
                empresa_vinculada = self.request.user.profile.relacionamento.id_company_vinculada
                # Define a empresa base como a empresa vinculada do parceiro logado
                empresa_base = empresa_vinculada
                
                # Pré-seleciona o campo empresa_base mas mantém ativo
                if 'empresa_base' in form.fields:
                    form.fields['empresa_base'].initial = empresa_base
                    form.fields['empresa_base'].queryset = form.fields['empresa_base'].queryset.filter(id=empresa_base.id)
                    
                    # Campo escondido para garantir que o valor seja enviado
                    form.fields['empresa_base_hidden'] = forms.ModelChoiceField(
                        queryset=form.fields['empresa_base'].queryset.filter(id=empresa_base.id),
                        initial=empresa_base,
                        widget=forms.HiddenInput()
                    )
                
                # Também configura o campo empresa_vinculada
                if 'empresa_vinculada' in form.fields:
                    form.fields['empresa_vinculada'].initial = empresa_vinculada
                    # Adiciona campo escondido para empresa_vinculada
                    form.fields['empresa_vinculada_hidden'] = forms.ModelChoiceField(
                        queryset=Empresa.objects.filter(id=empresa_vinculada.id),
                        initial=empresa_vinculada,
                        widget=forms.HiddenInput()
                    )
                    if not self.request.user.is_superuser and not self.request.user.is_staff:
                        form.fields['empresa_vinculada'].widget.attrs['readonly'] = True
                        
        
        return form
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_contato_options'] = Contatos.tipo_contato_options
        
        # Adiciona informação se o usuário é parceiro (para uso no template)
        context['is_partner'] = (
            hasattr(self.request.user, 'profile') and 
            getattr(self.request.user.profile, 'eh_parceiro', False) and
            not self.request.user.is_superuser and 
            not self.request.user.is_staff
        )
        
        return context
        
    def form_valid(self, form):
        # Imprime os dados recebidos para debug
        print("=== DEBUGGING FORM SUBMISSION ===")
        print("Formulário recebido:", dict(self.request.POST))
        print("Arquivos recebidos:", dict(self.request.FILES))
        print("Form is_valid():", form.is_valid())
        print("Form errors:", form.errors)
        print("Form cleaned_data:", form.cleaned_data)
        
        # Verificar se o formulário é válido antes de prosseguir
        if not form.is_valid():
            print("Formulário inválido, retornando form_invalid")
            return self.form_invalid(form)
        
        try:
            # Se tiver o campo escondido de tipo relacionamento, usa esse valor
            if 'id_tipo_relacionamento_hidden' in form.cleaned_data:
                form.instance.id_tipo_relacionamento = form.cleaned_data.get('id_tipo_relacionamento_hidden')
            elif 'id_tipo_relacionamento' in form.cleaned_data:
                form.instance.id_tipo_relacionamento = form.cleaned_data.get('id_tipo_relacionamento')
            
            # Se for parceiro e tiver o campo escondido de empresa base, usa esse valor
            if (hasattr(self.request.user, 'profile') and 
                getattr(self.request.user.profile, 'eh_parceiro', False) and 
                not self.request.user.is_superuser and 
                not self.request.user.is_staff and
                'empresa_base_hidden' in form.cleaned_data):
                empresa_base = form.cleaned_data.get('empresa_base_hidden')
                print(f"Usando empresa_base_hidden: {empresa_base}")
            else:
                # Pegar a empresa base selecionada (já existente no sistema)
                empresa_base = form.cleaned_data.get('empresa_base')
                print(f"Usando empresa_base: {empresa_base}")
                
            if not empresa_base:
                form.add_error('empresa_base', 'É necessário selecionar uma empresa base.')
                return self.form_invalid(form)
            
            # Se for parceiro comum e tiver campo escondido para empresa vinculada, usa esse valor
            if (hasattr(self.request.user, 'profile') and 
                getattr(self.request.user.profile, 'eh_parceiro', False) and 
                not self.request.user.is_superuser and 
                not self.request.user.is_staff):
                if 'empresa_vinculada_hidden' in form.cleaned_data:
                    # Para parceiros, usamos a empresa vinculada deles diretamente
                    empresa_vinculada = form.cleaned_data.get('empresa_vinculada_hidden')
                    print(f"Usando empresa_vinculada_hidden: {empresa_vinculada}")
                elif 'empresa_base_hidden' in form.cleaned_data:
                    # Se a empresa base for a empresa vinculada do parceiro, usamos ela
                    empresa_vinculada = empresa_base
                    print(f"Usando empresa_base como empresa_vinculada: {empresa_vinculada}")
                else:
                    # Não deve acontecer, mas por segurança definimos como a empresa base
                    empresa_vinculada = empresa_base
                    print(f"Fallback: usando empresa_base como empresa_vinculada: {empresa_vinculada}")
            else:
                # Para outros usuários, criamos uma nova empresa vinculada
                print("Criando nova empresa vinculada para usuário não-parceiro")
                empresa_vinculada = Empresa.objects.create(
                    cnpj=form.cleaned_data['cnpj'],
                    razao_social=form.cleaned_data['razao_social'],
                    nome_fantasia=form.cleaned_data['nome_fantasia'],
                    codigo_origem=form.cleaned_data['codigo_origem'],
                    logomarca=form.cleaned_data.get('logomarca')
                )
                print(f"Nova empresa criada: {empresa_vinculada}")
            
            # Não salvar o formulário diretamente, pois precisamos configurar os campos do modelo
            cliente_parceiro = form.instance
            cliente_parceiro.id_company_base = empresa_base
            cliente_parceiro.id_company_vinculada = empresa_vinculada
            cliente_parceiro.save()
            print(f"Cliente/Parceiro salvo: {cliente_parceiro}")
            
            # Processar os contatos (obrigatório)
            contact_count = int(self.request.POST.get('contact_count', 0))
            print(f"Contact count recebido: {contact_count}")
            
            # Verificar se pelo menos um contato foi adicionado
            if contact_count == 0:
                print("Nenhum contato foi adicionado")
                form.add_error(None, "É obrigatório adicionar pelo menos um contato.")
                cliente_parceiro.delete()  # Remove o cliente criado
                return self.form_invalid(form)
                
            # Processar cada formulário de contato
            contato_adicionado = False
            for i in range(1, contact_count + 1):
                tipo_contato = self.request.POST.get(f'tipo_contato_{i}')
                telefone = self.request.POST.get(f'telefone_{i}')
                email = self.request.POST.get(f'email_{i}')
                site = self.request.POST.get(f'site_{i}')
                
                print(f"Contato {i}: tipo={tipo_contato}, tel={telefone}, email={email}, site={site}")
                
                # Criar um novo registro de contato se os dados forem fornecidos
                if telefone or email or site:
                    try:
                        contato = Contatos.objects.create(
                            tipo_contato=tipo_contato or "OUTROS",
                            empresa_base=empresa_base,
                            empresa_vinculada=empresa_vinculada,
                            telefone=telefone or "",
                            email=email or "",
                            site=site or ""
                        )
                        contato_adicionado = True
                        print(f"Contato {i} criado com sucesso: {contato}")
                    except Exception as e:
                        print(f"Erro ao criar contato {i}: {str(e)}")
                        form.add_error(None, f"Erro ao salvar contato: {str(e)}")
                        cliente_parceiro.delete()  # Remove o cliente criado
                        return self.form_invalid(form)
                    
            # Se nenhum contato foi adicionado (campos vazios), retornar um erro
            if not contato_adicionado:
                print("Nenhum contato foi adicionado (campos vazios)")
                # Remover registros criados anteriormente para evitar dados orfãos
                cliente_parceiro.delete()
                
                # Só excluímos a empresa vinculada se não for a de um parceiro
                if (not hasattr(self.request.user, 'profile') or
                    not getattr(self.request.user.profile, 'eh_parceiro', False) or
                    self.request.user.is_superuser or
                    self.request.user.is_staff or
                    ('empresa_vinculada_hidden' not in form.cleaned_data and empresa_vinculada != empresa_base)):
                    if empresa_vinculada != empresa_base:
                        empresa_vinculada.delete()
                        print(f"Empresa vinculada deletada: {empresa_vinculada}")
                    
                form.add_error(None, "É obrigatório preencher pelo menos um contato com telefone, email ou site.")
                return self.form_invalid(form)
            
            print("=== SUCESSO: Cliente/Parceiro cadastrado ===")
            messages.success(self.request, 'Cliente/Parceiro cadastrado com sucesso!')
            return super().form_valid(form)
            
        except Exception as e:
            print(f"ERRO GERAL no form_valid: {str(e)}")
            import traceback
            traceback.print_exc()
            form.add_error(None, f"Erro interno: {str(e)}")
            return self.form_invalid(form)

class ListClienteParceiroView(LoginRequiredMixin, ListView):
    model = ClientesParceiros
    template_name = 'lista_clientes_parceiros.html'
    context_object_name = 'clientes_parceiros'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Se for superusuário ou staff, mostra todos os registros
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
            
        # Se for parceiro, mostra apenas os clientes vinculados à empresa do parceiro
        if hasattr(self.request.user, 'profile') and self.request.user.profile.relacionamento:
            # Obtém a empresa vinculada do usuário parceiro
            empresa_vinculada = self.request.user.profile.relacionamento.id_company_vinculada
            # Filtra clientes onde a empresa vinculada é a mesma do parceiro
            return queryset.filter(id_company_vinculada=empresa_vinculada)
            
        # Se não tiver perfil ou relacionamento, não mostra nada
        return ClientesParceiros.objects.none()

class ClienteParceiroUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientesParceiros
    template_name = 'editar_cliente_parceiro.html'
    form_class = ClienteParceiroUpdateForm
    success_url = reverse_lazy('lista_clientes_parceiros')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Filtra para mostrar apenas o vínculo do tipo "Cliente"
        if 'id_tipo_relacionamento' in form.fields:
            # Tenta encontrar o tipo de relacionamento "Cliente"
            try:
                tipo_cliente = TipoRelacionamento.objects.filter(tipo_relacionamento__icontains='cliente').first()
                if tipo_cliente:
                    # Se encontrou, limita o queryset apenas a esse tipo
                    form.fields['id_tipo_relacionamento'].queryset = TipoRelacionamento.objects.filter(id=tipo_cliente.id)
                    form.fields['id_tipo_relacionamento'].initial = tipo_cliente
                    # Mantém o campo ativo (removendo readonly e disabled)
                    
                    # Campo escondido para garantir que o valor seja enviado
                    form.fields['id_tipo_relacionamento_hidden'] = forms.ModelChoiceField(
                        queryset=TipoRelacionamento.objects.filter(id=tipo_cliente.id),
                        initial=tipo_cliente,
                        widget=forms.HiddenInput()
                    )
            except Exception as e:
                # Se não encontrar, não faz nada
                pass
        
        return form
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Se for superusuário ou staff, permite acesso a todos os registros
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
            
        # Se for parceiro, permite acesso apenas aos clientes vinculados à sua empresa
        if hasattr(self.request.user, 'profile') and self.request.user.profile.relacionamento:
            # Obtém a empresa vinculada do usuário parceiro
            empresa_vinculada = self.request.user.profile.relacionamento.id_company_vinculada
            # Filtra clientes onde a empresa vinculada é a mesma do parceiro
            return queryset.filter(id_company_vinculada=empresa_vinculada)
            
        # Se não tiver perfil ou relacionamento, não permite acesso a nenhum
        return ClientesParceiros.objects.none()
    
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
        # Se tiver o campo escondido de tipo relacionamento, usa esse valor
        if 'id_tipo_relacionamento_hidden' in form.cleaned_data:
            form.instance.id_tipo_relacionamento = form.cleaned_data.get('id_tipo_relacionamento_hidden')
        
        # Processar a atualização da logomarca se fornecida
        nova_logomarca = self.request.FILES.get('atualizar_logomarca')
        if nova_logomarca:
            # Atualizar a logomarca da empresa vinculada
            empresa_vinculada = self.object.id_company_vinculada
            empresa_vinculada.logomarca = nova_logomarca
            empresa_vinculada.save()
            
        messages.success(self.request, 'Cliente atualizado com sucesso!')
        return super().form_valid(form)

# Classe de exclusão removida conforme solicitado
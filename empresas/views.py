from django.shortcuts import render, get_object_or_404
from empresas.forms import EmpresaForm
from empresas.models import Empresa, Socio, ParticipacaoSocietaria
from contatos.models import Contatos
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
import os
from django.conf import settings
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .serializers import EmpresaSerializer


def home_view(request):
  return render(request, 'base.html')
class NewEmpresaView(CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'cadastro_empresa.html'
    success_url = reverse_lazy('empresas:lista_empresas')

    def form_valid(self, form):
        # Save Empresa
        empresa = form.save()

        # ================= Sócios =================
        socio_count = int(self.request.POST.get('socio_count', 0))
        for i in range(1, socio_count + 1):
            existing_id = self.request.POST.get(f'existing_socio_{i}')
            novo_nome = self.request.POST.get(f'nome_novo_{i}', '').strip()
            novo_cpf = self.request.POST.get(f'cpf_novo_{i}', '').strip()
            percentual_raw = self.request.POST.get(f'percentual_{i}', '').strip()
            socio_obj = None
            # Prioridade: existing select
            if existing_id:
                try:
                    socio_obj = Socio.objects.get(id=existing_id)
                except Socio.DoesNotExist:
                    socio_obj = None
            elif novo_cpf and novo_nome:
                # Normaliza CPF (somente dígitos)
                cpf_digits = ''.join(ch for ch in novo_cpf if ch.isdigit())
                if cpf_digits:
                    socio_obj, created = Socio.objects.get_or_create(cpf=cpf_digits, defaults={'nome': novo_nome})
                    # Se já existia e o nome mudou, opcionalmente não sobrescreve; poderíamos atualizar se vazio
            # Percentual parse
            percentual = None
            if percentual_raw:
                pr = percentual_raw.replace('%','').replace(',','.')
                try:
                    from decimal import Decimal
                    percentual = Decimal(pr)
                except Exception:
                    percentual = None
            if socio_obj:
                ParticipacaoSocietaria.objects.get_or_create(
                    empresa=empresa,
                    socio=socio_obj,
                    defaults={'percentual': percentual}
                )
                # Se já existia e percentual enviado, podemos atualizar
                if percentual is not None:
                    ps = ParticipacaoSocietaria.objects.filter(empresa=empresa, socio=socio_obj).first()
                    if ps and ps.percentual != percentual:
                        ps.percentual = percentual
                        ps.save()

        # ================= Contatos =================
        contact_count = int(self.request.POST.get('contact_count', 0))
        for i in range(1, contact_count + 1):
            tipo_contato = self.request.POST.get(f'tipo_contato_{i}')
            telefone = self.request.POST.get(f'telefone_{i}')
            email = self.request.POST.get(f'email_{i}')
            site = self.request.POST.get(f'site_{i}')
            if telefone or email or site:
                Contatos.objects.create(
                    tipo_contato=tipo_contato,
                    empresa_base=empresa,
                    telefone=telefone or "",
                    email=email or "",
                    site=site or ""
                )

        messages.success(self.request, 'Empresa cadastrada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_contato_options'] = Contatos.tipo_contato_options
        context['socios_existentes'] = Socio.objects.filter(ativo=True).order_by('nome')
        # Preserva campos dinâmicos de sócios em caso de erro de validação
        if self.request.method == 'POST':
            try:
                socio_count = int(self.request.POST.get('socio_count', '0') or 0)
            except ValueError:
                socio_count = 0
            entries = []
            for i in range(1, socio_count + 1):
                entries.append({
                    'existing': self.request.POST.get(f'existing_socio_{i}', ''),
                    'nome': self.request.POST.get(f'nome_novo_{i}', ''),
                    'cpf': self.request.POST.get(f'cpf_novo_{i}', ''),
                    'percentual': self.request.POST.get(f'percentual_{i}', ''),
                    'index': i,
                })
            if not entries:
                entries = [{'existing':'','nome':'','cpf':'','percentual':'','index':1}]
            context['socios_entries'] = entries
        else:
            context['socios_entries'] = [{'existing':'','nome':'','cpf':'','percentual':'','index':1}]
        return context

class EmpresaListView(ListView):
    model = Empresa
    template_name = 'empresas_list.html'
    context_object_name = 'empresas'
    
class EmpresaUpdateView(UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'editar_empresa.html'
    success_url = reverse_lazy('empresas:lista_empresas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all contacts for this company
        contatos = Contatos.objects.filter(empresa_base=self.object)
        
        context['form'] = EmpresaForm(instance=self.object)
        context['tipo_contato_options'] = Contatos.tipo_contato_options
        context['contatos'] = contatos
        
        return context
    
    def form_valid(self, form):
        empresa = form.save()
        
        # Get the number of contacts from the form
        contact_count = int(self.request.POST.get('contact_count', 0))
        
        # Process each contact form
        for i in range(1, contact_count + 1):
            tipo_contato = self.request.POST.get(f'tipo_contato_{i}')
            telefone = self.request.POST.get(f'telefone_{i}')
            email = self.request.POST.get(f'email_{i}')
            site = self.request.POST.get(f'site_{i}')
            contato_id = self.request.POST.get(f'contato_id_{i}')
            
            # If contact data is provided
            if telefone or email or site:
                if contato_id:
                    # Update existing contact
                    try:
                        contato = Contatos.objects.get(id=contato_id)
                        contato.tipo_contato = tipo_contato
                        contato.telefone = telefone or ""
                        contato.email = email or ""
                        contato.site = site or ""
                        contato.save()
                    except Contatos.DoesNotExist:
                        # If the contact doesn't exist anymore, create a new one
                        Contatos.objects.create(
                            tipo_contato=tipo_contato,
                            empresa_base=empresa,
                            telefone=telefone or "",
                            email=email or "",
                            site=site or ""
                        )
                else:
                    # Create new contact
                    Contatos.objects.create(
                        tipo_contato=tipo_contato,
                        empresa_base=empresa,
                        telefone=telefone or "",
                        email=email or "",
                        site=site or ""
                    )
        
        messages.success(self.request, 'Empresa atualizada com sucesso!')
        return super().form_valid(form)

class EmpresaDeleteView(DeleteView):
    model = Empresa
    template_name = 'excluir_empresa.html'
    success_url = reverse_lazy('empresas:lista_empresas')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Empresa excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============== DRF API ==================
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)


class EmpresaListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def get(self, request):
        objs = Empresa.objects.all()
        ser = EmpresaSerializer(objs, many=True)
        return Response(ser.data)


class EmpresaCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def post(self, request):
        ser = EmpresaSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class EmpresaDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def get_object(self, pk):
        return get_object_or_404(Empresa, pk=pk)
    def get(self, request, pk):
        ser = EmpresaSerializer(self.get_object(pk))
        return Response(ser.data)
    def patch(self, request, pk):
        obj = self.get_object(pk)
        ser = EmpresaSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile
from django.forms.widgets import ClearableFileInput


class UserUpdateForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ['first_name', 'last_name', 'email']
		labels = {
			'first_name': 'Nome',
			'last_name': 'Sobrenome',
			'email': 'Email',
		}
		widgets = {
			'first_name': forms.TextInput(attrs={'class': 'input w-full'}),
			'last_name': forms.TextInput(attrs={'class': 'input w-full'}),
			'email': forms.EmailInput(attrs={'class': 'input w-full'}),
		}


class MinimalClearableFileInput(ClearableFileInput):
	# Use explicit app-scoped path so the loader finds it for sure
	template_name = 'accounts/widgets/clear_file_input_minimal.html'


class ProfileUpdateForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		fields = ['telefone', 'foto_perfil']
		labels = {
			'telefone': 'Telefone',
			'foto_perfil': 'Foto de Perfil',
		}
		widgets = {
			'telefone': forms.TextInput(attrs={'class': 'input w-full'}),
			# Minimal clearable file input to avoid default Django extra markup
			'foto_perfil': MinimalClearableFileInput(attrs={'class': 'hidden', 'id': 'id_foto_perfil', 'accept': 'image/*'}),
		}


class MinimalClearableFileInput(ClearableFileInput):
	template_name = 'widgets/clear_file_input_minimal.html'


class ProfilePasswordChangeForm(PasswordChangeForm):
	old_password = forms.CharField(label='Senha atual', widget=forms.PasswordInput(attrs={'class': 'input w-full'}))
	new_password1 = forms.CharField(label='Nova senha', widget=forms.PasswordInput(attrs={'class': 'input w-full'}))
	new_password2 = forms.CharField(label='Confirmar nova senha', widget=forms.PasswordInput(attrs={'class': 'input w-full'}))


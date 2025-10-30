from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adesao', '0014_alter_adesao_metodo_credito_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='adesao',
            name='perdcomp_retificador',
            field=models.CharField(blank=True, help_text='Número do PER/DCOMP retificador vinculado a esta adesão.', max_length=30, null=True, verbose_name='PERDCOMP retificador'),
        ),
        migrations.AlterField(
            model_name='adesao',
            name='status',
            field=models.CharField(choices=[('solicitado', 'Solicitado'), ('protocolado', 'Protocolado'), ('retificado', 'Retificado')], default='solicitado', max_length=20, verbose_name='Status'),
        ),
    ]

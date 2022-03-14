# Generated by Django 3.0.5 on 2022-03-09 19:12

import annotator_api.models
from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import djongo.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('image', models.ImageField(blank=True, upload_to=annotator_api.models.User.get_upload_path)),
                ('username', models.CharField(max_length=255, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AnnotationModel',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('avgWidth', models.FloatField(default=0)),
                ('avgHeight', models.FloatField(default=0)),
                ('model', models.FileField(upload_to=annotator_api.models.AnnotationModel.get_upload_path)),
                ('model_pool', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ModelPool',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('subdescription_list', models.TextField(blank=True, default='')),
                ('modelpool_list', models.ManyToManyField(blank=True, related_name='sub_modelpools', to='annotator_api.ModelPool')),
                ('pool_models', models.ManyToManyField(related_name='models', to='annotator_api.AnnotationModel')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('owners', models.ManyToManyField(blank=True, related_name='owner', to=settings.AUTH_USER_MODEL)),
                ('staff', models.ManyToManyField(blank=True, related_name='staff', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('role', models.CharField(choices=[('1', 'owner'), ('2', 'staff')], default='2', max_length=20)),
                ('terminal', models.CharField(choices=[('1', 'user'), ('2', 'project')], default='1', max_length=20)),
                ('status', models.CharField(choices=[('1', 'is_pending'), ('2', 'accepted'), ('3', 'declined')], default='1', max_length=20)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotator_api.Project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ModelPoolStatus',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=True)),
                ('main_modelpool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='main_modelpool', to='annotator_api.ModelPool')),
                ('sub_modelpool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_modelpool', to='annotator_api.ModelPool')),
            ],
        ),
        migrations.AddField(
            model_name='modelpool',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotator_api.Project'),
        ),
        migrations.AddField(
            model_name='modelpool',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('image', models.ImageField(blank=True, upload_to=annotator_api.models.Document.get_upload_path)),
                ('is_annotated', models.BooleanField(default=False)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='annotator_api.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('topX', models.FloatField(default=0)),
                ('topY', models.FloatField(default=0)),
                ('bottomX', models.FloatField(default=0)),
                ('bottomY', models.FloatField(default=0)),
                ('is_antipattern', models.BooleanField(default=False)),
                ('ground_truth', models.BooleanField(default=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='annotator_api.Document')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

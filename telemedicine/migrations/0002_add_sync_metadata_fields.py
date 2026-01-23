# Generated migration for sync metadata fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telemedicine', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Last successful sync timestamp', null=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Last successful sync timestamp', null=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Last successful sync timestamp', null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddField(
            model_name='pharmacy',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Last successful sync timestamp', null=True),
        ),
        migrations.AlterField(
            model_name='pharmacy',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='pharmacy',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddField(
            model_name='medicine',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Last successful sync timestamp', null=True),
        ),
        migrations.AlterField(
            model_name='medicine',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='medicine',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddField(
            model_name='pharmacyinventory',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Last successful sync timestamp', null=True),
        ),
        migrations.AlterField(
            model_name='pharmacyinventory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='pharmacyinventory',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, db_index=True, help_text='When the quantity was last updated'),
        ),
        migrations.AddIndex(
            model_name='patient',
            index=models.Index(fields=['updated_at'], name='telemedicine_patient_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='patient',
            index=models.Index(fields=['last_synced_at'], name='telemedicine_patient_synced_idx'),
        ),
        migrations.AddIndex(
            model_name='doctor',
            index=models.Index(fields=['updated_at'], name='telemedicine_doctor_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='doctor',
            index=models.Index(fields=['last_synced_at'], name='telemedicine_doctor_synced_idx'),
        ),
    ]

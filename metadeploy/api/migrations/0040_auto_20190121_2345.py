# Generated by Django 2.1.5 on 2019-01-21 23:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("api", "0039_auto_20190117_2228")]

    operations = [
        migrations.AlterField(
            model_name="step",
            name="plan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="steps",
                to="api.Plan",
            ),
        )
    ]

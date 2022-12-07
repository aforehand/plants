from django.db import models

class PlantManager(models.Manager):
    def create_plant(self, attributes):
        plant = self.create(attributes=attributes)
        plant.save()
        return plant

class Plant(models.Model):
    attributes = models.JSONField()

    objects = PlantManager()

    def __str__(self):
        return f'{self.attributes["common name"]}: {self.attributes["genus"]} {self.attributes["species"]}'
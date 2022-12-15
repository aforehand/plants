from django.shortcuts import render
from django.views import View
import numpy as np
import pandas as pd
import random

from modules.plants import GuildRecommender

class GuildRecommenderView(View):
    template_name = 'guild_recommender.html'
    rec = None
    context = {
        'num_layers': None,
        'zone': 7,
        'region': 'all',
        'water': 'mesic',
        'ph': 6.5,
        'sun': 'full sun',
        'soil_texture': 'medium',
        # 'include_trees': True,
        'edible_only': False,
        'perennial_only': False,     
    }

    # TODO: include layer names in guild
    # TODO: make button to generate guild
    # TODO: make form to alter recommender params
    def get(self, request):
        return render(request, self.template_name, self.context)

    def post(self, request):
        try:
            num_layers = int(request.POST.get('layers'))
        except ValueError:
            num_layers = None
        params = {
            'num_layers': num_layers,
            'zone': int(request.POST.get('zone')),
            'region': request.POST.get('region'),
            'water': request.POST.get('water'),
            'ph': float(request.POST.get('ph')),
            'sun': request.POST.get('sun'),
            'soil_texture': request.POST.get('soil'),
            # 'include_trees': (request.POST.get('trees') == 'on'),
            'edible_only': (request.POST.get('edible') == 'on'),
            'perennial_only': (request.POST.get('perennials') == 'on'),
        }
        if (self.rec is None) or (self.context != params):
            self.context = params
            self.rec = GuildRecommender(
                num_layers=self.context['num_layers'],
                zone=self.context['zone'],
                region=self.context['region'],
                water=self.context['water'],
                ph=self.context['ph'],
                sun=self.context['sun'],
                soil_texture=self.context['soil_texture'],
                # include_trees=self.context['include_trees'],
                edible_only=self.context['edible_only'],
                perennial_only=self.context['perennial_only']
            )
        guild = self.rec.create_guild().to_dict(orient='records')
        self.context['guild'] = [f"{guild[i]['genus']} {guild[i]['species']}" for i in range(len(guild))]
        return render(request, self.template_name, self.context)
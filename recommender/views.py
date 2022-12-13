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
        'water': 'mesic',
        'ph': 6.5,
        'sun': 'full sun',
        'soil_texture': 'medium',
        'include_trees': True,
        'edible_only': False,
        'perennial_only': False,        
        # 'region': None,
        # 'state': None
    }

    # TODO: include layer names in guild
    # TODO: make button to generate guild
    # TODO: make form to alter recommender params
    def get(self, request):
        return render(request, self.template_name, self.context)

    def post(self, request):
        if self.rec is None:
            self.rec = GuildRecommender(
                num_layers=self.context['num_layers'],
                zone=self.context['zone'],
                water=self.context['water'],
                ph=self.context['ph'],
                sun=self.context['sun'],
                soil_texture=self.context['soil_texture'],
                include_trees=self.context['include_trees'],
                edible_only=self.context['edible_only'],
                perennial_only=self.context['perennial_only']
            )
        guild = self.rec.create_guild().to_dict(orient='records')
        self.context['guild'] = [f"{guild[i]['genus']} {guild[i]['species']}" for i in range(len(guild))]
        return render(request, self.template_name, self.context)
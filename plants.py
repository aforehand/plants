import pandas as pd 
import re
import numpy as np
import random
import selenium
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from collections import defaultdict

class PlantRecommender:
    """A recommender for designing plant guilds and permaculture gardens.
    Uses a REST API for the USDA Plants Database 
    (https://github.com/sckott/usdaplantsapi/) and the National Gardening 
    Association's plant database (https://garden.org) to recommend plants for 
    various uses.

    Parameters
    ----------
    soil_texture: string, default='medium'
        Values can be {'coarse', 'medium', 'fine'}, or from the Soil Texture 
        Triangle, {'sand', 'coarse_sand', 'fine_sand', 'loamy_coarse_sand', 
        'loamy_fine_sand', 'loamy_very_fine_sand', 'very_fine_sand', 
        'loamy_sand', 'silt', 'sandy_clay_loam', 'very_fine_sandy_loam', 
        'silty_clay_loam', 'silt_loam', 'loam', 'fine_sandy_loam', 'sandy_loam', 
        'coarse_sandy_loam', 'clay_loam', 'sandy_clay', 'silty_clay', 'clay'}.
    
    ph: float, default=6.5
        Soil pH can range from 3.5-9.0. Most plants thrive in soil between 6-7.

    moisture: {'high', 'medium' 'low'}, default='medium'
        How much moisture is available.

    zone: int, default=7
        USDA hardiness zone. Mapped to min_temp because USDA database uses 
        minimum temperature, but hardiness zone is more commonly used.

    region: {'northeast', 'southeast', 'midwest', 'plains', 'pacific'}, default=None
        Set to find plants that are native to a specific region.

    state: two-letter state sbbreviations, default=None
        set to find plants that are native to a specific state.
    """

    def __init__(self, soil_texture='medium', ph=6.5, moisture='medium',  
                zone=7, region=None, state=None):      
        # site parameters      
        if soil_texture in {'coarse', 'sand', 'coarse_sand', 'fine_sand', 
                            'loamy_coarse_sand', 'loamy_fine_sand', 
                            'loamy_very_fine_sand', 'very_fine_sand', 
                            'loamy_sand'}:
            self.soil_texture = {'Adapted_to_Coarse_Textured_Soils': 'Yes'}
        elif soil_texture in {'medium', 'silt', 'sandy_clay_loam', 
                            'very_fine_sandy_loam', 'silty_clay_loam', 
                            'silt_loam', 'loam', 'fine_sandy_loam', 'sandy_loam', 
                            'coarse_sandy_loam', 'clay_loam'}:
            self.soil_texture = {'Adapted_to_Medium_Textured_Soils': 'Yes'}
        elif soil_texture in {'fine', 'sandy_clay', 'silty_clay', 'clay'}:
            self.soil_texture = {'Adapted_to_Fine_Textured_Soils': 'Yes'}
        else:
            self.soil_texture = None
        self.ph = ph
        self.moisture = moisture
        hardiness_zone_to_temp = {1:-60, 2:-50, 3:-40, 4:-30, 5:-20, 6:-10, 7:0,
                                8:10, 9:20, 10:30}
        if zone is not None:
            self.min_temp = hardiness_zone_to_temp[zone]
        else:
            self.min_temp = None
        if region is not None:
            regions = {'northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 
                                    'NJ', 'PA', 'DE', 'MD', 'WV', 'VA'], 
                        'southeast': ['NC', 'TN', 'AR', 'SC', 'GA', 'AL', 'MS', 
                                    'LA', 'FL'], 
                        'midwest': ['MN', 'WI', 'MI', 'IA', 'IL', 'IN', 'OH', 
                                    'MO', 'KY'],
                        'plains': ['MT', 'ND', 'WY', 'SD', 'NE', 'CO', 'KS', 
                                    'NM', 'TX', 'OK'],
                        'pacific': ['WA', 'OR', 'ID', 'CA', 'NV', 'UT', 'AZ']}
            self.region = regions[region]
        else:
            self.region = region
        self.state = state 
        self.categorical_attributes = ['Genus', 'Species', 'Varieties']
        self.boolean_attributes = ['Coarse Soil', 'Medium Soil', 'Fine Soil']
        self.numeric_attributes = []

        options = Options()
        options.headless = True
        self.driver = Firefox(options=options)
        self.usda_url = 'https://plantsdb.xyz/search'
        self.garden_search_url = 'https://garden.org/plants/search/advanced.php'
        self.driver.get(self.garden_search_url)
        # garden.org search parameters
        self.sections = [s for s in self.driver.find_elements_by_xpath('//p') if
            s.text is not '']
        self.plant_habit = self.get_inputs(self.sections[0])
        self.life_cycle = Select(self.sections[1].find_element_by_xpath(
            './/select'))
        self.categorical_attributes.append('Life cycle')
        self.light = self.get_inputs(self.sections[2])
        self.water = self.get_inputs(self.sections[3])
        self.soil_ph = self.get_inputs(self.sections[4])
        self.cold_hardiness = Select(self.sections[5].find_element_by_xpath(
            './/select'))
        self.numeric_attributes.append('Minimum cold hardiness')
        self.maximum_zone = Select(self.sections[6].find_element_by_xpath(
            './/select'))
        self.numeric_attributes.append('Maximum recommended zone')
        self.plant_height = self.sections[7].find_element_by_xpath('.//input')
        self.numeric_attributes.append('Plant Height')
        self.plant_spread = self.sections[8].find_element_by_xpath('.//input')
        self.numeric_attributes.append('Plant Spread')
        self.leaves = self.get_inputs(self.sections[9], 'Leaves_')
        self.fruit = self.get_inputs(self.sections[10], 'Fruit_')
        self.fruiting_time = self.get_inputs(self.sections[11], 
                                            'Fruiting Time_')
        self.flowers = self.get_inputs(self.sections[12], 'Flowers_')
        self.flower_color = self.get_inputs(self.sections[13],)
        self.bloom_size = self.get_inputs(self.sections[14])
        self.flower_time = self.get_inputs(self.sections[15], 'Flower Time_')
        self.inflorescence_height = self.sections[16].find_element_by_xpath(
            './/input')
        self.numeric_attributes.append('Inflorescence Height')
        self.foliage_mound_height = self.sections[17].find_element_by_xpath(
            './/input')
        self.numeric_attributes.append('Foliage Mound Height')
        self.roots = self.get_inputs(self.sections[18])
        self.locations = self.get_inputs(self.sections[19])
        self.uses = self.get_inputs(self.sections[20])
        self.edible_parts = self.get_inputs(self.sections[21])
        self.eating_methods = self.get_inputs(self.sections[22])
        self.dynamic_accumulator = self.get_inputs(self.sections[23])
        self.wildlife_attract = self.get_inputs(self.sections[24])
        self.resistances = self.get_inputs(self.sections[25])
        self.toxicity = self.get_inputs(self.sections[26])
        # some of these have additional inputs once selected.
        # not implemented yet.
        self.propagation_seed = self.get_inputs(self.sections[27])
        self.propagation_other = self.get_inputs(self.sections[28])
        self.pollinators = self.get_inputs(self.sections[29])
        self.containers = self.get_inputs(self.sections[30])
        self.misc = self.get_inputs(self.sections[31])
        self.awards = self.get_inputs(self.sections[32])
        self.conservation_status = Select(self.sections[33].
            find_element_by_xpath('.//select'))
        self.parentage = self.sections[34].find_element_by_xpath('.//input')
        self.child_plants = self.sections[35].find_element_by_xpath('.//input')
        self.sort_by = Select(self.sections[36].find_element_by_xpath(
            './/select'))
        self.clear_form = self.sections[37].find_element_by_xpath('.//a')

    def get_inputs(self, section, field=''):
        inputs = section.find_elements_by_xpath('.//input')
        labels = section.find_elements_by_xpath('.//label')
        self.boolean_attributes += [field+l.text for l in labels]
        return {l.text: i for l,i in zip(labels,inputs)}

    def get_results(self):
        """Return a dict with the scientific name of each plant returned by a 
        query and a list of links to all varieties of that plant.
        Note: self.driver must be on a garden.org results page before calling.
        """
        links = self.driver.find_elements_by_xpath('.//a')
        results = defaultdict(list)
        for l in links:
            url = l.get_attribute('href')
            name = re.findall(r'(?<=\()([A-Z]\w+ [a-z]\w+)', l.text)
            if 'plants/view/' in url and len(name) > 0:
                results[name[0]].append(url)
        return results

    
    def filter_plants(self, results):
        """Cross-reference plants returned from a garden.org query with the USDA
        plants database to remove plants that do not meet requirements and 
        return filtered results.
        """
        print('Finding native plants', end='')
        plants = pd.DataFrame()
        for name in results.keys():
            print('.', end='')
            plant = {a:None for a in (self.categorical_attributes
                                    + self.boolean_attributes
                                    + self.numeric_attributes)}
            genus,species = name.split()
            self.driver.get(f'{self.usda_url}?Genus={genus}&Species={species}')
            self.driver.implicitly_wait(5)
            self.driver.find_element_by_id('rawdata-tab').click()
            data = self.driver.find_element_by_class_name('data')
            try:
                data = eval(data.text.replace('null', 'None'))['data'][0]
                is_native = ('L48 (N)' in data['Native_Status'])
                states = data['State_and_Province']
                states = states[states.index('(')+1:states.index(')')] 
                in_location = ((self.state is None and self.region is None) or 
                                (self.state in states) or 
                                (len(set(self.region) & set(states)) > 0))
                in_zone = self.min_temp >= eval(data['Temperature_Minimum_F'])
                in_ph_range = ((self.ph >= eval(data['pH_Minimum'])) and 
                                (self.ph <= eval(data['pH_Maximum'])))
            except:
                continue
            if is_native and in_location and in_zone and in_ph_range:
                plant['Genus'] = genus
                plant['Species'] = species
                plant['Varieties'] = results[name]
                plant['Coarse Soil'] = data['Adapted_to_Coarse_Textured_Soils']=='Yes'
                plant['Medium Soil'] = data['Adapted_to_Medium_Textured_Soils']=='Yes'
                plant['Fine Soil'] = data['Adapted_to_Fine_Textured_Soils']=='Yes'            
                self.driver.get(results[name][0])
                table = self.driver.find_element_by_xpath('//caption[contains('
                'text(),"General Plant Information")]/../tbody')
                rows = table.find_elements_by_xpath('.//tr')
                for row in rows:
                    field,values = row.find_elements_by_xpath('.//td')
                    field = field.text[:-1]
                    values = values.text.split('\n')
                    if (field in self.categorical_attributes 
                            + self.numeric_attributes):
                        plant[field] = values[0]
                    else:
                        for v in values:
                            if f'{field}_{v}' in self.boolean_attributes:
                                plant[f'{field}_{v}'] = True 
                            elif v in self.boolean_attributes:
                                plant[v] = True
                plants = plants.append(plant, ignore_index=True)
        return plants

        # TODO: implement function to search garden.org 

    def get_all_native_plants(self, new=False):
        """Download all native plants from USDA plant database with garden.org 
        data"""
        if new:
            plants = pd.DataFrame()
        else:
            plants = pd.read_csv('all_native_plants.csv')                   
        options = Options()
        options.headless = True
        for i in range(74200,93000,1000):
            print(f'\n{i} / 93000')
            self.driver.get(f'{self.usda_url}?limit=1000&offset={i}')
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located(
                (By.ID, 'rawdata-tab'))).click()
            data_list = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'data')))
            data_list = eval(data_list.text.replace('null', 'None'))['data']
            for j in range(len(data_list)):
                if j % 10 == 1:
                    plants.to_csv('all_native_plants.csv', index=False)
                    self.driver.quit()
                    self.driver = Firefox(options=options)
                    print('.', end='', flush=True)
                plant = {a:None for a in (self.categorical_attributes
                                        + self.boolean_attributes
                                        + self.numeric_attributes)}
                data = data_list[j]
                is_native = (('L48 (N)' in data['Native_Status']) or 
                            ('L48 (N?)' in data['Native_Status']))
                in_df =  (plants[['Genus','Species']] == ({k:v for k,v in 
                    data.items() if k in {'Genus','Species'}})).all(axis=1).any()
                if is_native and not in_df:
                    #  columns to add: states, coppice, growth (clumping, 
                    #  running, dispersive, etc.), active growth period?, 
                    #  foliage porosity summer?, growth form?, known allelopath?,
                    #  fertility requitement, height, temperature_minimum_f
                    #  maybe to add from pfaf: edible and medicinal ratings,
                    plant['Genus'] = data['Genus']
                    plant['Species'] = data['Species']
                    plant['Coarse Soil'] = data['Adapted_to_Coarse_Textured_Soils']=='Yes'
                    plant['Medium Soil'] = data['Adapted_to_Medium_Textured_Soils']=='Yes'
                    plant['Fine Soil'] = data['Adapted_to_Fine_Textured_Soils']=='Yes'            
                    self.driver.get(f'https://garden.org/plants/search/text/?q='
                        f'{plant["Genus"]}+{plant["Species"]}')
                    results = self.get_results()
                    plant['Varieties'] = results[f'{plant["Genus"]} '
                        f'{plant["Species"]}']
                    try:    
                        self.driver.get(plant['Varieties'][0])
                        table = self.driver.find_element_by_xpath('//caption['
                            'contains(text(), "General Plant Information")]/../'
                            'tbody')
                    except:
                        continue
                    rows = table.find_elements_by_xpath('.//tr')
                    for row in rows:
                        field,values = row.find_elements_by_xpath('.//td')
                        field = field.text[:-1]
                        values = values.text.split('\n')
                        if (field in self.categorical_attributes 
                                + self.numeric_attributes):
                            plant[field] = values[0]
                        else:
                            for v in values:
                                if f'{field}_{v}' in self.boolean_attributes:
                                    plant[f'{field}_{v}'] = True 
                                elif v in self.boolean_attributes:
                                    plant[v] = True
                    plants = plants.append(plant, ignore_index=True)
        self.driver.quit()


"""
considerations to implement:
number of layers/plants (2-7)
root structures
shade tolerances (shade tolerant short plants under sun loving tall plants)
combine root crops with vigorous plants that need thinning and won't mind the
disturbance
always include ground cover, nitrogen fixers, and mulchers
define function for each patch
use heights of pfaf canopy trees to set height range for all canopy trees. 
"""

class GuildRecommender:
    """Recommends a group of native plants to be planted together in a guild.

    num_layers: int, default=None
        Number of layers to include in guild. Can range from 2-7. If None, a
        random number of layers will be chosen.

    zone: int, default=7
        USDA hardiness zone of intended site. Can range from 1-10.

    water: {'In Water', 'Wet', 'Wet Mesic', 'Mesic', 'Dry Mesic', 'Dry'}, 
    default='Mesic'
        The moisute of the soil at the site.

    ph: int, default=6.5
        The pH of the soil at the site.
    
    sun: string, default='Full Sun'
        How much sun is available at the site.

    soil_texture: string, default='medium'
        Values can be {'coarse', 'medium', 'fine'}, or from the 
        Soil Texture Triangle, {'sand', 'coarse_sand', 'fine_sand', 
        'loamy_coarse_sand', 'loamy_fine_sand', 'loamy_very_fine_sand', 
        'very_fine_sand', 'loamy_sand', 'silt', 'sandy_clay_loam', 
        'very_fine_sandy_loam', 'silty_clay_loam', 'silt_loam', 'loam', 
        'fine_sandy_loam', 'sandy_loam', 'coarse_sandy_loam', 'clay_loam', 
        'sandy_clay', 'silty_clay', 'clay'}.

    include_trees: boolean, defualt=True
        Whether or not trees can be considered when creating guilds.

    edible_only: boolean, default=False
        Whether only edible plants can be considered when creating guilds.

    perennial_only: boolean, default=True
        Whether only perennial plants will be considered when creating guilds.
    """

    def __init__(self, num_layers=None, zone=7, water='Mesic', ph=6.5, 
                sun='Full Sun', soil_texture='medium', include_trees=True, 
                edible_only=False, perennial_only=True):
        if num_layers==None:
            self.num_layers = random.randint(2,7)
        else:
            self.num_layers = num_layers 
        self.zone = zone 
        self.water = water 
        if ph < 4.5:
            self.ph = 'Extremely acid (3.5 – 4.4)'
        elif ph < 5.1:
            self.ph = 'Very strongly acid (4.5 – 5.0)'
        elif ph < 5.6:
            self.ph = 'Strongly acid (5.1 – 5.5)'
        elif ph < 6.1:
            self.ph = 'Moderately acid (5.6 – 6.0)'
        elif ph < 6.6:
            self.ph = 'Slightly acid (6.1 – 6.5)'
        elif ph < 7.4:
            self.ph = 'Neutral (6.6 – 7.3)'
        elif ph < 7.9:
            self.ph = 'Slightly alkaline (7.4 – 7.8)'
        elif ph < 8.5:
            self.ph = 'Moderately alkaline (7.9 – 8.4)'
        else:
            self.ph = 'Strongly alkaline (8.5 – 9.0)'
        sun_list = ['Full Sun', 'Full Sun to Partial Shade',
            'Partial or Dappled Shade', 'Partial Shade to Full Shade', 
            'Full Shade']
        self.sun = sun_list[sun_list.index(sun):]
        if soil_texture in {'coarse', 'sand', 'coarse_sand', 'fine_sand', 
                            'loamy_coarse_sand', 'loamy_fine_sand', 
                            'loamy_very_fine_sand', 'very_fine_sand', 
                            'loamy_sand'}:
            self.soil_texture = 'Coarse Soil'
        elif soil_texture in {'medium', 'silt', 'sandy_clay_loam', 
                            'very_fine_sandy_loam', 'silty_clay_loam', 
                            'silt_loam', 'loam', 'fine_sandy_loam', 'sandy_loam', 
                            'coarse_sandy_loam', 'clay_loam'}:
            self.soil_texture = 'Medium Soil'
        elif soil_texture in {'fine', 'sandy_clay', 'silty_clay', 'clay'}:
            self.soil_texture = 'Fine Soil'
        self.habits = {'Herb/Forb', 'Shrub', 'Tree', 'Cactus/Succulent', 
            'Grass/Grass-like', 'Fern', 'Vine'}
        plants = pd.read_csv('all_native_plants.csv')
        plants = plants[(plants['Minimum cold hardiness']<=zone) & 
            ((plants['Maximum recommended zone']==np.nan) | 
            (plants['Maximum recommended zone']>=zone))]
        self.plants = pd.DataFrame()
        for s in self.sun:
            self.plants = self.plants.append(plants[plants[s]==True], 
                ignore_index=True)
        self.plants = self.plants[self.plants[self.ph]==True]
        self.plants = self.plants[self.plants[self.water]==True]
        self.plants = self.plants[self.plants[self.soil_texture]==True]
        if edible_only:
            self.plants = self.plants[(self.plants['Seeds or Nuts']==True) | 
                (self.plants['Stem']==True) | (self.plants['Leaves']==True) | 
                (self.plants['Roots']==True) | (self.plants['Bark']==True) |
                (self.plants['Sap']==True) |  (self.plants['Fruit']==True) | 
                (self.plants['Flowers']==True)]
        self.include_trees = include_trees
        if not self.include_trees:
            self.plants = self.plants[self.plants['Tree']!=True]
        if perennial_only:
            self.plants = self.plants[self.plants['Life cycle']=='Perennial']

    def create_guild(self):
        n_fixers = False
        if self.include_trees:
            all_layers = ['canopy', 'understory', 'shrub', 'herb','rhizome', 
                'vine']
            guild_layers = random.sample(all_layers, self.num_layers-1)
        else:
            all_layers = ['shrub', 'herb', 'rhizome', 'vine']
            guild_layers = random.choices(all_layers, self.num_layers-1)
        guild = pd.DataFrame()
        canopy = None
        understory = None
        shrub = None
        herb = None
        groundcover = None 
        rhizome = None 
        vine = None 
        if 'canopy' in guild_layers:
            canopies = self.plants[(self.plants['Tree']==True) &  
                (self.plants[self.sun[0]]==True)]
            canopy = canopies.iloc[random.randint(0, len(canopies))]
            guild = guild.append(canopy, ignore_index=True)
        if 'understory' in guild_layers:
            all_understories = self.plants[self.plants['Tree']==True]
            understories = pd.DataFrame()
            if 'canopy' in guild_layers:
                for s in self.sun[1:]:
                    understories = understories.append(all_understories[
                        all_understories[s]==True], ignore_index=True) 
                canopy_height = canopy['Min Height']
                if canopy_height is not np.nan:
                    understories = understories[understories['Max Height'] < 
                        canopy_height]
                else:
                    understories = understories[understories['Max Height'] < 50]
            else:
                understories = all_understories[all_understories[self.sun[0]]==
                    True]
                understories = understories[understories['Max Height'] < 50]
            understory = understories.iloc[random.randint(0, len(understories))]
            guild = guild.append(understory, ignore_index=True)
        canopy_present = 'canopy' in guild_layers
        understory_present = 'understory' in guild_layers
        if 'shrub' in guild_layers:
            shrub = self.get_lower_plants(['Shrub'], canopy_present, understory_present) 
            guild = guild.append(shrub, ignore_index=True)
        if 'herb' in guild_layers:
            herb = self.get_lower_plants(['Herb/Forb', 'Fern'], canopy_present, 
                understory_present)
            guild = guild.append(herb, ignore_index=True)
        if 'vine' in guild_layers:
            vine = self.get_lower_plants(['Vine'], canopy_present, understory_present)
            guild = guild.append(vine, ignore_index=True)
        if 'rhizome' in guild_layers:
            rhizome = self.get_lower_plants(['Rhizome', 'Tuber'], canopy_present, 
                understory_present)
            guild = guild.append(rhizome, ignore_index=True)
        n_fixers = (guild['Nitrogen fixer'] == True).any()
        groundcover = self.get_lower_plants(['Groundcover'], canopy_present,
            understory_present, n_fixers)
        guild = guild.append(groundcover, ignore_index=True)
        return guild
        


    def get_lower_plants(self, layers, canopy_present, understory_present, n_fix=True):
        all_in_layer = pd.DataFrame()
        for l in layers:
            all_in_layer = all_in_layer.append(self.plants[self.plants[l]==True])
        if not n_fix:
            all_in_layer = all_in_layer[all_in_layer['Nitrogen fixer']==True]
        selected = pd.DataFrame()
        if canopy_present or understory_present:
            for s in self.sun[1:]:
                selected = selected.append(all_in_layer[all_in_layer[s]==True])
        else:
            selected = all_in_layer[all_in_layer[self.sun[0]]==True]
        plant = selected.iloc[random.randint(0, len(selected))]
        return plant

# TODO: include 'Leaves Spring ephemeral' with herbs that grow later'
# TODO: add method to get columns and add option to filter by specified columns

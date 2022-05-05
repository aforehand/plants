This module for permaculture gardeners uses Pandas and Selenium to recommend groups of native plants to plant together in guilds mimicking forest ecology. I scraped and cleaned data from the [USDA plants database](https://plants.usda.gov/) using a [REST API](https://github.com/sckott/usdaplantsapi/) and from the [National Gardening Association database](https://garden.org). The module selects plants from different forest layers based on preferences and environmental conditions input by the user, such as USDA hardiness zone, soil pH, and edibility. 

To generate plant recommendations:

```python
>>> rec = plants.GuildRecommender()
>>> guild = rec.create_guild()
```

The `greate_guild()` method returns a pandas DataFrame consisting of the recommended plants along with all of the available data about them. 

```python
>>> guild[['Genus', 'Species']]
        Genus     Species
0    Magnolia  virginiana
1   Baccharis   pilularis
2  Ampelopsis     cordata
3   Comptonia   peregrina
```
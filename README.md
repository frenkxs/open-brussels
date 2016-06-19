# OpenStreetMap Data Case Study

#### Premysl Velek | June 2016

### Map Area
Brussels, Belgium
([preselected metropolitan area](https://s3.amazonaws.com/metro-extracts.mapzen.com/brussels_belgium.osm.bz2) downloaded from Map Zen
)
The dataset – as downloaded via Map Zen – is in ‘brussels_belgium.osm’.


I like Brussels! I lived in the city for five years and I still visit quite often. I was interested to see what the dataset could tell us about the city. I also thought that it would become an interesting exercise: Brussels is a bilingual city with a complicated administrative structure; I assumed the problems in cleaning the dataset would be very different form those in the lessons. 


## Data wrangling - challenges and problems in the dataset
I started exploring the dataset using a series of the dataset samples of the dataset with increasing size. I used the scripts in brussels-exploration.py and focused on street names, cities names and postcodes. Exploring the dataset I found three issues:

- Cities and streets have very often two official names – in French and Dutch 
- Errors in postal codes notation 
- French accents in cities and street names

For all the following edits I used the same function fix_osm. All details on the wrangling and cleaning process is in cleaning_brussels.ipynb. 

### Encoding
Many names of street and cities in this dataset contain French accents (eg. à, ç, è). This in itself would not be a problem, as the osm file is encoded in unicode. However, python outputs unicode characters as strings: the French `"Chaussée"` becomes `"u'Chauss\xe9e"`, `"Avenue des Frères Becqué"` becomes `"u'Avenue des Fr\xe8res Becqu\xe9"` etc. 

As all the output in the project will be printed out in python, it seemed sensible to convert all unicode characters into their ASCII equivalents (Chaussée becomes Chaussee, Frères become Freres etc.). The function `normalize` from the unicodedata library converted the values for the following keys (Dutch orthography doesn't use any non-ASCII characters): 

```python
'addr:name', 'addr:name:fr', 'addr:city', 'addr:city:fr', 'addr:street', 'addr:street:fr'
```

### Cities and street names
Brussels is a bilingual city with two official languages - French and Dutch. While most people in Brussels speak French (about 80-90 %), the city itself is an enclave in Flanders, a Dutch speaking part of Belgium. Wallonia, Belgium's French speaking region is nearby but doesn't border with Brussels. (See: [Wikipedia]( https://en.wikipedia.org/wiki/Communities,_regions_and_language_areas_of_Belgium).)

The dataset contains bilingual as well as French and Dutch speaking regions. In bilingual regions (mostly the city of Brussels) all streets and cities have two official names (eg. Bruxelles in French, Brussel in Dutch). Monolingual regions (either French or Dutch speaking) have only one official name for streets and cities, but may have another unofficial name in the other language (eg. Mechelen is the official Dutch name, but French speakers call it Malines). 

Naming conventions in the dataset are chaotic and inconsistent. Like [tourists finding their way though Belgium]( http://phlegmish-walloony.blogspot.co.uk/2015/02/why-place-names-are-so-confusing-in.html), anyone navigating through the Brussels dataset grapples with despair. The same street in the same city can take several different forms in the dataset:

##### 1. Monolingual
```xml
	<tag k="addr:city" v="Bruxelles"/>
    <tag k="addr:street" v="Place de la Vaillance"/>
	
    <tag k="addr:city" v="Brussel"/> 
	<tag k="addr:street" v="Dapperheidsplein"/>
``` 
##### 2. Bilingual
```xml
    <tag k="addr:city" v="Bruxelles - Brussel"/>
    <tag k="addr:street" v="Place de la Vaillance - Dapperheidsplein"/>
        
    <tag k="addr:city" v="Brussel - Bruxelles"/>
    <tag k="addr:street" v="Dapperheidsplein - Place de la Vaillance"/>
````
##### 3. With dedicated tags for each language version
```xml
    <tag k="addr:city" v="Bruxelles - Brussel"/>
    <tag k="addr:city:fr" v="Bruxelles"/>
    <tag k="addr:city:nl" v="Brussel"/>
    <tag k="addr:street" v="Place de la Vaillance - Dapperheidsplein"/>
    <tag k="addr:street:fr" v="Place de la Vaillance"/>
    <tag k="addr:street:nl" v="Dapperheidsplein"/>
```

The function 'process_names' looks at how frequent each of the above categories are:

```python
'addr:city:bi'................ 43997
'addr:city:fr': ............... 7285
'addr:city:mono': ............ 41350
'addr:city:nl': ............... 7285
'addr:street:bi': ............221764
'addr:street:fr': ............. 7325
'addr:street:mono': ......... 173648
'addr:street:nl': ............. 7324
'city_total': ................ 85347
'street_total': ............. 395412
````

The two basic naming conventions - to include only one version of the name (monolingual, 'mono'), and to include both language versions (bilingual, 'bi') are equally represented in the dataset. The dataset contains 85,347 instances of nodes with cities in the dataset, out of which 43,997 (~51%) is bilingual and 41,350 (49%) monolingual. 

Similarly for streets, out of 395,412 instances of street name, 221,764 (56%) is bilingual, the rest (173,648, 44%) is monolingual. (The instances with dedicated tags for each language version always include a tag with bilingual names, so they are already included in the figures for bilingual tags.)

Separate tags for French and Dutch names (option 3) for all places offer the most systematic approach. Alas, to describe each node in the map with these language-specific keys, we need additional information. We don't know both the French and Dutch names for all cities and streets in the dataset, and we don't know the language region they are in. Lastly, it is not particularly popular practice among the users: of all the nodes with cities and streets, only 8% (for cities) and 1% (for streets) have separate tags for French and Dutch names.

To bring some consistency into this chaos, I opted for a more realistic (and less ambitious) approach. I changed the value for cities and streets in cases where I could find the name of a city or a street in both French and Dutch (ie. there is at least one tag that contains both names, as in: `<tag k="addr:city" v="Bruxelles - Brussel"/>`). In those cases, the functions ‘build_dict’ and fix_osm check each tag with city and street and change their value to the bilingual form. 

However, cities and streets that exist in the dataset only in French or in Dutch (or indeed that are sometimes registered in French and sometimes in Dutch but never in both languages) remained unchanged. After thorough investigation of the dataset, I don't think there are many cases like this, but I cannot be certain. I would need to match the French and Dutch of each particular city, using a list of all streets and cities in the map with their French and Dutch names. I don't have such a list. 

#### Misspellings and typos
There were also a few typos, inconsistent spellings and other irregularities in the names of street and cities. I created a list of these cases based on previous exploration (see cleaning_brussels.ipynb). 

##### Cities
I printed out a list of all cities in the dataset and inspected them manually to see if there were some duplicate spellings and other problems. 

Examples of the inconsistencies for cities (the full list is in cleaning_brussels.ipynb):

```xml
<tag k="addr:city" v="Heist-Op-Den-Berg">
<tag k="addr:city" v="Heist op den Berg">
<tag k="addr:city" v="Heist-op-den Berg">

<tag k="addr:city" v="Brussel Evere">
<tag k="addr:city" v="Evere - Evere">
<tag k="addr:city" v="Ville de Bruxelles - Stad Brussel">
```
Of the different spellings, I chose the one that comes up most often in the dataset. In cases of quarters where users also included the larger city area (eg. 'Brussel Evere' - Evere is part of Brussels), I kept only the name of the quarter, as it is the predominant practice in this dataset.

Few values contained only digits. I invalidated them so that those tags are ignored when exporting into csv.

Finally, there were three cases where the fix wasn't obvious:

```xml
<tag k="addr:city", v="Anderlecht;Forest - Vorst">
<tag k="addr:city", v="Uccle;Brussels">
<tag k="addr:city", v="Kessel-Lo;Wilsele">
```
Since these values contain two different cities, I wanted to find out what place (street, spot, address...) they refer to. After printing out their child and parent tags, (function 'process_problems'), I could identify the correct city for two cases: the tag with "Anderlecht;Forest - Vorst" refer to a bank in Forest (Vorst), the tag with "Uccle;Brussels" refer to Van Buuren Museum in Uccle:

Attributes for parent and child tags for two tags with `v="Anderlecht;Forest - Vorst"`:

```python
{'k': 'addr:city', 'v': 'Anderlecht;Forest - Vorst'}
{'k': 'operator', 'v': 'BNP Paribas Fortis'}
{'k': 'amenity', 'v': 'bank'}
{'k': 'name', 'v': 'BNP Paribas Fortis'}
{'changeset': '19284216', 'uid': '42033', 'timestamp': '2013-12-05T07:31:23Z', 'lon': '4.3264567', 'version': '7', 'user': 'Tbj', 'lat': '50.8239929', 'id': '356622931'}
```

Selected attributes for parent and child tags for tag with `v="Uccle;Brussels"`:

```python
{'k': 'addr:city', 'v': 'Uccle;Brussels'}
{'k': 'name', 'v': 'Musee van Buuren Museum'}
```

The exact location of the third tag will remain a mystery. It was not possible to identify what place the tag refers to. I could find the name and type of the element:

```python
{'k': 'addr:city', 'v': 'Kessel-Lo;Wilsele'}
{'k': 'type', 'v': 'associatedStreet'}
{'k': 'name', 'v': 'Vuntcomplex'}
{'role': 'street', 'ref': '4004855', 'type': 'way'}
```
But I couldn't assign it either to Kessel-Lo, or to Wilsele: [google map says the street Vuntcomplex is right in between Wilsele and Kessel-Lo](https://www.google.co.uk/maps/place/Vuntcomplex,+Leuven,+Belgium/
@50.9071151,4.6814566,13z/data=!4m5!3m4!1s0x47c160b27c61e455:0xfb240be5198f98f4!8m2!3d50.9071151!4d4.7164755). As the next best solution, I replaced the value 'Kessel-Lo;Wilsele' with 'Leuven' (Kessel-Lo and Wilsele are quarters of the Flemish city of Leuven).

I used the same procedure for language specific tags for cities (`addr:city:fr`, `addr:city:nl`). - There was only one case of misspelling (bruxelles with lower case 'b').

##### Streets
As there are many many more streets than cities in the dataset, I couldn't use the same approach for streets. Instead, I only inspected those with problem characters (=, +, &, <, >, ?, %, #, dolar sign, @, comma, Tab, carriage return, and new line character):

``` python
problem_char = re.compile(r'[=\+&<>;\"\?%#@\,\t\r\n]')
```
There were only a handful of streets with those problem characters:

``` python
defaultdict(int,
            {'57+': 2,
             'Beverdijk?': 1,
             'Chaussee de Ninove - Ninoofsesteenweg;Chaussee de Ninove - Ninoofse Steenweg': 1,
             'Dreve de "La Brise" - "La Brise"(Dreef)': 7,
             'Gr. Egm. & Hoornlaan': 1,
             'Heirweg; Haststraat': 1,
             'Place Carnoy;Place Jean-Baptiste Carnoy - Jean-Baptiste Carnoyplein': 2,
             "Route de l'Empire;Rue de l'Empire": 6,
             'Sluis; Donklaan': 7,
             "name=Chaussee d'Anvers - Antwerpsesteenweg": 1,
             'ouvain - Leuvensesteenweg;Chaussee de Louvain - Leuvensesteenweg': 9})
```
Again, I used the same procedure for language specific tags with streets (`addr:street:fr`, `addr:street:nl`).

                                                * * *

Having inspected the outcome of the exploration phase, I created a dictionary of fixes for streets and cities and passed it as argument to the fix_osm function (the dictionaries are in `cleaning_brussels.ipynb`).


#### Post codes
A post code in Belgium has four digits, (eg: 1130). The notation of postcodes is relatively consistent, with only a few problems:
```xml
<tag k = "addr:post_code" v = "B 1040">
<tag k = "addr:post_code" v = "3120 Tremelo">
<tag k = "addr:post_code" v = "Grimbergen">
<tag k = "addr:post_code" v = "10303">

```

All of the issues can be ascribed to typos, different notation, or just plainly wrong data. In two cases the value had a wrong number of digits for a Belgian postcode: in those two cases, I printed out their parent tags to find out more about the nodes they are part of - in both cases they were just typos with one digit missing or redundant.

Few values for addr:post_code contained more than one postcode:

```xml
<tag k = "addr:post_code" v = "1040;1041;1042">
```
Seemingly it doesn't make sense to have three different post codes to denote an address. To found out more about the tags with such notation, I printed out their parent tags to see what kind of object they denote. It turned out that they refer to a city or a street that span more than one postal district. From what I could find, the best practice in the OSM community in those cases is to [split the way/node/relation where the postal code changes](http://wiki.openstreetmap.org/wiki/Talk:Key:postal_code). As there were only a handful such cases (23 out of 91,335), I decided to ignore them and not to export them into the SQL database.



## Export

To export the resulting osm file into SQL database, I first exported selected data into a series of csv files, using the methods in export.py file. The csv file were then imported into SQL database 'brussels.db', which follows the schema provided in the 'schema.py'. 



## Data Overview

This section provides a basic overview of the data in brussels.db. I ran the sql queries, using python's sqlite3 library. All queries are in brussels-exploration.py.

### File sizes
```
brussels_belgium.osm ..... 1,090 MB
brussels.db .............. 646.6 MB
nodes.csv ................ 366.7 MB
nodes_tags.csv .............. 22 MB
ways.csv .................. 46.3 MB
ways_tags.csv ............. 83.1 MB
ways_nodes.cv ............ 154.9 MB  
```  

### Number of nodes
```sql
SELECT COUNT(*) FROM nodes;
```
4,589,143

### Number of nodes, including those forming ways
```sql
SELECT
(SELECT COUNT(*) FROM nodes) + 
(SELECT COUNT(*) FROM way_nodes);
```
11,054,570


### Number of ways
```sql
SELECT COUNT(*) FROM ways;
```
795,223

### Number of unique users
```sql
SELECT COUNT(DISTINCT(users.uid))          
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) users;
```
2,537

### Top 10 contributing users
```sql
SELECT names.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) names
GROUP BY names.user
ORDER BY num DESC
LIMIT 10;
```

```
TAA ...................... 918,281
lodde1949 ................ 762,899
eMerzh ................... 625,829
foxandpotatoes ........... 350,266
Polyglot ................. 222,496
FantAntonio99 ............ 213,569
Paul-Andre Duchesne ...... 175,319
Potato_Spirit ............ 167,486
escada ................... 157,010
Scapor ................... 145,232
```
 
### Number of public transport stops 
The total number of bus stops, tram stops, underground and railway stations.
```sql
SELECT value, COUNT(*)
FROM (SELECT key, value from node_tags 
UNION ALL SELECT key, value from way_tags)
WHERE (value = 'tram_stop' OR value = 'bus_stop') OR (value = 'station' AND key = 'railway')
GROUP BY value;
```
```
bus stops .......................... 9,659
tram stops ......................... 607
railway and underground stations ... 255
```

### Comic strip murals in Brussels
Brussels boasts a number of comic strip murals. They show motifs of the most popular Belgian comics: the Adventures of Tintin, Lucky Luke, Le Chat, Asterix & Obelix, and others. (See [Wikipedia](https://en.wikipedia.org/wiki/Brussels%27_Comic_Book_Route)). 

#### Number of murals

```sql
SELECT COUNT(*)
FROM node_tags
WHERE value = 'mural' 
GROUP BY value
```
50

#### Comic book heroes depicted on Brussels murals
```sql
SELECT value, COUNT(*) AS artists
FROM (SELECT id FROM node_tags WHERE value = 'mural') AS murals
JOIN node_tags 
ON murals.id = node_tags.id
WHERE key = 'title'
GROUP BY value
ORDER BY artists DESC;
```
Two comic books have two murals in Brussels:

```
Ric Hochet ... 2
Tintin ....... 2
```
The rest have one mural:

```
Asterix et Obelix, Billy the Cat, Blake et Mortimer, Blondin et Cirage, Bob et Bobette, Boule et Bill, 
Broussaille, Caroline Baldwin, Cori, Corto Maltese, Cubitus, Gaston Lagaffe, Gil Jourdan, 
Isabelle et Calendula, Jojo, Kiekeboe, L'Ange de Sambre, La Vache, La patrouille des Castors, Le Chat, 
Le Jeune Albert, Le Passage, Le Petit Spirou, Le Scorpion, Le roi des mouches, Les reves de Nick, Lincoln, 
Lucky Luke, Martine, Monsieur Jean, Natacha, Neron, Odilon Verjus, Olivier Rameau, Passe-moi l'ciel, 
Quick et Flupke, Titeuf, Victor Sackville, XIII, Yoko Tsuno
```

As there are only 44 titles, but 50 murals in total, it seems that the dataset is missing the titles for six murals. 


## Additional Ideas

### Language - cleaning
This project dealt extensively with naming convention for cities and streets in the dataset. After exploring the different styles, I am more and more convinced that the system of tagging nodes and ways used by the contributors to the Brussels map is insufficient for the complex relations between the French and Dutch language communities in Brussels (and Belgium in general). 

A solution exist already in the dataset in tags that indicate the French and Dutch names in separate tags:

```xml
<tag k="addr:city:fr" v="Bruxelles">
<tag k="addr:city:nl" v="Brussel">
```
This is indeed the [recommended format for Brussels by the Belgian Open Street community](http://wiki.openstreetmap.org/wiki/Multilingual_names#Belgium). However, only a handful of users adopted this practice. 
Given the sheer number of elements in the dataset, it is clearly unfeasible to update the nodes manually. To update it programmatically, we may draw on the GPS coordinates of each particular node. Knowing the GPS coordinates, we can place each node in an appropriate language community (French, Dutch and bilingual), using a political or administrative map of Belgium. 

### Language – exploration
As I mentioned, Brussels is predominantly French speaking city, with only about 10 % of Dutch speaking population. By exploring the language in which cities, streets and other elements are registered in the dataset, we may get some insight into the geographic distribution of Dutch (and French) speakers within the city. 

When a street is registered only in Dutch (of French), we can assume that this is the predominant practice in the area, ergo majority of speakers are Dutch (French). We can then count the number of such monolingual streets per city and gain some indication of the language policy in that particular city. 

As streets in Dutch and French have very different and distinct patterns (the word ‘street’ comes before the actual street name in French (Rue Haute), and after it in Dutch (Hoogstraat)), we could use relative simple regular expressions to check programmatically if a given name is in French or in Dutch.


## Conclusion

Having explored the Brussels dataset, it is clear the complex language structure in Brussels (and Belgium) exposes many of the shortcomings of community driven data collection. The particular elements in the dataset are inconsistent with many different ways of notation; they are prone to various errors (eg. changing the order of names in bilingual tags makes it incompatible with other tags with the same name – ‘Bruxelles – Brussel’ and ‘Brussel – Bruxelles’ are then treated as two different cities.)
This report discusses some of the problems in naming conventions for cities and streets, but I expect that very similar problems will arise when cleaning others forms of data: names, titles, etc.

While I think that I did a decent job in harmonising cities in the dataset, it is nowhere near ideal for streets (and for other local nomenclature: name, title, etc.). My recommendation is to strictly follow the best practice for Brussels endorsed by the Open Street community. 

I realise however, that it is quite ambitious plan and perhaps not very practical. The dataset can be used in many different ways even with all its inconsistencies. Unless it is absolutely critical to have consistent names in the dataset, one can argue that the cost-benefit considerations will speak against this endeavour.

## References
- Schema, scripts and guidance provided in the OpenStreetMap Case study: https://classroom.udacity.com/nanodegrees/nd002/parts/0021345404/modules/316820862075461/lessons/5436095827/concepts/54908788190923 

- Udacity Forum: Changing attribute value in XML: https://discussions.udacity.com/t/changing-attribute-value-in-xml/44575/6 
- Stackoverflow: writing back into the same file after reading from the file: http://stackoverflow.com/questions/17646680/writing-back-into-the-same-file-after-reading-from-the-file 
- lxml library documentation: http://lxml.de/parsing.html

I would like to especially thank both martin-martin and myles – the main contributors to the Udacity forum. Without their insights, I wouldn’t not be able to finish this projects.

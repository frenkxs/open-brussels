#!/usr/bin/env python
# -*- coding: utf-8 -*-


# libraries needed
from collections import defaultdict
from lxml import etree as ET
import re
from pprint import pprint
import unicodedata


# original dataset downloaded form Open Street Map, the scripts below make edits directly to this file

######################     Helpers     #####################################

def get_element(filename):
# tag generator - parses through the supplied xml file and yields to its 
# caller a tag - one at a time
     
    tags = ['node', 'way', 'relation','meta','bounds','note']
    
    context = iter(ET.iterparse(filename, events=('start', 'end')))
    _, root = next(context)
    
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def fix_unicode(tag, address):        
# recode the unicode characters back to string, using unicodedata 
     
    if (address in tag.attrib['k']):
        if type(tag.attrib['v']) == unicode:
            tag.attrib['v'] = unicodedata.normalize('NFKD',     tag.attrib['v']).encode('ascii', 'ignore')    


def is_address(tag, address):
# tests if a tag has city or street name as its attribute ('addr:city' or 
# 'addr:street')    

     return (tag.attrib['k'] == address)


def fix_address(tag, address, **fixes):
# change the city 'v' attribute, based on the provided dictionary

     if is_address(tag, address):
          if tag.attrib['v'] in fixes:
                tag.attrib['v'] = fixes[tag.attrib['v']]
                
                
dash = re.compile(r'[\s-]+-[\s-]')
# Matches dash with a space in front and behind to detect dash inbetween two 
# names eg. 'Rue de la Comtesse de Flandre - Gravin Van Vlaanderenstraat'
# (This serves as an indication of bilingual naming of a city or street).

##########################################################################     


###########################################################################
######################    EDIT TAGS    ####################################
###########################################################################

'''
This function 'fix_osm' edits the names of street and cities in the osm file. It can edit the encoding of streets and cities
(from unicode to string), and change the cities'/streets' naming convention (eg. from 'Brussel' to 'Bruxelles - Brussel'). 
It takes two compulsory agruments - the source osm file and the type of edit (fix_unicode or fix_address). 
To edit streets and cities, two additional arguments are needed - type of address ('street' or 'city') and
a dictionary of 'fixes' (output of the function 'build_dict').
'''

def fix_element(filename, fix, *args, **kwargs):
# finds elements that may need fixing and fetches it to one of the helper
# functions above
     
    tags = ['node', 'way', 'relation','meta','bounds','note']            
    
    context = ET.iterparse(filename, events=('start', 'end'))
    _, root = next(context)
     
    for event, elem in context:
        if event == 'end' and elem.tag in tags:

            for tag in elem.iter('tag'):
                
                fix(tag, *args, **kwargs)             
        
            yield elem
            root.clear()             
        
            
def fix_osm(filename, fix, *args, **kwargs):
# Edits xml file - the core function

    import tempfile
    import sys

    temp_file = tempfile.NamedTemporaryFile(mode = 'r+')
    input_file = open(filename, 'r')

    temp_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    temp_file.write('<osm>\n  ')
    
    for i, element in enumerate(fix_element(filename, fix, *args, **kwargs)):
          temp_file.write(ET.tostring(element, encoding='utf-8'))
    temp_file.write('</osm>')

    input_file.close()
    temp_file.seek(0)

    with open(filename, 'w') as f:
        for line in temp_file:
            f.write(line)

    temp_file.close()

# fix_osm(bxl, fix_unicode, 'name:fr')
# fix_osm(bxl, fix_address, 'addr:city', **city_fix)
# fix_osm(bxl, fix_address, 'addr:street', **street_fix)
    
###########################################################################
######################    EXPLORE MAP    ##################################
###########################################################################     

'''
Dictionary builder - it parses through the xml and builds a dictionary of the different forms of naming a city or a street. 
Cities are streets can be either in Dutch (Brussel), in French (Bruxelles), or in both languages ('Brussel - Bruxelles' or 
'Bruxelles - Brussel'). This dictionary lists all four posibilities for each city found in the xml file (as keys) and assigns 
them one value. 

The value is always bilingual, but the order (Dutch - French or French - Dutch) may differ as it depends what form the 
parser encouters first. Note that the value of the city (attribute 'v') will only be fixed for cities 
for which at least one tag in the source file contains both French and Dutch name. Cities recorded only in French or 
only in Dutch (or indeed sometimes in French and sometimes in Dutch but never in both languages) will remain 
unchanged.    

The function takes two arguments: the source xml file and 'k' attribute either for street ('addr:street') or city ('addr:city'), 
depending on what we want to fix.
'''

def build_dict(filename, address):
# parses through the xml file and creates a dictionary of the different forms # of naming a city or a street. 
     
    names = {}
        
    for i, element in enumerate(get_element(filename)):
        for tag in element.iter('tag'):
            if tag.attrib['k'] == address:
                    m = re.search(dash, tag.attrib['v'])
                    if m:
                        splitted = tag.attrib['v'].split(' - ')
                        if tag.attrib['v'] not in names:
                            names[tag.attrib['v']] = tag.attrib['v']
                            names[splitted[0]] = tag.attrib['v']
                            names[splitted[1]] = tag.attrib['v']
                            names[splitted[1] + ' - ' + splitted[0]] = tag.attrib['v']
                      
    return names

# city_fix = build_dict(bxl, 'addr:city')
# street_fix = build_dict(bxl, 'addr:street')

'''
Prints out all cities in the dataset, together with how many of them the dataset contains. 
(The function could be also used for streets, but my exploration of smaller samples of the dataset showed that the map 
contains most streets only once only a couple of times. The huge number of streets in the dataset would also make the output 
fairly impractical. I epxplore streets in function 'process_streets' (see below).    
'''

def explore_names(filename, address):
# parses through the xml files and prints out the value for a given
# key(provided in the address argument)   
    
    names = defaultdict(int)
    
    for i, element in enumerate(get_element(filename)):
        for tag in element.iter('tag'):
            if tag.attrib['k'] == address: 
                names[tag.attrib['v']] += 1 

    return names    

# explore_names(bxl, 'addr:city')

'''
Prints out all values of a given key with problem characters. Used mainly to capture problems in the names of cities.
'''
problem_char = re.compile(r'[=\+&<>;\"\?%#$@\,\t\r\n]')

def process_problems(filename, address, pattern, parents = False):
# Takes three arguments, the xml file, the key ('addr:street', 'name', 'addr:street:fr', etc.) and the regex pattern to match.

    problems = defaultdict(int)
    
    for i, element in enumerate(get_element(filename)):
        for tag in element.iter('tag'):
            if tag.attrib['k'] == address:

                    is_problem_street = re.search(pattern, tag.attrib['v'])
                    if is_problem_street:
                        problems[tag.attrib['v']] += 1 

                        '''
                        the code below prints out the parents, siblings and children of a problem tag to learn more about the 
                        problematic element.               
                        '''       
                        if parents == True:
                            print '------'
                            print tag.attrib
                            for item in tag.itersiblings(preceding = True):
                                print item.attrib
                            for item in tag.iterancestors():
                                print item.attrib
                            for item in tag.iterdescendants():
                                print item.attrib
                            
    return problems

# process_problems(bxl, 'addr:street', problem_char, parents = 'True')

'''
Prints out the number for each of the different naming convention for streets and cities - 
how many street and city names are recorded both in Dutch and in French, how many of them are recorded in separate
tags ('addr:street:fr', 'addr:city:nl', etc.) and how many are recorded only in one language (French or Dutch).
'''


def process_names(filename):
# parses through the xml files and counts how many times each of the different # notations for names come up in the dataset 
    
    names = defaultdict(int)
        
    addresses = [['addr:street', 'addr:city'], ['addr:street:fr', 'addr:street:nl', 'addr:city:fr', 'addr:city:nl']]
    # list of the different naming conventions for street and cities as part         of an address
     
    for i, element in enumerate(get_element(filename)):
        for tag in element.iter('tag'):
            for item in addresses[0]:
                if tag.attrib['k'] == item:
                    m = re.search(dash, tag.attrib['v'])
                    if m:
                        names[item + ':bi'] += 1 
                    else:
                        names[item + ':mono'] += 1
                            
            for item in addresses[1]:
                if tag.attrib['k'] == item:
                    names[item] += 1
    
#    To get the total number of nodes/ways/relations with street/cities, we only sum up monolingual and bilingual tags. 
#    Nodes, ways or relations with dedicated tags for each language version, also have bilingual tags, so they are already included in the bilingual tags.
    names['city_total'] = sum((names['addr:city:bi'], names['addr:city:mono']))                    
    names['street_total'] = sum((names['addr:street:bi'], names['addr:street:mono']))                    
        
    return names

#process_names(bxl)

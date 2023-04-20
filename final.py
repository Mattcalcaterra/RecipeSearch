from flask import Flask, render_template, request
import requests
import json
from spoonacular_key import SPOON_KEY
import pprint as pp
from bs4 import BeautifulSoup
import csv
import time
import re

app = Flask(__name__, static_folder='staticFiles', template_folder='templateFiles')
RECIPE_CACHE = dict()
RECIPE_CACHE_FILENAME = 'recipeCache.json'
HTML_CACHE = dict()
HTML_CACHE_FILENAME = 'htmlCache.json'

class Vertex():
  def __init__(self, key, image=None, url=None):
    self.id = key
    self.connectedTo = {}
    self.image = image
    self.url = url
  def addNeighbor(self, nbr, weight=0):
    self.connectedTo[nbr] = weight
  def getId(self):
    return self.id
  def getWeight(self, nbr):
    return self.connectedTo[nbr]
  def getConnections(self):
    return self.connectedTo.keys()
  def __str__(self):
    return str(self.id)
    return str(self.id) + 'is connected to ' + str((x.id, x.weight) for x in self.connectedTo)
    # return str(self.id) + ' connectedTo: ' + str([x.id for x in self.connectedTo])


def get_ingredient_ids():
  '''
  gets list of top 1000 ingredient ids
  '''
  ingredient_ids = {}
  with open('top-1k-ingredients.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
      ingredient_ids[row[0]] = row[1]
  return ingredient_ids

def make_url_request(url):
  if url in HTML_CACHE.keys():
    response = HTML_CACHE[url]
  else:
    time.sleep(1)
    response = requests.get(url).text
    HTML_CACHE[url] = response
  return response

def get_gerd_data():
  '''
  Uses beautiful soup to webscrap for ingredients to eat or not to eat based on GERD
  '''
  response = make_url_request('https://www.hopkinsmedicine.org/health/wellness-and-prevention/gerd-diet-foods-that-help-with-acid-reflux-heartburn')
  soup = BeautifulSoup(response, 'html.parser')
  parents = soup.find_all('div', class_='rtf')
  li = []
  for div in parents:
    for l in div.find_all('li'):
      ingredient = l.string.replace('such as', ',').replace(' and ', ',').replace('.','')
      ingredient = re.sub("[\(\[].*?[\)\]]", "", ingredient)
      ingredient = ingredient.split(',')
      for i in range(len(ingredient)):
        li.append(ingredient[i].strip().lower())

  return {'exclude': li[0:16], 'include': li[16:]}

def get_heartdisease_data():
  '''
  Uses beautiful soup to webscrap for ingredient to eat or avoid for heart disease
  '''
  response = make_url_request('https://www.mayoclinic.org/diseases-conditions/heart-disease/in-depth/heart-healthy-diet/art-20047702')
  soup = BeautifulSoup(response, 'html.parser')
  parent = soup.find('div', id='main')
  li = []
  tables = parent.find_all('table')
  for table in tables:
    for l in table.find_all('li'):
      ingredient = l.string.replace('such as', ',').replace(' and ', ',').replace('.','')
      ingredient = re.sub("[\(\[].*?[\)\]]", "", ingredient)
      ingredient = ingredient.split(',')
      for i in range(len(ingredient)):
        li.append(ingredient[i].strip().lower())
  return {'exclude': li[4:9] + li[19:33] + li[79:91], 'include': li[0:4] + li[9:19] + li[60:79]}

def get_diabetes_data():
  '''
  Uses beautiful soup to webscrap for ingredient to eat or avoid for heart disease
  '''
  response = make_url_request('https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295')
  soup = BeautifulSoup(response, 'html.parser')
  parent = soup.find('div', id='main-content', role='main')
  lists = parent.find_all('ul')
  li=[]
  for ul in lists:
    for l in (ul.find_all('li')):
      if l.string != None:
        ingredient = l.string.replace('such as', ',').replace(' and ', ',').replace('.','').replace('or', ',')
        ingredient = re.sub("[\(\[].*?[\)\]]", "", ingredient)
        ingredient = ingredient.split(',')
        for i in range(len(ingredient)):
          li.append(ingredient[i].strip().lower())
  return {'exclude': [], 'include': li}


  # li = []
  # tables = parent.find_all('table')
  # for table in tables:
  #   for l in table.find_all('li'):
  #     ingredient = l.string.replace('such as', ',').replace(' and ', ',').replace('.','')
  #     ingredient = re.sub("[\(\[].*?[\)\]]", "", ingredient)
  #     ingredient = ingredient.split(',')
  #     for i in range(len(ingredient)):
  #       li.append(ingredient[i].strip().lower())
  # return {'exclude': li[4:9] + li[19:33] + li[79:91], 'include': li[0:4] + li[9:19] + li[60:79]}


def get_condition_data(condition):
  '''
  Gets ingredients to exclude/include from diet based on medical condition webscraping
  '''
  if condition == 'diabetes':
    return get_diabetes_data()
  elif condition == 'gerd':
    return get_gerd_data()
  elif condition == 'heartdisease':
    return get_heartdisease_data()
  else:
    return {'include': [], 'exclude': []}

def ingredient_to_id(ingredient, ingredient_ids):
  '''
  Converts ingredient name into spoonacular id
  '''
  if ingredient.lower() in ingredient_ids.keys():
    return str(ingredient_ids[ingredient.lower()])
  else:
    return ''

def clean_recipe_data(recipe_data):
    ''' Takes a dictionary of recipe data and thins down to relevant key/value pairs

    Parameters
    ----------
    recipe_data (dict):
        Dictionary containing recipe data

    Returns
    -------
    Dict:
        Cleaned dictionary
    '''
    ingredients = []
    try:
      for step in recipe_data.get('analyzedInstructions')[0].get('steps'):
        for ingredient in step.get('ingredients'):
          ingredients.append(ingredient)
    except:
      ingredient = ['none']
    cleaned_data = {
        # 'diets': recipe_data.get('diets'),
        'dishTypes': recipe_data.get('dishTypes'),
        # 'dairyFree': recipe_data.get('dairyFree'),
        # 'glutenFree': recipe_data.get('glutenFree'),
        'image': recipe_data.get('image'),
        'sourceUrl': recipe_data.get('sourceUrl'),
        'title': recipe_data.get('title'),
        # 'vegan': recipe_data.get('vegan'),
        # 'vegetarian': recipe_data.get('vegetarian'),
        'ingredients': ingredients # [ingredient for step in recipe_data.get('analyzedInstructions')[0].get('steps') for ingredient in step.get('ingredients')]
   }

    return cleaned_data


def get_recipe_data(query='', diet='', intolerances='', includeIngredients='', excludeIngredients=''):
    ''' Takes entered params to call spoonacular API. If there is data in the cache uses cached data instead.

    ----------
    query (str):
    diet (str):
    intolerances (str):
    includeIngredients (str):
    excludeIngredients (str):

    Returns
    -------
        List of dictionaries containing recipe data
    '''

    if diet != '':
      _diet = f'&diet={diet}'
    else:
      _diet = diet
    if intolerances != '':
      _intolerances = f'&intolerances={intolerances}'
    else:
      _intolerances = intolerances
    if includeIngredients != '':
      _includeIngredients = f'&includeIngredients={",".join(includeIngredients)}'
    else:
      _includeIngredients = includeIngredients
    if excludeIngredients != '':
      _excludeIngredients = f'&excludeIngredients={excludeIngredients}'
    else:
      _excludeIngredients = excludeIngredients
    if query != '':
      _query = f'query={query.replace(" ", "")}'
    else:
      _query = query

    url = f'https://api.spoonacular.com/recipes/complexSearch?{_query}{_diet}{_intolerances}{_includeIngredients}{_excludeIngredients}&apiKey={SPOON_KEY}&addRecipeInformation=true&number=100'

    if url in RECIPE_CACHE.keys():
        return RECIPE_CACHE[url]
    else:
        response = requests.get(url)
        RECIPE_CACHE[url] = response.json()['results']

    return response.json()['results']


def open_recipe_cache():
  ''' opens the cache file if it exists and loads the JSON into
  a dictionary, which it then returns.
  if the cache file doesn't exist, creates a new cache dictionary
  Parameters
  ----------
  None
  Returns
  -------
  The opened cache
  '''
  try:
    cache_file = open(RECIPE_CACHE_FILENAME, 'r')
    cache_contents = cache_file.read()
    cache_dict = json.loads(cache_contents)
    cache_file.close()
  except:
    cache_dict = {}
  return cache_dict

def open_html_cache():
  ''' opens the cache file if it exists and loads the JSON into
  a dictionary, which it then returns.
  if the cache file doesn't exist, creates a new cache dictionary
  Parameters
  ----------
  None
  Returns
  -------
  The opened cache
  '''
  try:
    cache_file = open(HTML_CACHE_FILENAME, 'r')
    cache_contents = cache_file.read()
    cache_dict = json.loads(cache_contents)
    cache_file.close()
  except:
    cache_dict = {}
  return cache_dict


def save_recipe_cache(cache_dict):
  ''' saves the current state of the cache to disk
  Parameters
  ----------
  cache_dict: dict
  The dictionary to save
  Returns
  -------
  None
  '''
  dumped_json_cache = json.dumps(cache_dict)
  fw = open(RECIPE_CACHE_FILENAME,"w")
  fw.write(dumped_json_cache)
  fw.close()

def save_html_cache(cache_dict):
  ''' saves the current state of the cache to disk
  Parameters
  ----------
  cache_dict: dict
  The dictionary to save
  Returns
  -------
  None
  '''

  cache_file = open(HTML_CACHE_FILENAME, 'w')
  contents_to_write = json.dumps(cache_dict)
  cache_file.write(contents_to_write)
  cache_file.close()

def build_network(cleaned_data):
  '''
  cleaned_data (list):
    a list of dictionaries of recipe data

  '''
  recipes = []
  ingredients = []

  for recipe in cleaned_data:
    recipes.append(Vertex(key=recipe['title'], image=recipe['image'], url=recipe['sourceUrl'], dishTypes=recipe['dishTypes']))
    for ingredient in recipe['ingredients']:
        ingredients.append(Vertex(key=str(ingredient['id'])))
        recipes[-1].addNeighbor(nbr=ingredients[-1], weight=1)
        ingredients[-1].addNeighbor(nbr=recipes[-1], weight=1)
  write_graph_to_json(recipes=recipes, ingredients=ingredients)
  return (recipes, ingredients)


def find_recipes(ingredients, ingredient_in=[], ingredient_ex=[]):
  '''
  Searches graph to find recipes connected to ingredients to include and returns them if they aren't neighbors with ingredients to exclude
  '''

  # Disgusting code but it works :)
  return_recipes = []
  for ingredient in ingredient_in:
      for ing in ingredients:
         if ingredient == ing.getId():
            ing_recipes = ing.getConnections()
            for rec in ing_recipes:
              if any(connection not in ingredient_ex for connection in rec.getConnections()):
                if rec not in return_recipes:
                   return_recipes.append(rec)
  return return_recipes

def prep_for_flask(user_query, ingredient_in=[], ingredient_ex=[], diet='', condition=''):
  '''
  Combines prior functions for output to user
  '''
  # get ingredient ids
  ingredient_ids = get_ingredient_ids()

  # convert ingredient include/exclude to ids
  ingredient_in = [ingredient_to_id(ingredient, ingredient_ids=ingredient_ids) for ingredient in get_condition_data(condition=condition)['include']]
  ingredient_ex = [ingredient_to_id(ingredient, ingredient_ids=ingredient_ids) for ingredient in get_condition_data(condition=condition)['exclude']]


  print(ingredient_in)
  print(ingredient_ex)
  # get recipe data from apis
  recipe_data = get_recipe_data(query=user_query, diet=diet, includeIngredients=ingredient_in)
  print(len(recipe_data))

  # cleans recipe data
  cleaned_recipe_data = [clean_recipe_data(recipe) for recipe in recipe_data]

  # builds graph from recipe data
  recipes, ingredients = build_network(cleaned_data=cleaned_recipe_data)

  # searches recipe/ingredient graph based on ingredients include/exclude
  returned_recipes = find_recipes(ingredients=ingredients, ingredient_in=ingredient_in, ingredient_ex=ingredient_ex)

  # Saves cache after call
  save_html_cache(HTML_CACHE)
  save_recipe_cache(RECIPE_CACHE)


  return [(recipe.getId(), recipe.url, recipe.image) for recipe in returned_recipes]

def write_graph_to_json(recipes, ingredients):
  '''
  Writes graph into a json file
  '''
  dictionary = {'graph': {}}
  for recipe in recipes:
    dictionary['graph'][recipe.getId()] = {'connectedTo': [str(connection) for connection in recipe.getConnections()], 'url': str(recipe.url), 'image': str(recipe.image)}
  for ingredient in ingredients:
    dictionary['graph'][ingredient.getId()] = {'connectedTo': [str(connection) for connection in ingredient.getConnections()], 'url': str(recipe.url), 'image': str(recipe.image)}

  json_object = json.dumps(dictionary, indent=4)

  with open('foodGraph.json', 'w') as outfile:
    outfile.write(json_object)


### Flask routes ###

@app.route('/')
def index():
  return render_template('index.html')


@app.route('/results', methods=['POST'])
def handle_the_form():
  condition = request.form['condition']
  diet = request.form['diet']
  user_query = request.form["query"]
  return_recipes = prep_for_flask(user_query=user_query, ingredient_in=[], ingredient_ex=[], condition=condition, diet=diet)
  return render_template('results.html', return_recipes=return_recipes, user_query=user_query.title(), diet=diet.title(), condition=condition.title(), number=len(return_recipes))




if __name__ == '__main__':
    HTML_CACHE = open_html_cache()
    RECIPE_CACHE = open_recipe_cache()
    app.run(debug=True)

    save_html_cache(HTML_CACHE)
    save_recipe_cache(RECIPE_CACHE)
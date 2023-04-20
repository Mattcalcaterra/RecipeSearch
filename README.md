# RecSearch
This project was developed as a part of SI 507. RecSearch is a web-based application developed using python and flask. Rec search pairs user inputs with data from the Spoonacular API and webscraped healthdata from mayoclinic.ord and hopkinsmedicine.org. Through the web interface users are able to input a query for the type of recipe they want, and select a medical condition and diet. These inputs are then used to pull recipe and condition data from the data sources. The recipe data is then sorted in a graph of ingredients and recipes. This graph is then searched and entries which match the medical conditions are returned to the user through the web-interface. 

---

## Requirements

- Python 3.6 or higher

### Required Packages

- flask
- requests
- bs4
- json (standard library)
- re (standard library)
- time (standard library)
- csv (standard library)

To install the required packages, run the following code:
```python
pip install flask
pip install requests
pip install bs4
```

### API Keys

In order to use the application an API key for Spoonacular API must be provided. Save the key in the same directory as the program with the following code in a file called **spoonacular_key.py**.

`SPOON_KEY = {your spoonacular key}`

## Data Structure

### Data Sources
- mayoclinic.org
- hopkinsmedicine.org
- Spoonacular API
- top-1k-ingredients.csv (from spoonacular)

The data structure used for this application is a graph. Each recipe and ingredient is stored as a vertex in the graph once called from the Spoonacular API. The graph can then be accessed by either an ingredient or recipe and the connections can be found using `Vertex.getConnections()`. Each Vertex object contains the id of the recipe or ingredient, and if the vertex is a recipe, contains the url and image for that recipe. In the application the Vertexs are stored in two list `recipes` and `ingredients`. The graph is accessed via the `ingredients` list and all connections of the desired ingredients (determined from the condition data) are accessed. If the neighbors of the desired ingredients does not neighbor and excluded ingredient (determined from the condition data) that recipe is returned to the user (along with its image and url) in the web interface.

`top-1k-ingredients.csv` is loaded to convert ingredients sourced from webscraping to id numbers compatiable with the Spoonacular API

The data from these sources are stored in two Caches, one for the spoonacular API data and one for the webscraping data. These are written to the .json items `htmlCache.json` and `recipeCache.json`. Additionally, after each user search the graph which is created is stored in a json named `foodGraph.json` which can be seperately accessed via the program `read_graph.py`.

## User Interaction

The user is able to interact with the application through a flask-based web application. In the web application users are able to enter the kind of recipe they desire and select a medical condition and diet. Once the user presses search the datasources will be called and the graph is searched: returning matching recipes to the user. These recipes are displayed in a vertical list with the image, name, and url for each recipe.


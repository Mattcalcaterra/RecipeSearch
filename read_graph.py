import json

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

with open('foodGraph.json', 'r') as openfile:
    food_graph = json.load(openfile)

foodGraph = []
for key in food_graph['graph'].keys():
  foodGraph.append(Vertex(key=key, url=food_graph['graph'][key]['url'], image=food_graph['graph'][key]['image']))


print([str(food) for food in foodGraph])
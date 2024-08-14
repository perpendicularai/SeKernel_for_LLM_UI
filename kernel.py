# List class
class MyList(list):
     pass

# Model class
class Model(str):
     pass

# Template function that takes a string as input and returns a list
def DBTemplate(plugin, context):
     my_list = MyList
     my_list = [
          {"role": "system", "content": plugin},
          {"role": "user", "content": f"Create a Data Table using this data {context}"}
          ]
     return my_list

def shopTemplate(prompt: str, plugin, context):
     my_list = MyList
     my_list = [
          {"role": "system", "content": plugin},
          {"role": "user", "content": f"Using this data {context}, respond to this prompt {prompt}"},
          ]
     return my_list

def chatTemplate(plugin):
     my_list = MyList
     my_list = [
          {"role": "system", "content": plugin},
          ]
     return my_list

# Model function that returns the model as a string
def model():
     model = Model("<YOUr MODEL PATH>")
     return model
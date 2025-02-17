from wfcommons import WfChef

# Load a workflow instance from a JSON file (in WfFormat)
workflow_instance_path = "path/to/your/workflow-instance.json"
chef = WfChef(workflow_instance_path)

# Generate a synthetic workflow recipe based on the instance
recipe = chef.cook_recipe()

# Save the generated recipe to a file
recipe_path = "synthetic-recipe.json"
recipe.to_file(recipe_path)

print(f"Synthetic workflow recipe saved to {recipe_path}")


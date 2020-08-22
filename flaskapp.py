from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def main():
    return "<h1>CITS3200_17 Flask App<h1>"

# Below is an example of how to add other pages
# To go to this webpage you would need to add "/Examplepage" to the end of the main page url
@app.route("/Examplepage")
def example():
    return "<h1>Example page<h1>"
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template
app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def main():
    return render_template('main.html', title='Main')

# Below is an example of how to add other pages
# To go to this webpage you would need to add "/Examplepage" to the end of the main page url
@app.route("/Examplepage", methods=['GET', 'POST'])
def example():
    return render_template('example.html', title='Example')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

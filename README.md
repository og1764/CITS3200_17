# CITS3200_17

### Project: A new web-based galaxy classification tool using deep learning

#### Project Goal
The goal of this project is to develop a web-based platform, where users can input a galaxy image, then the AI (i.e., python code using Keras/tensorflow) in the platform will automatically classify the image into a morphological category (e.g., spiral or elliptical galaxy) and show the result online.

The platform will require a connection to a server where the classification task by the AI can be done very quickly.

We also require the input/output image transfer between the server and the web to be done quickly. 

Many images of galaxies can be found [here](https://apod.nasa.gov/apod/astropix.html)


## Development Environment

### Sections

[git setup](#gitsetup)

[Branching](#branching)

[Running The Web App](#running-the-web-app)

[Folder structure](#folder-structure)


### git setup
Since we are using git to collaborate it is important that you get familiar with branching, rebasing, merging & pull requests in order to keep the workflow smooth.

Make sure that you have forked this repo. Once you have forked it, clone it to your desktop.
You can do this by using the gitHub desktop app which can be found over at [desktop.github.com](https://desktop.github.com/).
If you prefer to use git in terminal then change into the directory you want the cloned repo in and run the following command followed by the url for your forked repo. For me this is:
```git clone https://github.com/Abdi-Isse/CITS3200_17.git```

Once you have done that you want to make sure that the remote for your repo is set up right. Run the following command from the directory of where your cloned repo is:
```git remote -v```

You should see an output that looks similar to this:
<pre><code>origin  https://github.com/Abdi-Isse/CITS3200_17.git (fetch)
origin  https://github.com/Abdi-Isse/CITS3200_17.git (push)
upstream        https://github.com/GREYXXX/CITS3200_17.git (fetch)
upstream        https://github.com/GREYXXX/CITS3200_17.git (push)</code></pre>

Your upstream should be GREYXXX/CITS3200_17.git and your origin should be your forked repo.

It is important to always run the following commands before you start working on making any changes in your local environment:

<pre><code>git fetch upstream
git rebase upstream/master
git push origin master
</code></pre>

The first command will fetch the most up to date version of the upstream repo.
The second command will make sure that your master branch is up to date with the upstream repo.
The third command will push your up to date master branch to your cloned repo on github so that they become the same.

This will help avoid any merge conflicts, which are a pain to fix at times. It will also incorporate any changes that have been added to the main upstream repo into your forked one.

### Branching

The first thing you should do before writing any code is to make sure your local environment is up to date, and to also create a new branch on which to make your changes. Avoid writing code directly from your master branch. To make a new branch run the following command followed by the name you want to give your branch:

```git checkout -b your-new-branch-name```

This command will create a new branch and at the same time move to the new branch. To move between branches use the following command followed by the branch you want to change to:

```git checkout the-branch-name-you-want-to-switch-to```

Once you are done making changes to code and you are happy for it to be added to the codebase, you will need to stage all your changes. This command will stage them:

```git add .```

Once you have staged your changes you will need to commit your changes. To do this run the following command followed by a short description of the changes you have made. For example:

```git commit -m "Added new image classification function"```

Now you are ready to push your changes up to your origin. To do this use the following command followed by the name of the branch you are pushing up to your origin. If you are working on a branch called "classification-tool" then the command would be:

```git push origin classification-tool```

Once you have done this, you should go onto github, go inside of either your forked repo or the upstream repo, and you should see a green button asking you to create a pull request. Once youve made your pull request whoever is designated the git gatekeeper role will review and approve your changes. Once they are approved, click squash and merge to merge your commits into the codebase.

If the git gatekeeper notices that there are any potential bugs or some minor typo or any other bugs, they should leave a comment on the file and line number where that bug is. This way itll be easier for the person who made the changes to fix them up.

The nice thing about pull requests is that if you need to make any changes, you just simply go back into your local environment and make the changes on the branch that you used to create the pull request. This way, once you are done squashing the bugs/typos and you push the same branch back up, the pull request will update with the new changes added. Then just get it reviewed again.

### Running The web app
Make sure you have python 3 installed. If you dont have it you can download it from [python.org](https://www.python.org/downloads/).

Once you have made sure you have python 3 installed, go ahead and download flask using pip.
If you are on a macbook the terminal command would be:

```pip3 install flask```

I think on windows the command would be: 

```python3 -m pip3 install flask```

I have just added a  python file called flaskapp.py which will contain the main function that will run our web app. If you go inside the file you'll see how simple it is to add pages. At the moment there are two pages, but to add more you would simply copy the the example function and write a new app route with the name of the url that you want and dont forget to give your function a different name.

All you need to do to run the web app is to run the flaskapp.py file like you would any other python program.
If you are running the main function with:

```app.run()```

Then anytime you make changes to your code you would have to kill and re run the program. To avoid this run the web app in debug mode, that way in order to see the changes you make you just need to refresh the page. You can do this by using the following in your main:

```app.run(debug=True)```

Just dont forget to change it back to 

```app.run()```

Before you put up a pull request.

### Folder structure

To keep our code nice and clean we need to seperate different files into different folders. We should have a templates folder that will contain all our html files. A static folder will that will contain static files, in other words all our css, images and javascript files. When we add our python scripts we should probably also make a folder for them aswell.

Feel free to update this doc if you think its missing stuff!

Testing out if pr reviews are enabled ....

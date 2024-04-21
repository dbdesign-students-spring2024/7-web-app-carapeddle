# Flask-MongoDB Web App

# Title of App
The title of my app is *PageTurner*.
# Description of App
The app allows users to review books and comment on other users' book reviews. The app requires users to log in before reviewing a book. The user must register an account and then log in. The user can also log out of their account and create a new account. The app is interactive and allows users to edit reviews.
# Link to Deployed Copy of App
https://i6.cims.nyu.edu/~$cep454/$7-web-app-carapeddle

*Could not get app running on i6*.


Here is a copy of the .env file:


MONGO_DBNAME=cep454
MONGO_URI=mongodb://cep454:Yt6CP6he@class-mongodb.cims.nyu.edu:27017/cep454?authSource=cep454&retryWrites=true&w=majority
SENTRY_DSN=https://b5052ab15a33cbbf60f0a3b988ff65d4@o4507087780249600.ingest.us.sentry.io/4507087790473216 # get by registering at https://sentrio.io and configuring new flask project there
FLASK_APP=app.py
FLASK_ENV=development
GITHUB_REPO=https://github.com/your-repository-url # unnecessary for basic operations
GITHUB_SECRET=your_github_secret # unnecessary for basic operations
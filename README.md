# news_chewer

This application reads popular news aggregation sources, then attempts to classify the articles, determine if they meet the application's definition of "hard news". If so, it stores the article link, along with a summary and a headline. It maintains an encyclopedia-like overview of a handful of topics. It has the ability to generate an .html page that lets a user see all current and recent articles. The intent is for the whole system to run locally (with the obvious exception of needing to fetch the articles).

Batteries not included. You'll need:
- Gemma 2 9B, running locally under Ollama
- A set of classified articles, generated from a .csv file called "classifier training material.csv", that is processed by "dense_embed_trainer.py", generating "article_classifier.joblib".
- Obviously, you'll need a system with a GPU with at least 8GB of onboard RAM to run the Gemma model. The classifier itself is dead simple and super fast, so no special requirements there.

Current disappointments:
- The inclusion prompting seems to have hit a quality limit. It does what I expect/intend about 80% of the time. Additional measures like prompt modification, new layers and after analysis, etc. do not improve things. Rather, they just shuffle the failures and introduce additional failure points. So, this is not nearly as good as, say, ME scanning through all of these articles and triaging them.
- The system does not examine or attempt to respect robots.txt. It's acting as an agent on my behalf. The summaries the agent produces are purely for my own consumption. So, next steps here are to alter user-agent strings to properly identify myself to webmasters and leverage individual news source RSS feeds, including summary feeds where possible. If you want to try this system yourself, please consider your own ethical stance on bypassing the intent of robots.txt files for personal consumption before doing so.
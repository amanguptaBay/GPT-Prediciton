# Goal

Replicate Paper: https://arxiv.org/pdf/2306.11025.pdf

Basically they use chat gpt to understand news articles and the company then estimate how the stock price is affected by the news.

# Results

# GPT-3.5 Turbo Some-Shot

57.1% Binary Accuracy
13.14% Bin Error
12.14 MSE Error

### Experiment Description

Utilized example of Amazon performance of the first week as example, and provided the model a summary of the news of the week for Apple and some stock market index tickers.

### Deviations from Paper

Used different news source and not sure how they got macreconomic news.
Used GPT 3.5 instead of GPT-4
MSE Calclation for this and prior experiment incorrect

### Path Forward
Change from using stock market ticker news to actual macroecnomic news, maybe adjust to using their news api. However, google custom search api only allows 100 API calls a day for free which means I either have to pay or wait a while.

Want to implement baseline models using pure time-series data without news based NLP.

# GPT-3.5 Turbo No-Shot

55.0% Binary Accuracy.
8.076% Bin Accuracy.
8.46$ MSE Error
Pretty dismal.

### Deviations from Paper

No inclusion of related summaries or the macro news.
Used GPT 3.5 instead of GPT-4 (cost issue most likely due to coding error not just api cost)

### Steps Forward

Include the related summaries of the macro news.
Include the summaries of similar stocks for the week.


# GPT-4 No-Shot

Didnt run, ended up burning a lot of credits due to a bug, will re-run and give it a try.
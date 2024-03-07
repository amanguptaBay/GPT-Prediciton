# Goal

Replicate Paper: https://arxiv.org/pdf/2306.11025.pdf

Basically they use chat gpt to understand news articles and the company then estimate how the stock price is affected by the news.

# Results

## GPT-3.5 Turbo No-Shot

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

## GPT-4 No-Shot

Didnt run, ended up burning a lot of credits due to a bug, will re-run and give it a try.
# dancer_for_multi_news

1. Install necessary python packages(checkout requirements.txt if needed). We need java 1.8 to run pyspark. 

3. Download multi-news original dataset from [here](https://drive.google.com/drive/folders/1uDarzpu2HFc-vjXNJCRv2NIHzakpSGOw).

4. Reformat the files to have .txt extension.

5. Update the paths in `prep_data_multi_news.py` and run it to format the training set.This will remove the leftover social media text from articles. We treat each article-> summary pair as a input. Each article will contain sections which correspond to news from the raw dataset and corresponding summary. Please see `example_multi_news_formatted.json` as the output of `prep_data_multi_news.py`. This can be extended to validation and test set too.

6. Now, we need to prepare our dataset so that it has the same format with arxiv data before going into dancer. We decided to change the preprocessing part instead of actual dancer code so that we can keep all the features such as scoring and summary mapping in `rouge_match`. Please update the paths accordingly in `prep_to_dancer.py` and run it. The output should be similar to `example_processed.json`. 
What we do in this step is to match which section(news) provides which part of the summary. We don't assign news articles to categories like they do in arxiv cases because we don't have particular sections in news articles. Instead we treat the entire news set beloning to one subject as a whole document by considering each seperate news as a section in a document. Therefore the section names simply correspond to index of the news. On the contrary of arxiv case, we won't filter any news even if they don't contibute to the summary. 

Our contribution can be found in `prep_sentence_selection.py`. This file should be run before to preprocess the dataset and it generates saves the result into another json file. Afterwards, you need to give the path of the processed files into the training script. Then, it is possible to obtain our results.

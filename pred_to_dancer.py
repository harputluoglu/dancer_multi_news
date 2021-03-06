import os
import argparse

import numpy as np
import json

import pyspark
from pyspark.sql import functions as F
from pyspark.sql import types as spark_types

from rouge_score import rouge_scorer


#KEYWORDS = {}


def rouge_targets(abstract_sentences, section_sentences, rg_scorer):
    """
    Given an array of M abstract sentences and an array of N section sentences,
    returns a vector of size M, where at each position m we have the max ROUGE-L score
    between abstract sentence m and all the full text sections.
    """
    #print(len(abstract_sentences))
    #print(len(section_sentences))
    sum_targets = [0] * len(abstract_sentences)

    #print(abstract_sentences)
    #print(section_sentences)
    for j, abs_sent in enumerate(abstract_sentences):
        max_rouge = 0.
        for si, sec_sent in enumerate(section_sentences):
            rouge_score = rg_scorer.score(abs_sent, sec_sent)
            rouge_r = rouge_score['rougeL'][1]
            if rouge_r > max_rouge:
                max_rouge = rouge_r

        sum_targets[j] = max_rouge

    return sum_targets


def rouge_match(scorer):
    """UDF wrapper for rouge_match_"""
    def rouge_match_(cols):
        """
        Given the full text of a section and an array of summary sentences,
        computes the ROUGE-L score of each summary sentence with the section text.
        See the definition of 'rouge_targets' for more details.
        """
        full_section, summary_sents = cols.text_section.sections, cols.summary
        sum_scores = rouge_targets(summary_sents, full_section, scorer)
        
        return sum_scores
    return F.udf(rouge_match_, spark_types.ArrayType(spark_types.FloatType()))


def summary_match(col):
    """
    Given an array with the score arrays of each summary sentence we match
    each summary sentence with the section that has the highest similarity score.
    """
    scores = np.array(col)
    max_idx = np.argmax(scores, axis=0)
    return max_idx.tolist()


def index_array(col):
    """
    Assemble an array of (head, text) tuples into an array of
    {"section_head": head, "section_text": text, "section_idx": i}
    """
    indexed_text = [{"section_head": h, "section_text": t, "section_idx": i} for i, (h, t) in enumerate(col)]
    return indexed_text


def collect_summary(cols):
    """Select the summary sentences that are matched with a given section into an array of sentences"""
    section_idx, matched_summaries = cols.section_idx, cols.matched_summaries
    collected_summary = [t for (t, s_idx) in matched_summaries if s_idx == section_idx]
    return collected_summary


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root",default="", type=str, help="")
    parser.add_argument("--driver_memory", type=str, default="4g", help="")
    parser.add_argument("--partitions", type=int, default=100, help="")

    args, unknown = parser.parse_known_args()
    return args, unknown

#--------------------------------------output file----------------------------------------------#
def write_json(new_data, filename='train.json'):
    
    with open(filename,'r+') as file:
        file_data = json.load(file)
        file_data.append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)
        


def main():
    args, unknown = read_args()

    #------------------------------------input data------------------------------------------#
    train_data = os.path.join(args.data_root, 'multi_news_train_preprocessed.json')
    #val_data = os.path.join(args.data_root, 'val.txt')
    #test_data = os.path.join(args.data_root, 'test.txt')
    #selected_section_types = ["i", "m", "r", "l", "c"]

    metrics = ['rouge1', 'rouge2', 'rougeL']
    scorer = rouge_scorer.RougeScorer(metrics, use_stemmer=True)

    conf = pyspark.SparkConf()
    conf.set('spark.driver.memory', args.driver_memory)
    sc = pyspark.SparkContext(conf=conf)
    spark = pyspark.sql.SparkSession(sc)

    data_prefixes = ['example']
    data_paths = [train_data]
    task_output_dir = os.path.join(args.data_root, "processed")
    if not os.path.exists(task_output_dir):
        os.makedirs(task_output_dir)

    summary_match_udf = F.udf(summary_match, spark_types.ArrayType(spark_types.IntegerType()))
    index_array_udf = F.udf(
        index_array,
        spark_types.ArrayType(
            spark_types.StructType([
                spark_types.StructField(
                    'section_head', spark_types.StringType()),
                spark_types.StructField(
                    'section_text', spark_types.ArrayType(spark_types.StringType())),
                spark_types.StructField(
                    'section_idx', spark_types.IntegerType())])))
    collect_summary_udf = F.udf(
        collect_summary,
        spark_types.ArrayType(spark_types.StringType()))

    for data_path, prefix in zip(data_paths, data_prefixes):
        df = spark.read.json(data_path) \
            .repartition(args.partitions, "article_number")

        df = df.withColumn(
            'zipped_text',
            F.arrays_zip(F.col('section_names'), F.col('sections'))) \
            .withColumn(
            "text_section",
            F.explode("zipped_text")) \
            .withColumn(
            "summary_scores",
            rouge_match(scorer)(F.struct(F.col('text_section'), F.col('summary')))) \
            .groupby(["summary", "article_number"]) \
            .agg(
            F.collect_list("summary_scores").alias("summary_scores"),
            F.collect_list("text_section").alias("full_text_sections")) \
            .withColumn(
            "matched_summaries",
            summary_match_udf("summary_scores")) \
            .withColumn(
            "full_text_sections",
            index_array_udf("full_text_sections")) \
            .withColumn(
            "matched_summaries",
            F.arrays_zip(F.col("summary"), F.col("matched_summaries"))) \
            .select(
            F.explode(F.col("full_text_sections")).alias("full_text_section"),
            F.col("full_text_section").section_head.alias("section_head"),
            F.col("full_text_section").section_idx.alias("section_idx"),
            F.col("matched_summaries"),
            "summary",
            "article_number") \
            .withColumn(
            "section_summary",
            collect_summary_udf(F.struct(F.col("section_idx"), F.col("matched_summaries")))) \
            .withColumn(
            "document",
            F.concat_ws(" ", F.col("full_text_section").section_text)) \
            .withColumn(
            "summary_individual",
            F.concat_ws(" ", F.col("section_summary"))) \
            .withColumn(
            "summary_all",
            F.concat_ws(" ", F.col("summary"))) \
            .withColumn(
            "document_len",
            F.size(F.split(F.col("document"), " "))) \
            .withColumn(
            "summary_len",
            F.size(F.split(F.col("summary_all"), " "))) \
            .where(
            F.col('document_len') > 50) \
            .select(
            "article_number",
            "section_idx",
            "document",
            "summary_individual",
            "summary_all")

            #Put after collect_summary_udf if we want to filter the articles which doesn't contribute to overall summary
            #.where(
            #F.size(F.col("section_summary")) > 0) \
        pandas_df = df.toPandas()
        pandas_df.to_json("xyz_trial_data.json")
        
        
    
        
        
        #df.write.json(
        #    path=os.path.join(task_output_dir, prefix),
        #    mode="overwrite")
        print(f"Finished writing {prefix} split to {task_output_dir}")
        

    #----------------------------------------Output data ------------------------------------#
    json_obj = []
    with open('train.json','w') as jsonFile:
        json.dump(json_obj, jsonFile)
    f = open("xyz_trial_data.json")
    example_data = json.load(f)
    for i in example_data['article_number']:
        y = {"article_number":example_data['article_number'][i],
                "article_idx":example_data['section_idx'][i],
                "article_text":example_data['document'][i],
                "summary":example_data['summary_individual'][i],
                "summary_all":example_data['summary_all'][i]
                }
        json_obj.append(y)
        #print(y)
    write_json(json_obj)


if __name__ == "__main__":
    main()

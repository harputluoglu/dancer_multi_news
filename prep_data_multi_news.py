
import json


def clean(line):

    line = line.strip().replace("newline_char", " ")
    line = line.replace("( opens in new window )", "")
    line = line.replace("click to email this to a friend", "")
    line = line.replace("lick to share on whatsapp", "")
    line = line.replace("click to share on facebook", "")
    line = line.replace("share on facebook", "")
    line = line.replace("click to share on twitter", "")
    line = line.replace("click to share on pinterest", "")
    line = line.replace("click to share on tumblr", "")
    line = line.replace("click to share on google+", "")
    line = line.replace("feel free to share these resources in your social "
                        "media networks , websites and other platforms", "")
    line = line.replace("share share tweet link", "")
    line = line.replace("e-mail article print share", "")
    line = line.replace("read or share this story :", "")
    line = line.replace("share the map view in e-mail by clicking the share "
                        "button and copying the link url .     embed the map "
                        "on your website or blog by getting a snippet of html "
                        "code from the share button .     if you wish to "
                        "provide feedback or comments on the map , or if "
                        "you are aware of map layers or other "
                        "datasets that you would like to see included on our maps , "
                        "please submit them for our evaluation using this this form .", "")
    line = line.replace("share this article share tweet post email", "")
    line = line.replace("skip in skip x embed x share close", "")
    line = line.replace("share tweet pin email", "")
    line = line.replace("share on twitter", "")
    line = line.replace("feel free to weigh-in yourself , via"
                        "the comments section . and while you ’ "
                        "re here , why don ’ t you sign up to "
                        "follow us on twitter us on twitter .", "")
    line = line.replace("follow us on facebook , twitter , instagram and youtube", "")
    line = line.replace("follow us on twitter", "")
    line = line.replace("follow us on facebook", "")
    line = line.replace("play facebook twitter google plus embed", "")
    line = line.replace("play facebook twitter embed", "")
    line = line.replace("enlarge icon pinterest icon close icon", "")
    line = line.replace("follow on twitter", "")
    line = line.replace("autoplay autoplay copy this code to your website or blog", "")
    line = line.replace("NEWLINE_CHAR", " ")
    line = line.replace("\n", "\n-----")
    line = line.replace('\"', '')
    lines = line.split("|||||")
    lines = lines[:-1]
    
    return line, lines




if __name__ == "__main__":
    # Using readlines()
    news_to_read_src = open('train.src.txt', 'r')
    news_to_read_trg = open('train.tgt.txt', 'r')

    news_to_summarize = news_to_read_src.readlines()
    news_summaries = news_to_read_trg.readlines()

    with open('multi_news_train_preprocessed.json', 'w') as json_file:
        for index in range(len(news_to_summarize)):
            news = news_to_summarize[index]
            summary = news_summaries[index]

            json_data = {}
            news, sections = clean(news)
            json_data["article_number"]=index
            json_data["section_names"] = list(range(len(sections)))
            json_data["sections"] = sections
            #json_data["document"] = news

            summary = summary.strip().lstrip("- ")
            json_data["summary"] = summary
            #json_data["abstract_text"] = summary in 

            json_object = json.dumps(json_data, ensure_ascii=False)
            json_file.write(json_object + '\n')


   

import csv
import json
import os
import torch
from transformers import pipeline, RobertaTokenizer
import matplotlib.pyplot as plt
import time

DEVICE = torch.device("cuda")
MODEL_NAME = "SamLowe/roberta-base-go_emotions"
TOKENIZER = RobertaTokenizer.from_pretrained(MODEL_NAME)
CLASSIFIER = pipeline(task="text-classification",
                      model=MODEL_NAME,
                      tokenizer=TOKENIZER,
                      truncation=True,
                      device=DEVICE,
                      top_k=None)


def plot_words_with_correlations(words,
                                 values,
                                 title="Word Correlations",
                                 fontsize=12):
    """
  Plots words with corresponding float values from highest to lowest.

  Args:
    words: List of strings representing the words.
    values: List of floats corresponding to the words.
    title: Optional title for the plot (default: "Word Correlations").
    fontsize: Font size for the words and values (default: 14).

  Returns:
    None

  Raises:
    ValueError: If the lengths of `words` and `values` are not equal.
  """

    if len(words) != len(values):
        raise ValueError("Lengths of words and values must be equal.")

    # Sort words and values together by descending values
    sorted_data = sorted(zip(words, values), key=lambda x: x[1], reverse=True)
    words, values = zip(*sorted_data)

    # Create the plot
    plt.figure(figsize=(14, 6))  # Adjust figure size as needed

    # Plot bars for values
    plt.bar(words, values, color='skyblue',
            align='center')  # Use words directly on x-axis

    # Annotate each bar with value above it
    for i, (word, value) in enumerate(zip(words, values)):
        plt.text(word,
                 value + 0.1,
                 f"{value:.2f}",
                 ha='center',
                 va='top',
                 fontsize=fontsize)

    # Set labels and title
    plt.xlabel("Word")
    plt.ylabel("Correlation Value")
    plt.title(title)

    # Rotate x-axis labels for better readability if needed
    plt.xticks(rotation=45, ha='right')  # uncomment if labels overlap

    # Show the plot
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


# def summarize_text(text: str, max_len: int) -> str:
#     try:
#         summary = CLASSIFIER(text, max_length=max_len)
#         return summary
#     except IndexError as ex:
#         print(
#             "Sequence length too large for model, cutting text in half and calling again"
#         )
#         return summarize_text(text=text[:(len(text) // 2)],
#                               max_len=max_len // 2) + summarize_text(
#                                   text=text[(len(text) // 2):],
#                                   max_len=max_len // 2)


def main():
    start_time = time.perf_counter_ns()

    csv_data = [[
        "Forum Category", "File Name", "Thread URL", "Page", "Timestamp",
        "Message Text", "admiration", "amusement", "anger", "annoyance",
        "approval", "caring", "confusion", "curiosity", "desire",
        "disappointment", "disapproval", "disgust", "embarrassment",
        "excitement", "fear", "gratitude", "grief", "joy", "love",
        "nervousness", "neutral", "optimism", "pride", "realization", "relief",
        "remorse", "sadness", "surprise"
    ]]

    # For each main folder:
    dir_list = os.listdir("JSON")
    print(f"dir_list: '{dir_list}'")
    # For each JSON file:
    for directory in dir_list:
        sub_dir_file_list = os.listdir(f"JSON/{directory}")
        for file_name in sub_dir_file_list:
            if "__ERROR-LOG__" in file_name:
                continue

            # Load JSON
            print(f"file_name: '{file_name}'")
            filepath = f"JSON/{directory}/{file_name}"
            with open(filepath, "r") as file:
                json_data = json.load(file)
            # print(json_data)

            cur_thread_url = json_data["thread_url"]
            print(f"cur_thread_url: '{cur_thread_url}'")
            print()

            # For each "page" in the JSON:
            for cur_page in json_data:
                if cur_page == "thread_url":
                    continue

                # For each sentence in the page:
                for index, cur_post in enumerate(json_data[cur_page]):
                    # print(f"cur_post: '{cur_post}'")
                    cur_message_timestamp = cur_post['timestamp']
                    cur_message_text = cur_post['message_text']
                    # print(f"message_text: '{cur_message_text}'")

                    # Process sentence
                    cur_result_pre_format = CLASSIFIER(
                        f"{cur_message_text}")[0]
                    # print(f"cur_result_pre_format: '{cur_result_pre_format}'")
                    # print(
                    #     f"type(cur_result_pre_format): '{type(cur_result_pre_format)}'"
                    # )

                    cur_result = {}
                    # Convert output to easily referenced JSON.
                    for emotion_element in cur_result_pre_format:
                        cur_result[emotion_element['label']] = emotion_element[
                            'score']

                    # print(f"cur_result: '{cur_result}'")

                    # Append results to JSON obj
                    json_data[cur_page][index]['results'] = cur_result
                    # print(
                    #     f"json_data[cur_page][index]: '{json_data[cur_page][index]}'"
                    # )
                    # print()
                    cur_csv_results = [
                        directory, file_name, cur_thread_url, cur_page,
                        cur_message_timestamp, cur_message_text,
                        cur_result["admiration"], cur_result["amusement"],
                        cur_result["anger"], cur_result["annoyance"],
                        cur_result["approval"], cur_result["caring"],
                        cur_result["confusion"], cur_result["curiosity"],
                        cur_result["desire"], cur_result["disappointment"],
                        cur_result["disapproval"], cur_result["disgust"],
                        cur_result["embarrassment"], cur_result["excitement"],
                        cur_result["fear"], cur_result["gratitude"],
                        cur_result["grief"], cur_result["joy"],
                        cur_result["love"], cur_result["nervousness"],
                        cur_result["neutral"], cur_result["optimism"],
                        cur_result["pride"], cur_result["realization"],
                        cur_result["relief"], cur_result["remorse"],
                        cur_result["sadness"], cur_result["surprise"]
                    ]
                    csv_data.append(cur_csv_results)

            #     print(cur_page)
            #     print()
            #     break
            # break

            try:
                # Write results JSON
                filepath = f"JSON_results/{directory}/{file_name}"
                with open(filepath, "w", encoding="utf-8") as results_file:
                    results_file.write(json.dumps(json_data, indent=4))
            except Exception as e:
                print(f"EXCEPTION: '{e}'")


#         break

    print(f"csv_data: '{csv_data}'")
    try:
        # Open the file in write mode ("w") with newline='' for proper handling
        with open("results.csv", "w", newline='', encoding="utf-8") as f:
            # Create a csv writer object
            csv_writer = csv.writer(f)

            # Write the header row
            csv_writer.writerow(
                csv_data[0])  # This row contains the header names

            # Write remaining data rows
            for row in csv_data[1:]:
                csv_writer.writerow(row)
    except Exception as e:
        print("NOOOOOO!!!!!")
        print(f"EXCEPTION: '{e}'")
        # Open the file in write mode ("w") with newline='' for proper handling
        with open("results.csv", "w", newline='', encoding="utf-8") as f:
            # Create a csv writer object
            csv_writer = csv.writer(f)

            # Write the header row
            csv_writer.writerow(
                csv_data[0][0:5] +
                csv_data[0][6:])  # This row contains the header names

            # Write remaining data rows
            for row in csv_data[1:]:
                csv_writer.writerow(row[0][0:5] + row[0][6:])

    end_time = time.perf_counter_ns()
    elapsed_time_ns = end_time - start_time
    elapsed_time_sec = elapsed_time_ns / (10**9)
    print(f"Elapsed time: {elapsed_time_sec:.6f} seconds")

if __name__ == "__main__":

    main()

    # sentences = [
    #     "I'm feeling overwhelmed with work here. I don't have time for anything else. I fucking hate this workplace.",
    #     "I love this job and I am so happy here. I can't imagine doing anything else with my life. I feel fulfilled.",
    #     "This job is average.",
    # ]
    #
    # model_outputs = CLASSIFIER(sentences)
    # i = 0
    # for sentenceOutput in model_outputs:
    #     print(sentenceOutput)

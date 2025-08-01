from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
import torch



model=pipeline(
    "text2text-generation",
    model="MBZUAI/LaMini-Flan-T5-783M",
    min_length=256,
    max_length=1024,
    truncation=True,
    repetition_penalty=2.5,
    do_sample=True,
    no_repeat_ngram_size=3,
    early_stopping=False
)

llm=HuggingFacePipeline(pipeline=model)


template = PromptTemplate.from_template("Explain {topic} in detail for a {age} year old to understand")

chain=template | llm
topic=input("Enter a topic: ")
age=input("Enter an age: ")

response=chain.invoke({"topic": topic, "age": age})
# Post-processing: trim to last complete sentence
import re
def trim_to_last_sentence(text):
    sentences = re.split(r'([.!?])', text)
    if len(sentences) < 2:
        return text
    trimmed = ''
    for i in range(0, len(sentences)-1, 2):
        trimmed += sentences[i].strip() + sentences[i+1] + ' '
    return trimmed.strip()

if isinstance(response, dict) and 'result' in response:
    output = response['result']
else:
    output = response
print(trim_to_last_sentence(output))

#model = pipeline("summarization", model="facebook/bart-large-cnn")
#response=model("text to summarize")
#print(response)
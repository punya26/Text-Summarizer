# summarizer/views.py

import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from django.http import HttpResponse
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest

# Load the English language model
nlp = spacy.load('en_core_web_sm')

# Define punctuation here, outside the summarize_text function
punctuation = punctuation + '\n'

def summarize_text(text):
    if text.startswith("http://") or text.startswith("https://"):
        # URL input, perform web scraping
        try:
            response = requests.get(text)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get the first heading and all <p> tags
            heading = soup.find('h1')  # Modify as needed for the specific heading tag
            paragraphs = soup.find_all('p')

            # Combine the heading and paragraphs into a single text
            scraped_text = heading.text if heading else ""
            for paragraph in paragraphs:
                scraped_text += " " + paragraph.text

            text = scraped_text  # Use the scraped text for summarization
        except Exception as e:
            return str(e)  # Handle any errors that may occur during web scraping

    # Create a list of stopwords
    stopwords = list(STOP_WORDS)

    # Get a spaCy doc object
    doc = nlp(text)

    # Initialize word frequencies dictionary
    word_frequencies = {}

    # Calculate word frequencies
    for word in doc:
        if word.text.lower() not in stopwords and word.text.lower() not in punctuation:
            if word.text not in word_frequencies.keys():
                word_frequencies[word.text] = 1
            else:
                word_frequencies[word.text] += 1

    # Normalize word frequencies
    max_frequency = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word] / max_frequency

    # Tokenize the text into sentences
    sentence_tokens = [sent for sent in doc.sents]

    # Calculate sentence scores
    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]

    # Calculate the target summary length based on the 1:10 ratio
    target_summary_length = len(text.split()) // 10

    # Select sentences for the summary until the target length is reached
    summary = []
    summary_length = 0
    for sent in sentence_tokens:
        if summary_length + len(sent.text.split()) <= target_summary_length:
            summary.append(sent)
            summary_length += len(sent.text.split())
        else:
            break

    # Convert the summary sentences to a string
    final_summary = [sent.text for sent in summary]
    summary = ' '.join(final_summary)

    return summary

def index(request):
    if request.method == 'POST':
        input_type = request.POST.get('input-type', 'text')  # Get the input type (text or url)
        input_data = request.POST.get('input', '')

        if input_data:
            if input_type == 'url':
                # If the input type is a URL, use it directly
                text = input_data
            elif input_type == 'text':
                # If the input type is text, use it as is
                text = input_data
            else:
                # Handle unsupported input types here
                text = ''

            summary = summarize_text(text)
            return render(request, 'summarizer/index.html', {'text': input_data, 'summary': summary, 'input_type': input_type})

    return render(request, 'summarizer/index.html', {'text': '', 'summary': '', 'input_type': 'text'})

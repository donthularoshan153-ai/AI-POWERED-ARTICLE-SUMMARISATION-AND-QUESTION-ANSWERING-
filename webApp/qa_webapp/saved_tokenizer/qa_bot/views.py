from django.shortcuts import render
from django.http import JsonResponse
from .forms import InputForm  # Ensure this import is correct
from .utils import load_model, answer_question
import PyPDF2
import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk

# Ensure NLTK tokenizer is available
nltk.download('punkt')

# Load model once to avoid reloading with each request
MODEL = load_model()


def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def extract_text_from_url(link):
    """Extract text from a webpage."""
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text().strip()
    except requests.RequestException as e:
        return f"Error fetching URL: {str(e)}"


def generate_summary(content, sentence_count=5):
    """Generate a summary of the given content."""
    if not content or len(content.split()) < 10:
        return "Content is too short for summarization."
    
    try:
        parser = PlaintextParser.from_string(content, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        
        # Print summary to terminal for debugging
        print("\n--- Generated Summary ---")
        print(summary)
        print("-------------------------\n")
        
        return " ".join(str(sentence) for sentence in summary)
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def home(request):
    """Handle homepage and form submission."""
    context = {}
    if request.method == 'POST':
        form = InputForm(request.POST, request.FILES)
        if form.is_valid():
            text = form.cleaned_data['text']
            link = form.cleaned_data['link']
            pdf = request.FILES.get('pdf')

            # Extract content based on input type
            if pdf:
                content = extract_text_from_pdf(pdf)
            elif link:
                content = extract_text_from_url(link)
            else:
                content = text or "No content provided."

            # Generate summary of the content
            summary = generate_summary(content, sentence_count=5)

            # Save content and summary to session for future chat interactions
            request.session['content'] = content
            request.session['summary'] = summary
            request.session['chat_history'] = [{'question': None, 'answer': summary}]  # Initialize chat history

            return render(request, 'qa_bot/chat.html', {'chat_history': request.session['chat_history']})

    else:
        form = InputForm()

    context['form'] = form
    return render(request, 'qa_bot/home.html', context)


def chat(request):
    """Handle chat page and provide AI-generated answers."""
    if request.method == 'POST':
        question = request.POST.get('question')
        content = request.session.get('content', '')

        if not content:
            return JsonResponse({'answer': 'No content available. Please upload content first.'})

        # Get model and generate an answer
        answer = answer_question(MODEL, content, question)

        # Manage chat history in session
        chat_history = request.session.get('chat_history', [])

        # Append user question and bot answer
        chat_history.append({'question': question, 'answer': answer})
        request.session['chat_history'] = chat_history[-20:]  # Limit to 20 recent chats

        return JsonResponse({'answer': answer})

    # Retrieve chat history
    chat_history = request.session.get('chat_history', [])

    return render(request, 'qa_bot/chat.html', {'chat_history': chat_history})

import emoji
import re
#from nltk.corpus import stopwords
import string
#from nltk.tokenize import word_tokenize

#stop_words = set(stopwords.words('english'))
url_pattern = re.compile(r'https?://\S+|www\.\S+')
non_ascii_pattern = re.compile(r"[^\x00-\x7F]")

lemmatizer = None
wordnet_map = None
pos_tag = None
wordnet = None
def lemmatize_words(text):
    global lemmatizer, wordnet_map, pos_tag, wordnet
    if lemmatizer is None:
        from nltk.stem import WordNetLemmatizer
        from nltk.corpus import wordnet as wn
        from nltk import pos_tag as ps
        pos_tag = ps
        wordnet = wn
        lemmatizer = WordNetLemmatizer()
        wordnet_map = {"N":wordnet.NOUN, "V":wordnet.VERB, "J":wordnet.ADJ, "R":wordnet.ADV}
    pos_tagged_text = pos_tag(text.split())
    return " ".join([lemmatizer.lemmatize(word, wordnet_map.get(pos[0], wordnet.NOUN)) for word, pos in pos_tagged_text])

translation_table = str.maketrans({
    "\u2019": "'",  # ’
    "\u0060": '"',  # `
    "\u201D": '"',  # ”
    "\u201C": '"'   # “
})
def preprocess_text(text):
    # If you want multi-label support, join all labels with spaces
    # e.g., "__label__2 __label__3 text"
    text = text.lower()
    text = text.replace("[name]", 'nnnaaammmeee')
    text = text.translate(translation_table)
    text = url_pattern.sub(r'', text)
    text = lemmatize_words(text)
    text = (
        re.sub(
            r"([!\"#$%&\()*+,-./:;<=>?@\[\\\]^_{|}~`])",
            r" \1 ", text)  # Add spaces around specific punctuation characters
        .lower()  # Convert to lowercase
        .strip()  # Remove leading and trailing spaces
        .replace("  ", " ")  # Replace double spaces with a single space
        .replace("  ", " ")  # Ensure spaces are clean
        .replace("'", "")  # ignore single quote
        .replace("", "")  # ignore single quote
    )
    text = "".join([f" {char} " if non_ascii_pattern.match(char) else char for char in text])  # Add spaces around non-ASCII characters
    #words = word_tokenize(text)
    #filtered_txt = [
    #    word
    #    for word in words if
    #    #word.lower() not in stop_words and
    #    word not in string.punctuation
    ##]
    #text = ' '.join(filtered_txt)
    text = text.replace('\n', ' ')
    text = emoji.demojize(text)
    return text

if __name__ == "__main__":
    while True:
        val = input("some text to preprocess\n")
        print(preprocess_text(val))

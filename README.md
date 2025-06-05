# BinaryRetriever

Document Search Engine with Binary Model. A web application implementing classical binary model information retrieval with Flask backend and web interface.

![image](https://github.com/user-attachments/assets/6d288f76-a5cd-46fd-b741-5df2e3369c35)

## ✨ Features

- **Binary Retrieval Model**: Implements the classic binary (Boolean) IR model
- **Efficient Indexing**: Uses inverted index with MAP/REDUCE processing
- **Natural Language Processing**:
  - Spanish stopwords removal
  - Text normalization and tokenization
- **Ranked Results**: Documents ranked by query term frequency

## 📂 Document Collection

- Curated set of 20 documents in Spanish
- Supports `.txt` file format

## 🔍 Search Capabilities

- Boolean AND search (all terms must match)
- Case-insensitive matching
- Stopword filtering (Spanish)
- Punctuation handling
- Relevance scoring based on:
  - Term presence (binary)
  - Term frequency in document

## 🏗️ System Architecture

### Backend Components

- **Flask** web server
- **Search Engine Core**:
  - Document processor
  - Inverted index builder
  - Query processor
  - Ranking algorithm

### Frontend Components

- **Search Interface**
- **Results Display**

## 📜 License

[MIT License](LICENSE) - Free for educational and research use

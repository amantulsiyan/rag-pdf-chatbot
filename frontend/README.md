# Frontend Setup

## Features

✨ **Modern UI/UX**
- Gradient background with smooth animations
- Responsive design
- Real-time chat interface
- Confidence score visualization
- Loading states and error handling

🎨 **Enhanced Components**
- PDF upload with drag-and-drop feel
- Animated progress indicators
- Color-coded confidence badges (High/Medium/Low)
- Source chunk counter
- Smooth message animations

## How to Run

1. **Start the FastAPI backend:**
   ```bash
   cd "c:\Users\USER\Desktop\Engineering\ML Projects\RAG PDF Chatbot"
   uvicorn api.main:app --reload
   ```

2. **Open the frontend:**
   - Simply open `frontend/index.html` in your browser
   - Or use a local server:
     ```bash
     cd frontend
     python -m http.server 8080
     ```
   - Then visit: `http://localhost:8080`

## Usage Flow

1. **Upload PDF** → Click "Choose PDF File" and select your document
2. **Wait for Indexing** → System processes and chunks the document
3. **Ask Questions** → Type your question and press Enter or click send
4. **View Results** → See answers with confidence scores and source references

## API Endpoints Used

- `POST /upload_pdf` - Upload and index PDF document
- `POST /ask_query` - Query the indexed document

## Confidence Levels

- 🟢 **High (70%+)** - Strong evidence from retrieved chunks
- 🟡 **Medium (40-70%)** - Moderate confidence
- 🔴 **Low (<40%)** - Weak evidence or uncertain answer

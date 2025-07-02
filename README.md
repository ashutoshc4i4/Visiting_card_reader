# 📇 Visiting Card Scanner

A modern web application that uses AI (Google Gemini) to automatically extract details from visiting card images and store them in MongoDB.

## ✨ Features

- **Drag & Drop Upload**: Easy file upload with drag-and-drop functionality
- **AI-Powered Extraction**: Uses Google Gemini API to extract card details
- **MongoDB Storage**: Automatically saves extracted information to database
- **Modern UI**: Beautiful, responsive design with real-time feedback
- **Card History**: View all previously scanned cards
- **Multiple Formats**: Supports JPG, JPEG, and PNG image formats

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** installed on your system
2. **MongoDB** running on localhost:27017
3. **Google Gemini API Key** (already configured in the code)

### Installation

1. **Clone or download** this project to your local machine

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Start MongoDB** (if not already running):

   ```bash
   # On Windows
   mongod

   # On macOS/Linux
   sudo systemctl start mongod
   ```

4. **Run the application**:

   ```bash
   python back.py
   ```

5. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```

## 📋 How to Use

1. **Upload a Card**:

   - Drag and drop a visiting card image onto the upload area
   - Or click the upload area to browse and select a file

2. **Wait for Processing**:

   - The AI will analyze the image and extract details
   - You'll see a loading spinner during processing

3. **View Results**:

   - Extracted details will be displayed in a clean format
   - Information is automatically saved to MongoDB

4. **Browse History**:
   - View all previously scanned cards
   - Click "Refresh Cards" to update the list

## 🗄️ Database Structure

The application uses MongoDB with the following structure:

- **Database**: `visiting_card`
- **Collection**: `cards`

Each card document contains:

```json
{
  "name": "Full name of the person",
  "company": "Company name",
  "designation": "Job title/position",
  "email": "Email address",
  "phone": "Phone number",
  "address": "Address",
  "website": "Website URL",
  "additional_info": "Any other relevant information",
  "uploaded_at": "Timestamp",
  "original_filename": "Original file name"
}
```

## 🔧 Configuration

### MongoDB Connection

The application connects to MongoDB at `localhost:27017`. If you need to change this:

1. Edit `back.py`
2. Update the `MONGO_URI` variable:
   ```python
   MONGO_URI = 'mongodb://your-mongodb-host:port/'
   ```

### Gemini API Key

The API key is already configured in the code. If you need to use your own:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update the `GEMINI_API_KEY` variable in `back.py`

## 📁 Project Structure

```
Scanner/
├── back.py              # Flask backend server
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── templates/
│   └── index.html      # Frontend HTML/CSS/JS
└── uploads/            # Temporary upload folder (auto-created)
```

## 🛠️ API Endpoints

- `GET /` - Main application page
- `POST /upload` - Upload and process visiting card image
- `GET /cards` - Retrieve all stored cards

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**:

   - Ensure MongoDB is running on localhost:27017
   - Check if the MongoDB service is started

2. **Upload Fails**:

   - Verify the image format (JPG, JPEG, PNG only)
   - Check file size (should be reasonable for web upload)

3. **AI Extraction Fails**:
   - Ensure the image is clear and readable
   - Check if the Gemini API key is valid
   - Verify internet connection for API calls

### Error Messages

- **"No file part"**: No file was selected for upload
- **"Invalid file type"**: File format not supported
- **"API request failed"**: Gemini API connection issue
- **"No JSON found in response"**: AI couldn't extract structured data

## 🔒 Security Notes

- The application runs in debug mode for development
- File uploads are temporarily stored and automatically cleaned up
- API keys are hardcoded for simplicity (consider environment variables for production)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Happy Scanning! 🎉**
